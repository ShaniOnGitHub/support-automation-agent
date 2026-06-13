import requests

# We have the backend running locally on port 8000
url = "http://localhost:8000/api/v1/workspaces/1/knowledge/parse-file"

# We need to authenticate. Let's first register/login locally if needed,
# or we can override the authentication if we want.
# But wait! We can login using the user's credentials on localhost!
login_url = "http://localhost:8000/api/v1/auth/login"
try:
    login_resp = requests.post(login_url, data={
        "username": "roshaanali128@gmail.com",
        "password": "Roshaan123!"
    })
    if login_resp.status_code != 200:
        # Try registering first
        requests.post("http://localhost:8000/api/v1/auth/register", json={
            "email": "roshaanali128@gmail.com",
            "password": "Roshaan123!",
            "full_name": "Shani"
        })
        login_resp = requests.post(login_url, data={
            "username": "roshaanali128@gmail.com",
            "password": "Roshaan123!"
        })
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try parsing the PDF file
    files = {"file": ("minimal.pdf", open("scratch/minimal.pdf", "rb"), "application/pdf")}
    resp = requests.post(url, files=files, headers=headers)
    print("Status Code:", resp.status_code)
    print("Response Body:", resp.text)

except Exception as e:
    print("Test error:", str(e))
