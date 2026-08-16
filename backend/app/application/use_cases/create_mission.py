from app.application.ports.event_publisher import EventPublisher
from app.application.ports.mission_repository import MissionRepository
from app.domain.mission import Mission, Priority

class InvalidMissionDataError(Exception):
    pass

class CreateMission:
    def __init__(self, repository: MissionRepository, publisher: EventPublisher):
        self._repository = repository
        self._publisher = publisher
        
    def execute(self, name: str, priority: str) -> Mission:
        
        if not name or len(name) < 2 or len(name) > 100:
            raise InvalidMissionDataError("Name must be between 2 and 100 characters")
        
        try:
            priority_enum = Priority(priority)
        except ValueError:
            raise InvalidMissionDataError(f"Invalid priority: {priority}")
        
        mission = Mission(name=name, priority=priority_enum)
        self._repository.save(mission)
        
        try:
            self._publisher.publish("missions", {
                "event_type": "mission.created",
                "mission_id": mission.id,
                "name": mission.name,
                "priority": mission.priority.value,
                "status": mission.status.value,
                "created_at": mission.created_at.isoformat(),
            })
        except Exception:
            pass
        
        return mission