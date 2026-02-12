import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.user import User

def check_user():
    with Session(engine) as session:
        # Check by name or email
        statement = select(User).where(
            (User.name.ilike("%karthik%")) | 
            (User.email.ilike("%karthik%"))
        )
        users = session.exec(statement).all()
        
        if users:
            print(f"MATCH FOUND: {len(users)} user(s) found.")
            for u in users:
                print(f" - ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {u.role}")
        else:
            print("NO MATCH: No user found with name or email containing 'karthik'.")

if __name__ == "__main__":
    check_user()
