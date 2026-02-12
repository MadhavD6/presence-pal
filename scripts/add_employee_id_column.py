
from sqlmodel import Session, text
from backend.core.database import engine

def migrate():
    print("Starting migration: Adding employee_id to AuditLog table...")
    with Session(engine) as session:
        try:
            # Check if column exists first
            result = session.exec(text("PRAGMA table_info(auditlog)")).all()
            columns = [row[1] for row in result]
            
            if "employee_id" in columns:
                print("Column 'employee_id' already exists. Skipping.")
                return

            # Add Column
            session.exec(text("ALTER TABLE auditlog ADD COLUMN employee_id VARCHAR"))
            session.commit()
            print("Successfully added 'employee_id' column.")
            
        except Exception as e:
            session.rollback()
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
