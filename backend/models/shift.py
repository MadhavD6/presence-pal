from typing import Optional
from datetime import time, date
from sqlmodel import Field, SQLModel

class Shift(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True) # e.g. "General Shift", "Morning Shift"
    start_time: time
    end_time: time
    grace_period_mins: int = Field(default=15)
    crosses_midnight: bool = Field(default=False) # True if end_time < start_time


class EmployeeShift(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    shift_id: int = Field(foreign_key="shift.id")
    start_date: date
    end_date: Optional[date] = Field(default=None) # Null means currently active logic
    is_active: bool = Field(default=True)
    weekly_offs: str = Field(default="6") # Comma-separated weekday numbers (0=Mon, 6=Sun). Default is Sunday.
