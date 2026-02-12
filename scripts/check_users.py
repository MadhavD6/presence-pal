from sqlmodel import Session, select, func
from backend.core.database import engine
from backend.models.user import User, Embedding

def check_users():
    with Session(engine) as session:
        user_count = session.exec(select(func.count(User.id))).one()
        embedding_count = session.exec(select(func.count(Embedding.id))).one()
        
        print(f"Total Users: {user_count}")
        print(f"Total Embeddings: {embedding_count}")
        
        users = session.exec(select(User)).all()
        for u in users:
            print(f"- User ID: {u.id}, Name: {u.name}, Employee ID: {u.employee_id}")

if __name__ == "__main__":
    check_users()
