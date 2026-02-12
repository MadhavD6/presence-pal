
import sqlite3
import os

DB_PATH = "kiosk.db"

def migrate_shift_history():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employeeshift'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("Creating 'employeeshift' table...")
            # SQL matching the model
            sql = """
            CREATE TABLE employeeshift (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                shift_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES user (id),
                FOREIGN KEY (shift_id) REFERENCES shift (id)
            );
            """
            cursor.execute(sql)
            print("Table created.")
            
            # Index
            cursor.execute("CREATE INDEX ix_employeeshift_user_id ON employeeshift (user_id)")
            cursor.execute("CREATE INDEX ix_employeeshift_shift_id ON employeeshift (shift_id)")
            
        else:
            print("'employeeshift' table already exists. Checking columns...")
            cursor.execute("PRAGMA table_info(employeeshift)")
            columns = [info[1] for info in cursor.fetchall()]
            
            # Simple check for start_date
            if "start_date" not in columns:
                print("Table schema mismatch (old version). Dropping and recreating for dev...")
                cursor.execute("DROP TABLE employeeshift")
                cursor.execute("""
                CREATE TABLE employeeshift (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    shift_id INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES user (id),
                    FOREIGN KEY (shift_id) REFERENCES shift (id)
                );
                """)
                print("Table recreated.")
            else:
                print("Schema looks correct.")

        conn.commit()
            
    except Exception as e:
        print(f"Migration failed: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_shift_history()
