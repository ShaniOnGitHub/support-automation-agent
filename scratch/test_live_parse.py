import requests

live_url = "https://shanixali-support-automation-backend.hf.space/api/v1/workspaces/1/knowledge/parse-file"
login_url = "https://shanixali-support-automation-backend.hf.space/api/v1/auth/login"

try:
    # Login on live backend with correct user
    login_resp = requests.post(login_url, data={
        "username": "shani@gmail.com",
        "password": "Roshaan123@"
    })
    print("Login status:", login_resp.status_code)
    
    if login_resp.status_code != 200:
        print("Login failed:", login_resp.text)
    else:
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Parse PDF file
        files = {"file": ("minimal.pdf", open("scratch/minimal.pdf", "rb"), "application/pdf")}
        resp = requests.post(live_url, files=files, headers=headers)
        print("Live Parse Status Code:", resp.status_code)
        print("Live Parse Response Body:", resp.text)
except Exception as e:
    print("Error:", str(e))
