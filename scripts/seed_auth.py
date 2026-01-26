
from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.user import User
from backend.models.shift import Shift
from backend.models.site import Site
from backend.core.security import get_password_hash

def seed_test_user():
    # Credentials: demo@example.com / password123
    email = "demo@example.com"
    pwd = "password123"
    
    with Session(engine) as session:
        # Check if user 1 exists, if so update it, else create
        user = session.get(User, 1)
        if not user:
            print("User 1 not found. Creating...")
            user = User(
                id=1,
                name="John Doe",
                employee_id="E001",
                role="user",
                email=email,
                hashed_password=get_password_hash(pwd)
            )
            session.add(user)
        else:
            print(f"Updating User 1 ({user.name}) with auth credentials...")
            user.email = email
            user.hashed_password = get_password_hash(pwd)
            session.add(user)
        
        session.commit()
        print(f"Done. Login with: {email} / {pwd}")

if __name__ == "__main__":
    seed_test_user()
