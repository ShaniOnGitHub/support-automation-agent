import json
import sys
from fastapi.testclient import TestClient
from app.main import app

# Create a TestClient to interact with the API
client = TestClient(app)

def verify():
    print("--- POST /api/v1/tickets ---")
    try:
        response = client.post("/api/v1/tickets/", json={
            "subject": "Verify Ticket",
            "description": "Created by verification script",
            "priority": "high"
        })
        # Print JSON output
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- GET /api/v1/tickets ---")
    try:
        response = client.get("/api/v1/tickets/")
        # Print JSON output
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
