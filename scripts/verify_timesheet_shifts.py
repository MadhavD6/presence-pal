
import requests
import json
from datetime import date, timedelta
from verify_utils import get_auth_token, API_BASE_URL, MANAGER_EMAIL, MANAGER_PASSWORD

def verify_timesheet_shifts():
    print("--- Verifying Timesheet Shifts ---")
    
    # 1. Login as Manager (Skipped as endpoint is unprotected for MVP)
    # token = get_auth_token(MANAGER_EMAIL, MANAGER_PASSWORD)
    # if not token:
    #     print("Failed to login as manager")
    #     return
    token = "dummy_token"

    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Call Manager Timesheet API
    start_date = date.today().isoformat()
    end_date = (date.today() + timedelta(days=6)).isoformat()
    
    url = f"{API_BASE_URL}/manager/timesheet?start_date_str={start_date}&end_date_str={end_date}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch manager timesheet: {response.text}")
        return

    data = response.json()
    print(f"Fetched {len(data)} staff entries")
    
    if not data:
        print("No staff data returned. Ensure users exist.")
        return

    # 3. Verify Structure
    first_entry = data[0]
    print(f"Checking entry for: {first_entry['name']}")
    
    days = first_entry.get("days", [])
    if not days:
        print("No days data found")
        return
        
    first_day = days[0]
    print(f"First Day Entry: {first_day}")
    
    # Check for new fields
    if isinstance(first_day, dict):
        if "shift_code" in first_day and "tooltip" in first_day:
            print("✅ SUCCESS: Day entry contains 'shift_code' and 'tooltip'")
            print(f"   Shift Code: {first_day['shift_code']}")
            print(f"   Tooltip: {first_day['tooltip']}")
        else:
            print("❌ FAILURE: Day entry missing expected fields")
    else:
        print(f"❌ FAILURE: Day entry is not a dictionary. Got: {type(first_day)}")

if __name__ == "__main__":
    try:
        verify_timesheet_shifts()
    except Exception as e:
        print(f"Error: {e}")
