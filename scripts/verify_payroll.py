import sys
import os
from datetime import datetime, date, time
from sqlmodel import Session, select, create_engine

# Add project root
sys.path.append(os.getcwd())

from backend.models.user import User
from backend.models.shift import Shift
from backend.models.audit import AuditLog
from backend.models.payroll import PayrollConfig, DailySummary, PayrollRun, Payslip
from backend.core.config import get_settings
from backend.services.payroll_service import aggregate_daily_attendance, generate_payroll_run, get_or_create_config

def verify_payroll():
    print("--- Verifying Phase 3: Payroll Logic ---")
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        # 1. Setup Data
        # User
        user = session.exec(select(User).where(User.employee_id == "PAYROLL_TEST_USER")).first()
        if not user:
            user = User(name="Payroll Test", employee_id="PAYROLL_TEST_USER", role="user")
            session.add(user)
            session.commit()
            session.refresh(user)
            
        print(f"User ID: {user.id}")
        
        # Payroll Config
        config = get_or_create_config(session, user.id)
        config.base_hourly_rate = 100.0 # Clear number
        config.overtime_multiplier = 1.5
        session.add(config)
        session.commit()
        
        # Shift
        shift = session.exec(select(Shift).where(Shift.name == "Payroll Shift")).first()
        if not shift:
            shift = Shift(name="Payroll Shift", start_time=time(9,0), end_time=time(18,0), grace_period_mins=30) # 30 min grace
            session.add(shift)
            session.commit()
        
        user.shift_id = shift.id
        session.add(user)
        session.commit()
        
        # Clean logs/summaries/slips for today
        today = date.today()
        session.exec(select(AuditLog).where(AuditLog.user_id == user.id)).all()
        # To avoid deleting other tests, we just use specific dates or clean carefully? 
        # Ideally clean all related to this user.
        logs = session.exec(select(AuditLog).where(AuditLog.user_id == user.id)).all()
        for l in logs: session.delete(l)
        
        sums = session.exec(select(DailySummary).where(DailySummary.user_id == user.id)).all()
        for s in sums: session.delete(s)
        
        slips = session.exec(select(Payslip).where(Payslip.user_id == user.id)).all()
        for s in slips: session.delete(s)
        
        session.commit()

        # 2. Test Cases
        
        # Case A: On Time, 9 Hours Work (1h Overtime)
        # Shift 9-18 (9h total span). If work 9-19 (10h span, minus break? Logic uses simple duration)
        # Let's say 9:00 - 18:00 is 9 hours. Standard is 8. So 1h OT.
        print("\nCase A: On Time, 1h Overtime (09:00 - 18:00 = 9h)")
        l1 = AuditLog(user_id=user.id, event_type="in", timestamp=datetime.combine(today, time(9,0)), confidence=1.0)
        l2 = AuditLog(user_id=user.id, event_type="out", timestamp=datetime.combine(today, time(18,0)), confidence=1.0)
        session.add(l1); session.add(l2)
        session.commit()
        
        summary_a = aggregate_daily_attendance(session, user.id, today)
        print(f"  Status: {summary_a.status}")
        print(f"  Is Late: {summary_a.is_late}")
        print(f"  Regular Hrs: {summary_a.regular_hours}")
        print(f"  OT Hrs: {summary_a.overtime_hours}")
        
        assert summary_a.is_late == False
        assert summary_a.regular_hours == 8.0
        assert summary_a.overtime_hours == 1.0 # 9h total - 8h std = 1h OT
        
        # Case B: Late, 9 Hours Work
        # Clear logs
        print("\nCase B: Late (09:40 > 9:30), 9h Work")
        session.delete(l1); session.delete(l2); session.commit()
        
        l3 = AuditLog(user_id=user.id, event_type="in", timestamp=datetime.combine(today, time(9,40)), confidence=1.0)
        l4 = AuditLog(user_id=user.id, event_type="out", timestamp=datetime.combine(today, time(18,40)), confidence=1.0) # 9h work
        session.add(l3); session.add(l4); session.commit()
        
        # We need to clear summary to re-calc? aggregate_daily update logic checks if exists.
        # It updates existing.
        summary_b = aggregate_daily_attendance(session, user.id, today)
        print(f"  Is Late: {summary_b.is_late}")
        print(f"  Late Mins: {summary_b.is_late}") # Boolean, but logic inside calculated mins
        
        assert summary_b.is_late == True
        assert summary_b.regular_hours == 8.0
        assert summary_b.overtime_hours == 1.0
        
        # 3. Generate Payslip
        print("\nGenerating Payslip...")
        run = generate_payroll_run(session, today, today) # Run for just today
        
        slip = session.exec(select(Payslip).where(Payslip.run_id == run.id).where(Payslip.user_id == user.id)).first()
        
        print(f"  Gross: {slip.gross_pay}")
        print(f"  Deductions: {slip.total_deductions}") # Late fee
        print(f"  Net: {slip.net_pay}")
        
        # Expected:
        # Regular: 8h * 100 = 800
        # OT: 1h * 100 * 1.5 = 150
        # Gross: 950
        # Late Deduction: 1 late day * (0.5 * 100) = 50
        # Net: 900
        
        assert slip.gross_pay == 950.0
        assert slip.total_deductions == 50.0
        assert slip.net_pay == 900.0
        
        print("\n✅ SUCCESS: All Payroll Logic Verified!")

if __name__ == "__main__":
    verify_payroll()
