import numpy as np
import cv2
import threading
from deepface import DeepFace
from backend.core.config import get_settings
from backend.core.performance import log_execution_time
from backend.core.logger import logger

settings = get_settings()

# Model Helper — Thread-safe singleton for DeepFace model loading
class ModelLoader:
    _model = None
    _lock = threading.Lock()  # Prevent race condition when multiple threads load simultaneously

    @classmethod
    def get_model(cls):
        if cls._model is None:
            with cls._lock:
                # Double-checked locking: re-check after acquiring lock
                if cls._model is None:
                    logger.info("Loading DeepFace model", model=settings.RECOGNITION_MODEL)
                    cls._model = DeepFace.build_model(settings.RECOGNITION_MODEL)
                    logger.info("DeepFace model loaded successfully")
        return cls._model


# Module-level function (NOT a @staticmethod — there is no enclosing class)
@log_execution_time
def compute_embedding(image_bytes: bytes):
    """
    CPU-bound task to compute face embedding.
    Returns dict or None.
    """
    try:
        # Ensure model is loaded in this worker process (thread-safe)
        ModelLoader.get_model()
        
        # 1. Decode bytes
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None

        # 2. Inference
        embeddings = DeepFace.represent(
            img_path=img,
            model_name=settings.RECOGNITION_MODEL,
            detector_backend=settings.DETECTOR_BACKEND,
            enforce_detection=True,
            align=True
        )
        
        if not embeddings:
            return None
            
        embedding_obj = embeddings[0]
        result = {
            "embedding": embedding_obj["embedding"],
            "confidence": embedding_obj.get("face_confidence", 0.0),
            "facial_area": embedding_obj.get("facial_area", {})
        }
        return result

    except ValueError:
        return None # Face not found
    except Exception as e:
        logger.error("Error in compute_embedding", error=str(e))
        return None

