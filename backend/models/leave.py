from typing import Optional
from datetime import date
from sqlmodel import Field, SQLModel

class Leave(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    leave_type: str # "Sick", "Casual", "Earned"
    start_date: date
    end_date: date
    reason: Optional[str] = None
    attachment: Optional[str] = None # Path to file
    status: str = Field(default="Pending") # "Pending", "Approved", "Rejected"
