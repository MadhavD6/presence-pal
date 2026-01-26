from sqlmodel import Session, create_engine, text
from backend.core.config import get_settings
from backend.models.holiday import Holiday
import os
import sys

# Add parent dir to path
sys.path.append(os.getcwd())

def migrate_phase5():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    print(f"Migrating Phase 5 (Holidays) at: {settings.DATABASE_URL}")
    
    # We need to import all models to ensure metadata is populated.
    from sqlmodel import SQLModel
    from backend.models.user import User
    from backend.models.shift import Shift
    from backend.models.audit import AuditLog
    from backend.models.leave import Leave
    from backend.models.payroll import Payslip, PayrollRun, PayrollConfig, DailySummary
    # from backend.models.kiosk import KioskConfig # KioskConfig doesn't exist? KioskSession? 
    from backend.models.kiosk import Kiosk
    # Holiday already imported at top, but ensure it's in metadata
    from backend.models.holiday import Holiday
    
    SQLModel.metadata.create_all(engine)
    
    print("Migration Phase 5 Complete (Holiday table created).")

if __name__ == "__main__":
    migrate_phase5()
