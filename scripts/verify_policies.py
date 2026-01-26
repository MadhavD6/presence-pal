import sys
import os
from unittest.mock import MagicMock
from datetime import date, datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

# Mock Services
sys.modules["backend.services.face"] = MagicMock()
sys.modules["backend.services.liveness"] = MagicMock()
sys.modules["backend.services.vector"] = MagicMock()

# Import main
from backend.main import app
from backend.core.database import get_session
from backend.models.user import User
from backend.models.payroll import PayrollConfig, DailySummary
from backend.services.payroll_service import generate_payroll_run

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
    from backend.core.security import get_current_manager_user
    u_manager = User(name="Manager", role="manager", employee_id="MGR01")
    app.dependency_overrides[get_current_manager_user] = lambda: u_manager
    
    print("--- Starting Policy Verification Tests ---")
    
    # 1. Create a User
    with Session(engine) as session:
        session.add(u_manager) # Add manager to DB too
        u = User(name="Policy User", employee_id="P001", role="user")
        session.add(u)
        session.commit()
        session.refresh(u)
        user_id = u.id
        
    # 2. Set Policy Config (PUT)
    print("\nTest 1: Set Policy Config")
    res = client.put(f"/api/v1/manager/payroll/config/{user_id}", json={
        "base_hourly_rate": 100.0,
        "currency": "USD",
        "overtime_multiplier": 2.0, # Double pay
        "late_deduction_amount": 50.0 # Flat 50 deduction per late
    })
    
    if res.status_code == 200:
        print("✅ Config Updated:", res.json())
        assert res.json()["overtime_multiplier"] == 2.0
        assert res.json()["late_deduction_amount"] == 50.0
    else:
        print("❌ FAILED Config Update:", res.status_code, res.text)
        return

    # 3. Verify Payroll Calculation with Policy
    print("\nTest 2: Verify Payroll Logic")
    with Session(engine) as session:
        # Create a DailySummary (Mock attendance)
        # 1 day Late, 10 hours worked (8 regular + 2 OT)
        summary = DailySummary(
            user_id=user_id,
            date=date(2026, 1, 1),
            total_hours=10.0,
            regular_hours=8.0,
            overtime_hours=2.0,
            is_late=True,
            status="Present"
        )
        session.add(summary)
        session.commit()
        
        # Determine expected Pay:
        # Rate: 100
        # OT Rate: 100 * 2.0 = 200
        # Regular Pay: 8 * 100 = 800
        # OT Pay: 2 * 200 = 400
        # Gross: 1200
        # Deduction (Flat): 50
        # Net: 1150
        
        run = generate_payroll_run(session, date(2026, 1, 1), date(2026, 1, 1))
        
        # Check Payslip
        from backend.models.payroll import Payslip
        # Need to re-fetch or check DB
        slip = session.exec(select(Payslip).where(Payslip.run_id == run.id).where(Payslip.user_id == user_id)).first()
        
        print(f"  Gross Pay: {slip.gross_pay} (Expected 1200.0)")
        print(f"  Net Pay: {slip.net_pay} (Expected 1150.0)")
        
        assert slip.gross_pay == 1200.0
        assert slip.net_pay == 1150.0
        print("✅ Payroll Calculation Matches Policy")

if __name__ == "__main__":
    run_tests()
