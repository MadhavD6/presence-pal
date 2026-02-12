
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import create_engine, text
from backend.core.config import get_settings
from backend.models.shift import Shift

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

def migrate():
    print("Migrating Shift model...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE shift ADD COLUMN crosses_midnight BOOLEAN DEFAULT 0"))
            conn.commit()
            print("✅ Added 'crosses_midnight' column successfully.")
        except Exception as e:
            print(f"⚠️ Shift migration skipped (or column exists): {e}")
            
        try:
            conn.execute(text("ALTER TABLE employeeshift ADD COLUMN weekly_offs VARCHAR DEFAULT '6'"))
            conn.commit()
            print("✅ Added 'weekly_offs' column successfully.")
        except Exception as e:
            print(f"⚠️ EmployeeShift migration skipped (or column exists): {e}")
            
        try:
            conn.execute(text("ALTER TABLE user ADD COLUMN department VARCHAR"))
            conn.commit()
            print("✅ Added 'department' column successfully.")
        except Exception as e:
            print(f"⚠️ User department migration skipped (or column exists): {e}")

if __name__ == "__main__":
    migrate()
