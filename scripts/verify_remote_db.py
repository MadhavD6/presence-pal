
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load env to get DATABASE_URL
load_dotenv(dotenv_path='.env')

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("Error: DATABASE_URL not found in .env")
    exit(1)

# Ensure sync driver
if "+asyncmy" in database_url:
    database_url = database_url.replace("+asyncmy", "+pymysql")

print(f"Connecting to: {database_url.split('@')[1]}") # Print host only for safety

try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        print("\n--- Latest Audit Logs (Limit 5) ---")
        
        # Select latest logs
        stmt = text("""
            SELECT 
                id, user_id, employee_id, identified_name, event_type, 
                timestamp, confidence, match_type, metadata_info, thumbnail_path
            FROM auditlog 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        
        result = conn.execute(stmt)
        rows = result.fetchall()
        
        if not rows:
            print("No logs found.")
        
        for row in rows:
            print("-" * 50)
            print(f"ID: {row.id}")
            print(f"User: {row.identified_name} (ID: {row.user_id})")
            print(f"EmployeeID: {row.employee_id}")
            print(f"Timestamp: {row.timestamp}")
            print(f"Event: {row.event_type} | Match: {row.match_type}")
            print(f"Confidence: {row.confidence}")
            print(f"Metadata: {row.metadata_info}")
            print("-" * 50)

except Exception as e:
    print(f"Connection Failed: {e}")
