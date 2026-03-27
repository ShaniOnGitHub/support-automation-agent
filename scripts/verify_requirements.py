import json
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember

# Use Real DB
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def print_json(data):
    print(json.dumps(data, indent=2))

def verify_requirements():
    client = TestClient(app)
    db = SessionLocal()

    # 1. Auth Response JSON
    print("\n--- 3) Auth response JSON ---")
    
    # Register
    print("Registering User A...")
    user_a_email = "usera@example.com"
    user_a_pass = "password123"
    
    # Cleanup User A if exists
    existing_user = db.query(User).filter(User.email == user_a_email).first()
    if existing_user:
        # We can't easily delete due to foreign keys without cascading, so we'll just use unique email if needed
        # Or hopefully cleanup script ran. 
        # For now, let's assume fresh DB or use random emails.
        # Ideally, we truncate tables or similar.
        pass

    # Better approach: Use unique emails every run to avoid conflicts
    import time
    timestamp = int(time.time())
    user_a_email = f"usera_{timestamp}@example.com"
    user_b_email = f"userb_{timestamp}@example.com"
    user_c_email = f"userc_{timestamp}@example.com"

    resp = client.post("/api/v1/auth/register", json={
        "email": user_a_email, 
        "password": user_a_pass, 
        "full_name": "User A"
    })
    print("Register Response:")
    print_json(resp.json())

    # Login
    print("Logging in User A...")
    resp = client.post("/api/v1/auth/login", data={
        "username": user_a_email, 
        "password": user_a_pass
    })
    print("Login Response:")
    login_json = resp.json()
    print_json(login_json)
    token_a = login_json["access_token"]
    
    # Get User A ID
    user_a = db.query(User).filter(User.email == user_a_email).first()
    
    # Create Workspace 1
    print("\nCreating Workspace 1 for User A...")
    ws1 = Workspace(name="Workspace 1", owner_id=user_a.id)
    db.add(ws1)
    db.commit()
    db.refresh(ws1)
    # Add User A as Admin
    db.add(WorkspaceMember(workspace_id=ws1.id, user_id=user_a.id, role="admin"))
    db.commit()

    # Create Ticket in WS 1
    print("Creating ticket in Workspace 1...")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    client.post(f"/api/v1/workspaces/{ws1.id}/tickets/", json={
        "subject": "Ticket A", 
        "priority": "high"
    }, headers=headers_a)

    # 2. Security Tests
    print("\n--- 4) Security Tests ---")

    # Test A: Cross workspace isolation
    print("Test A: Cross workspace isolation")
    print("Registering User B...")
    client.post("/api/v1/auth/register", json={
        "email": user_b_email, 
        "password": "password123", 
        "full_name": "User B"
    })
    resp_b = client.post("/api/v1/auth/login", data={"username": user_b_email, "password": "password123"})
    token_b = resp_b.json()["access_token"]
    
    # Create Workspace 2 for User B (just to have one)
    user_b = db.query(User).filter(User.email == user_b_email).first()
    ws2 = Workspace(name="Workspace 2", owner_id=user_b.id)
    db.add(ws2)
    db.commit()
    db.refresh(ws2)
    db.add(WorkspaceMember(workspace_id=ws2.id, user_id=user_b.id, role="admin"))
    db.commit()

    print(f"User B trying to list tickets in User A's Workspace {ws1.id}...")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp = client.get(f"/api/v1/workspaces/{ws1.id}/tickets/", headers=headers_b)
    print(f"Status Code: {resp.status_code}")
    print("Response Body:")
    print_json(resp.json())

    # Test B: Role restriction
    print("\nTest B: Role restriction")
    print("Registering User C...")
    client.post("/api/v1/auth/register", json={
        "email": user_c_email, 
        "password": "password123", 
        "full_name": "User C"
    })
    resp_c = client.post("/api/v1/auth/login", data={"username": user_c_email, "password": "password123"})
    token_c = resp_c.json()["access_token"]
    user_c = db.query(User).filter(User.email == user_c_email).first()

    # Make User C a viewer in Workspace 1
    print(f"Adding User C as viewer to Workspace {ws1.id}...")
    db.add(WorkspaceMember(workspace_id=ws1.id, user_id=user_c.id, role="viewer"))
    db.commit()

    print("User C trying to create ticket in Workspace 1...")
    headers_c = {"Authorization": f"Bearer {token_c}"}
    resp = client.post(f"/api/v1/workspaces/{ws1.id}/tickets/", json={
        "subject": "Malicious Ticket", 
        "priority": "high"
    }, headers=headers_c)
    print(f"Status Code: {resp.status_code}")
    print("Response Body:")
    print_json(resp.json())

    db.close()

if __name__ == "__main__":
    verify_requirements()
