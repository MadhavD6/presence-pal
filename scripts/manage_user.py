from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.user import User
from backend.models.shift import Shift
from backend.models.site import Site
from backend.core.security import get_password_hash

def manage_user(employee_id, new_password=None):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.employee_id == employee_id)).first()
        
        if not user:
            print(f"User {employee_id} not found.")
            return

        print(f"User Found: {user.name} (ID: {user.id})")
        print(f"Role: {user.role}")
        print(f"Has Password: {'YES' if user.hashed_password else 'NO'}")
        
        if new_password:
            user.hashed_password = get_password_hash(new_password)
            session.add(user)
            session.commit()
            print(f"Password for {employee_id} has been updated to: {new_password}")

if __name__ == "__main__":
    # Check 001 and set to 'password' if currently missing or just force reset for convenience
    import sys
    emp_id = "001"
    pwd = "password" 
    manage_user(emp_id, pwd)
