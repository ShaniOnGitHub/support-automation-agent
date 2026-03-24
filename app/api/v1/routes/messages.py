from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.services import message_service

router = APIRouter()


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    workspace_id: int,
    ticket_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return message_service.create_message(
        db, workspace_id, ticket_id, current_user.id, message.body
    )


@router.get("/", response_model=List[MessageResponse])
def list_messages(
    workspace_id: int,
    ticket_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return message_service.list_messages(
        db, workspace_id, ticket_id, current_user.id, skip, limit
    )
