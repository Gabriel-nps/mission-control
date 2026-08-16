from datetime import datetime
from pydantic import BaseModel

class MissionCreatedEvent(BaseModel):
    mission_id: str
    name: str
    priority: str
    status: str
    created_at: datetime
    
class MissionStatusEvent(BaseModel):
    mission_id: str
    status: str
    updated_at: datetime
    