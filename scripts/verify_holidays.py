import sys
import os
from datetime import datetime, date, time, timedelta
from sqlmodel import Session, select, create_engine

sys.path.append(os.getcwd())

from backend.models.user import User
from backend.models.audit import AuditLog
from backend.models.holiday import Holiday
from backend.models.payroll import PayrollConfig, DailySummary, PayrollRun, Payslip
from backend.core.config import get_settings
from backend.services.payroll_service import aggregate_daily_attendance, generate_payroll_run, get_or_create_config

def verify_holidays_flow():
    print("--- Verifying Phase 5: Holiday Management ---")
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        # Setup User
        user = session.exec(select(User).where(User.employee_id == "HOLIDAY_TEST_USER")).first()
        if not user:
            user = User(name="Holiday Test", employee_id="HOLIDAY_TEST_USER", role="user")
            session.add(user)
            session.commit()
            session.refresh(user)
            
        # Config
        config = get_or_create_config(session, user.id)
        config.base_hourly_rate = 50.0 
        session.add(config)
        session.commit()
        
        # Scenario: 
        # Target Date: Tomorrow (to avoid conflict with today's real data potentially)
        # Actually let's use a specific past date to ensure aggregation logic is stable.
        # Date X: User is ABSENT (No punches).
        
        target_date = date.today() - timedelta(days=10)
        
        # Clean logs/summaries/holidays for this day
        session.exec(select(AuditLog).where(AuditLog.user_id == user.id)).all() # load
        logs = session.exec(select(AuditLog).where(AuditLog.user_id == user.id)).all()
        # Filter for target date
        logs = [l for l in logs if l.timestamp.date() == target_date]
        for l in logs: session.delete(l)
        
        summaries = session.exec(select(DailySummary).where(DailySummary.user_id == user.id, DailySummary.date == target_date)).all()
        for s in summaries: session.delete(s)
        
        holidays = session.exec(select(Holiday).where(Holiday.date == target_date)).all()
        for h in holidays: session.delete(h)
        
        session.commit()
        
        # 1. Verify Baseline: Absent
        print(f"1. Baseline: Absent on {target_date}")
        summary = aggregate_daily_attendance(session, user.id, target_date)
        print(f"Status: {summary.status}, Hours: {summary.total_hours}")
        # Assuming Absent -> 0 hours. Or MissedPunch depending on logic.
        # But absence usually means no logs. 
        # Our logic handles logs. If NO logs?
        # calculate_daily_stats -> if no logs -> "Absent".
        # aggregate -> if "Absent" -> is_late? Usually Absent is not "Late", it's Absent.
        # Attendance logic might return "Absent".
        
        assert summary.status == "Absent"
        assert summary.total_hours == 0
        
        # 2. Creating Holiday
        print("2. Creating Holiday")
        holiday = Holiday(date=target_date, name="Test Holiday", is_national=True)
        session.add(holiday)
        session.commit()
        
        # 3. Aggregate with Holiday
        print("3. Aggregating with Holiday...")
        summary = aggregate_daily_attendance(session, user.id, target_date)
        print(f"Status: {summary.status}, Hours: {summary.total_hours}, Late: {summary.is_late}")
        
        assert summary.status == "Holiday"
        assert summary.total_hours == 8.0
        assert summary.is_late == False
        
        # 4. Generate Payroll Run Snippet
        print("4. Checking Payroll Calculation...")
        # Just manually check expected pay
        # 50/hr * 8 = 400.
        pay = summary.regular_hours * config.base_hourly_rate
        print(f"Pay: {pay}")
        assert pay == 400.0
        
        # 5. Delete Holiday
        print("5. Deleting Holiday & Reverting...")
        session.delete(holiday)
        session.commit()
        
        summary = aggregate_daily_attendance(session, user.id, target_date)
        print(f"Status: {summary.status}")
        
        assert summary.status == "Absent"
        
        print("✅ SUCCESS: Holiday Flow Verified!")

if __name__ == "__main__":
    verify_holidays_flow()
