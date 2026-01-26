import sys
import os
 
# Add project root to path
sys.path.append(os.getcwd())

from sqlmodel import SQLModel, create_engine
from backend.core.config import get_settings
from backend.models.user import User  # Needed for FK resolution
from backend.models.payroll import PayrollConfig, DailySummary, PayrollRun, Payslip

def migrate():
    settings = get_settings()
    print(f"Migrating Payroll DB at: {settings.DATABASE_URL}")
    
    engine = create_engine(settings.DATABASE_URL)
    
    # SQLModel.metadata.create_all(engine) will create ALL tables in metadata.
    # Since other tables exist, it checks and skips them, or creates missing ones.
    # This is safe for adding new tables.
    print("Creating Phase 3 tables...")
    SQLModel.metadata.create_all(engine)
    print("Migration Phase 3 Complete.")

if __name__ == "__main__":
    migrate()
