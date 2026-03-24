from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from app.models.job import JobStatus

class JobResponse(BaseModel):
    id: str
    name: str
    status: JobStatus
    payload: dict[str, Any]
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
