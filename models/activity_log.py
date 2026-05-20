from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ActivityLog:
    id: Optional[int]
    board_id: int
    user_id: int
    entity_type: str
    entity_id: Optional[int]
    entity_name: Optional[str]
    action: str
    meta: Optional[str] = None
    created_at: Optional[datetime] = None
