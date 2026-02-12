from sqlmodel import SQLModel, create_engine, Session
from backend.core.config import get_settings
import os

settings = get_settings()

# Dynamic pool sizing based on worker count to prevent MySQL connection exhaustion.
# Formula: workers × (pool_size + max_overflow) must be < MySQL max_connections (default 151)
_gunicorn_workers = int(os.getenv("GUNICORN_WORKERS", "4"))

# connect_args needed for SQLite
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

# Connection pooling for MySQL
engine_args = {
    "echo": False,
    "connect_args": connect_args,
}

if "sqlite" not in settings.DATABASE_URL:
    engine_args["pool_pre_ping"] = True
    # Dynamic pool sizing: ensure total connections across all workers < MySQL limit
    # Example with 4 workers: 4 × (3 + 5) = 32 sync connections (safe)
    engine_args["pool_size"] = max(2, 10 // _gunicorn_workers)
    engine_args["max_overflow"] = max(3, 15 // _gunicorn_workers)
    engine_args["pool_recycle"] = 3600
    engine_args["pool_timeout"] = 30  # Wait max 30s for connection
    
    # MySQL specific connection timeout
    if "mysql" in settings.DATABASE_URL:
        engine_args["connect_args"] = {"connect_timeout": 10}

engine = create_engine(settings.DATABASE_URL, **engine_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    # Enable WAL mode for better concurrency
    if "sqlite" in settings.DATABASE_URL:
        with engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA journal_mode=WAL;")

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.core.logger import logger

# ... (Sync Engine Code remains for legacy support) ...

# Async Engine (The Ferrari)
# Handle Async Database URL explicitly to avoid replacement conflicts
if settings.DATABASE_URL.startswith("sqlite://"):
    async_db_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
elif settings.DATABASE_URL.startswith("mysql+pymysql://"):
    async_db_url = settings.DATABASE_URL.replace("mysql+pymysql://", "mysql+asyncmy://")
elif settings.DATABASE_URL.startswith("mysql://"):
    async_db_url = settings.DATABASE_URL.replace("mysql://", "mysql+asyncmy://")
else:
    async_db_url = settings.DATABASE_URL

# Log without credentials — only show driver and host
_safe_url = async_db_url.split("@")[-1] if "@" in async_db_url else "configured"
logger.info("Database engine initialized", driver=async_db_url.split("://")[0], host=_safe_url)

async_connect_args = {}
if "mysql" in async_db_url:
    async_connect_args = {"connect_timeout": 10}  # 10s MySQL connection timeout

# Async pool sizing: workers × (pool_size + max_overflow) must stay safe
# Example with 4 workers: 4 × (5 + 5) = 40 async connections (safe)
_async_pool_size = max(3, 20 // _gunicorn_workers)
_async_overflow = max(3, 12 // _gunicorn_workers)

async_engine = create_async_engine(
    async_db_url, 
    echo=False, 
    future=True,
    pool_pre_ping=True,
    pool_size=_async_pool_size,
    max_overflow=_async_overflow,
    pool_timeout=30,
    pool_recycle=3600,
    connect_args=async_connect_args
)

# Async Session Factory
async_session_factory = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_session():
    async with async_session_factory() as session:
        yield session

def get_session():
    with Session(engine) as session:
        yield session

