from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MessageCreate(BaseModel):
    body: str


class MessageResponse(BaseModel):
    id: int
    body: str
    ticket_id: int
    sender_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
