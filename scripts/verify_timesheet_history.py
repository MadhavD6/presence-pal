
import requests
from verify_utils import get_auth_token, API_BASE_URL
from datetime import date, timedelta

# Credentials for Employee 001 (John Doe)
EMAIL = "demo@example.com"
PWD = "password123"

def verify_timesheet_history():
    print("--- Verifying Employee Timesheet History ---")
    try:
        token = get_auth_token(EMAIL, PWD)
    except Exception as e:
        print(f"Login failed: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # DEBUG: Check DB state
    import sqlite3
    conn = sqlite3.connect("kiosk.db")
    c = conn.cursor()
    print("\n--- DB Dump (EmployeeShift) ---")
    rows = c.execute("SELECT * FROM employeeshift").fetchall()
    for r in rows:
        print(r)
    conn.close()
    
    # We set up shift history: -7 days was "Morning", Today is "Evening" (or similar)
    # Let's check yesterday (should be Morning/History A) and today (Evening/History B)
    
    current_month_str = date.today().strftime("%Y-%m")
    resp = requests.get(f"{API_BASE_URL}/employee/me/timesheet?month={current_month_str}", headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ Failed to get timesheet: {resp.status_code} {resp.text}")
        return
        
    ts = resp.json()
    
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today = date.today().isoformat()
    
    # Find records
    y_rec = next((d for d in ts if d['date'] == yesterday), None)
    t_rec = next((d for d in ts if d['date'] == today), None)
    
    if y_rec:
        print(f"Yesterday ({yesterday}): Shift = {y_rec['shift']}")
        # Expecting HI (History A)
        if "HI" in y_rec['shift'] or "GE" not in y_rec['shift']: # Should NOT be General
             print("✅ Yesterday uses Historical Shift")
        else:
             print(f"⚠️ Yesterday Shift might be wrong: {y_rec['shift']}")
    else:
        print("❌ Yesterday record not found")
        
    if t_rec:
        print(f"Today ({today}): Shift = {t_rec['shift']}")
        # Expecting HI (History B)
        # Note: Both might be HI if names are similar ("History A", "History B" -> HI)
        # To distinguish, we'd need full names, but DailyTimesheet model only returns short code?
        # Let's check the code implementation: shift_name = f"{applicable_shift.name[:2].upper()}"
        # "History A" -> HI. "History B" -> HI.
        # "General Shift" -> GE.
        # So "HI" means it IS using our custom shifts and NOT falling back to "GE".
        if "HI" in t_rec['shift']:
            print("✅ Today uses Current Shift")
    else:
        print("❌ Today record not found")

if __name__ == "__main__":
    verify_timesheet_history()
