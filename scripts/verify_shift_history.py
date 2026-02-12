
import requests
import json
from datetime import date, timedelta
from verify_utils import get_auth_token, API_BASE_URL, MANAGER_EMAIL, MANAGER_PASSWORD

def verify_shift_history():
    print("--- Verifying Shift History ---")
    token = get_auth_token(MANAGER_EMAIL, MANAGER_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create 2 Shifts
    s1_name = "History A"
    s2_name = "History B"
    
    # Check if they exist or create
    resp = requests.get(f"{API_BASE_URL}/manager/shifts", headers=headers)
    shifts = resp.json()
    
    s1 = next((s for s in shifts if s['name'] == s1_name), None)
    if not s1:
        resp = requests.post(f"{API_BASE_URL}/manager/shifts", json={
            "name": s1_name, "start_time": "08:00", "end_time": "17:00", "grace_period_mins": 15
        }, headers=headers)
        s1 = resp.json()
        print(f"Created Shift A: {s1['id']}")
    else:
        print(f"Found Shift A: {s1['id']}")

    s2 = next((s for s in shifts if s['name'] == s2_name), None)
    if not s2:
        resp = requests.post(f"{API_BASE_URL}/manager/shifts", json={
            "name": s2_name, "start_time": "14:00", "end_time": "22:00", "grace_period_mins": 15
        }, headers=headers)
        s2 = resp.json()
        print(f"Created Shift B: {s2['id']}")
    else:
        print(f"Found Shift B: {s2['id']}")

    user_id = 1 # John Doe

    import sqlite3
    db_path = "kiosk.db"
    
    # 2. Assign Shift A
    print(f"\nAssigning Shift A ({s1_name}) to user {user_id}...")
    requests.post(f"{API_BASE_URL}/manager/roster/assign", json={
        "user_ids": [user_id], "shift_id": s1['id']
    }, headers=headers)
    
    # HACK: Backdate Shift A in DB to simulate it started last week
    # otherwise assigning Shift B today will delete Shift A (same day correction logic)
    print("Simulating time passing (Backdating Shift A to -7 days)...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    past_date = (date.today() - timedelta(days=7)).isoformat()
    cursor.execute("UPDATE employeeshift SET start_date = ? WHERE user_id = ? AND shift_id = ?", (past_date, user_id, s1['id']))
    conn.commit()
    conn.close()

    # 3. Assign Shift B (Should archive A as Yesterday, B as Today)
    print(f"Assigning Shift B ({s2_name}) to user {user_id}...")
    requests.post(f"{API_BASE_URL}/manager/roster/assign", json={
        "user_ids": [user_id], "shift_id": s2['id']
    }, headers=headers)

    # 4. Verify Reports
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    
    # 4a. Get Timesheet for Yesterday (Should be A)
    print(f"\nChecking Timesheet for Yesterday ({yesterday_str})... Expecting {s1_name}")
    resp = requests.get(f"{API_BASE_URL}/manager/timesheet?start_date_str={yesterday_str}&end_date_str={yesterday_str}", headers=headers)
    ts = resp.json()
    print(ts)
    if isinstance(ts, dict) and "detail" in ts:
        print(f"API Error: {ts['detail']}")
        return

    user_row = next((u for u in ts if u['id'] == "E001"), ts[0] if ts else None)
    # Check the day
    if user_row:
        # The days_status list corresponds to date range. Since 1 day, it's index 0.
        # But wait, my get_timesheet returns "days" array? 
        # No, ManagerTimesheetView returns users array with "days_status": [{...}]
        # Let's inspect the first day status
        day_stat = user_row['days'][0]
        tooltip = day_stat.get('tooltip', '')
        print(f"Yesterday Tooltip: {tooltip}")
        
        if s1_name in tooltip:
            print("✅ PASSED: Yesterday shows Shift A")
        else:
            print(f"❌ FAILED: Yesterday shows {tooltip}")
    else:
        print("❌ FAILED: User not found in timesheet")

    # 4b. Get Timesheet for Today (Should be B)
    print(f"\nChecking Timesheet for Today ({today_str})... Expecting {s2_name}")
    resp = requests.get(f"{API_BASE_URL}/manager/timesheet?start_date_str={today_str}&end_date_str={today_str}", headers=headers)
    ts = resp.json()
    user_row = next((u for u in ts if u['id'] == "E001"), ts[0] if ts else None)
    if user_row:
        day_stat = user_row['days'][0]
        tooltip = day_stat.get('tooltip', '')
        print(f"Today Tooltip: {tooltip}")
        
        if s2_name in tooltip:
            print("✅ PASSED: Today shows Shift B")
        else:
            print(f"❌ FAILED: Today shows {tooltip}")

if __name__ == "__main__":
    verify_shift_history()
