import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    # e.g. "ticket_created", "message_created"
    event_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)  # "ticket" or "message"
    entity_id = Column(Integer, nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
