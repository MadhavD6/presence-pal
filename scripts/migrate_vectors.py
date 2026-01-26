from sqlmodel import Session, select
from backend.core.database import engine, create_db_and_tables
from backend.models.user import Embedding
from backend.models.gallery import FaceGallery
import pickle
import numpy as np

def migrate_vectors():
    print("Starting Migration: Embedding -> FaceGallery")
    
    # Ensure tables exist
    create_db_and_tables()
    
    with Session(engine) as session:
        # 1. Fetch old embeddings
        old_embeddings = session.exec(select(Embedding)).all()
        print(f"Found {len(old_embeddings)} existing embeddings.")
        
        migrated_count = 0
        for old in old_embeddings:
            # Check if already migrated (simple check by user_id for anchor)
            existing_anchor = session.exec(
                select(FaceGallery)
                .where(FaceGallery.user_id == old.user_id)
                .where(FaceGallery.is_anchor == True)
            ).first()
            
            if existing_anchor:
                print(f"User {old.user_id} already has anchor. Skipping.")
                continue
                
            # Convert bytes to pickle (Old stored raw bytes from numpy.tobytes(), Service expects pickle)
            # Wait, `vector_service.add_embedding` in OLD code did `vec_bytes = vec_np.tobytes()`.
            # New `GalleryService` does `pickle.dumps(vector)`.
            # We need to convert safely.
            
            try:
                # 1. Load raw bytes back to numpy
                vec_np = np.frombuffer(old.vector, dtype=np.float32)
                vec_list = vec_np.tolist()
                
                # 2. Pickle it
                vec_pickle = pickle.dumps(vec_list)
                
                # 3. Create Gallery Entry
                gallery_entry = FaceGallery(
                    user_id=old.user_id,
                    vector=vec_pickle,
                    is_anchor=True, # Old embeddings are the original enrollments -> Anchor
                    confidence=1.0,
                    created_at=old.created_at
                )
                session.add(gallery_entry)
                migrated_count += 1
                
            except Exception as e:
                print(f"Failed to migrate User {old.user_id}: {e}")
                
        session.commit()
        print(f"Migration Complete. Migrated {migrated_count} vectors.")

if __name__ == "__main__":
    migrate_vectors()
