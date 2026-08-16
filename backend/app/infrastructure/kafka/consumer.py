import json
import logging
import threading
from typing import Any

from confluent_kafka import Consumer, KafkaError

from app.domain.mission import Status, InvalidTransitionError
from app.application.ports.mission_repository import MissionRepository

logger = logging.getLogger(__name__)

class KafkaStatusConsumer:
    def __init__(self, bootstrap_servers: str, repository: MissionRepository):
        self._repository = repository
        self._consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": "api-status-consumer",
            "auto.offset.reset": "earliest",
            })
        self._running = False
        self._thread: threading.Thread | None = None
        
    def start(self) -> None:
        self._running = True
        self._consumer.subscribe(["mission-status"])    
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()
        
    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._consumer.close()
    
    def _consume_loop(self) -> None:
        while self._running:
            msg = self._consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error(f"Consumer error: ${msg.error()}")
                continue
            self._process_message(msg)
            
    def _process_message(self, msg: Any) -> None:
        try:
            event = json.loads(msg.value().decode("utf-8"))
            mission_id = event.get("mission_id")
            status_str = event.get("status")

            if not mission_id or not status_str:
                return

            mission = self._repository.get_by_id(mission_id)
            if mission is None:
                return  # Descarta silenciosamente

            target_status = Status(status_str)
            mission.transition_to(target_status)
            self._repository.update(mission)

        except (json.JSONDecodeError, ValueError, InvalidTransitionError) as e:
            logger.warning(f"Discarding invalid status event: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing status event: {e}")

