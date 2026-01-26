import sys
import os
from datetime import datetime, date, time, timedelta
from sqlmodel import Session, select, create_engine

sys.path.append(os.getcwd())

from backend.models.user import User
from backend.models.shift import Shift
from backend.models.audit import AuditLog
from backend.models.payroll import PayrollConfig, DailySummary, PayrollRun, Payslip
from backend.core.config import get_settings
from backend.services.payroll_service import aggregate_daily_attendance, generate_payroll_run, get_or_create_config

def verify_manager_flow():
    print("--- Verifying Phase 4: Manager Payroll ---")
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        # Setup User
        user = session.exec(select(User).where(User.employee_id == "MGR_TEST_USER")).first()
        if not user:
            user = User(name="Mgr Test", employee_id="MGR_TEST_USER", role="user")
            session.add(user)
            session.commit()
            session.refresh(user)
            
        # Config
        config = get_or_create_config(session, user.id)
        config.base_hourly_rate = 50.0 
        session.add(config)
        session.commit()
        
        # Scenario: 2 Days. 
        # Day 1: Perfect.
        # Day 2: Missed Punch.
        
        d1 = date.today() - timedelta(days=1)
        d2 = date.today()
        
        # Clean logs
        session.exec(select(AuditLog).where(AuditLog.user_id == user.id)).all() # load
        logs = session.exec(select(AuditLog).where(AuditLog.user_id == user.id)).all()
        for l in logs: session.delete(l)
        
        # Clean Runs & Payslips
        slips = session.exec(select(Payslip)).all()
        for s in slips: session.delete(s)
        
        runs = session.exec(select(PayrollRun)).all()
        for r in runs: session.delete(r)
        
        session.commit()
        
        # Day 1: 9-17 (8h)
        l1 = AuditLog(user_id=user.id, event_type="in", timestamp=datetime.combine(d1, time(9,0)), confidence=1.0)
        l2 = AuditLog(user_id=user.id, event_type="out", timestamp=datetime.combine(d1, time(17,0)), confidence=1.0)
        
        # Day 2: 9-?? (Missed Out)
        l3 = AuditLog(user_id=user.id, event_type="in", timestamp=datetime.combine(d2, time(9,0)), confidence=1.0)
        # No out
        
        session.add(l1); session.add(l2); session.add(l3)
        session.commit()
        
        # 1. Aggregate
        print("Aggregating...")
        aggregate_daily_attendance(session, user.id, d1)
        aggregate_daily_attendance(session, user.id, d2)
        
        # Verify Day 2 is MissedPunch
        s2 = session.exec(select(DailySummary).where(DailySummary.user_id == user.id, DailySummary.date == d2)).first()
        print(f"Day 2 Status: {s2.status}")
        assert s2.status == "MissedPunch" or s2.total_hours == 0
        
        # 2. Generate Run (Manager Action)
        print("Generating Run...")
        run = generate_payroll_run(session, d1, d2)
        print(f"Run ID: {run.id}, Total: {run.total_payout}")
        
        # Check Payslip Status
        slip = session.exec(select(Payslip).where(Payslip.run_id == run.id, Payslip.user_id == user.id)).first()
        print(f"DEBUG SCRIPT: User ID: {user.id}")
        if slip:
            print(f"DEBUG SCRIPT: Slip ID: {slip.id}, User ID: {slip.user_id}, Status: {slip.status}, Warnings: {slip.warnings}")
        else:
            print("DEBUG SCRIPT: Slip not found!")
            
        print(f"Payslip Status: {slip.status}")
        print(f"Warnings: {slip.warnings}")
        
        assert slip.status == "Blocked"
        assert "Missed Punch" in slip.warnings
        
        # 3. Try Finalize (Should Fail)
        print("Attempting to Finalize (Expect Failure)...")
        # Simulating Manager Router Logic
        can_finalize = True
        slips = session.exec(select(Payslip).where(Payslip.run_id == run.id)).all()
        if any(s.status == "Blocked" for s in slips):
            can_finalize = False
            
        print(f"Can Finalize? {can_finalize}")
        assert can_finalize == False
        
        # 4. Fix Issue
        print("Fixing Issue (Adding Out Punch)...")
        l4 = AuditLog(user_id=user.id, event_type="out", timestamp=datetime.combine(d2, time(17,0)), confidence=1.0)
        session.add(l4)
        session.commit()
        
        # Re-aggregate
        aggregate_daily_attendance(session, user.id, d2)
        
        # Re-generate (Manager would create NEW run or update? Logic creates new run usually)
        # Let's delete old run to keep it clean for test
        session.delete(run)
        session.delete(slip) 
        session.commit()
        
        print("Regenerating Run...")
        run_new = generate_payroll_run(session, d1, d2)
        slip_new = session.exec(select(Payslip).where(Payslip.run_id == run_new.id, Payslip.user_id == user.id)).first()
        
        print(f"New Payslip Status: {slip_new.status}")
        assert slip_new.status == "Ready"
        
        # 5. Finalize (Should Success)
        can_finalize = True
        slips = session.exec(select(Payslip).where(Payslip.run_id == run_new.id)).all()
        if any(s.status == "Blocked" for s in slips):
            can_finalize = False
            
        print(f"Can Finalize? {can_finalize}")
        assert can_finalize == True
        
        run_new.is_finalized = True
        session.add(run_new)
        session.commit()
        
        print("✅ SUCCESS: Manager Payroll Flow Verified!")

if __name__ == "__main__":
    verify_manager_flow()
