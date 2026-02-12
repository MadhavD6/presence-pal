
import sys
import os
from sqlmodel import Session, select
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.database import engine
from backend.models.audit import AuditLog

def check_logs():
    with Session(engine) as session:
        logs = session.exec(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10)).all()
        print(f"Found {len(logs)} recent logs:")
        print("-" * 50)
        for log in logs:
            print(f"Time: {log.timestamp}")
            print(f"User ID: {log.user_id} | Name: {log.identified_name}")
            print(f"Confidence: {log.confidence}")
            print(f"Event: {log.event_type}")
            print(f"Error: {log.error_code}")
            print(f"Match Type: {log.match_type}")
            if log.metadata_info:
                print(f"Metadata: {log.metadata_info}")
            print("-" * 50)

if __name__ == "__main__":
    check_logs()
