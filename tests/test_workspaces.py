"""
Tests for workspace creation and member management API.
Covers: create workspace, list/add/remove members, RBAC guards.
"""
from app.models.user import User


# ── Helpers ──────────────────────────────────────────────────────────────────

def register_and_login(client, email, password="pass123", full_name="Test"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_create_workspace(client):
    """
    📚 Method: create_workspace auto-adds owner as admin
    After POST /workspaces, the owner is automatically a member with role=admin.
    We verify this by listing members immediately afterwards.
    """
    token = register_and_login(client, "ws_owner@example.com")

    resp = client.post(
        "/api/v1/workspaces/",
        json={"name": "My Support Team"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    ws = resp.json()
    assert ws["name"] == "My Support Team"
    assert "id" in ws

    # Owner should appear in member list
    members_resp = client.get(
        f"/api/v1/workspaces/{ws['id']}/members",
        headers=auth_headers(token),
    )
    assert members_resp.status_code == 200
    member_user_ids = [m["user_id"] for m in members_resp.json()]
    user = None  # we don't have the owner's id directly, but at least 1 member
    assert len(members_resp.json()) == 1
    assert members_resp.json()[0]["role"] == "admin"


def test_add_and_remove_member(client, db_session):
    """
    📚 Method: Admin-only write, any-member read
    Admins can add members. The new member can then read the member list.
    Admins can remove members. Removed members get 403 on the member list.
    """
    token_admin = register_and_login(client, "member_admin@example.com")
    token_target = register_and_login(client, "member_target@example.com")

    # Create workspace (admin auto-added)
    ws = client.post(
        "/api/v1/workspaces/",
        json={"name": "Member Mgmt WS"},
        headers=auth_headers(token_admin),
    ).json()
    ws_id = ws["id"]

    # Get target user's id from DB
    target_user = db_session.query(User).filter(
        User.email == "member_target@example.com"
    ).first()

    # Add target as agent
    add_resp = client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": target_user.id, "role": "agent"},
        headers=auth_headers(token_admin),
    )
    assert add_resp.status_code == 201
    assert add_resp.json()["role"] == "agent"

    # Target can now list members
    list_resp = client.get(
        f"/api/v1/workspaces/{ws_id}/members",
        headers=auth_headers(token_target),
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2  # admin + target

    # Remove target
    del_resp = client.delete(
        f"/api/v1/workspaces/{ws_id}/members/{target_user.id}",
        headers=auth_headers(token_admin),
    )
    assert del_resp.status_code == 204

    # Target can no longer access
    after_resp = client.get(
        f"/api/v1/workspaces/{ws_id}/members",
        headers=auth_headers(token_target),
    )
    assert after_resp.status_code == 403


def test_non_admin_cannot_add_member(client, db_session):
    """
    📚 Method: RBAC guard on write path
    A non-admin (here: agent) should get 403 when trying to add a member.
    """
    token_admin = register_and_login(client, "rbac_admin@example.com")
    token_agent = register_and_login(client, "rbac_agent@example.com")
    token_outsider = register_and_login(client, "rbac_outsider@example.com")

    ws = client.post(
        "/api/v1/workspaces/",
        json={"name": "RBAC Guard WS"},
        headers=auth_headers(token_admin),
    ).json()
    ws_id = ws["id"]

    # Get agent user id
    agent_user = db_session.query(User).filter(
        User.email == "rbac_agent@example.com"
    ).first()
    outsider_user = db_session.query(User).filter(
        User.email == "rbac_outsider@example.com"
    ).first()

    # Admin adds agent
    client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": agent_user.id, "role": "agent"},
        headers=auth_headers(token_admin),
    )

    # Agent tries to add outsider → 403
    resp = client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": outsider_user.id, "role": "viewer"},
        headers=auth_headers(token_agent),
    )
    assert resp.status_code == 403
    assert "admins" in resp.json()["detail"].lower()


def test_admin_cannot_remove_self(client):
    """Admins are blocked from removing themselves to prevent workspace lockout."""
    token = register_and_login(client, "self_remove@example.com")

    ws = client.post(
        "/api/v1/workspaces/",
        json={"name": "Self Remove WS"},
        headers=auth_headers(token),
    ).json()

    resp_user = None  # need owner user id — get from member list
    members = client.get(
        f"/api/v1/workspaces/{ws['id']}/members",
        headers=auth_headers(token),
    ).json()
    owner_id = members[0]["user_id"]

    resp = client.delete(
        f"/api/v1/workspaces/{ws['id']}/members/{owner_id}",
        headers=auth_headers(token),
    )
    assert resp.status_code == 400
    assert "cannot remove themselves" in resp.json()["detail"]
