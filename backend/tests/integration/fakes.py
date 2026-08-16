"""In-memory doubles for confluent-kafka Producer/Consumer.

These fakes let integration tests exercise the real publisher, worker and
status-consumer code paths without a running Kafka broker.
"""
from __future__ import annotations

from typing import Any, Optional


class FakeBroker:
    """Minimal topic-based message store shared by fake producers/consumers."""

    def __init__(self) -> None:
        self.topics: dict[str, list[bytes]] = {}

    def append(self, topic: str, value: bytes) -> None:
        self.topics.setdefault(topic, []).append(value)

    def messages(self, topic: str) -> list[bytes]:
        return list(self.topics.get(topic, []))


class FakeMessage:
    """Mimics confluent_kafka.Message for the subset used by the code."""

    def __init__(self, value: bytes, error: Any = None) -> None:
        self._value = value
        self._error = error

    def value(self) -> bytes:
        return self._value

    def error(self) -> Any:
        return self._error


class FakeProducer:
    """Records produced messages into a FakeBroker."""

    def __init__(self, config: dict[str, Any], broker: FakeBroker) -> None:
        self.config = config
        self.broker = broker
        self.flush_count = 0

    def produce(self, topic: str, value: bytes | None = None, **_: Any) -> None:
        self.broker.append(topic, value)

    def flush(self, *_: Any, **__: Any) -> int:
        self.flush_count += 1
        return 0


class FakeConsumer:
    """Serves a scripted list of messages, then signals shutdown."""

    def __init__(
        self,
        config: dict[str, Any],
        messages: Optional[list[FakeMessage]] = None,
    ) -> None:
        self.config = config
        self.subscribed_topics: list[str] = []
        self.closed = False
        self._pending: list[Optional[FakeMessage]] = list(messages or [])

    def subscribe(self, topics: list[str]) -> None:
        self.subscribed_topics = list(topics)

    def poll(self, timeout: float = 1.0) -> Optional[FakeMessage]:
        if self._pending:
            return self._pending.pop(0)
        # Nothing left to deliver: unblock the consume loop like a Ctrl-C would.
        raise KeyboardInterrupt

    def close(self) -> None:
        self.closed = True
