
import requests
import json
from verify_utils import get_auth_token, API_BASE_URL, MANAGER_EMAIL, MANAGER_PASSWORD

def verify_site_assignment():
    print("--- Verifying Site Assignment ---")
    token = get_auth_token(MANAGER_EMAIL, MANAGER_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get Sites
    print("\n1. Fetching Sites...")
    resp = requests.get(f"{API_BASE_URL}/manager/sites", headers=headers)
    if resp.status_code != 200:
        print(f"FAILED to get sites: {resp.text}")
        return
    sites = resp.json()
    print(f"Sites found: {len(sites)}")
    if len(sites) == 0:
        print("No sites to assign. Skipping assignment test.")
        return
    target_site_id = sites[0]['id']
    print(f"Target Site: {sites[0]['name']} (ID: {target_site_id})")

    # 2. Get Employees (Before)
    print("\n2. Fetching Employees...")
    resp = requests.get(f"{API_BASE_URL}/manager/employees", headers=headers)
    employees = resp.json()
    if not employees:
        print("No employees found.")
        return
        
    target_user = employees[0]
    print(f"Target User: {target_user['name']} (Current Site: {target_user.get('site_name')})")

    # 3. Assign Site
    print(f"\n3. Assigning Site ID {target_site_id} to User ID {target_user['id']}...")
    payload = {
        "user_ids": [target_user['id']],
        "site_id": target_site_id
    }
    resp = requests.post(f"{API_BASE_URL}/manager/employees/assign-site", json=payload, headers=headers)
    if resp.status_code == 200:
        print("Assignment Successful.")
    else:
        print(f"Assignment FAILED: {resp.text}")
        return

    # 4. Verify Update
    print("\n4. Verifying Update...")
    resp = requests.get(f"{API_BASE_URL}/manager/employees", headers=headers)
    employees = resp.json()
    updated_user = next(u for u in employees if u['id'] == target_user['id'])
    print(f"Updated User Site: {updated_user.get('site_name')} (ID: {updated_user.get('site_id')})")
    
    if updated_user.get('site_id') == target_site_id:
        print("✅ VERIFICATION PASSED: Site updated correctly.")
    else:
        print("❌ VERIFICATION FAILED: Site ID mismatch.")

if __name__ == "__main__":
    verify_site_assignment()
