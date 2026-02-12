from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Prodify Face App"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str  # Must be provided via environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite:///./kiosk.db"
    
    # Audit
    AUDIT_RETENTION_DAYS: int = 30
    
    # Face Rec
    DETECTOR_BACKEND: str = "retinaface"
    RECOGNITION_MODEL: str = "ArcFace"
    FACE_RECOGNITION_THREADS: int = 4 # Default to 4, override in docker-compose

    # AWS S3 Storage
    S3_BUCKET_NAME: str = "prodify-fr-images-bucket"
    AWS_ACCESS_KEY_ID: str = "" # Loaded from env
    AWS_SECRET_ACCESS_KEY: str = "" # Loaded from env
    AWS_REGION: str = "us-east-1"
    
    # Accuracy Settings
    ENROLLMENT_MIN_BLUR_SCORE: float = 100.0  # Minimum blur score for registration photos
    LIVENESS_BLUR_THRESHOLD: float = 15.0    # Minimum blur for liveness check
    LIVENESS_LBP_THRESHOLD: float = 20.0     # LBP texture variance threshold (lower = stricter)
    LIVENESS_MOTION_THRESHOLD: float = 0.0005  # Motion detection threshold
    LIVENESS_MIN_FACE_RATIO: float = 0.5     # Minimum frames that must have face detected
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
