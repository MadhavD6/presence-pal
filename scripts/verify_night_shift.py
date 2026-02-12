
import requests
from datetime import date, datetime, timedelta
from verify_utils import get_auth_token, API_BASE_URL, MANAGER_EMAIL, MANAGER_PASSWORD

# Needs to be a valid file path for image upload
SELFIE_PATH = "scripts/selfie.jpg" 

def ensure_selfie():
    import os
    if not os.path.exists(SELFIE_PATH):
        with open(SELFIE_PATH, "wb") as f:
            f.write(b"\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01")

def verify_night_shift():
    print("--- Verifying Night Shift Logic ---")
    ensure_selfie()
    token = get_auth_token(MANAGER_EMAIL, MANAGER_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Night Shift (10 PM to 6 AM)
    print("1. Creating Night Shift...")
    resp = requests.post(f"{API_BASE_URL}/manager/shifts", json={
        "name": "Night Shift Test",
        "start_time": "22:00",
        "end_time": "06:00",
        "grace_period_mins": 15
    }, headers=headers)
    if resp.status_code == 200:
        ns_id = resp.json()['id']
        print(f"   Created Shift ID: {ns_id}")
    else:
        print(f"❌ Failed to create shift: {resp.text}")
        return

    # 2. Assign to User 1 (John Doe) for TODAY
    # Note: verify_shift_history.py assigned distinct shifts. We will override for investigation.
    # We assign starting TODAY.
    today = date.today().isoformat()
    print(f"2. Assigning Night Shift to User 1 starting {today}...")
    # Using 'assignRoster' endpoint which likely creates EmployeeShift
    # Actually, let's use the bulk assign endpoint or roster assign?
    # services/api.ts uses /manager/roster/assign
    resp = requests.post(f"{API_BASE_URL}/manager/roster/assign", json={
        "user_ids": [1],
        "shift_id": ns_id,
        "is_permanent": True,
        "start_date": today
    }, headers=headers)
    print(f"   Status: {resp.status_code}")

    # 3. Punch IN (Today 22:00)
    # We need to force timestamp? The punch API uses Server Time.
    # We can't easily force server time without mocking.
    # BUT we can insert directly into AuditLog via Python script if we want precise control?
    # OR we can just rely on the Logic: If I punch NOW (7 PM?), will it count?
    # If Night Shift starts 22:00, and I punch at 19:00. It's early but should be captured if I query Today.
    # Wait, the verification requirement is "Crosses Midnight".
    # I cannot real-time simulate crossing midnight.
    # I MUST inject Logs directly to DB with custom timestamps.
    
    print("3. Injecting Punches directly to DB...")
    import sqlite3
    conn = sqlite3.connect("kiosk.db")
    cursor = conn.cursor()
    
    # Clear previous logs for today to avoid noise
    cursor.execute(f"DELETE FROM auditlog WHERE user_id=1 AND date(timestamp) >= '{today}'")
    
    # Timestamps
    t_in = f"{today} 22:00:00"
    # t_out is TOMORROW 06:00:00
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    t_out = f"{tomorrow} 06:00:00"
    
    cursor.execute(f"""
        INSERT INTO auditlog (user_id, event_type, timestamp, confidence, identified_name, latitude, longitude, accuracy)
        VALUES (1, 'in', '{t_in}', 0.99, 'John Doe', 12.9, 77.6, 10.0)
    """)
    cursor.execute(f"""
        INSERT INTO auditlog (user_id, event_type, timestamp, confidence, identified_name, latitude, longitude, accuracy)
        VALUES (1, 'out', '{t_out}', 0.99, 'John Doe', 12.9, 77.6, 10.0)
    """)
    conn.commit()
    conn.close()
    print(f"   Injected IN: {t_in}")
    print(f"   Injected OUT: {t_out}")

    # 4. Verify Daily Timesheet for TODAY
    # Should see BOTH punches and 8 hours worked.
    print("4. Fetching Daily Timesheet for Today...")
    user_token = get_auth_token("demo@example.com", "password123")
    u_headers = {"Authorization": f"Bearer {user_token}"}
    
    resp = requests.get(f"{API_BASE_URL}/employee/me/timesheet/day?date={today}", headers=u_headers)
    if resp.status_code != 200:
        print(f"❌ Failed to fetch timesheet: {resp.status_code} {resp.text}")
        return
        
    data = resp.json()
    print(f"   Status: {data['status']}")
    print(f"   Worked: {data['workedHours']}")
    print(f"   Punches Found: {len(data['punches'])}")
    for p in data['punches']:
        print(f"    - {p['type']} at {p['time']} on {p['date']}")
        
    expected_hours = "8h 0m"
    if data['workedHours'] == expected_hours:
        print("✅ Night Shift Logic Works: 8 Hours Calculated across midnight")
    else:
        print(f"❌ Failed: Expected {expected_hours}, got {data['workedHours']}")

if __name__ == "__main__":
    verify_night_shift()
