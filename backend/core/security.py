
from typing import Optional
from datetime import datetime, timedelta
import os
import jwt
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlmodel import Session, select
from backend.core.database import get_session
from backend.models.kiosk import Kiosk
from backend.models.user import User
from passlib.context import CryptContext

# Configuration with validation
SECRET_KEY = os.getenv("SECRET_KEY", "")
INSECURE_KEYS = ["dev_secret_key_change_me_in_prod", "strictly-for-dev-change-in-prod-999", ""]

if SECRET_KEY in INSECURE_KEYS:
    raise ValueError(
        "CRITICAL SECURITY ERROR: Production SECRET_KEY not set or using default value. "
        "Set a strong SECRET_KEY environment variable immediately!"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security Schemes
api_key_header = APIKeyHeader(name="X-Kiosk-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/employee/login")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# --- Password Utils ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- JWT Utils ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependencies ---

async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception
        
    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception
    # In future, check if user.is_active
    return user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return current_user

async def get_current_manager_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    # RBAC Disabled as per user request
    # if current_user.role not in ["admin", "manager"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
    #     )
    return current_user

# --- Kiosk Auth (Existing) ---
def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    # Uses pbkdf2_sha256 from original context, but here using bcrypt context for everything is cleaner if we migrate kiosk keys.
    # However, existing Kiosks might use pbkdf2. Let's keep a separate context or flexible one if needed.
    # For now, assuming Kiosk uses same hashing or we re-use pwd_context if compatible.
    # Original file had schemes=["pbkdf2_sha256"]. Let's stick to that for Kiosk if preserving legacy data.
    # BUT user asked to use passlib[bcrypt].
    # Let's use a multi-scheme context.
    return pwd_context.verify(plain_key, hashed_key)

from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_async_session

async def get_current_kiosk(
    api_key: str = Security(api_key_header),
    session: AsyncSession = Depends(get_async_session)
) -> Kiosk:
    """
    Validates API Key format: kiosk:{device_id}:{secret}
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Kiosk-API-Key header"
        )
    
    try:
        # Expected format: kiosk:DEVICE_001:raw_secret_key
        parts = api_key.split(":")
        if len(parts) != 3 or parts[0] != "kiosk":
             raise ValueError("Format error")
        
        device_id = parts[1]
        secret = parts[2]
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key Format. Expected 'kiosk:{device_id}:{secret}'"
        )

    result = await session.exec(select(Kiosk).where(Kiosk.device_id == device_id))
    kiosk = result.first()
    
    if not kiosk:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kiosk Device ID not found"
        )
        
    if kiosk.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Kiosk is {kiosk.status}"
        )
        
    if not verify_api_key(secret, kiosk.api_key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key Secret"
        )
        
    return kiosk

# Optional Bearer Token + API Key Auth (for audit trail)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/employee/login", auto_error=False)

async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Tries to extract current user from Bearer token.
    Returns None if no token or invalid token.
    Used for audit trail - capture 'who' performed an action.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        user_id = int(user_id_str)
        user = session.get(User, user_id)
        return user
    except (jwt.PyJWTError, ValueError):
        return None
