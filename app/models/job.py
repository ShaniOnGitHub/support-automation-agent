import enum
import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum, JSON

from app.core.database import Base


class JobStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Job(Base):
    """
    📚 Method: Database-backed Queue
    Tracks asynchronous execution of slow tasks (like AI processing).
    """
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True) # UUID
    name = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.pending, nullable=False)
    error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
