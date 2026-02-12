import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.user import User
from backend.models.shift import Shift
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def list_users():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        print(f"{'ID':<5} {'Name':<20} {'Employee ID':<15} {'Role':<10} {'Email':<25}")
        print("-" * 75)
        for u in users:
            print(f"{u.id:<5} {u.name:<20} {u.employee_id:<15} {u.role:<10} {u.email or '-':<25}")

def set_password(employee_id: str, password: str):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.employee_id == employee_id)).first()
        if not user:
            print(f"User with Employee ID '{employee_id}' not found.")
            return

        hashed = pwd_context.hash(password)
        user.hashed_password = hashed
        session.add(user)
        session.commit()
        print(f"Password updated for user '{user.name}' ({employee_id}).")

def create_admin():
    with Session(engine) as session:
        # Check if exists
        user = session.exec(select(User).where(User.employee_id == "ADMIN001")).first()
        if user:
            print("Admin user already exists.")
            return

        hashed = pwd_context.hash("admin123")
        user = User(
            name="System Admin",
            employee_id="ADMIN001",
            email="admin@example.com",
            role="admin",
            hashed_password=hashed
        )
        session.add(user)
        session.commit()
        print("Created Admin user: ADMIN001 / admin123")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_users.py list")
        print("  python manage_users.py set-password <employee_id> <password>")
        print("  python manage_users.py create-admin")
        sys.exit(1)

    cmd = sys.argv[1]
    
    if cmd == "list":
        list_users()
    elif cmd == "set-password":
        if len(sys.argv) != 4:
            print("Usage: python manage_users.py set-password <employee_id> <password>")
            sys.exit(1)
        set_password(sys.argv[2], sys.argv[3])
    elif cmd == "create-admin":
        create_admin()
    else:
        print("Unknown command")
