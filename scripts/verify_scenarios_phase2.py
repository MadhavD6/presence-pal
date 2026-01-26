import sys
import os
from datetime import datetime, date, time
from sqlmodel import Session, select, create_engine, SQLModel
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.getcwd())

from backend.main import app
from backend.models.user import User
from backend.models.shift import Shift
from backend.models.audit import AuditLog
from backend.core.database import get_session
from backend.routers import employee

# Setup DB connection (using the actual dev DB or a test one? 
# Using actual DB with a designated Test User is safest for "real" behavior verification without complex mocking)
from backend.core.config import get_settings
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

def setup_test_user(session: Session):
    # Check if exists
    user = session.exec(select(User).where(User.employee_id == "TEST_999")).first()
    if not user:
        user = User(
            name="Test Verification User", 
            employee_id="TEST_999", 
            role="user",
            hashed_password="fake_hash"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

def setup_shift(session: Session, name="Test Shift"):
    shift = session.exec(select(Shift).where(Shift.name == name)).first()
    if not shift:
        shift = Shift(
            name=name,
            start_time=time(9, 0),
            end_time=time(18, 0),
            grace_period_mins=15
        )
        session.add(shift)
        session.commit()
        session.refresh(shift)
    return shift

def clear_logs(session: Session, user_id: int):
    logs = session.exec(select(AuditLog).where(AuditLog.user_id == user_id)).all()
    for log in logs:
        session.delete(log)
    session.commit()

async def run_scenarios():
    print("--- Starting Manual Verification Scenarios A-D ---")
    
    with Session(engine) as session:
        user = setup_test_user(session)
        shift = setup_shift(session)
        
        # Assign shift
        user.shift_id = shift.id
        session.add(user)
        session.commit()
        session.refresh(user)

        # --- Scenario A: On Time ---
        print("\nScenario A: On Time (09:12 AM)")
        clear_logs(session, user.id)
        
        # Add punch at 09:12 Today
        today = date.today()
        # Ensure we delete any existing punches for today to be clean
        # (Running verify clears all logs for user, so we are good)
        
        log_in = AuditLog(
            user_id=user.id,
            event_type="in",
            timestamp=datetime.combine(today, time(9, 12)),
            confidence=0.9
        )
        session.add(log_in)
        session.commit()
        
        # Call Endpoint Logic directly to avoid Auth Token hassle in script
        # We can call the function `get_my_dashboard` injecting dependencies
        dashboard = await employee.get_my_dashboard(current_user=user, session=session)
        
        print(f"  Status: {dashboard.today_status}")
        print(f"  First In: {dashboard.first_in}")
        print(f"  Is Late: {dashboard.is_late}")
        
        if dashboard.today_status == "In" and not dashboard.is_late:
            print("  ✅ Scenario A PASS")
        else:
            print("  ❌ Scenario A FAIL")

        # --- Scenario B: Late ---
        print("\nScenario B: Late (09:25 AM)")
        clear_logs(session, user.id)
        
        log_in_late = AuditLog(
            user_id=user.id,
            event_type="in",
            timestamp=datetime.combine(today, time(9, 25)),
            confidence=0.9
        )
        session.add(log_in_late)
        session.commit()
        
        dashboard = await employee.get_my_dashboard(current_user=user, session=session)
        
        print(f"  Status: {dashboard.today_status}")
        print(f"  Is Late: {dashboard.is_late}")
        print(f"  Late Mins: {dashboard.late_minutes}")
        
        # Expected: Late, 25 mins (since 9:25 - 9:00 = 25)
        if dashboard.is_late and dashboard.late_minutes == 25:
             print("  ✅ Scenario B PASS")
        else:
             print(f"  ❌ Scenario B FAIL (Got {dashboard.late_minutes} mins)")

        # --- Scenario C: No Shift Assigned ---
        print("\nScenario C: No Shift Assigned")
        user.shift_id = None
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Re-run dashboard fetch (reuse Scenario B data or clear? Let's clear)
        clear_logs(session, user.id)
        
        dashboard = await employee.get_my_dashboard(current_user=user, session=session)
        
        print(f"  Current Shift: {dashboard.current_shift}")
        
        if "General Shift" in dashboard.current_shift:
            print("  ✅ Scenario C PASS")
        else:
            print(f"  ❌ Scenario C FAIL (Got {dashboard.current_shift})")

        # --- Scenario D: Timesheet Visuals ---
        print("\nScenario D: Timesheet Visuals (Late Punch)")
        # Re-setup Scenario B data (Late)
        user.shift_id = shift.id
        session.add(user)
        session.commit()
        
        log_in_late = AuditLog(
            user_id=user.id,
            event_type="in",
            timestamp=datetime.combine(today, time(9, 30)), # Very late
            confidence=0.9
        )
        log_out = AuditLog(
            user_id=user.id,
            event_type="out",
            timestamp=datetime.combine(today, time(18, 0)),
            confidence=0.9
        )
        session.add(log_in_late)
        session.add(log_out)
        session.commit()
        
        # Fetch timesheet
        month_str = today.strftime("%Y-%m")
        timesheet = await employee.get_my_timesheet(month=month_str, current_user=user, session=session)
        
        # Find today
        today_entry = next((d for d in timesheet if d.date == today), None)
        
        if today_entry:
            print(f"  Date: {today_entry.date}")
            print(f"  Status: {today_entry.status}")
            print(f"  Color: {today_entry.color}")
            print(f"  Is Late: {today_entry.is_late}")
            
            # Logic says color is "green" if Present, but checked `is_late` flag. 
            # The backend explicitly sets color="green" if Present. 
            # Frontend uses `is_late` to override/add visual.
            # So checking `is_late` is the key here.
            
            if today_entry.status == "Present" and today_entry.is_late:
                 print("  ✅ Scenario D PASS")
            else:
                 print("  ❌ Scenario D FAIL")
        else:
            print("  ❌ Scenario D FAIL (Entry not found)")
            
        # Cleanup
        clear_logs(session, user.id)
        session.delete(user)
        # Keep shift as it might be used by others or is harmless
        session.commit()
        print("\nCleanup Complete.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_scenarios())
