from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.user import User
from backend.models.shift import Shift
from backend.models.site import Site

def check_and_upgrade_role(employee_id):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.employee_id == employee_id)).first()
        
        if not user:
            print(f"User {employee_id} not found.")
            return

        print(f"User: {user.name}")
        print(f"Current Role: {user.role}")
        
        if user.role != "manager":
            print("Upgrading user to 'manager'...")
            user.role = "manager"
            session.add(user)
            session.commit()
            print("Role updated to: manager")
            print("Please logout and login again for changes to take effect.")
        else:
            print("User is already a manager.")

if __name__ == "__main__":
    check_and_upgrade_role("001")
