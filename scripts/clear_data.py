import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, text
from backend.core.database import engine

def clear_data():
    with Session(engine) as session:
        # Disable foreign key checks to allow truncation order independence
        session.exec(text("PRAGMA foreign_keys = OFF;"))
        
        tables = ["auditlog", "embedding", "employeeshift", "payrollitem", "payrollrun", "user", "shift", "leave", "kiosk"]
        for table in tables:
            try:
                session.exec(text(f"DELETE FROM {table};"))
                # SQLite doesn't reuse auto-increment IDs unless you clear sqlite_sequence
                session.exec(text(f"DELETE FROM sqlite_sequence WHERE name='{table}';"))
                print(f"Cleared table: {table}")
            except Exception as e:
                print(f"Error clearing {table}: {e}")
        
        session.exec(text("PRAGMA foreign_keys = ON;"))
        session.commit()
        print("All data cleared successfully.")

        # Re-initialize Vector Engine in-memory if running? 
        # Since this is a script, the running server won't know until next reload or cache clear.
        # But we are going to restart the server or rely on it picking up empty DB on next request if it re-checks.
        # VectorService loads on startup. We might need to restart backend.

if __name__ == "__main__":
    clear_data()
