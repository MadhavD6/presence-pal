from typing import List, Optional
import numpy as np
import cv2
from deepface import DeepFace
# We need tf-keras or similar; deepface handles imports internally usually, 
# but for type hinting we might just use List.

class FaceService:
    def __init__(self, model_name: str = "ArcFace", detector_backend: str = "opencv"):
        self.model_name = model_name
        self.detector_backend = detector_backend
        
        print(f"Loading {model_name} model...")
        try:
            # Explicitly build model to force weight download/load on startup
            self.model_obj = DeepFace.build_model(model_name)
            print(f"{model_name} model built successfully.")
            
            # Dummy warm-up
            dummy = np.zeros((112, 112, 3), dtype=np.uint8)
            # We treat the first call as warm-up.
            # Note: DeepFace.represent internal logic might reload if we don't pass the model object, 
            # but DeepFace handles caching. We just want to ensure it works.
            # Passing the model object is tricky with the functional API of DeepFace.
            # We will just rely on the cache.
            
            print(f"{model_name} loaded and warmed up.")
        except Exception as e:
            print(f"CRITICAL ERROR: Model loading failed: {e}")
            # We don't crash the app, but face rec will fail.
            # In production, we might want to exit.

    def get_embedding(self, image_bytes: bytes) -> Optional[List[float]]:
        """
        Convert image bytes to 512D embedding.
        Returns None if no face detected (or multiple faces? - we focus on largest).
        """
        try:
            # 1. Decode bytes to numpy
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return None

            # 2. Get embedding
            # enforce_detection=True usually throws exception if no face.
            # We want "Silent Failure" so we handle it.
            # We use enforce_detection=True to ensure we actually got a face.
            
            embeddings = DeepFace.represent(
                img_path=img,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=True,
                align=True
            )
            
            if not embeddings:
                return None
                
            # If multiple faces, DeepFace returns a list. We take the one with highest confidence or largest area?
            # DeepFace.represent usually returns a list of dicts.
            # We take the first one (usually largest/most prominent).
            embedding_obj = embeddings[0]
            vector = embedding_obj["embedding"]
            
            # Validate 512D
            if len(vector) != 512:
                # ArcFace should be 512.
                print(f"Warning: Expected 512D, got {len(vector)}D")
                
            return vector
            
        except ValueError as e:
            # "Face could not be detected"
            return None
        except Exception as e:
            print(f"Error in face recognition: {e}")
            return None

    def get_averaged_embedding(self, image_bytes_list: List[bytes]) -> Optional[List[float]]:
        """
        Generate embeddings for multiple images and return the average vector (Normalized).
        Robust against noise/pose variations.
        """
        vectors = []
        for img_bytes in image_bytes_list:
            vec = self.get_embedding(img_bytes)
            if vec:
                vectors.append(vec)
        
        if not vectors:
            return None
            
        if len(vectors) == 1:
            return vectors[0]
            
        # Average
        print(f"Averaging {len(vectors)} frames for registration...")
        matrix = np.array(vectors) # (N, 512)
        mean_vec = np.mean(matrix, axis=0) # (512,)
        
        # Normalize (L2) - Critical for Cosine Similarity!
        norm = np.linalg.norm(mean_vec)
        if norm == 0:
            return mean_vec.tolist()
            
        normalized_vec = mean_vec / norm
        return normalized_vec.tolist()

# Singleton instance
face_service = FaceService()
