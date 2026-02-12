
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# DB Connection from .env
# DATABASE_URL="mysql+pymysql://root:root@localhost:3306/presence_pal"
DB_URL = "mysql+pymysql://root:root@localhost:3306/prodify_apps"

def check_logs():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("Connected to MySQL Database.")
            
            query = text("""
                SELECT id, user_id, event_type, timestamp, confidence, identified_name 
                FROM auditlog 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            
            result = conn.execute(query)
            rows = result.fetchall()
            
            print(f"\nFound {len(rows)} recent audit logs:")
            print("-" * 80)
            print(f"{'ID':<5} {'Time':<25} {'Type':<10} {'User':<15} {'Conf':<10}")
            print("-" * 80)
            
            for row in rows:
                # row is a tuple/object, accessing by index or name
                # timestamp is index 3
                print(f"{row[0]:<5} {str(row[3]):<25} {row[2]:<10} {row[5] or 'Unknown':<15} {row[4]:<10}")
            
            print("-" * 80)
            
    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    check_logs()
