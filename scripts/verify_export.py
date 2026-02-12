
import sys
import os
import csv
import io
from datetime import date, timedelta

sys.path.append(os.getcwd())
try:
    from backend.core.config import get_settings
    from backend.models.user import User
    from sqlmodel import Session, select, create_engine
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.core.security import create_access_token
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def verify_export():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    # 1. Get Manager Token
    with Session(engine) as session:
        mgr = session.exec(select(User).where(User.employee_id == "TEST_MGR")).first()
        if not mgr:
            print("TEST_MGR not found")
            return
            
        token = create_access_token({"sub": str(mgr.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
    # 2. Call Export Endpoint
    client = TestClient(app)
    start = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    end = date.today().strftime("%Y-%m-%d")
    
    print(f"Requesting export for {start} to {end}...")
    response = client.get(
        f"/api/v1/manager/reports/export?start_date_str={start}&end_date_str={end}",
        headers=headers
    )
    
    print(f"Response Status: {response.status_code}")
    print("Response Headers:")
    for k, v in response.headers.items():
        print(f"  {k}: {v}")
        
    if response.status_code != 200:
        print(f"Failed: {response.status_code}")
        print(response.text)
        return
        
    # 3. Parse CSV
    content = response.content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(content))
    
    print(f"CSV Headers: {reader.fieldnames}")
    
    # Verify Columns Exist
    required = ["Overtime (hrs)", "Paid Hrs", "Unpaid Hrs", "Payable Fraction"]
    missing = [c for c in required if c not in reader.fieldnames]
    
    if missing:
        print(f"FAILED: Missing columns: {missing}")
    else:
        print("SUCCESS: All payroll columns present.")
        
    # Print first row
    rows = list(reader)
    if rows:
        print("Sample Row:")
        print(rows[0])
    else:
        print("No rows in export.")

if __name__ == "__main__":
    verify_export()
