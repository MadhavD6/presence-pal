from typing import Optional
from datetime import date, datetime
from sqlmodel import Field, SQLModel

class AttendanceCorrection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    original_date: date
    corrected_in: Optional[datetime] = None
    corrected_out: Optional[datetime] = None
    reason: str
    attachment: Optional[str] = None # Path to file
    status: str = Field(default="Pending") # Pending, Approved, Rejected
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolver_id: Optional[int] = None # Manager who approved/rejected
