from sqlmodel import Session, create_engine, text
from backend.core.config import get_settings
import os
import sys

# Add parent dir to path
sys.path.append(os.getcwd())

def migrate_phase4():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    print(f"Migrating Phase 4 (Manager Payroll) at: {settings.DATABASE_URL}")
    
    with Session(engine) as session:
        # Check if columns exist
        try:
            session.exec(text("SELECT status FROM payslip LIMIT 1"))
            print("Column 'status' already exists.")
        except Exception:
            print("Adding column 'status'...")
            session.exec(text("ALTER TABLE payslip ADD COLUMN status TEXT DEFAULT 'Ready'"))
            
        try:
            session.exec(text("SELECT warnings FROM payslip LIMIT 1"))
            print("Column 'warnings' already exists.")
        except Exception:
            print("Adding column 'warnings'...")
            session.exec(text("ALTER TABLE payslip ADD COLUMN warnings TEXT DEFAULT '[]'"))
            
        session.commit()
    
    print("Migration Phase 4 Complete.")

if __name__ == "__main__":
    migrate_phase4()
