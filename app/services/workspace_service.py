from typing import List, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.workspace import Workspace, WorkspaceMember


def check_workspace_membership(db: Session, user_id: int, workspace_id: int) -> str:
    """Return the user's role in the workspace, or raise 403 if not a member."""
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.user_id == user_id,
        WorkspaceMember.workspace_id == workspace_id,
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this workspace",
        )
    return member.role


def _require_admin(db: Session, actor_user_id: int, workspace_id: int) -> None:
    """
    📚 Method: Actor/target identity separation
    We always distinguish who is ACTING (the request caller) from who is being
    MODIFIED (the target user). This function checks the ACTOR's role.
    Only after this check passes do we touch the target.
    This prevents a viewer from promoting themselves by calling add_member.
    """
    role = check_workspace_membership(db, actor_user_id, workspace_id)
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace admins can manage members",
        )


def create_workspace(db: Session, owner_id: int, name: str) -> Workspace:
    """Create workspace and automatically add the owner as admin."""
    ws = Workspace(name=name, owner_id=owner_id)
    db.add(ws)
    db.flush()  # get ws.id before commit

    # Owner is always an admin member
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=owner_id, role="admin"))
    db.commit()
    db.refresh(ws)
    return ws


def list_members(db: Session, workspace_id: int, actor_user_id: int) -> List[WorkspaceMember]:
    """Any workspace member can list all members."""
    check_workspace_membership(db, actor_user_id, workspace_id)
    return db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
    ).all()


def add_member(
    db: Session,
    workspace_id: int,
    actor_user_id: int,
    target_user_id: int,
    role: str,
) -> WorkspaceMember:
    """
    📚 Method: Idempotent add
    If the user is already a member, we update their role rather than raising
    a duplicate-key error. This makes the endpoint safe to call multiple times
    (idempotent from the caller's perspective).
    """
    _require_admin(db, actor_user_id, workspace_id)

    if role not in ("admin", "agent", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role '{role}'. Must be admin, agent, or viewer.",
        )

    existing = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == target_user_id,
    ).first()

    if existing:
        existing.role = role
        db.commit()
        db.refresh(existing)
        return existing

    member = WorkspaceMember(workspace_id=workspace_id, user_id=target_user_id, role=role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_member(
    db: Session,
    workspace_id: int,
    actor_user_id: int,
    target_user_id: int,
) -> None:
    """Admin removes a member. Admins cannot remove themselves."""
    _require_admin(db, actor_user_id, workspace_id)

    if actor_user_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot remove themselves from the workspace",
        )

    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == target_user_id,
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()


def list_workspaces(db: Session, user_id: int) -> List[Workspace]:
    """List all workspaces where the user is a member."""
    return (
        db.query(Workspace)
        .join(WorkspaceMember)
        .filter(WorkspaceMember.user_id == user_id)
        .all()
    )


def get_audit_logs(
    db: Session,
    workspace_id: int,
    actor_user_id: int,
    skip: int = 0,
    limit: int = 100,
    event_type: str | None = None,
) -> List[Any]:  # AuditLog is imported within route or we can import it here
    """List audit logs for a workspace. Admin only."""
    _require_admin(db, actor_user_id, workspace_id)
    
    from app.models.audit_log import AuditLog
    query = db.query(AuditLog).filter(AuditLog.workspace_id == workspace_id)
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
        
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
