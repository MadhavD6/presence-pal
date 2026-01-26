import sys
import os
from sqlmodel import Session, select, create_engine

sys.path.append(os.getcwd())

from backend.models.user import User
from backend.models.shift import Shift
from backend.core.config import get_settings
from backend.core.security import get_password_hash

def seed_users():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        # Employee
        emp = session.exec(select(User).where(User.employee_id == "browser_emp")).first()
        if not emp:
            emp = User(
                name="Browser Employee",
                employee_id="browser_emp", 
                role="employee",
                hashed_password=get_password_hash("password123")
            )
            session.add(emp)
            print("Created browser_emp / password123")
        else:
            print("browser_emp exists")
            
        # Manager
        mgr = session.exec(select(User).where(User.employee_id == "browser_mgr")).first()
        if not mgr:
            mgr = User(
                name="Browser Manager",
                employee_id="browser_mgr",
                role="manager", 
                hashed_password=get_password_hash("password123")
            )
            session.add(mgr)
            print("Created browser_mgr / password123")
        else:
            print("browser_mgr exists")
            
        session.commit()

if __name__ == "__main__":
    seed_users()
