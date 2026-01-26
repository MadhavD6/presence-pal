from sqlmodel import Session, select, col
from backend.models.gallery import FaceGallery
from typing import List, Tuple
import numpy as np
import pickle

MAX_GALLERY_SIZE = 10  # Max dynamic vectors per user

class GalleryService:
    def add_to_gallery(self, session: Session, user_id: int, vector: List[float], confidence: float, is_anchor: bool = False):
        """
        Adds a vector to the gallery.
        If not an anchor and gallery is full, removes the oldest non-anchor vector.
        """
        # Convert list to bytes
        vector_bytes = pickle.dumps(vector)
        
        if is_anchor:
            # Anchors are just added
            entry = FaceGallery(
                user_id=user_id,
                vector=vector_bytes,
                is_anchor=True,
                confidence=confidence
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return entry

        # For Dynamic vectors, check limit
        statement = select(FaceGallery).where(FaceGallery.user_id == user_id).where(FaceGallery.is_anchor == False).order_by(FaceGallery.created_at.asc())
        dynamic_vectors = session.exec(statement).all()
        
        if len(dynamic_vectors) >= MAX_GALLERY_SIZE:
            # Remove oldest
            to_remove = dynamic_vectors[0]
            session.delete(to_remove)
        
        # Add new
        entry = FaceGallery(
            user_id=user_id,
            vector=vector_bytes,
            is_anchor=False,
            confidence=confidence
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry

    def get_all_vectors(self, session: Session) -> List[Tuple[int, List[float]]]:
        """
        Returns all vectors for indexing.
        """
        entries = session.exec(select(FaceGallery)).all()
        results = []
        for entry in entries:
            try:
                vec = pickle.loads(entry.vector)
                results.append((entry.user_id, vec))
            except Exception as e:
                print(f"Error loading vector for gallery id {entry.id}: {e}")
        return results

gallery_service = GalleryService()
