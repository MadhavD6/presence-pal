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
        # 1. Add site_id to user table
        try:
            conn.execute(text("ALTER TABLE user ADD COLUMN site_id INTEGER REFERENCES site(id)"))
            print("Added site_id to user table.")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("Column site_id already exists in user table.")
            else:
                print(f"Error adding site_id: {e}")

        # 2. Add Location Fields to AuditLog
        # latitude, longitude, accuracy, is_geofence_verified, distance_from_site, spoof_risk_score
        
        columns = [
            ("latitude", "FLOAT"),
            ("longitude", "FLOAT"),
            ("accuracy", "FLOAT"),
            ("is_geofence_verified", "BOOLEAN DEFAULT 0"),
            ("distance_from_site", "FLOAT"),
            ("spoof_risk_score", "INTEGER")
        ]
        
        for col_name, col_type in columns:
            try:
                conn.execute(text(f"ALTER TABLE auditlog ADD COLUMN {col_name} {col_type}"))
                print(f"Added {col_name} to auditlog table.")
            except Exception as e:
                # SQLite error for duplicate column is strict text match
                if "duplicate column name" in str(e):
                    print(f"Column {col_name} already exists in auditlog table.")
                else:
                    print(f"Error adding {col_name}: {e}")
        
        conn.commit()
    
    print("Migration Phase 3 (Geofencing) Complete.")

if __name__ == "__main__":
    migrate()
