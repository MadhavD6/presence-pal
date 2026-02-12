import sys
import os

# ============================================================
# PRODUCTION SAFETY GUARD
# This script contains DESTRUCTIVE operations (DELETE).
# It will NOT run unless ALLOW_DESTRUCTIVE_SCRIPTS=true is set.
# ============================================================
if os.getenv("ALLOW_DESTRUCTIVE_SCRIPTS", "false").lower() != "true":
    print("❌ BLOCKED: This script clears test data.")
    print("   To run, set environment variable: ALLOW_DESTRUCTIVE_SCRIPTS=true")
    sys.exit(1)

from sqlmodel import Session, select, delete
from backend.core.database import engine
# Models to Clear
from backend.models.audit import AuditLog
from backend.models.leave import Leave
try:
    from backend.models.correction import AttendanceCorrection
except ImportError:
    AttendanceCorrection = None

try:
    from backend.models.shift import EmployeeShift
except ImportError:
    EmployeeShift = None

try:
    from backend.models.payroll import PayrollRun, PayrollSlip
except ImportError:
    PayrollRun = None
    PayrollSlip = None

def clear_data():
    print("Connecting to DB...")
    with Session(engine) as session:
        print("Clearing Audit Logs (Punches)...")
        session.exec(delete(AuditLog))
        
        print("Clearing Leaves...")
        session.exec(delete(Leave))
        
        if AttendanceCorrection:
            print("Clearing Corrections...")
            session.exec(delete(AttendanceCorrection))
            
        if EmployeeShift:
            print("Clearing Employee Shift History...")
            session.exec(delete(EmployeeShift))
            
        if PayrollSlip:
            print("Clearing Payroll Slips...")
            session.exec(delete(PayrollSlip))
            
        if PayrollRun:
            print("Clearing Payroll Runs...")
            session.exec(delete(PayrollRun))
            
        session.commit()
        print("Transaction Data Cleared Successfully.")
        print("Users, Sites, Kiosks, and Shift Definitions were PRESERVED.")

if __name__ == "__main__":
    clear_data()
