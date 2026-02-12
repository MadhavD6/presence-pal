import sys
import os
import shutil
from sqlmodel import SQLModel, create_engine, Session, select, text
from dotenv import load_dotenv

# ============================================================
# PRODUCTION SAFETY GUARD
# This script TRUNCATES and DELETES data from the destination DB.
# It will NOT run unless ALLOW_DESTRUCTIVE_SCRIPTS=true is set.
# ============================================================
if os.getenv("ALLOW_DESTRUCTIVE_SCRIPTS", "false").lower() != "true":
    print("❌ BLOCKED: This script modifies the remote database.")
    print("   To run, set environment variable: ALLOW_DESTRUCTIVE_SCRIPTS=true")
    sys.exit(1)

# Add parent directory to path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load backend .env explicitly
backend_env_path = os.path.join(os.path.dirname(__file__), '../.env.production')
print(f"Loading .env from: {backend_env_path}")
load_dotenv(backend_env_path, override=True)

from backend.core.config import get_settings
from backend.models.kiosk import Kiosk
from backend.models.user import User, Embedding
from backend.models.shift import Shift
from backend.models.site import Site
from backend.models.audit import AuditLog
from backend.models.holiday import Holiday
from backend.models.leave import Leave
from backend.models.payroll import PayrollConfig, DailySummary, PayrollRun, Payslip
from backend.models.gallery import FaceGallery
from backend.models.correction import AttendanceCorrection

def migrate():
    print("Starting migration from SQLite (kiosk.db) to Remote MySQL...")

    # SQLite Connection (Source)
    # Using kiosk.db in the project root
    sqlite_url = "sqlite:///kiosk.db"
    print(f"Source: {sqlite_url}")
    
    source_engine = create_engine(sqlite_url)

    # Remote MySQL Connection (Destination)
    settings = get_settings()
    dest_url = settings.DATABASE_URL
    print(f"Destination: {dest_url}")
    
    if "localhost" in dest_url or "127.0.0.1" in dest_url:
        print("WARNING: Destination looks like localhost. Ensure backend/.env is pointing to REMOTE.")
        if "n8n.prodify.co.in" not in dest_url:
             print("Aborting to prevent local data overwrite.")
             return
    
    dest_engine = create_engine(dest_url)

    # maintain a list of all models to migrate in dependency order
    ordered_models = [
        Site,
        Shift,
        Holiday,
        Kiosk,
        User,
        Embedding,      
        FaceGallery,
        AuditLog,
        Leave,
        AttendanceCorrection, 
        PayrollConfig,
        DailySummary,
        PayrollRun,
        Payslip
    ]
    
    # Create tables in MySQL (Destination) - SQLModel metadata does this, but good to ensure
    print("Ensuring tables exist in destination...")
    SQLModel.metadata.create_all(dest_engine)

    # Helper function to migrate data for a specific model
    def migrate_model(model_cls, session_source, session_dest):
        model_name = model_cls.__name__
        print(f"Migrating {model_name}...")
        try:
            records = session_source.exec(select(model_cls)).all()
            if not records:
                print(f"No records found for {model_name}.")
                return 0
            
            count = 0
            for record in records:
                data = record.model_dump()
                # Handle potential ID conflicts or differences? SQLite might have different types? 
                # Usually SQLModel handles basics.
                new_record = model_cls(**data)
                session_dest.add(new_record)
                count += 1
            
            session_dest.commit()
            print(f"Migrated {count} records for {model_name}.")
            return count
        except Exception as e:
            # Check for duplicate entry error
            if "Duplicate entry" in str(e):
                 print(f"Skipping duplicates for {model_name}")
                 session_dest.rollback()
                 return 0
            
            print(f"Error migrating {model_name}: {e}")
            session_dest.rollback()
            return 0

    # Perform Migration
    total_migrated = 0
    
    with Session(source_engine) as source_session, Session(dest_engine) as dest_session:
        # Clear existing data in destination
        print("Clearing existing data in destination (if any)...")
        try:
            dest_session.exec(text("SET FOREIGN_KEY_CHECKS = 0;"))
            for model in reversed(ordered_models):
                try:
                    # Use backticks for table name specifically for 'leave' and safety
                    dest_session.exec(text(f"TRUNCATE TABLE `{model.__tablename__}`;"))
                except Exception as table_err:
                     # Fallback to DELETE if TRUNCATE fails (though TRUNCATE shouldn't fail on MySQL usually)
                     print(f"Truncate failed for {model.__tablename__}, trying DELETE: {table_err}")
                     dest_session.exec(text(f"DELETE FROM `{model.__tablename__}`;"))

            dest_session.exec(text("SET FOREIGN_KEY_CHECKS = 1;"))
            dest_session.commit()
        except Exception as e:
            print(f"Warning clearing tables: {e}")
            dest_session.rollback()

        for model in ordered_models:
            total_migrated += migrate_model(model, source_session, dest_session)

    print(f"Migration completed. Total records migrated: {total_migrated}")

if __name__ == "__main__":
    migrate()
