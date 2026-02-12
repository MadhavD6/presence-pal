
import sys
import os
sys.path.append(os.getcwd())
from sqlmodel import Session, select, create_engine
from backend.models.user import User
from backend.models.shift import Shift
from backend.models.site import Site
from backend.core.config import get_settings
from backend.core.security import get_password_hash

def reset_password():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        user = session.exec(select(User).where(User.employee_id == "TEST_MGR")).first()
        if user:
            user.hashed_password = get_password_hash("password123")
            session.add(user)
            session.commit()
            print("Password reset for TEST_MGR")
        else:
            print("TEST_MGR not found")

if __name__ == "__main__":
    reset_password()
