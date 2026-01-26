
import requests

API_BASE_URL = "http://localhost:8000/api/v1"
MANAGER_EMAIL = "demo@example.com"
MANAGER_PASSWORD = "password123"

def get_auth_token(email, password):
    response = requests.post(f"{API_BASE_URL}/employee/login", data={"username": email, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    print(f"Login failed: {response.text}")
    return None
