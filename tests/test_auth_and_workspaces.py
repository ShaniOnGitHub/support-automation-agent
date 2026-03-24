import pytest
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember

def test_register_and_login(client):
    # Register
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]

def get_auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def test_workspace_isolation(client, db_session):
    # 1. Register two users
    # User A
    client.post("/api/v1/auth/register", json={"email": "userA@example.com", "password": "passwordA", "full_name": "User A"})
    token_a = client.post("/api/v1/auth/login", data={"username": "userA@example.com", "password": "passwordA"}).json()["access_token"]
    
    # User B
    client.post("/api/v1/auth/register", json={"email": "userB@example.com", "password": "passwordB", "full_name": "User B"})
    token_b = client.post("/api/v1/auth/login", data={"username": "userB@example.com", "password": "passwordB"}).json()["access_token"]

    # 2. Get User IDs
    # Use db_session fixture
    db = db_session
    
    user_a = db.query(User).filter(User.email == "userA@example.com").first()
    user_b = db.query(User).filter(User.email == "userB@example.com").first()

    # 3. Create Workspaces
    ws_a = Workspace(name="Workspace A", owner_id=user_a.id)
    ws_b = Workspace(name="Workspace B", owner_id=user_b.id)
    db.add_all([ws_a, ws_b])
    db.commit()
    db.refresh(ws_a)
    db.refresh(ws_b)

    # 4. Create Memberships
    # User A is admin in WS A via owner relation (logic is not implicit, need to add member)
    # Wait, my workspace model says owner_id, but usually owner is also a member.
    # The routes check WorkspaceMember.
    db.add(WorkspaceMember(workspace_id=ws_a.id, user_id=user_a.id, role="admin"))
    db.add(WorkspaceMember(workspace_id=ws_b.id, user_id=user_b.id, role="admin"))
    db.commit()

    # 5. User A creates ticket in WS A
    response = client.post(
        f"/api/v1/workspaces/{ws_a.id}/tickets/",
        json={"subject": "Ticket A", "priority": "high"},
        headers=get_auth_headers(token_a)
    )
    assert response.status_code == 201
    ticket_a_id = response.json()["id"]

    # 6. User B tries to read tickets in WS A (Should fail)
    response = client.get(
        f"/api/v1/workspaces/{ws_a.id}/tickets/",
        headers=get_auth_headers(token_b)
    )
    assert response.status_code == 403 # Not a member

    # 7. User B tries to read specific ticket from WS A
    response = client.get(
        f"/api/v1/workspaces/{ws_a.id}/tickets/{ticket_a_id}",
        headers=get_auth_headers(token_b)
    )
    assert response.status_code == 403

    # 8. User A tries to read tickets in WS B (Should fail)
    response = client.get(
        f"/api/v1/workspaces/{ws_b.id}/tickets/",
        headers=get_auth_headers(token_a)
    )
    assert response.status_code == 403

def test_rb_permissions(client, db_session):
    # Setup: Admin user and Viewer user in same workspace
    db = db_session
    
    # Create users
    client.post("/api/v1/auth/register", json={"email": "admin@ws.com", "password": "pass", "full_name": "Admin"})
    client.post("/api/v1/auth/register", json={"email": "viewer@ws.com", "password": "pass", "full_name": "Viewer"})
    
    token_admin = client.post("/api/v1/auth/login", data={"username": "admin@ws.com", "password": "pass"}).json()["access_token"]
    token_viewer = client.post("/api/v1/auth/login", data={"username": "viewer@ws.com", "password": "pass"}).json()["access_token"]
    
    user_admin = db.query(User).filter(User.email == "admin@ws.com").first()
    user_viewer = db.query(User).filter(User.email == "viewer@ws.com").first()
    
    # Create Workspace
    ws = Workspace(name="Test RBAC", owner_id=user_admin.id)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    
    # Add members
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=user_admin.id, role="admin"))
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=user_viewer.id, role="viewer"))
    db.commit()
    
    # Viewer tries to create ticket (Should fail)
    response = client.post(
        f"/api/v1/workspaces/{ws.id}/tickets/",
        json={"subject": "Viewer Ticket", "priority": "low"},
        headers=get_auth_headers(token_viewer)
    )
    assert response.status_code == 403
    assert "Viewers cannot create tickets" in response.json()["detail"]
    
    # Admin creates ticket (Should succeed)
    response = client.post(
        f"/api/v1/workspaces/{ws.id}/tickets/",
        json={"subject": "Admin Ticket", "priority": "high"},
        headers=get_auth_headers(token_admin)
    )
    assert response.status_code == 201
    ticket_id = response.json()["id"]
    
    # Viewer can read tickets
    response = client.get(
        f"/api/v1/workspaces/{ws.id}/tickets/",
        headers=get_auth_headers(token_viewer)
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
