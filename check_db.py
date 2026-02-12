import sys
from sqlalchemy import create_engine, text
from backend.core.config import get_settings

settings = get_settings()
print(f"Testing connection to: {settings.DATABASE_URL}")

try:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Connection Successful!")
except Exception as e:
    print(f"Connection FAILED: {e}")
    sys.exit(1)
