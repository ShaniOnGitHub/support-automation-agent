"""
Workspace management routes.

📚 Method: Nested resource routing
Members are nested under workspaces: /workspaces/{id}/members
This follows REST convention — members *belong to* a workspace, so they live
under that resource in the URL hierarchy. The workspace_id comes from the
path, not the request body, which avoids inconsistency bugs.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    AddMemberRequest,
    MemberResponse,
)
from app.services import workspace_service
from app.schemas.audit_log import AuditLogResponse

router = APIRouter()


@router.get("/", response_model=List[WorkspaceResponse])
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List all workspaces where the current user is a member."""
    return workspace_service.list_workspaces(db, current_user.id)


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    body: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create a workspace. The caller becomes its first admin member."""
    return workspace_service.create_workspace(db, owner_id=current_user.id, name=body.name)


@router.get("/{workspace_id}/members", response_model=List[MemberResponse])
def list_members(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List all members. Any member can call this."""
    return workspace_service.list_members(db, workspace_id, current_user.id)


@router.post(
    "/{workspace_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    workspace_id: int,
    body: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Add or update a member's role. Admin only."""
    return workspace_service.add_member(
        db, workspace_id, current_user.id, body.user_id, body.role
    )


@router.delete("/{workspace_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    workspace_id: int,
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Remove a member. Admin only. Admins cannot remove themselves."""
    workspace_service.remove_member(db, workspace_id, current_user.id, target_user_id)


@router.get("/{workspace_id}/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(
    workspace_id: int,
    skip: int = 0,
    limit: int = 100,
    event_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List audit logs for a workspace. Admin only."""
    return workspace_service.get_audit_logs(
        db, workspace_id, current_user.id, skip, limit, event_type
    )
