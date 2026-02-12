
import sqlite3
from datetime import datetime
import json

def get_recent_logs():
    # Connect to DB (Relative path)
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'kiosk.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auditlog';")
    if not cursor.fetchone():
        print("Table 'auditlog' not found.")
        return

    query = """
    SELECT 
        id, user_id, employee_id, event_type, timestamp, confidence, identified_name, 
        kiosk_id, metadata_info, match_type, error_code, rejection_reason, thumbnail_path 
    FROM auditlog 
    ORDER BY timestamp DESC 
    LIMIT 20;
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} recent logs:")
    print("-" * 80)
    
    for row in rows:
        data = dict(row)
        print(f"ID: {data['id']}")
        print(f"Time: {data['timestamp']}")
        print(f"User: {data['identified_name']} (ID: {data['user_id']}, EMP ID: {data['employee_id']})")
        print(f"Type: {data['event_type']}")
        print(f"Confidence: {data['confidence']}")
        print(f"Match Type: {data['match_type']}")
        print(f"IMAGE PATH: {data.get('thumbnail_path', 'N/A')}")
        if data['metadata_info']:
            try:
                meta = json.loads(data['metadata_info'])
                print(f"Metadata: {json.dumps(meta, indent=2)}")
            except:
                print(f"Metadata: {data['metadata_info']}")
        if data['error_code']:
            print(f"Error: {data['error_code']} - {data['rejection_reason']}")
        print("-" * 80)

    conn.close()

if __name__ == "__main__":
    get_recent_logs()
