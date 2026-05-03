import httpx
import os
import json
from dotenv import load_dotenv

def run_debug():
    load_dotenv()
    url = "https://api.x.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "grok-4.20-reasoning", 
        "input": "Say hi"
    }
    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            print(f"SUCCESS: {resp.text}")
        else:
            print(f"FAIL {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    run_debug()
