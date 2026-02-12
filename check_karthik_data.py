import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in .env")
    exit(1)

# Fix for asyncmy/pymysql if needed, but we can just use pymysql for sync script
if "asyncmy" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("asyncmy", "pymysql")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # 1. Find User
    print("--- Searching for User 'karthik' ---")
    result = conn.execute(text("SELECT id, name, employee_id, role FROM user WHERE name LIKE :name"), {"name": "%karthik%"})
    users = result.fetchall()
    
    if not users:
        print("No user found with name 'karthik'")
        exit()
        
    for user in users:
        print(f"User Found: ID={user.id}, Name={user.name}, EmpID={user.employee_id}, Role={user.role}")
        user_id = user.id

        # 2. Get Audit Logs
        print(f"\n--- Recent Audit Logs for User {user_id} ---")
        logs = conn.execute(text("""
            SELECT id, timestamp, event_type, confidence, identified_name, metadata_info 
            FROM auditlog 
            WHERE user_id = :uid 
            ORDER BY timestamp DESC 
            LIMIT 5
        """), {"uid": user_id})
        
        for log in logs:
            print(f"\n[Log ID: {log.id}]")
            print(f"Time: {log.timestamp}")
            print(f"Event: {log.event_type}")
            print(f"Confidence: {log.confidence}")
            print(f"Name: {log.identified_name}")
            
            if log.metadata_info:
                try:
                    meta = json.loads(log.metadata_info) if isinstance(log.metadata_info, str) else log.metadata_info
                    print("Metadata Details:")
                    print(json.dumps(meta, indent=2))
                except Exception as e:
                    print(f"raw metadata: {log.metadata_info}")
            else:
                print("No metadata info.")
