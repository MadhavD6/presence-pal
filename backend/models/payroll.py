from typing import Optional, List
from datetime import date, datetime
from sqlmodel import Field, SQLModel, Relationship

class PayrollConfig(SQLModel, table=True):
    """Stores individual salary settings per employee."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    base_hourly_rate: float = Field(default=0.0)
    currency: str = Field(default="USD")
    overtime_multiplier: float = Field(default=1.5) 
    late_deduction_amount: float = Field(default=0.0) # Fixed amount or we calculate dynamically? Plan says 0.5 * hourly.
    # We can store the policy logic in code, or params here. 
    # Let's keep it simple: code logic will use base_hourly_rate * 0.5.

class DailySummary(SQLModel, table=True):
    """
    Pre-calculated daily record. 
    Populated by a daily cron or 'Refresh' action.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: date
    
    first_in: Optional[datetime] = None
    last_out: Optional[datetime] = None
    
    # Hours
    total_hours: float = Field(default=0.0)
    regular_hours: float = Field(default=0.0)
    overtime_hours: float = Field(default=0.0)
    
    # Status
    is_late: bool = Field(default=False)
    status: str = Field(default="Absent") # Present, Absent, Leave, Holiday, MissedPunch
    
class PayrollRun(SQLModel, table=True):
    """Represents a generated batch for a month."""
    id: Optional[int] = Field(default=None, primary_key=True)
    start_date: date
    end_date: date
    is_finalized: bool = Field(default=False) 
    total_payout: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.now)

class Payslip(SQLModel, table=True):
    """The final artifact for an employee."""
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="payrollrun.id")
    user_id: int = Field(foreign_key="user.id")
    
    gross_pay: float = Field(default=0.0)
    total_deductions: float = Field(default=0.0)
    net_pay: float = Field(default=0.0)
    
    total_hours: float = Field(default=0.0)
    ot_hours: float = Field(default=0.0)
    late_days: int = Field(default=0)
    
    # Status
    status: str = Field(default="Ready") # Ready, Blocked, Error
    warnings: str = Field(default="[]") # JSON list of warning strings
    
    # Details JSON string for breakdown
    details: str = Field(default="{}") 
