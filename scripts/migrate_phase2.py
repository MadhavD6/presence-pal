import sys
import os
 
# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from backend.core.config import get_settings

def migrate():
    settings = get_settings()
    print(f"Migrating DB at: {settings.DATABASE_URL}")
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 1. Add grace_period_mins to shift table
        try:
            conn.execute(text("ALTER TABLE shift ADD COLUMN grace_period_mins INTEGER DEFAULT 15"))
            print("Added grace_period_mins to shift table.")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("Column grace_period_mins already exists in shift table.")
            else:
                print(f"Error adding grace_period_mins: {e}")

        # 2. Add shift_id to user table
        try:
            conn.execute(text("ALTER TABLE user ADD COLUMN shift_id INTEGER REFERENCES shift(id)"))
            print("Added shift_id to user table.")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("Column shift_id already exists in user table.")
            else:
                print(f"Error adding shift_id: {e}")
        
        conn.commit()
    
    print("Migration Phase 2 Complete.")

if __name__ == "__main__":
    migrate()
