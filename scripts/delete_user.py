
import sys
import os
from sqlmodel import Session, select, delete

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# PRODUCTION SAFETY GUARD
# This script contains DESTRUCTIVE operations.
# It will NOT run unless ALLOW_DESTRUCTIVE_SCRIPTS=true is set.
# ============================================================
if os.getenv("ALLOW_DESTRUCTIVE_SCRIPTS", "false").lower() != "true":
    print("❌ BLOCKED: This script deletes user data.")
    print("   To run, set environment variable: ALLOW_DESTRUCTIVE_SCRIPTS=true")
    sys.exit(1)

from backend.core.database import engine
from backend.models.user import User
from backend.models.audit import AuditLog
from backend.models.gallery import FaceGallery
from backend.models.leave import Leave
from backend.models.correction import AttendanceCorrection
from backend.models.site import Site
# payroll and shift might have robust dependencies, we'll try to delete what matches user_id
try:
    from backend.models.payroll import PayrollSlip
except ImportError:
    PayrollSlip = None

try:
    from backend.models.shift import ShiftAssignment
except ImportError:
    # Might be named differently in shift.py
    ShiftAssignment = None

def delete_user(query):
    with Session(engine) as session:
        user = None
        # Try as ID first
        if query.isdigit():
            user = session.get(User, int(query))
        
        if not user:
            # Try as name
            users = session.exec(select(User).where(User.name.ilike(f"%{query}%"))).all()
            if not users:
                print(f"No user found matching '{query}'")
                return
            if len(users) > 1:
                print(f"Found {len(users)} users matching '{query}'. Use ID to delete specific user:")
                for u in users:
                    print(f" - {u.name} (ID: {u.id}, EMP: {u.employee_id})")
                return
            user = users[0]

        print(f"Deleting user: {user.name} (ID: {user.id}, EMP: {user.employee_id})")
        
        # 1. Delete Audit Logs
        logs = session.exec(select(AuditLog).where(AuditLog.user_id == user.id)).all()
        print(f" - Deleting {len(logs)} Audit Logs...")
        for log in logs:
            session.delete(log)
            
        # 2. Delete Gallery Entries
        gallery = session.exec(select(FaceGallery).where(FaceGallery.user_id == user.id)).all()
        print(f" - Deleting {len(gallery)} Face Gallery entries...")
        for g in gallery:
            session.delete(g)
            
        # 3. Delete Leaves
        leaves = session.exec(select(Leave).where(Leave.user_id == user.id)).all()
        print(f" - Deleting {len(leaves)} Leave Requests...")
        for l in leaves:
            session.delete(l)
            
        # 4. Delete Corrections
        corrections = session.exec(select(AttendanceCorrection).where(AttendanceCorrection.user_id == user.id)).all()
        print(f" - Deleting {len(corrections)} Correction Requests...")
        for c in corrections:
            session.delete(c)

        # 5. Delete Payroll Slips
        if PayrollSlip:
            slips = session.exec(select(PayrollSlip).where(PayrollSlip.user_id == user.id)).all()
            print(f" - Deleting {len(slips)} Payroll Slips...")
            for s in slips:
                session.delete(s)
                
        # 6. Delete User
        session.delete(user)
        
        session.commit()
        print("\nSuccess! User and all related data deleted.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_user.py <name_or_id>")
    else:
        delete_user(sys.argv[1])
