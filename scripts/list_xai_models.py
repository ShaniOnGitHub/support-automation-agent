import httpx
import os
from dotenv import load_dotenv

def list_xai_models():
    load_dotenv()
    url = "https://api.x.ai/v1/models"
    headers = {
        "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    try:
        resp = httpx.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            models = resp.json()["data"]
            print(f"Models: {[m['id'] for m in models]}")
        else:
            print(f"Fail {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_xai_models()
