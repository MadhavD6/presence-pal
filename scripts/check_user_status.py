
import sys
import os
from sqlmodel import Session, select
import numpy as np
import pickle

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.database import engine
from backend.models.user import User
from backend.models.gallery import FaceGallery

def check_user(name_query):
    with Session(engine) as session:
        # Find user
        user = session.exec(select(User).where(User.name.ilike(f"%{name_query}%"))).first()
        if not user:
            print(f"User '{name_query}' NOT FOUND in database.")
            return

        print(f"User Found: {user.name} (ID: {user.id}, Employee ID: {user.employee_id}, Role: {user.role})")
        
        # Check Gallery
        gallery_entries = session.exec(select(FaceGallery).where(FaceGallery.user_id == user.id)).all()
        print(f"Gallery Entries: {len(gallery_entries)}")
        
        if not gallery_entries:
            print("WARNING: No face data enrolled for this user!")
        else:
            for entry in gallery_entries:
                embedding = pickle.loads(entry.embedding)
                print(f" - Entry ID: {entry.id}, Timestamp: {entry.created_at}, Embedding Shape: {np.array(embedding).shape}")
                
                # Check for zero vector
                if np.all(np.array(embedding) == 0):
                    print("   CRITICAL: Embedding is all zeros!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_user_status.py <name>")
        # Default to karthik
        check_user("karthik")
    else:
        check_user(sys.argv[1])
