from typing import Optional, Protocol

from app.domain.mission import Mission

class MissionRepository(Protocol):
    def save(self, mission: Mission) -> None:
        ...
    def get_by_id(self, mission_id: str) -> Optional[Mission]:
        ...
    def list_all(self) -> list[Mission]:
        ...
    def update(self, mission: Mission) -> None:
        ...
    
    