import sys
import os
# Add parent directory to path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.config import get_settings
from backend.core.database import create_db_and_tables, engine
from sqlmodel import Session, select, text

def verify():
    settings = get_settings()
    print(f"Verifying database: {settings.DATABASE_URL.split('@')[-1]}")
    
    with Session(engine) as session:
        try:
            # Check user count
            result = session.exec(text("SELECT count(*) FROM user")).one()
            print(f"User count in remote DB: {result}")
            
            # Check if any Shift data exists (just another check)
            shift_count = session.exec(text("SELECT count(*) FROM shift")).one()
            print(f"Shift count in remote DB: {shift_count}")
            
        except Exception as e:
            print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify()
