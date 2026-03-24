import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

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

def verify():
    client = TestClient(app)
    
    print("Registering user...")
    email = "real_test@example.com"
    password = "password123"
    
    # Clean up first (optional, or just handle 400)
    
    resp = client.post("/api/v1/auth/register", json={
        "email": email, 
        "password": password, 
        "full_name": "Real Test"
    })
    
    if resp.status_code == 400:
        print("User already exists, proceeding to login...")
    elif resp.status_code != 200:
        print(f"Register failed: {resp.text}")
        return

    print("Logging in...")
    resp = client.post("/api/v1/auth/login", data={
        "username": email, 
        "password": password
    })
    
    if resp.status_code == 200:
        print("Login Successful!")
        print("Response:")
        print(resp.json())
    else:
        print(f"Login failed: {resp.text}")

if __name__ == "__main__":
    verify()
