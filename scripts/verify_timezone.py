import sys
import os
from datetime import datetime, timedelta
from sqlmodel import Session, select, create_engine

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.config import get_settings
from backend.models.site import Site
from backend.models.shift import Shift
from backend.models.user import User

def verify_timezone():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        # Create a temp user
        test_id = f"TZ-TEST-{int(datetime.now().timestamp())}"
        user = User(
            employee_id=test_id,
            name="Timezone Tester",
            role="user"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Check timestamps
        now_local = datetime.now()
        db_time = user.created_at
        
        print(f"Local System Time: {now_local}")
        print(f"DB Created At:     {db_time}")
        
        diff = abs((now_local - db_time).total_seconds())
        print(f"Difference (sec):  {diff}")
        
        if diff < 5:
            print("SUCCESS: Timestamps align (using Local Time).")
        elif diff > 19000 and diff < 20000: # ~5.5 hours = 19800s
            print("FAILURE: DB seems to be using UTC vs System Local (IST mismatch).")
        else:
            print(f"FAILURE: Unexpected difference {diff}s.")

        # Cleanup
        session.delete(user)
        session.commit()

if __name__ == "__main__":
    verify_timezone()
