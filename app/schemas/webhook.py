from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.ticket import TicketResponse

class TicketIngestRequest(BaseModel):
    sender_email: EmailStr
    subject: str
    body: str
    priority: Optional[str] = "medium"

class TicketIngestResponse(BaseModel):
    ticket: TicketResponse
    job_id: Optional[str] = None
