from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now, index=True)  # Index for date range queries
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)  # Index for user filtering
    kiosk_id: Optional[int] = Field(default=None, index=True)  # Index for kiosk filtering
    event_type: str = Field(default="unknown") # "in" or "out"
    identified_name: Optional[str] = None
    employee_id: Optional[str] = Field(default=None, description="Employee ID e.g. EMP-123")
    confidence: float
    thumbnail_path: Optional[str] = None # Path to ephemeral low-res image
    metadata_info: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Rejection tracking for analytics
    rejection_reason: Optional[str] = Field(default=None, description="Specific reason for rejection")
    error_code: Optional[str] = Field(default=None, description="Error code: liveness_failed, user_not_found, etc.")
    match_type: Optional[str] = Field(default=None, description="Match type: strong_match, rescue_match, rejected")
    
    # Location Verification
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None # in meters
    is_geofence_verified: Optional[bool] = Field(default=False)
    distance_from_site: Optional[float] = None
    spoof_risk_score: Optional[int] = None # 0-100


