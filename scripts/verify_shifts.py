import sys
import os
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Mock Services
sys.modules["backend.services.face"] = MagicMock()
sys.modules["backend.services.liveness"] = MagicMock()
sys.modules["backend.services.vector"] = MagicMock()

from backend.services.face import face_service
from backend.services.liveness import liveness_service
from backend.services.vector import vector_service

# Import main
from backend.main import app
from backend.core.database import get_session
from backend.models.user import User
from backend.models.shift import Shift

# Setup Test DB
engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
SQLModel.metadata.create_all(engine)

def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

def run_tests():
    client = TestClient(app)
    
    # Mock Auth - Manager
    from backend.core.security import get_current_active_user
    # Actually managing shifts usually requires 'admin' or 'manager' role.
    # But `shifts.py` endpoints didn't enforce specific role dependency yet (just get_session).
    # If they do in future, we need to mock it properly.
    # Currently `shifts.py` uses `APIRouter()` without top-level dependencies.
    
    print("--- Starting Shift Verification Tests ---")
    
    # 1. Create Shift
    print("\nTest 1: Create Shift")
    res = client.post("/api/v1/manager/shifts", json={
        "name": "Morning Shift",
        "start_time": "09:00",
        "end_time": "18:00",
        "grace_period_mins": 15
    })
    if res.status_code == 200:
        print("✅ SUCCESS:", res.json())
        shift_id = res.json()["id"]
    else:
        print("❌ FAILED:", res.status_code, res.text)
        return

    # 2. List Shifts
    print("\nTest 2: List Shifts")
    res = client.get("/api/v1/manager/shifts")
    if res.status_code == 200:
        shifts = res.json()
        print(f"✅ SUCCESS: Found {len(shifts)} shifts")
        assert len(shifts) >= 1
    else:
        print("❌ FAILED:", res.status_code, res.text)

    # 3. Update Shift
    print("\nTest 3: Update Shift")
    res = client.put(f"/api/v1/manager/shifts/{shift_id}", json={
        "name": "Morning Shift Updated",
        "start_time": "08:30",
        "end_time": "17:30",
        "grace_period_mins": 10
    })
    if res.status_code == 200:
        print("✅ SUCCESS:", res.json())
        assert res.json()["name"] == "Morning Shift Updated"
    else:
        print("❌ FAILED:", res.status_code, res.text)

    # 4. Roster Assign (Mock User)
    print("\nTest 4: Roster Assign")
    # First create a user
    with Session(engine) as session:
        u = User(name="Shift Worker", employee_id="SW01")
        session.add(u)
        session.commit()
        session.refresh(u)
        user_id = u.id

    res = client.post("/api/v1/manager/roster/assign", json={
        "user_ids": [user_id],
        "shift_id": shift_id,
        "is_permanent": True
    })
    if res.status_code == 200:
         print("✅ SUCCESS:", res.json())
         # Verify DB
         with Session(engine) as session:
             u_check = session.get(User, user_id)
             assert u_check.shift_id == shift_id
             print("✅ DB Verification: User.shift_id updated.")
    else:
         print("❌ FAILED:", res.status_code, res.text)

    # 5. Delete Shift
    print("\nTest 5: Delete Shift")
    res = client.delete(f"/api/v1/manager/shifts/{shift_id}")
    if res.status_code == 200:
        print("✅ SUCCESS")
    else:
        print("❌ FAILED:", res.status_code, res.text)

if __name__ == "__main__":
    run_tests()
