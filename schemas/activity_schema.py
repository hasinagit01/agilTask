from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ActorResponse(BaseModel):
    id: int
    email: str
    firstname: Optional[str] = None
    name: Optional[str] = None


class ActivityLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    action: str
    meta: Optional[str] = None
    created_at: datetime
    actor: ActorResponse


class ActivityListResponse(BaseModel):
    data: List[ActivityLogResponse]
