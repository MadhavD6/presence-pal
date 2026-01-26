from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "FaceKiosk"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "strictly-for-dev-change-in-prod-999"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    # Database
    # DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/presencepal"
    DATABASE_URL: str = "sqlite:///./kiosk.db"
    
    # Audit
    AUDIT_RETENTION_DAYS: int = 30
    
    # Face Rec
    DETECTOR_BACKEND: str = "opencv" # or retreat to mtcnn if opencv fails, but opencv is fastest
    RECOGNITION_MODEL: str = "ArcFace"

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379 # User confirms this is running
    REDIS_DB: int = 0
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
