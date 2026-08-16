import json
import logging
from typing import Any

from confluent_kafka import Producer

logger = logging.getLogger(__name__)

class KafkaEventPublisher:
    def __init__(self, bootstrap_servers: str):
        self._producer = Producer({"bootstrap.servers": bootstrap_servers})
        
    def publish(self, topic: str, event: dict[str, Any]) -> None:
        try:
            message = json.dumps(event, default=str)
            self._producer.produce(topic, value=message.encode("utf-8"))
            self._producer.flush()
        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")    
            raise