from sqlmodel import Session, delete, select
from backend.core.database import engine
from backend.models.user import User, Embedding
from backend.models.gallery import FaceGallery
from backend.core.security import get_password_hash
from backend.services.vector import vector_service

def clear_enrollments():
    with Session(engine) as session:
        print("Clearing Face Gallery (Embeddings)...")
        session.exec(delete(FaceGallery))
        
        print("Clearing Legacy Embeddings...")
        session.exec(delete(Embedding))
        
        print("Clearing Users...")
        session.exec(delete(User))
        
        print("Users cleared. No Admin account created (User Request).")
        # print("Re-creating Default Admin User (001)...")
        # admin_user = User(
        #     name="Administrator",
        #     employee_id="001",
        #     role="manager",
        #     hashed_password=get_password_hash("password")
        # )
        # session.add(admin_user)
        session.commit()
        
        print("Reloading Vector Index (clearing memory)...")
        # Direct call to reload which will see empty DB and reset engine
        vector_service.load_index()
        
        print("Enrollments cleared. System reset. Default Admin: 001/password")

if __name__ == "__main__":
    clear_enrollments()
