from app.application.ports.mission_repository import MissionRepository
from app.domain.mission import Mission


class ListMissions:
    def __init__(self, repository: MissionRepository):
        self._repository = repository

    def execute(self) -> list[Mission]:
        return self._repository.list_all()
