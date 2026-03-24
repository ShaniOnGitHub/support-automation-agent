from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AuditLogResponse(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: int
    workspace_id: int
    actor_user_id: int
    detail: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
