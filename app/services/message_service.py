from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.message import Message
from app.models.ticket import Ticket
from app.services.workspace_service import check_workspace_membership


def _get_ticket_or_404(db: Session, ticket_id: int, workspace_id: int) -> Ticket:
    """Return the ticket or raise 404."""
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.workspace_id == workspace_id,
    ).first()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def create_message(
    db: Session,
    workspace_id: int,
    ticket_id: int,
    user_id: int,
    body: str,
) -> Message:
    """Check membership, verify ticket exists, create message + audit log."""
    check_workspace_membership(db, user_id, workspace_id)
    ticket = _get_ticket_or_404(db, ticket_id, workspace_id)

    db_message = Message(
        body=body,
        ticket_id=ticket.id,
        sender_user_id=user_id,
    )
    db.add(db_message)
    db.flush()  # get db_message.id before commit

    audit = AuditLog(
        event_type="message_created",
        entity_type="message",
        entity_id=db_message.id,
        workspace_id=workspace_id,
        actor_user_id=user_id,
        detail=f"Message on ticket #{ticket.id}",
    )
    db.add(audit)
    db.commit()
    db.refresh(db_message)
    return db_message


def list_messages(
    db: Session,
    workspace_id: int,
    ticket_id: int,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> List[Message]:
    """Check membership, verify ticket exists, return messages."""
    check_workspace_membership(db, user_id, workspace_id)
    _get_ticket_or_404(db, ticket_id, workspace_id)

    return (
        db.query(Message)
        .filter(Message.ticket_id == ticket_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
