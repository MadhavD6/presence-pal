import os
import shutil
from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.audit import AuditLog
from backend.core.config import get_settings

settings = get_settings()

class AuditService:
    def __init__(self):
        self.retention_days = settings.AUDIT_RETENTION_DAYS
        self.thumbnail_dir = "thumbnails"
        os.makedirs(self.thumbnail_dir, exist_ok=True)
        
    def log_event(self, 
                  user_id: Optional[int], 
                  confidence: float, 
                  image_bytes: Optional[bytes] = None,
                  identified_name: Optional[str] = None,
                  event_type: str = "unknown",
                  kiosk_id: Optional[int] = None,
                  metadata_info: Optional[dict] = None,
                  rejection_reason: Optional[str] = None,
                  error_code: Optional[str] = None,
                  match_type: Optional[str] = None):
        """
        Log an access attempt with full rejection tracking.
        Saves a LOW-RES thumbnail.
        """
        thumb_path = None
        if image_bytes:
            # Create a unique filename
            filename = f"{datetime.now().timestamp()}_{user_id or 'unknown'}.jpg"
            thumb_path = os.path.join(self.thumbnail_dir, filename)
            
            with open(thumb_path, "wb") as f:
                f.write(image_bytes)
                
        with Session(engine) as session:
            log = AuditLog(
                user_id=user_id,
                identified_name=identified_name,
                confidence=confidence,
                thumbnail_path=thumb_path,
                event_type=event_type,
                kiosk_id=kiosk_id,
                timestamp=datetime.now(),
                metadata_info=metadata_info,
                rejection_reason=rejection_reason,
                error_code=error_code,
                match_type=match_type
            )
            session.add(log)
            session.commit()
            
    def purge_old_logs(self):
        """
        Delete logs and files older than retention period.
        """
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        print(f"Running purging job. Cutoff: {cutoff}")
        
        with Session(engine) as session:
            # 1. Find old logs
            statement = select(AuditLog).where(AuditLog.timestamp < cutoff)
            results = session.exec(statement).all()
            
            count = 0
            for log in results:
                # 2. Delete file
                if log.thumbnail_path and os.path.exists(log.thumbnail_path):
                    try:
                        os.remove(log.thumbnail_path)
                    except Exception as e:
                        print(f"Error deleting file {log.thumbnail_path}: {e}")
                
                # 3. Delete DB record
                session.delete(log)
                count += 1
            
            session.commit()
            print(f"Purged {count} old audit logs.")

audit_service = AuditService()
