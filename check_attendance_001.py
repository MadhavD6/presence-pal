
import sqlite3

def check_attendance():
    try:
        conn = sqlite3.connect('kiosk.db')
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables found:", [t[0] for t in tables])
        
        internal_id = None
        
        # Check users table
        print("\nChecking 'user' table:")
        try:
             cursor.execute("SELECT * FROM user")
             users = cursor.fetchall()
             user_found = False
             for user in users:
                 if user['employee_id'] == '001':
                     print("\nFound user '001':")
                     print(dict(user))
                     internal_id = user['id']
                     user_found = True
                     break
             if not user_found:
                 print("User '001' not found.")
                 return

        except Exception as e:
            print(f"Error checking user: {e}")
            return

        if internal_id:
            for table_name in ['auditlog', 'dailysummary']:
                print(f"\n--- Checking {table_name} ---")
                try:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    col_names = [c[1] for c in columns]
                    print(f"Columns: {col_names}")
                    
                    user_col = next((c for c in col_names if 'user' in c.lower() or 'emp' in c.lower()), None)
                    if user_col:
                        print(f"Querying {table_name} for {user_col} = {internal_id}...")
                        query = f"SELECT * FROM {table_name} WHERE {user_col} = ?"
                        cursor.execute(query, (internal_id,))
                        rows = cursor.fetchall()
                        if rows:
                            print(f"Found {len(rows)} records. Showing last 5:")
                            for row in rows[-5:]:
                                print(dict(row))
                        else:
                            print("No records found.")
                    else:
                         print(f"No user column found in {table_name}")
                except Exception as e:
                    print(f"Error checking {table_name}: {e}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_attendance()
