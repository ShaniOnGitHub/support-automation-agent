from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.ticket import Ticket

# Setup in-memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def verify():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    client = TestClient(app)
    
    print("Registering user...")
    try:
        resp = client.post("/api/v1/auth/register", json={
            "email": "test@example.com", 
            "password": "password", 
            "full_name": "Test"
        })
        print(f"Register status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Register error: {resp.text}")
            return
            
        print("Logging in...")
        resp = client.post("/api/v1/auth/login", data={
            "username": "test@example.com", 
            "password": "password"
        })
        print(f"Login status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Login error: {resp.text}")
            return
        
        token = resp.json()["access_token"]
        print(f"Token obtained: {token[:10]}...")
        
        print("Creating workspace...")
        # Need to get user ID first - can't rely on API return since register return might not include ID in some schemas
        # Register returns UserResponse which has ID.
        # But we didn't capture it.
        # We can query DB or just assume ID 1.
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "test@example.com").first()
        ws = Workspace(name="Test WS", owner_id=user.id)
        db.add(ws)
        db.commit()
        db.refresh(ws)
        
        # Add member
        db.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin"))
        db.commit()
        
        workspace_id = ws.id
        db.close()
        
        print("Creating ticket with token...")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(f"/api/v1/workspaces/{workspace_id}/tickets/", json={
            "subject": "Auth Ticket", 
            "priority": "high"
        }, headers=headers)
        print(f"Create ticket status: {resp.status_code}")
        if resp.status_code != 201:
            print(f"Create ticket error: {resp.text}")
        else:
            print("Ticket created successfully.")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
