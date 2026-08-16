"""Integration tests for the Kafka flow (offline, using in-memory fakes).

Covers:
- KafkaEventPublisher publishes to the correct topic (Req 6.6, 2.4)
- Worker connects with the "mission-workers" consumer group (Req 5.1)
- Full mission lifecycle: created -> processing -> completed (Req 5.2, 5.3)
"""
from __future__ import annotations

import json

import pytest

import worker.main as worker_main
from app.application.use_cases.create_mission import CreateMission
from app.domain.mission import Status
from app.infrastructure.kafka import consumer as consumer_module
from app.infrastructure.kafka import producer as producer_module
from app.infrastructure.kafka.consumer import KafkaStatusConsumer
from app.infrastructure.kafka.producer import KafkaEventPublisher
from app.infrastructure.repositories.in_memory_mission_repository import (
    InMemoryMissionRepository,
)
from tests.integration.fakes import FakeBroker, FakeConsumer, FakeMessage, FakeProducer


@pytest.fixture
def broker() -> FakeBroker:
    return FakeBroker()


@pytest.fixture
def publisher(broker: FakeBroker, monkeypatch: pytest.MonkeyPatch) -> KafkaEventPublisher:
    monkeypatch.setattr(
        producer_module, "Producer", lambda config: FakeProducer(config, broker)
    )
    return KafkaEventPublisher(bootstrap_servers="localhost:9092")


def _status_consumer(
    repository: InMemoryMissionRepository, monkeypatch: pytest.MonkeyPatch
) -> KafkaStatusConsumer:
    monkeypatch.setattr(consumer_module, "Consumer", lambda config: FakeConsumer(config))
    return KafkaStatusConsumer(
        bootstrap_servers="localhost:9092", repository=repository
    )


# --- KafkaEventPublisher: correct topic (Req 6.6) ---------------------------


def test_kafka_publisher_publishes_to_requested_topic(
    publisher: KafkaEventPublisher, broker: FakeBroker
) -> None:
    publisher.publish("missions", {"event_type": "mission.created", "mission_id": "abc"})

    assert broker.messages("mission-status") == []
    published = broker.messages("missions")
    assert len(published) == 1
    assert json.loads(published[0].decode("utf-8")) == {
        "event_type": "mission.created",
        "mission_id": "abc",
    }


def test_create_mission_publishes_mission_created_to_missions_topic(
    publisher: KafkaEventPublisher, broker: FakeBroker
) -> None:
    repository = InMemoryMissionRepository()
    use_case = CreateMission(repository=repository, publisher=publisher)

    mission = use_case.execute(name="Apollo", priority="HIGH")

    events = [json.loads(m.decode("utf-8")) for m in broker.messages("missions")]
    assert len(events) == 1
    assert events[0]["event_type"] == "mission.created"
    assert events[0]["mission_id"] == mission.id
    assert events[0]["name"] == "Apollo"
    assert events[0]["priority"] == "HIGH"


# --- Worker consumer group (Req 5.1) ---------------------------------------


def test_worker_consumer_uses_mission_workers_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(worker_main, "Consumer", lambda config: FakeConsumer(config))

    consumer = worker_main.create_consumer()

    assert consumer.config["group.id"] == "mission-workers"
    assert consumer.config["bootstrap.servers"] == worker_main.KAFKA_BOOTSTRAP_SERVERS


def test_worker_subscribes_to_missions_topic(
    broker: FakeBroker, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_consumer = FakeConsumer({}, messages=[])
    monkeypatch.setattr(worker_main, "Consumer", lambda config: fake_consumer)
    monkeypatch.setattr(
        worker_main, "Producer", lambda config: FakeProducer(config, broker)
    )

    worker_main.main()

    assert fake_consumer.subscribed_topics == ["missions"]
    assert fake_consumer.closed is True


# --- Full lifecycle (Req 5.2, 5.3) -----------------------------------------


def test_full_mission_lifecycle_created_processing_completed(
    publisher: KafkaEventPublisher,
    broker: FakeBroker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = InMemoryMissionRepository()

    # 1. API creates the mission and publishes mission.created to "missions".
    mission = CreateMission(repository=repository, publisher=publisher).execute(
        name="Artemis", priority="MEDIUM"
    )
    assert repository.get_by_id(mission.id).status is Status.CREATED

    created_messages = broker.messages("missions")
    assert len(created_messages) == 1

    # 2. Worker consumes mission.created and emits the status events.
    sleeps: list[float] = []
    monkeypatch.setattr(worker_main.time, "sleep", lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr(
        worker_main,
        "Consumer",
        lambda config: FakeConsumer(
            config, messages=[FakeMessage(created_messages[0])]
        ),
    )
    monkeypatch.setattr(
        worker_main, "Producer", lambda config: FakeProducer(config, broker)
    )

    worker_main.main()

    # 2-second delay before PROCESSING, 3-second delay before COMPLETED.
    assert sleeps == [2, 3]

    status_events = [
        json.loads(m.decode("utf-8")) for m in broker.messages("mission-status")
    ]
    assert [e["status"] for e in status_events] == ["PROCESSING", "COMPLETED"]
    assert all(e["mission_id"] == mission.id for e in status_events)

    # 3. API status consumer applies both events to the repository.
    status_consumer = _status_consumer(repository, monkeypatch)

    status_consumer._process_message(FakeMessage(broker.messages("mission-status")[0]))
    assert repository.get_by_id(mission.id).status is Status.PROCESSING

    status_consumer._process_message(FakeMessage(broker.messages("mission-status")[1]))
    assert repository.get_by_id(mission.id).status is Status.COMPLETED
