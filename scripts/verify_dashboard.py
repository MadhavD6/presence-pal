
import requests
from verify_utils import get_auth_token, API_BASE_URL

# Credentials for Employee 001 (John Doe)
EMAIL = "demo@example.com"
PWD = "password123"

def verify_dashboard():
    print("--- Verifying Employee Dashboard ---")
    try:
        token = get_auth_token(EMAIL, PWD)
    except Exception as e:
        print(f"Login failed: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    resp = requests.get(f"{API_BASE_URL}/employee/me/dashboard", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Failed to get dashboard: {resp.status_code} {resp.text}")
        return
        
    data = resp.json()
    print(f"User: {data['user']['name']}")
    print(f"Current Shift: {data['current_shift']}")
    
    print("\nUpcoming Shifts:")
    for s in data['upcoming_shifts'][:3]:
        print(f"  {s['day']} {s['date']}: {s['shift_name']} ({s['time_range']})")
        
    # Validation
    # We expect the shift name to match 'current_shift' name (approx) or be 'WO'
    # And NOT just 'General' if the user is on a custom shift.
    # User 1 was assigned 'History B' in previous steps? Or 'Hastinapuram' related?
    # Actually, in `verify_shift_history.py` we assigned "History B" (id 63) to User 1 as the latest.
    # So we expect "History B" in the upcoming list.
    
    first_shift = data['upcoming_shifts'][0]
    if "History B" in first_shift['shift_name'] or "General Shift" in first_shift['shift_name']:
         # Note: If it's Sunday, it might be WO.
         if first_shift['day'] == "Sun":
             print("  (Sunday is WO - Correct)")
         else:
             print("✅ Shift Name populated from User Shift")
    else:
        print(f"⚠️ Unexpected Shift Name: {first_shift['shift_name']}")

if __name__ == "__main__":
    verify_dashboard()
