import pickle
from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.user import User
from backend.models.gallery import FaceGallery
def check_db():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        faces = session.exec(select(FaceGallery)).all()
        
        print(f"Total Users: {len(users)}")
        for u in users:
            print(f" - ID: {u.id}, Name: {u.name}, EmpID: {u.employee_id}")
            
        print(f"\nTotal Face Embeddings: {len(faces)}")
        for f in faces:
             try:
                 vec = pickle.loads(f.vector)
                 print(f" - Face ID: {f.id}, User ID: {f.user_id}, Anchor: {f.is_anchor}, Vector Len: {len(vec)}")
             except Exception as e:
                 print(f" - Face ID: {f.id} Error unpickling: {e}")

if __name__ == "__main__":
    check_db()
