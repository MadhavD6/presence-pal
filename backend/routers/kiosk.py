from typing import Annotated, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, Security, Body
from sqlmodel import Session, select
from backend.core.database import get_session
from backend.models.kiosk import Kiosk
from backend.core.security import get_password_hash, get_current_kiosk
import secrets

router = APIRouter()

@router.post("/kiosk/register")
async def register_kiosk(
    device_id: str,
    location: str,
    building: str,
    session: Session = Depends(get_session)
):
    # Check if exists
    existing = session.exec(select(Kiosk).where(Kiosk.device_id == device_id)).first()
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
    session.commit()
    session.refresh(kiosk)
    
    return {
        "status": "success",
        "kiosk_id": kiosk.id,
        "api_key": f"kiosk:{device_id}:{secret}",
        "message": "Save this key securely. It will not be shown again."
    }

@router.post("/kiosk/heartbeat")
async def heartbeat(
    kiosk: Kiosk = Depends(get_current_kiosk),
    session: Session = Depends(get_session)
):
    kiosk.last_heartbeat = datetime.now()
    session.add(kiosk)
    session.commit()
    return {"status": "online", "kiosk": kiosk.device_id}

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
    session: Session = Depends(get_session)
):
    """
    Sync offline punches. Batch process.
    """
    processed = 0
    skipped = 0
    
    for item in items:
        # Check duplicate
        time_window = timedelta(seconds=5)
        
        exists = session.exec(
            select(AuditLog)
            .where(AuditLog.user_id == item.user_id)
            .where(AuditLog.event_type == item.event_type)
            .where(AuditLog.timestamp >= item.timestamp - time_window)
            .where(AuditLog.timestamp <= item.timestamp + time_window)
        ).first()
        
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
        
    session.commit()
    
    return {"processed": processed, "skipped": skipped, "status": "success"}

from fastapi import UploadFile, File, Form
from backend.services.face import face_service
from backend.services.vector import vector_service
from backend.services.audit import audit_service
from backend.services.liveness import liveness_service
from backend.services.rate_limiter import rate_limiter
from backend.models.user import User
from backend.core.database import engine

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
    
    if not files:
         raise HTTPException(status_code=400, detail="No images provided")

    # Read all frames
    frames_content = []
    for f in files:
        frames_content.append(await f.read())
    
    # 1. Passive Liveness
    is_live, reason = liveness_service.check_liveness(frames_content)
    if not is_live:
        rate_limiter.record_attempt(rate_key, success=False)
        audit_service.log_event(
            user_id=None, 
            confidence=0.0, 
            image_bytes=frames_content[0],
            identified_name="Spoof/Static",
            event_type=event_type,
            kiosk_id=kiosk.id,
            rejection_reason=reason,
            error_code="liveness_failed",
            match_type="rejected"
        )
        return {
            "status": "failure", 
            "reason": reason,
            "error_code": "liveness_failed"
        }

    # 2. Get Embedding (Multi-Frame Averaging) with Early Exit
    valid_vectors = []
    best_frame = frames_content[len(frames_content)//2]
    early_exit_triggered = False
    
    for i, frame_bytes in enumerate(frames_content):
        # Generate embedding for this frame
        vec = face_service.get_embedding(frame_bytes)
        if vec:
            valid_vectors.append(vec)
            
            # --- Early Exit Optimization ---
            # If >99% confidence on first frame, stop immediately.
            t_uid, t_conf = vector_service.find_nearest(vec)
            if t_uid and t_conf > 0.99:
                print(f"⚡ Early Exit Triggered: Frame {i+1} with {t_conf:.4f} conf")
                # Discard others (optimization), focus on this perfect capture
                valid_vectors = [vec] 
                best_frame = frame_bytes
                early_exit_triggered = True
                break
            # -------------------------------
            
    if not valid_vectors:
        return {
            "status": "failure", 
            "reason": "no_face", 
            "error_code": "no_face_detected"
        }
        
    # Calculate Mean Vector (Centroid) to reduce noise
    import numpy as np
    
    if len(valid_vectors) == 1:
        vector = valid_vectors[0]
    else:
        # Average
        matrix = np.array(valid_vectors)
        mean_vector = np.mean(matrix, axis=0) # Shape: (512,)
        
        # Normalize (L2) - Critical for Cosine Similarity
        norm = np.linalg.norm(mean_vector)
        if norm > 0:
            mean_vector = mean_vector / norm
            
        vector = mean_vector.tolist()

    # 3. Multi-Reference Aggregation Match
    user_scores = vector_service.search_all_matches(vector)
    user_id, confidence, match_reason = vector_service.decide_match(user_scores)
    
    # 4. Resolve User
    name = None
    final_status = "unknown"
    
    if user_id:
        # Check Cache
        from backend.core.cache import cache
        cached_user = cache.get(f"user:{user_id}")
        
        if cached_user:
            name = cached_user['name']
            final_status = "success"
        else:
            with Session(engine) as session:
                user = session.get(User, user_id)
                if user:
                    name = user.name
                    final_status = "success"
                    cache.set(f"user:{user_id}", {"name": user.name, "id": user.id}, ttl=3600)

        # 4.5. Check Constraints (Prevent Double Punch)
        if final_status == "success" and event_type in ["in", "out"]:
             with Session(engine) as session:
                 # Get last successful punch for this user
                 last_log = session.exec(
                     select(AuditLog)
                     .where(AuditLog.user_id == user_id)
                     .where(AuditLog.identified_name != None) # Only valid identifies
                     .order_by(AuditLog.timestamp.desc())
                 ).first()
                 
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
    
    # 5. Audit
    audit_service.log_event(
        user_id=user_id, 
        confidence=confidence, 
        image_bytes=best_frame,
        identified_name=name,
        event_type=event_type,
        kiosk_id=kiosk.id,
        metadata_info={
            "early_exit": early_exit_triggered,
            "frames_processed": len(valid_vectors) if not early_exit_triggered else 1,
            "engine_used": vector_service.engine_name,
            "threshold": vector_service.threshold,
            "rescue_delta": vector_service.rescue_delta
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
            "reason": "Identification failed - User not recognized", 
            "error_code": "user_not_found"
        }
