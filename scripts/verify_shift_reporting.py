
import requests
import csv
import io
import random
from datetime import date, timedelta, time, datetime
from verify_utils import get_auth_token, API_BASE_URL, MANAGER_EMAIL, MANAGER_PASSWORD

def verify_shift_reporting():
    print("--- Verifying Shift Reporting (30+ Shifts) ---")
    
    # 1. Login
    # Note: Using dummy token if auth is disabled for MVP, else real token
    token = get_auth_token(MANAGER_EMAIL, MANAGER_PASSWORD)
    if not token and "localhost" in API_BASE_URL:
        unique_token = "dummy_token" 
    else:
        unique_token = token
        
    headers = {"Authorization": f"Bearer {unique_token}"}
    
    # 2. Create 30 Shifts
    print("Creating 30 Test Shifts...")
    created_shift_ids = []
    
    for i in range(1, 31):
        shift_name = f"Test Shift {i}"
        # Stagger times slightly
        start_h = 8 + (i % 4)
        end_h = start_h + 9
        
        payload = {
            "name": shift_name,
            "start_time": f"{start_h:02d}:00",
            "end_time": f"{end_h:02d}:00",
            "grace_period_mins": 15
        }
        
        # Create
        res = requests.post(f"{API_BASE_URL}/manager/shifts", json=payload, headers=headers)
        if res.status_code == 200:
            created_shift_ids.append(res.json()["id"])
        else:
            print(f"Failed to create shift {i}: {res.text}")
            
    print(f"Created {len(created_shift_ids)} shifts.")
    
    # 3. Assign Users (Mock)
    # We need users to assign. Let's assume we have some or create one for testing.
    # For reporting test, we need at least one user in a shift to verify 'shift_name' in export.
    
    # Create a test user
    u_res = requests.post(f"{API_BASE_URL}/admin/enroll", data={
        "name": f"Shift Tester",
        "employee_id": f"ST001",
        "password": "password"
    }, files={"file": ("pixel.png", b"fake_image_data", "image/png")})
    
    user_id = None
    if u_res.status_code == 200:
        user_id = u_res.json()["user_id"]
    elif u_res.status_code == 400 and "already exists" in u_res.text:
         # Try to find user? For now just skip if fails, relying on existing users
         pass
         
    # Assign a specific shift to a user (e.g. Shift 30)
    target_shift_id = created_shift_ids[-1] if created_shift_ids else None
    
    if target_shift_id and user_id:
        print(f"Assigning Shift {target_shift_id} to User {user_id}")
        assign_res = requests.post(f"{API_BASE_URL}/manager/roster/assign", json={
            "user_ids": [user_id],
            "shift_id": target_shift_id,
            "is_permanent": True
        }, headers=headers)
        if assign_res.status_code == 200:
            print("Assignment Success")
        else:
            print(f"Assignment Failed: {assign_res.text}")

    # 4. Verify Export
    print("Verifying Export CSV...")
    start_date = date.today().isoformat()
    end_date = date.today().isoformat()
    
    export_url = f"{API_BASE_URL}/manager/reports/export?start_date_str={start_date}&end_date_str={end_date}"
    csv_res = requests.get(export_url, headers=headers)
    
    if csv_res.status_code == 200:
        content = csv_res.content.decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        header = next(reader)
        rows = list(reader)
        
        print("CSV Header:", header)
        print(f"Row Count: {len(rows)}")
        
        # Check for 'Shift Name' column
        if "Shift Name" in header:
            print("✅ 'Shift Name' column present")
        else:
            print("❌ 'Shift Name' column MISSING")
            
        # Check for 'Late Duration' column
        if "Late Duration" in header:
            print("✅ 'Late Duration' column present")
            # Verify format in first data row if available
            if len(rows) > 0:
                late_idx = header.index("Late Duration")
                val = rows[0][late_idx]
                if ":" in val:
                    print(f"✅ 'Late Duration' format correct: {val}")
                else:
                    print(f"❌ 'Late Duration' format incorrect: {val}")
        else:
            print("❌ 'Late Duration' column MISSING")
             
        # Cleanup (Optional - Delete shifts)
        # for sid in created_shift_ids:
        #    requests.delete(f"{API_BASE_URL}/manager/shifts/{sid}", headers=headers)
        
    else:
        print(f"Export Failed: {csv_res.status_code} {csv_res.text}")

if __name__ == "__main__":
    verify_shift_reporting()
