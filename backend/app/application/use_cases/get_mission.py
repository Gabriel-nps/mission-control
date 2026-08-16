from app.application.ports.mission_repository import MissionRepository
from app.domain.mission import Mission


class MissionNotFoundError(Exception):
    pass


class GetMission:
    def __init__(self, repository: MissionRepository):
        self._repository = repository

    def execute(self, mission_id: str) -> Mission:
        mission = self._repository.get_by_id(mission_id)
        if mission is None:
            raise MissionNotFoundError(f"Mission {mission_id} not found")
        return mission
