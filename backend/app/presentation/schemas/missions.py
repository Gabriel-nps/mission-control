from datetime import datetime
from pydantic import BaseModel, Field

class MissionCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    priority: str
    
class MissionResponse(BaseModel):
    id: str
    name: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime