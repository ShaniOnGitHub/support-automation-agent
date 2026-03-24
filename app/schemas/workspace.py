from pydantic import BaseModel
from typing import Literal


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    owner_id: int

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    user_id: int
    role: Literal["admin", "agent", "viewer"]
    """
    📚 Method: Literal type for enums in Pydantic v2
    Instead of a plain str, we use Literal["admin", "agent", "viewer"].
    Pydantic will automatically validate and reject any other string.
    This gives us request-body validation for free, without extra code.
    """


class MemberResponse(BaseModel):
    workspace_id: int
    user_id: int
    role: str

    class Config:
        from_attributes = True
