from fastapi import APIRouter
from app.api.v1.routes import auth, health, tickets, messages, workspaces, webhooks

router = APIRouter()
router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
router.include_router(
    webhooks.router,
    prefix="/workspaces",
    tags=["Webhooks"],
)
router.include_router(
    tickets.router,
    prefix="/workspaces/{workspace_id}/tickets",
    tags=["Tickets"],
)
router.include_router(
    messages.router,
    prefix="/workspaces/{workspace_id}/tickets/{ticket_id}/messages",
    tags=["Messages"],
)
