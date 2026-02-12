# Payroll Module Design Document

## 1. Overview
This design introduces a robust Payroll module to transform raw biometrics into actionable financial data. It moves away from on-the-fly calculations to a persistent, state-based model using **Daily Summaries** and **Payroll Runs**.

## 2. Database Schema (SQLModel)

We need three new tables to handle configuration, daily aggregation, and finalized pay runs.

```python
# backend/models/payroll.py
from typing import Optional
from datetime import date, datetime
from sqlmodel import Field, SQLModel, Relationship

class PayrollConfig(SQLModel, table=True):
    """Stores individual salary settings per employee."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    base_hourly_rate: float = Field(default=0.0)
    overtime_multiplier: float = Field(default=1.5) # e.g. 1.5x for OT
    currency: str = Field(default="USD")
    # Link to shift if needed, or default 9-5
    shift_start_time: str = Field(default="09:00") 

class DailySummary(SQLModel, table=True):
    """
    Pre-calculated daily record. 
    Critically separates raw punches from business logic.
    Populated by a daily cron or 'Refresh' action.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: date
    
    # Aggregated from AuditLog
    first_in: Optional[datetime] = None
    last_out: Optional[datetime] = None
    
    # Computed Headers
    total_hours: float = Field(default=0.0)
    regular_hours: float = Field(default=0.0)
    overtime_hours: float = Field(default=0.0)
    
    # Status
    is_late: bool = Field(default=False)
    status: str = Field(default="Absent") # Present, Absent, Leave, Holiday, MissedPunch
    
    # Financial snapshot (rates can change, so we verify here?) 
    # Usually kept separate, but calculated during PayrollRun.

class PayrollRun(SQLModel, table=True):
    """Represents a generated batch for a month."""
    id: Optional[int] = Field(default=None, primary_key=True)
    start_date: date
    end_date: date
    is_finalized: bool = Field(default=False) # If true, locks changes
    total_payout: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Payslip(SQLModel, table=True):
    """The final artifact for an employee."""
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="payrollrun.id")
    user_id: int = Field(foreign_key="user.id")
    
    gross_pay: float
    total_deductions: float
    net_pay: float
    
    # Breakdown structure stored as JSON
    details: str = Field(default="{}") 
```

## 3. Calculation Logic (Backend Service)

### Algorithm: Daily Aggregation
Instead of calculating payroll directly from raw logs, we first normalize data into `DailySummary`.

```python
# backend/services/payroll_service.py

def aggregate_daily_attendance(user_id: int, target_date: date, session: Session):
    # 1. Fetch raw punches
    logs = session.exec(select(AuditLog)...).all()
    
    # 2. Identify First In / Last Out
    in_punches = [l for l in logs if l.event_type == 'in']
    out_punches = [l for l in logs if l.event_type == 'out']
    
    if not in_punches:
        # Check leave table
        return create_summary(status="Absent" or "Leave")
        
    first_in = in_punches[0].timestamp
    
    # 3. Handle Missing Out (Edge Case)
    if not out_punches:
        # Strategy: Mark as 'MissedPunch' - requires manual manager override
        # OR Auto-close at 6 PM (risky)
        return create_summary(status="MissedAction", first_in=first_in)
        
    last_out = out_punches[-1].timestamp
    
    # 4. Calculate Duration
    duration = (last_out - first_in).total_seconds() / 3600.0
    
    # 5. Apply Rules
    STANDARD_Hours = 8.0
    regular = min(duration, STANDARD_Hours)
    overtime = max(0, duration - STANDARD_Hours)
    
    # 6. Late Check
    SHIFT_START = 9.0 # 9 AM
    is_late = first_in.hour + (first_in.minute/60) > SHIFT_START + 0.25 # 15 min grace
    
    create_summary(
        regular_hours=regular,
        overtime_hours=overtime,
        is_late=is_late,
        status="Present"
    )
```

### Algorithm: Payroll Generation
Iterate over `DailySummary` rows for the date range.

`Pay = (RegularHours * Rate) + (OvertimeHours * Rate * 1.5) - (LateCount * Deduction)`

## 4. API Endpoints

### Manager
*   `POST /api/v1/payroll/aggregate`: Force re-calculation of daily summaries for a date range (e.g., after fixing a punch).
*   `POST /api/v1/payroll/generate`: Create a draft `PayrollRun`. Returns a Run ID.
*   `GET /api/v1/payroll/run/{run_id}`: View totals for review.
*   `POST /api/v1/payroll/run/{run_id}/finalize`: Lock the run, allowing employees to see slips.

### Employee
*   `GET /api/v1/payroll/slips`: List available slips.
*   `GET /api/v1/payroll/slips/{id}`: Detailed view.

## 5. Integration Points
*   **Existing `ManagerTimesheetView`**:
    *   **Change**: Stop summing `AuditLog` directly in the frontend/backend timesheet API.
    *   **New**: Read from `DailySummary` table. It's faster (O(1) vs O(N)) and accurate (includes manual overrides).
*   **Manual Corrections**:
    *   Add a "Fix Punch" button in Manager Dashboard. When a manager manually edits a time, **trigger the Aggregation Logic** for that day immediately to update `DailySummary`.

## 6. Frontend Screens

### A. Manager Payroll Dashboard
1.  **Overview Card**: "Pending Payroll for Jan 2026".
2.  **Batch Generation**: Button "Generate January Payroll".
3.  **Review Table**:
    *   List of Employees | Total Hours | OT Hours | Estimated Payout | Status (Ready/Error).
    *   *Highlight "Error" rows (Missed Punches) in red.*

### B. Employee Payslip
A clean, printable component:
*   **Header**: Company Logo, Pay Period.
*   **Grid**:
    *   Base Pay: 160hrs @ $20/hr = $3200
    *   Overtime: 5hrs @ $30/hr = $150
    *   Deductions: Late (2) = -$20
*   **Footer**: Net Pay, Tax hints (if applicable).

## 7. Handling Edge Cases
1.  **Missing Out Punch**:
    *   *System*: Flags day as `MissedPunch` in `DailySummary`.
    *   *Payroll Calc*: Defaults hours to 0 for that day to force Manager attention.
    *   *Fix*: Manager adds manual `Out` time -> recalculates summary -> user gets paid.
2.  **Holidays**:
    *   Need a `Holiday` table. `aggregate_daily_attendance` should check this list first. If user punches on holiday -> Auto-mark as OT or specialized Holiday Pay.
3.  **Active Leaves**:
    *   Start of aggregation checks `Leave` table. If `Approved` leave exists, set `DailySummary.status = "Leave"` and `payable_hours = 0` (or 8 if paid leave).
