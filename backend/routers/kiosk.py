from typing import Annotated, Optional, List
from datetime import datetime, timedelta
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Header, Security, Body
from sqlmodel import select, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_async_session
from backend.models.kiosk import Kiosk
from backend.core.security import get_password_hash, get_current_kiosk
import secrets
from backend.models.site import Site

router = APIRouter()

@router.post("/kiosk/register")
async def register_kiosk(
    device_id: str,
    location: str,
    building: str,
    session: AsyncSession = Depends(get_async_session)
):
    # Check if exists
    result = await session.exec(select(Kiosk).where(Kiosk.device_id == device_id))
    existing = result.first()
    if existing:
        raise HTTPException(status_code=400, detail="Kiosk already registered")
        
    secret = secrets.token_urlsafe(32)
    api_key_hash = get_password_hash(secret)
    
    kiosk = Kiosk(
        device_id=device_id,
        location=location,
        building=building,
        api_key_hash=api_key_hash
    )
    session.add(kiosk)
    await session.commit()
    await session.refresh(kiosk)
    
    return {
        "status": "success",
        "kiosk_id": kiosk.id,
        "api_key": f"kiosk:{device_id}:{secret}",
        "message": "Save this key securely. It will not be shown again."
    }

@router.post("/kiosk/heartbeat")
async def heartbeat(
    kiosk: Kiosk = Depends(get_current_kiosk),
    session: AsyncSession = Depends(get_async_session)
):
    kiosk = await session.merge(kiosk)
    kiosk.last_heartbeat = datetime.now()
    session.add(kiosk)
    await session.commit()
    return {
        "status": "online", 
        "kiosk": {
            "id": kiosk.id,
            "device_id": kiosk.device_id,
            "location": kiosk.location,
            "building": kiosk.building
        }
    }

# --- Setup Endpoints (Public/Initial) ---

@router.get("/kiosk/setup/sites")
async def get_setup_sites(
    session: AsyncSession = Depends(get_async_session)
):
    """List all active sites for initial setup selection."""
    result = await session.exec(select(Site).where(Site.is_active == True))
    return result.all()

@router.get("/kiosk/setup/kiosks")
async def get_setup_kiosks(
    site_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """List kiosks registered for a specific site."""
    result = await session.exec(select(Kiosk).where(Kiosk.site_id == site_id))
    return result.all()

class KioskActivateRequest(SQLModel):
    site_id: int
    device_id: str
    location: str
    building: str
    kiosk_id: Optional[int] = None # If activating an existing record

@router.post("/kiosk/setup/activate")
async def activate_kiosk(
    data: KioskActivateRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Activate a kiosk. If kiosk_id is provided, it updates existing.
    Otherwise, it checks for device_id uniqueness and creates new.
    Returns the final API key.
    """
    secret = secrets.token_urlsafe(32)
    api_key_hash = get_password_hash(secret)
    
    if data.kiosk_id:
        kiosk = await session.get(Kiosk, data.kiosk_id)
        if not kiosk:
            raise HTTPException(status_code=404, detail="Kiosk record not found")
        
        # Check if already has a hash? Maybe allow re-activation (regeneration)
        kiosk.api_key_hash = api_key_hash
        kiosk.site_id = data.site_id
        kiosk.device_id = data.device_id
        kiosk.location = data.location
        kiosk.building = data.building
    else:
        # Check if device_id exists
        result = await session.exec(select(Kiosk).where(Kiosk.device_id == data.device_id))
        existing = result.first()
        if existing:
            # If it exists, maybe we should just use it? 
            # User wants: "Initially, I thought there would be a page listing all registered kiosks. By selecting a site, the kiosk key would be generated"
            # So if it exists, we update it.
            kiosk = existing
            kiosk.api_key_hash = api_key_hash
            kiosk.site_id = data.site_id
            kiosk.location = data.location
            kiosk.building = data.building
        else:
            kiosk = Kiosk(
                device_id=data.device_id,
                location=data.location,
                building=data.building,
                site_id=data.site_id,
                api_key_hash=api_key_hash
            )
            
    session.add(kiosk)
    await session.commit()
    await session.refresh(kiosk)
    
    return {
        "status": "success",
        "kiosk_id": kiosk.id,
        "api_key": f"kiosk:{kiosk.device_id}:{secret}",
        "message": "Kiosk activated successfully. API key saved to device."
    }

@router.post("/kiosk/auto-register")
async def auto_register_kiosk(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Automatically registers a new kiosk with generated credentials.
    Used for 'Plug and Play' mode without manual setup.
    """
    # 1. Generate unique Device ID
    import random
    import string
    
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    device_id = f"AUTO-KIOSK-{suffix}"
    
    # Ensure uniqueness (simple retry)
    result = await session.exec(select(Kiosk).where(Kiosk.device_id == device_id))
    while result.first():
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        device_id = f"AUTO-KIOSK-{suffix}"
        result = await session.exec(select(Kiosk).where(Kiosk.device_id == device_id))
    
    secret = secrets.token_urlsafe(32)
    api_key_hash = get_password_hash(secret)
    
    kiosk = Kiosk(
        device_id=device_id,
        location="Auto-Location",
        building="Auto-Building",
        site_id=None, # Default to None or assign a default site if needed
        api_key_hash=api_key_hash,
        status="active"
    )
    
    session.add(kiosk)
    await session.commit()
    await session.refresh(kiosk)
    
    return {
        "status": "success",
        "kiosk_id": kiosk.id,
        "device_id": device_id,
        "api_key": f"kiosk:{device_id}:{secret}",
        "message": "Auto-registration successful"
    }

from sqlmodel import SQLModel
from backend.models.audit import AuditLog

class SyncItem(SQLModel):
    user_id: int
    timestamp: datetime
    event_type: str = "in" # in, out
    confidence: float
    kiosk_id: str # Device ID

def get_api_key_header(x_kiosk_api_key: str = Header(...)):
    # Validate API Key if needed or pass through
    return x_kiosk_api_key

@router.post("/kiosk/sync")
async def sync_punches(
    items: List[SyncItem],
    api_key_header: str = Security(get_api_key_header),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Sync offline punches. Batch process.
    """
    processed = 0
    skipped = 0
    
    for item in items:
        # Check duplicate
        time_window = timedelta(seconds=5)
        
        result = await session.exec(
            select(AuditLog)
            .where(AuditLog.user_id == item.user_id)
            .where(AuditLog.event_type == item.event_type)
            .where(AuditLog.timestamp >= item.timestamp - time_window)
            .where(AuditLog.timestamp <= item.timestamp + time_window)
        )
        exists = result.first()
        
        if exists:
            skipped += 1
            continue
            
        # Create Log
        log = AuditLog(
            user_id=item.user_id,
            event_type=item.event_type,
            confidence=item.confidence,
            timestamp=item.timestamp,
            kiosk_id=item.kiosk_id
        )
        session.add(log)
        processed += 1
        
    await session.commit()
    
    return {"processed": processed, "skipped": skipped, "status": "success"}

from fastapi import UploadFile, File, Form
from backend.services.face import face_service
from backend.services.vector import vector_service
from backend.services.audit import audit_service
from backend.services.liveness import liveness_service
from backend.services.rate_limiter import rate_limiter
from backend.models.user import User
# from backend.core.database import engine # REMOVE BLOCKING ENGINE IMPORT
from backend.core.database import get_async_session

@router.post("/kiosk/identify")
async def identify_user(
    files: list[UploadFile] = File(..., alias="file"),
    event_type: str = Form("unknown", alias="type"),
    kiosk: Kiosk = Depends(get_current_kiosk)
):
    """
    Kiosk: Identify user from face with rate limiting and enhanced audit.
    """
    # Rate Limiting Check
    rate_key = f"kiosk:{kiosk.id}"
    is_blocked, cooldown_secs = rate_limiter.is_blocked(rate_key)
    if is_blocked:
        return {
            "status": "failure",
            "reason": f"Too many failed attempts. Please wait {cooldown_secs} seconds.",
            "error_code": "rate_limited"
        }
    
    # Start timer
    import time
    start_time = time.time()

    if not files:
         raise HTTPException(status_code=400, detail="No images provided")

    # Read all frames
    frames_content = []
    for f in files:
        frames_content.append(await f.read())
    
    # 1. Passive Liveness (Offloaded to avoid blocking)
    t_liveness_start = time.time()
    loop = asyncio.get_running_loop()
    is_live, reason, liveness_metrics = await loop.run_in_executor(
        None, # Use default executor
        lambda: liveness_service.check_liveness(frames_content)
    )
    t_liveness_end = time.time()
    
    if not is_live:
        rate_limiter.record_attempt(rate_key, success=False)
        await audit_service.log_event(
            user_id=None, 
            confidence=0.0, 
            image_bytes=frames_content[0],
            identified_name="Spoof/Static",
            event_type=event_type,
            kiosk_id=kiosk.id,
            rejection_reason=reason,
            error_code="liveness_failed",
            match_type="rejected",
            metadata_info={
                **liveness_metrics,  # Include blur, motion, texture scores
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
        )
        return {
            "status": "failure", 
            "reason": reason,
            "error_code": "liveness_failed"
        }

    # 2. Get Embedding (Parallel Processing)
    valid_vectors = []
    valid_confidences = []
    best_frame = frames_content[len(frames_content)//2]
    early_exit_triggered = False
    
    # Process all frames in parallel to reduce latency
    t_embedding_start = time.time()
    tasks = [face_service.get_embedding(f) for f in frames_content]
    embedding_results = await asyncio.gather(*tasks)
    t_embedding_end = time.time()

    for i, result in enumerate(embedding_results):
        if not result:
            continue

        vec = result["embedding"]
        conf = result.get("confidence", 0.0)
        
        # Additional Check: Ignore low-confidence faces in stream
        if conf < 0.85:
            continue
            
        valid_vectors.append(vec)
        valid_confidences.append(conf)
        
        # --- High Confidence Optimization ---
        # If >99% confidence on ANY frame, prefer that one exclusively.
        t_uid, t_conf = vector_service.find_nearest(vec)
        if t_uid and t_conf > 0.99:
            from backend.core.logger import logger
            logger.info("High Confidence Match Found", frame=i+1, confidence=f"{t_conf:.4f}")
            # Use only this perfect capture
            valid_vectors = [vec] 
            best_frame = frames_content[i]
            early_exit_triggered = True
            break
            # -------------------------------
            
    if not valid_vectors:
        return {
            "status": "failure", 
            "reason": "No face detected. Please ensure good lighting and face the camera directly.", 
            "error_code": "no_face_detected"
        }
        
    # Calculate Mean Vector (Centroid) to reduce noise
    import numpy as np
    
    if len(valid_vectors) == 1:
        vector = valid_vectors[0]
    else:
        # Weighted Average based on detection confidence
        matrix = np.array(valid_vectors)
        weights = np.array(valid_confidences)
        
        # Normalize weights to sum to 1 (optional for average but good practice)
        if np.sum(weights) > 0:
             mean_vector = np.average(matrix, axis=0, weights=weights)
        else:
             mean_vector = np.mean(matrix, axis=0)
        
        # Normalize (L2) - Critical for Cosine Similarity
        norm = np.linalg.norm(mean_vector)
        if norm > 0:
            mean_vector = mean_vector / norm
            
        vector = mean_vector.tolist()

    # 3. Multi-Reference Aggregation Match
    t_search_start = time.time()
    user_scores = vector_service.search_all_matches(vector)
    user_id, confidence, match_reason = vector_service.decide_match(user_scores)
    t_search_end = time.time()
    
    # 4. Resolve User
    name = None
    final_status = "unknown"
    found_employee_id = None
    
    if user_id:
        # Check Cache
        # Database Lookup (Replacing Cache)

        # Check User Details
        if not found_employee_id:
            # We need to fetch the user details if not already available
            # Use the existing session if possible, or a new context
             async for session in get_async_session(): 
                user = await session.get(User, user_id)
                if user:
                    name = user.name
                    found_employee_id = user.employee_id
                    final_status = "success"
                break 
        else:
             final_status = "success"


        # 4.5. Check Constraints (Prevent Double Punch)
        if final_status == "success" and event_type in ["in", "out"]:
             async for session in get_async_session():
                 # Get last successful punch for this user
                 result = await session.exec(
                     select(AuditLog)
                     .where(AuditLog.user_id == user_id)
                     .where(AuditLog.identified_name != None) # Only valid identifies
                     .order_by(AuditLog.timestamp.desc())
                 )
                 last_log = result.first()
                 
                 if event_type == "in":
                     # Cannot clock in if already in
                     if last_log and last_log.event_type == "in":
                         return {
                             "status": "failure",
                             "reason": f"Hey {name}, you are already clocked in!",
                             "error_code": "constraint_violation"
                         }
                 elif event_type == "out":
                     # Cannot clock out if not in (or already out)
                     if not last_log or last_log.event_type == "out":
                          return {
                             "status": "failure",
                             "reason": f"Hey {name}, please clock in first.",
                             "error_code": "constraint_violation"
                         }
                 break # Close session
    
    # 5. Audit
    await audit_service.log_event(
        user_id=user_id, 
        confidence=confidence, 
        image_bytes=best_frame,
        identified_name=name,
        employee_id=found_employee_id,
        event_type=event_type,
        kiosk_id=kiosk.id,
        metadata_info={
            "early_exit": early_exit_triggered,
            "frames_processed": len(valid_vectors) if not early_exit_triggered else 1,
            "engine_used": vector_service.engine_name,
            "threshold": vector_service.threshold,
            "rescue_delta": vector_service.rescue_delta,
            **liveness_metrics, # Detailed liveness scores
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "liveness_ms": int((t_liveness_end - t_liveness_start) * 1000),
            "embedding_ms": int((t_embedding_end - t_embedding_start) * 1000),
            "search_ms": int((t_search_end - t_search_start) * 1000),
        },
        match_type=match_reason if user_id else "rejected",
        error_code=None if final_status == "success" else "user_not_found"
    )
    
    if final_status == "success":
        rate_limiter.record_attempt(rate_key, success=True)
        return {
            "status": "success", 
            "user": {"name": name, "id": user_id}, 
            "confidence": confidence,
            "error_code": None
        }
    else:
        rate_limiter.record_attempt(rate_key, success=False)
        # Standardized error codes for frontend handling
        return {
            "status": "failure", 
            "reason": "Face not recognized. Please try again or contact HR if this persists.", 
            "error_code": "user_not_found"
        }
