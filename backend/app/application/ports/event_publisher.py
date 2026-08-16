from typing import Any, Protocol

class EventPublisher(Protocol):
    def publish(self, topic: str, event: dict[str, Any]) -> None:
        ...
