import sys
import os
import shutil
from sqlmodel import SQLModel, create_engine, Session, select, text

# Add parent directory to path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.config import get_settings
from backend.models.kiosk import Kiosk
from backend.models.user import User
from backend.models.shift import Shift
from backend.models.site import Site
from backend.models.audit import AuditLog
from backend.models.holiday import Holiday
from backend.models.leave import Leave
from backend.models.payroll import PayrollConfig, DailySummary, PayrollRun, Payslip
from backend.models.gallery import FaceGallery

def migrate():
    print("Starting migration from SQLite to MySQL...")

    # SQLite Connection (Source)
    sqlite_url = "sqlite:///./kiosk.db"
    sqlite_engine = create_engine(sqlite_url)

    # MySQL Connection (Destination)
    settings = get_settings()
    mysql_url = settings.DATABASE_URL
    
    if "sqlite" in mysql_url:
        print("Error: Destination database URL is still SQLite. Please check .env file.")
        print(f"Current URL: {mysql_url}")
        return

    print(f"Destination: {mysql_url}")
    mysql_engine = create_engine(mysql_url)

    # maintain a list of all models to migrate in dependency order
    ordered_models = [
        Site,
        Shift,
        Holiday,
        Kiosk,
        User,
        FaceGallery,
        AuditLog,
        Leave,
        PayrollConfig,
        DailySummary,
        PayrollRun,
        Payslip
    ]
    
    # Create tables in MySQL
    print("Creating tables in MySQL...")
    try:
        SQLModel.metadata.create_all(mysql_engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        return

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
                new_record = model_cls(**data)
                session_dest.add(new_record)
                count += 1
            
            session_dest.commit()
            print(f"Migrated {count} records for {model_name}.")
            return count
        except Exception as e:
            print(f"Error migrating {model_name}: {e}")
            session_dest.rollback()
            return 0

    # Perform Migration
    total_migrated = 0
    
    with Session(sqlite_engine) as source_session, Session(mysql_engine) as dest_session:
        # Clear existing data in destination
        print("Clearing existing data in destination (if any)...")
        try:
            dest_session.exec(text("SET FOREIGN_KEY_CHECKS = 0;"))
            for model in reversed(ordered_models):
                dest_session.exec(text(f"TRUNCATE TABLE {model.__tablename__};"))
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
