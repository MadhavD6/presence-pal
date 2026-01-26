from sqlmodel import Session, select
from datetime import datetime, timedelta, date, time
from backend.core.database import engine
from backend.models.audit import AuditLog
from backend.models.user import User

def seed_attendance():
    with Session(engine) as session:
        # Get demo user
        user = session.exec(select(User).where(User.email == "demo@example.com")).first()
        if not user:
            print("Demo user not found. Run seed_auth.py first.")
            return

        print(f"Seeding data for {user.name} ({user.id})...")
        
        # Clear existing logs for cleaner test
        old_logs = session.exec(select(AuditLog).where(AuditLog.user_id == user.id)).all()
        for log in old_logs:
            session.delete(log)
        session.commit()

        # 1. Today (In Progress - Unpaired)
        today = date.today()
        # In at 9:05 AM
        in_today_1 = AuditLog(
            user_id=user.id,
            timestamp=datetime.combine(today, time(9, 5)),
            event_type="in",
            confidence=0.99,
            identified_name=user.name
        )
        # Redundant In at 9:10 AM (Should be ignored for calculation but shown in list)
        in_today_2 = AuditLog(
            user_id=user.id,
            timestamp=datetime.combine(today, time(9, 10)),
            event_type="in",
            confidence=0.98,
            identified_name=user.name
        )
        session.add(in_today_1)
        session.add(in_today_2)

        # 2. Yesterday (Complete)
        yesterday = today - timedelta(days=1)
        in_yst = AuditLog(
            user_id=user.id,
            timestamp=datetime.combine(yesterday, time(9, 0)),
            event_type="in",
            confidence=0.98
        )
        out_yst = AuditLog(
            user_id=user.id,
            timestamp=datetime.combine(yesterday, time(18, 30)),
            event_type="out",
            confidence=0.98
        )
        session.add(in_yst)
        session.add(out_yst)

        # 3. Dec 1st, 2025 (Complete) - For Timesheet nav check
        # Assuming current date is Jan 2026, Dec 2025 is previous month
        # If today is Jan 13, 2026
        dec_1 = date(2025, 12, 1)
        in_dec = AuditLog(
            user_id=user.id,
            timestamp=datetime.combine(dec_1, time(10, 0)),
            event_type="in",
            confidence=0.95
        )
        out_dec = AuditLog(
            user_id=user.id,
            timestamp=datetime.combine(dec_1, time(19, 0)),
            event_type="out",
            confidence=0.95
        )
        session.add(in_dec)
        session.add(out_dec)

        session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    seed_attendance()
