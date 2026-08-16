import json
import logging
import os
import time

from confluent_kafka import Consumer, Producer, KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
CONSUME_TOPIC = "missions"
STATUS_TOPIC = "mission-status"


def create_consumer() -> Consumer:
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "mission-workers",
        "auto.offset.reset": "earliest",
    })


def create_producer() -> Producer:
    return Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})


def publish_status(producer: Producer, mission_id: str, status: str) -> None:
    event = json.dumps({
        "mission_id": mission_id,
        "status": status,
    })
    producer.produce(STATUS_TOPIC, value=event.encode("utf-8"))
    producer.flush()


def process_event(event: dict, producer: Producer) -> None:
    mission_id = event.get("mission_id")
    event_type = event.get("event_type")

    if not mission_id or event_type != "mission.created":
        logger.warning(f"Ignoring event: {event}")
        return

    logger.info(f"Processing mission {mission_id}")

    time.sleep(2)
    publish_status(producer, mission_id, "PROCESSING")
    logger.info(f"Mission {mission_id} → PROCESSING")

    time.sleep(3)
    publish_status(producer, mission_id, "COMPLETED")
    logger.info(f"Mission {mission_id} → COMPLETED")


def main() -> None:
    consumer = create_consumer()
    producer = create_producer()
    consumer.subscribe([CONSUME_TOPIC])

    logger.info(f"Worker started. Consuming from '{CONSUME_TOPIC}'...")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error(f"Consumer error: {msg.error()}")
                continue

            try:
                event = json.loads(msg.value().decode("utf-8"))
                process_event(event, producer)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Discarding malformed event: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")

    except KeyboardInterrupt:
        logger.info("Worker shutting down...")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
