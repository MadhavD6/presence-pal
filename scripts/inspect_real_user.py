import sys
import os
from datetime import date, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.user import User
from backend.models.audit import AuditLog
from backend.models.shift import Shift
from backend.services.attendance import calculate_daily_stats
from backend.services.payroll_service import aggregate_daily_attendance

def inspect_user(user_id):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            print(f"User {user_id} not found")
            return

        print(f"\n=== User Details ===")
        print(f"ID: {user.id}")
        print(f"Name: {user.name}")
        print(f"Employee ID: {user.employee_id}")
        print(f"Role: {user.role}")
        
        # Logs for today
        print(f"\n=== Audit Logs (Today) ===")
        today_start = datetime.combine(date.today(), datetime.min.time())
        logs = session.exec(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .where(AuditLog.timestamp >= today_start)
            .order_by(AuditLog.timestamp)
        ).all()
        
        if not logs:
            print("No logs found for today.")
        for log in logs:
            print(f"[{log.timestamp.strftime('%H:%M:%S')}] Type: {log.event_type} | Conf: {log.confidence} | Kiosk: {log.kiosk_id}")

        # Calculate Stats
        print(f"\n=== Attendance Calculation ===")
        shift = session.get(Shift, user.shift_id) if user.shift_id else None
        stats = calculate_daily_stats(logs, shift)
        print(f"Daily Status: {stats['attendance_status']}") # Present/Absent
        print(f"Current State: {stats['status']}") # In/Out
        print(f"First In: {stats['first_in']}")
        
        # Only show Last Out if valid or different
        if stats['status'] == 'In':
             print(f"Last Activity: {stats['last_out']} (Still Working)")
        else:
             print(f"Last Out: {stats['last_out']}")

        print(f"Worked: {stats['worked_hours']}")
        
        # Payroll / Summary check
        print(f"\n=== Daily Summary (Payroll) ===")
        try:
            summary = aggregate_daily_attendance(session, user_id, date.today())
            print(f"Summary Status: {summary.status}")
            if summary.status == "MissedPunch":
                print("  (Note: 'MissedPunch' is normal while the shift is still in progress with odd number of punches)")
            print(f"Payable Regular Hours: {summary.regular_hours}")
            print(f"Overtime Hours: {summary.overtime_hours}")
        except Exception as e:
            print(f"Error calculating summary: {e}")

if __name__ == "__main__":
    inspect_user(13)
