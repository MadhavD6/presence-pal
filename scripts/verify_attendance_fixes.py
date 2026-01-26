
import requests
import time
from verify_utils import get_auth_token, API_BASE_URL, MANAGER_EMAIL, MANAGER_PASSWORD

# Needs to be a valid file path for image upload
SELFIE_PATH = "scripts/selfie.jpg" 

# Helper to create dummy selfie if not exists
def ensure_selfie():
    import os
    if not os.path.exists(SELFIE_PATH):
        with open(SELFIE_PATH, "wb") as f:
            f.write(b"\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01") # minimal jpg header

def verify_fixes():
    ensure_selfie()
    print("--- Verifying Attendance Fixes ---")
    token = get_auth_token(MANAGER_EMAIL, MANAGER_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Clock In (Success)
    print("\n1. Testing Clock In (Normal)...")
    files = {'file': open(SELFIE_PATH, 'rb')}
    data = {
        'event_type': 'in',
        'latitude': 17.3850,
        'longitude': 78.4867,
        'accuracy': 10.0,
        'is_mock': False
    }
    resp = requests.post(f"{API_BASE_URL}/attendance/punch", files=files, data=data, headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("✅ Success")
    else:
        print(f"❌ Failed: {resp.text}")

    # 2. Double Punch (Should Fail 429)
    print("\n2. Testing Double Punch (Throttle)...")
    files = {'file': open(SELFIE_PATH, 'rb')}
    resp = requests.post(f"{API_BASE_URL}/attendance/punch", files=files, data=data, headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 429:
        print("✅ Correctly Throttled (429)")
    else:
        print(f"❌ Failed to throttle: {resp.status_code} {resp.text}")

    # 3. Mock Location (Should Fail 400)
    print("\n3. Testing Mock Location...")
    time.sleep(1) # just slightly distinct
    files = {'file': open(SELFIE_PATH, 'rb')}
    data['is_mock'] = True
    resp = requests.post(f"{API_BASE_URL}/attendance/punch", files=files, data=data, headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 400 and "Mock" in resp.text:
        print("✅ Correctly Rejected Mock")
    else:
        print(f"❌ Failed to reject mock: {resp.text}")

    # 4. Clock Out (Should be Success & recorded as OUT)
    # Wait 2 seconds to avoid double punch throttle? No, logic says 2 minutes.
    # We need to manually hack DB or wait? Or user is different?
    # Let's use a different user if possible, or just accept the 429 and verify the mock check passed first (it checks input before throttle? No, strict order)
    # Check code order: Mock check is step 0, Throttle step 1. So Mock test above is valid.
    
    # To test Clock Out, we need to bypass throttle. 
    # Let's delete the last log for this user in DB to clear throttle.
    print("\n4. Testing Clock Out (Clearing throttle first)...")
    import sqlite3
    conn = sqlite3.connect("kiosk.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM auditlog WHERE user_id = 1") # Clear logs for John Doe
    conn.commit()
    conn.close()
    
    files = {'file': open(SELFIE_PATH, 'rb')}
    data['is_mock'] = False
    data['event_type'] = 'out'
    resp = requests.post(f"{API_BASE_URL}/attendance/punch", files=files, data=data, headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        rj = resp.json()
        if rj['type'] == 'out':
            print("✅ Success: Recorded as OUT")
        else:
            print(f"❌ Type mismatch: {rj['type']}")
    else:
        print(f"❌ Failed: {resp.text}")

if __name__ == "__main__":
    verify_fixes()
