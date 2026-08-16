import threading
from typing import Optional

from app.domain.mission import Mission

class InMemoryMissionRepository:
    def __init__(self):
        self._missions: dict[str, Mission] = {}
        self._lock = threading.Lock()
        
    def save(self, mission: Mission) -> None:
        with self._lock:
            self._missions[mission.id] = mission

    def get_by_id(self, mission_id: str) -> Optional[Mission]:
        with self._lock:
            return self._missions.get(mission_id)
        
    def list_all(self) -> list[Mission]:
        with self._lock:
            return list(self._missions.values())
        
    def update(self, mission: Mission) -> None:
        with self._lock:
            self._missions[mission.id] = mission