import uuid

from datetime import datetime, timezone
from enum import Enum

class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    
class Status(str, Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    
VALID_TRANSITIONS: dict[Status, list[Status]] = {
    Status.CREATED: [Status.PROCESSING, Status.FAILED],
    Status.PROCESSING: [Status.COMPLETED, Status.FAILED],
    Status.COMPLETED: [],
    Status.FAILED: [],
}

class InvalidTransitionError(Exception):
    def __init__(self, current: Status, target: Status):
        super().__init__(f"Cannot transition from {current.value} to {target.value}")
        self.current = current
        self.target = target


class Mission:
    def __init__(self, name: str, priority: Priority):
        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.priority: Priority = priority
        self.status: Status = Status.CREATED
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = self.created_at
        
    def transition_to(self, target: Status) -> None:
        if target not in VALID_TRANSITIONS[self.status]:
            raise InvalidTransitionError(self.status, target)
        self.status = target
        self.updated_at = datetime.now(timezone.utc)