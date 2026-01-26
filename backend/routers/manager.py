from datetime import date, datetime, time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func, col, and_
from pydantic import BaseModel
from backend.core.database import get_session
from backend.core.security import get_current_manager_user, get_current_kiosk
from backend.models.user import User
from backend.models.audit import AuditLog
from backend.models.leave import Leave
from backend.models.shift import EmployeeShift, Shift

from backend.models.kiosk import Kiosk

router = APIRouter()

@router.get("/manager/kiosks")
async def get_kiosks(
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    kiosks = session.exec(select(Kiosk)).all()
    # Mask secrets? Maybe no need to send hash.
    return kiosks

from backend.models.site import Site

class AssignSiteRequest(BaseModel):
    user_ids: List[int]
    site_id: Optional[int]

@router.get("/manager/employees")
async def get_employees(
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    # Join User with Site to get site names
    statement = select(User, Site).outerjoin(Site)
    results = session.exec(statement).all()
    
    data = []
    for user, site in results:
         data.append({
            "id": user.id,
            "name": user.name,
            "employee_id": user.employee_id,
            "shift_id": user.shift_id,
            "role": user.role,
            "site_id": user.site_id,
            "site_name": site.name if site else "No Site Assigned"
        })
    return data

@router.get("/manager/sites")
async def get_sites(
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    return session.exec(select(Site).where(Site.is_active == True)).all()

@router.post("/manager/employees/assign-site")
async def assign_site(
    data: AssignSiteRequest, 
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    # If site_id is provided, verify it exists
    if data.site_id:
        site = session.get(Site, data.site_id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
            
    statement = select(User).where(col(User.id).in_(data.user_ids))
    users = session.exec(statement).all()
    
    for user in users:
        user.site_id = data.site_id
        session.add(user)
        
    session.commit()
    return {"status": "success", "updated": len(users)}

# ... imports ...
from backend.core.security import get_password_hash

class EmployeeCreate(BaseModel):
    name: str
    employee_id: str
    role: str = "user"
    site_id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = "password" # Default password

@router.post("/manager/employees")
async def create_employee(
    data: EmployeeCreate,
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    # Check ID uniqueness
    existing = session.exec(select(User).where(User.employee_id == data.employee_id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")

    new_user = User(
        name=data.name,
        employee_id=data.employee_id,
        role=data.role,
        site_id=data.site_id,
        email=data.email,
        hashed_password=get_password_hash(data.password) if data.password else None
    )
    session.add(new_user)
    session.commit()
    return {"status": "success", "id": new_user.id}

@router.put("/manager/employees/{user_id}")
async def update_employee(
    user_id: int,
    data: EmployeeCreate, # Reusing schema for simplicity
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.name = data.name
    # Don't update employee_id easily to avoid consistency issues? Or allow it.
    if data.employee_id != user.employee_id:
        existing = session.exec(select(User).where(User.employee_id == data.employee_id)).first()
        if existing:
            raise HTTPException(status_code=400, detail="New Employee ID already taken")
        user.employee_id = data.employee_id
        
    user.role = data.role
    user.site_id = data.site_id
    user.email = data.email
    
    if data.password and data.password != "password": # Only update if changed from default? Or basic logic
         pass # Skip password update here for simplicity unless explicit
         
    session.add(user)
    session.commit()
    return {"status": "success"}

@router.get("/manager/stats")
async def get_manager_stats(
    date_str: str, 
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        target_date = date.today()

    # 1. Total Staff (Active)
    total_staff = session.exec(select(func.count(User.id))).one()

    # 2. Daily Attendance Logs (for calculations)
    # Get all logs for the day
    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)
    
    daily_logs = session.exec(
        select(AuditLog).where(
            and_(
                AuditLog.timestamp >= start_of_day,
                AuditLog.timestamp <= end_of_day
            )
        )
    ).all()

    # 3. Calculate Present / In / Out
    present_user_ids = set()
    currently_in = 0
    currently_out = 0
    
    # We need to reconstruct current status for each user based on their last event
    # Group by user_id
    user_logs = {}
    for log in daily_logs:
        if not log.user_id: continue
        present_user_ids.add(log.user_id)
        if log.user_id not in user_logs:
            user_logs[log.user_id] = []
        user_logs[log.user_id].append(log)

    for uid, logs in user_logs.items():
        # Sort logs by time
        sorted_logs = sorted(logs, key=lambda x: x.timestamp)
        last_event = sorted_logs[-1]
        if last_event.event_type == 'in':
            currently_in += 1
        else:
            currently_out += 1

    present_count = len(present_user_ids)
    
    # 4. Leaves & Holidays (Placeholder logic for now, or real if data exists)
    # Using Leave model
    leaves_count = session.exec(
        select(func.count(Leave.id)).where(
            and_(
                Leave.start_date <= target_date,
                Leave.end_date >= target_date,
                Leave.status == "Approved"
            )
        )
    ).one()

    # 5. Not In (People who haven't punched yet and aren't on leave)
    # This is rough approximation. Total - Present - Leave
    not_in_count = max(0, total_staff - present_count - leaves_count)

    return {
        "date": target_date.isoformat(),
        "total": total_staff,
        "present": present_count,
        "in": currently_in,
        "out": currently_out,
        "notIn": not_in_count,
        "leave": leaves_count,
        "holiday": 0, # TODO: Add Holiday model
        "weeklyOff": 0 # TODO: Logic for weekends
    }

@router.get("/manager/timesheet")
async def get_timesheet(
    start_date_str: str,
    end_date_str: str,
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        # Default to current week
        today = date.today()
        # simplified logic, caller should send correct dates
        start_date = today
        end_date = today

    # 1. Fetch Data
    users = session.exec(select(User)).all()
    
    # Logs for the range
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    
    logs = session.exec(
        select(AuditLog).where(
            and_(
                AuditLog.timestamp >= start_dt,
                AuditLog.timestamp <= end_dt
            )
        )
    ).all()
    
    # Leaves for the range
    leaves = session.exec(
        select(Leave).where(
            and_(
                Leave.end_date >= start_date,
                Leave.start_date <= end_date,
                Leave.status == "Approved"
            )
        )
    ).all()

    # 2. Index Data
    # map[(user_id, date_str)] = [logs]
    logs_map = {}
    for log in logs:
        d_str = log.timestamp.date().isoformat()
        key = (log.user_id, d_str)
        if key not in logs_map:
            logs_map[key] = []
        logs_map[key].append(log)

    # map[(user_id, date_str)] = True (if on leave)
    leave_map = {}
    from datetime import timedelta
    
    for leave in leaves:
        curr = leave.start_date
        while curr <= leave.end_date:
            if start_date <= curr <= end_date:
                leave_map[(leave.user_id, curr.isoformat())] = True
            curr += timedelta(days=1)

    # 3. Build Grid
    timesheet_data = []
    
    # Generate list of date strings in the range
    date_strs = []
    curr = start_date
    while curr <= end_date:
        date_strs.append(curr.isoformat())
        curr += timedelta(days=1)
        
    # Pre-fetch all shifts
    all_shifts = {s.id: s for s in session.exec(select(Shift)).all()}
    default_shift = Shift(name="General Shift", start_time=time(9,0), end_time=time(18,0), grace_period_mins=15)

    for user in users:
        days_status = []
        total_worked_seconds = 0
        
        # Fetch Shift History
        history = session.exec(
            select(EmployeeShift)
            .where(EmployeeShift.user_id == user.id)
            .order_by(EmployeeShift.start_date)
        ).all()
        
        # Resolve Current Cache Shift
        current_cache_shift = all_shifts.get(user.shift_id) if user.shift_id else default_shift

        for d_str in date_strs:
            curr_d = datetime.strptime(d_str, "%Y-%m-%d").date()
            
            # Find applicable shift for this day
            applicable_shift = current_cache_shift # Fallback
            for rec in history:
                if rec.start_date <= curr_d and (rec.end_date is None or rec.end_date >= curr_d):
                    # Found a historical record covering this date
                    applicable_shift = all_shifts.get(rec.shift_id, default_shift)
                    # Keep looking? No, records might overlap? Assuming valid robust data, take latest valid or first valid?
                    # If multiple, take the one with latest start_date?
                    # Since we ordered simply by start_date, the later ones come later.
                    # But actually if we order by start_date, we just iterate.
                    # Correct logic: Pick the record where date IN [start, end].
                    # If multiple match (should not happen), pick one.
                    break 
            
            # Use applicable_shift for this specific day
            user_shift = applicable_shift
            shift_code = user_shift.name[:2].upper()
            shift_tooltip = f"{user_shift.name} ({user_shift.start_time.strftime('%H:%M')} - {user_shift.end_time.strftime('%H:%M')})"
            key = (user.id, d_str)
            day_logs = logs_map.get(key, [])
            
            status = "-"
            current_shift_code = shift_code
            current_shift_tooltip = shift_tooltip
            
            # Check weekday for WO (Sunday=6)
            curr_d = datetime.strptime(d_str, "%Y-%m-%d").date()
            if curr_d.weekday() == 6: # Sunday
                status = "WO"
                current_shift_code = "WO"
                current_shift_tooltip = "Weekly Off"
            
            # Check Logs
            if day_logs:
                status = "PR"
                # Calc hours
                day_logs.sort(key=lambda x: x.timestamp)
                first = day_logs[0]
                last = day_logs[-1]
                if last.timestamp > first.timestamp:
                    total_worked_seconds += (last.timestamp - first.timestamp).total_seconds()
            elif leave_map.get(key):
                status = "LV"
                current_shift_code = "LV"
                current_shift_tooltip = "Leave"
                
            days_status.append({
                "status": status,
                "shift_code": current_shift_code,
                "tooltip": current_shift_tooltip
            })
            
        # Format total hours
        hours = int(total_worked_seconds // 3600)
        minutes = int((total_worked_seconds % 3600) // 60)
        worked_str = f"{hours}h {minutes}m"
        
        timesheet_data.append({
            "name": user.name,
            "id": user.employee_id,
            "dept": "Engineering", # Placeholder until Dept added to User model
            "avatar": "".join([n[0] for n in user.name.split(" ")[:2]]),
            "stats": { "payable": worked_str, "worked": worked_str }, # Payable logic can be complex
            "days": days_status
        })

    return timesheet_data

@router.get("/manager/daily-log")
async def get_daily_log(
    date_str: str,
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        target_date = date.today()

    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)

    results = session.exec(
        select(AuditLog, User)
        .where(
            and_(
                AuditLog.timestamp >= start_of_day,
                AuditLog.timestamp <= end_of_day,
                AuditLog.user_id == User.id
            )
        )
        .order_by(AuditLog.timestamp.desc())
    ).all()
    
    all_users = session.exec(select(User)).all()
    logs_by_user = {}
    
    leaves = session.exec(
        select(Leave).where(
            and_(
                Leave.start_date <= target_date,
                Leave.end_date >= target_date,
                Leave.status == "Approved"
            )
        )
    ).all()
    leave_user_ids = {l.user_id for l in leaves}

    for log, user in results:
        if user.id not in logs_by_user:
            logs_by_user[user.id] = []
        logs_by_user[user.id].append(log)

    staff_view = []
    for user in all_users:
        user_logs = logs_by_user.get(user.id, [])
        user_logs.sort(key=lambda x: x.timestamp)
        
        status = "Not In"
        in_time = "-"
        duration_str = "-"
        
        if user.id in leave_user_ids:
            status = "Leave"
        
        if user_logs:
            first_in = next((l for l in user_logs if l.event_type == 'in'), None)
            if first_in:
                in_time = first_in.timestamp.strftime("%I:%M %p")
                
            last_event = user_logs[-1]
            if last_event.event_type == 'in':
                status = "In"
            else:
                status = "Out"
                
            if first_in:
                end_time = last_event.timestamp if last_event.event_type == 'out' else datetime.utcnow()
                if end_time > first_in.timestamp:
                    diff = end_time - first_in.timestamp
                    hours = diff.seconds // 3600
                    minutes = (diff.seconds % 3600) // 60
                    duration_str = f"{hours}h {minutes}m"

        staff_view.append({
            "id": user.employee_id,
            "name": user.name,
            "avatar": "".join([n[0] for n in user.name.split(" ")[:2]]),
            "inTime": in_time,
            "duration": duration_str,
            "status": status,
            "last_log_id": user_logs[-1].id if user_logs else None
        })
        
    staff_view.sort(key=lambda x: (x['status'] == 'Not In', x['name']))

    return staff_view
    
from backend.models.correction import AttendanceCorrection
from fastapi import HTTPException

# --- Approval Endpoints ---

@router.get("/manager/approvals/leaves")
async def get_pending_leaves(
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    leaves = session.exec(
        select(Leave, User)
        .where(Leave.user_id == User.id)
        .where(Leave.status == "Pending")
    ).all()
    
    return [
        {
            "id": l.id,
            "name": u.name,
            "type": l.leave_type,
            "start_date": l.start_date,
            "end_date": l.end_date,
            "reason": l.reason,
            "created_at": date.today() # todo: add created_at to Leave model
        } for l, u in leaves
    ]

@router.post("/manager/approvals/leaves/{leave_id}")
async def approve_leave(
    leave_id: int, 
    action: str, # "approve" or "reject"
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    leave = session.get(Leave, leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
        
    if action == "approve":
        leave.status = "Approved"
    elif action == "reject":
        leave.status = "Rejected"
    else:
         raise HTTPException(status_code=400, detail="Invalid action")
         
    session.add(leave)
    session.commit()
    return {"status": "success"}

@router.get("/manager/approvals/corrections")
async def get_pending_corrections(
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    corrections = session.exec(
        select(AttendanceCorrection, User)
        .where(AttendanceCorrection.user_id == User.id)
        .where(AttendanceCorrection.status == "Pending")
    ).all()
    
    return [
        {
            "id": c.id,
            "name": u.name,
            "date": c.original_date,
            "corrected_in": c.corrected_in,
            "corrected_out": c.corrected_out,
            "reason": c.reason,
            "created_at": c.created_at
        } for c, u in corrections
    ]

@router.post("/manager/approvals/corrections/{correction_id}")
async def approve_correction(
    correction_id: int,
    action: str, # "approve" or "reject"
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    correction = session.get(AttendanceCorrection, correction_id)
    if not correction:
        raise HTTPException(status_code=404, detail="Correction not found")
        
    if action == "approve":
        correction.status = "Approved"
        correction.resolved_at = datetime.utcnow()
        
        # Logic to update AuditLog!
        # This is CRITICAL. If approved, we must insert/update logs to reflect new time.
        # Strategy: Insert new logs with manually set timestamps.
        # But wait, AuditLog stores raw punches. 
        # A correction implies overriding the daily stats. 
        # For MVP: We will insert TWO new logs: one 'in' and one 'out' (if provided) at the corrected times.
        # This might duplicate existing punches? 
        # Ideally we should soft-delete old punches or mark them invalid, but that's complex.
        # Simple approach: Insert new logs with a flag or trust `calculate_daily_stats` handles multiple punches (it picks first in / last out).
        # So inserting the CORRECTED times (if they extend the range) works.
        # If they *shrink* the range (e.g. forgot to punch out earlier), adding a later punch doesn't help.
        # BUT `calculate_daily_stats` uses first In and last Out.
        # If user forgot to punch In: Adding an earlier In works.
        # If user forgot to punch Out: Adding a later Out works.
        # If user wants to CHANGE time to be shorter (e.g. strict shift), simply adding logs won't overwrite the existing wider range.
        # However, for MVP: Let's assume corrections are mostly for "Missing" punches.
        
        if correction.corrected_in:
            log_in = AuditLog(
                user_id=correction.user_id,
                timestamp=correction.corrected_in,
                event_type="in",
                confidence=1.0,
                metadata_info={"verification_method": "manual_correction"}
            )
            session.add(log_in)
            
        if correction.corrected_out:
            log_out = AuditLog(
                user_id=correction.user_id,
                timestamp=correction.corrected_out,
                event_type="out",
                confidence=1.0,
                metadata_info={"verification_method": "manual_correction"}
            )
            session.add(log_out)
            
    elif action == "reject":
        correction.status = "Rejected"
        correction.resolved_at = datetime.utcnow()
    else:
         raise HTTPException(status_code=400, detail="Invalid action")
         
    session.add(correction)
    session.commit()
    return {"status": "success"}

@router.get("/manager/approvals/history")
@router.get("/manager/approvals/history")
async def get_approval_history(
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    # Fetch resolved leaves
    leaves = session.exec(
        select(Leave, User)
        .where(Leave.user_id == User.id)
        .where(Leave.status != "Pending")
        .order_by(Leave.start_date.desc())
        .limit(50)
    ).all()
    
    # Fetch resolved corrections
    corrections = session.exec(
        select(AttendanceCorrection, User)
        .where(AttendanceCorrection.user_id == User.id)
        .where(AttendanceCorrection.status != "Pending")
        .order_by(AttendanceCorrection.created_at.desc())
        .limit(50)
    ).all()
    
    history = []
    for l, u in leaves:
        history.append({
            "id": l.id,
            "type": "Leave",
            "name": u.name,
            "details": f"{l.leave_type} ({l.start_date} to {l.end_date})",
            "status": l.status,
            "date": l.start_date.isoformat()
        })
        
    for c, u in corrections:
        history.append({
            "id": c.id,
            "type": "Correction",
            "name": u.name,
            "details": f"Correction for {c.original_date}: {c.reason}",
            "status": c.status,
            "date": c.created_at.date().isoformat()
        })
        
    # Sort combined history by date desc
    history.sort(key=lambda x: x['date'], reverse=True)
    return history

# --- Enhanced Reporting ---

class DetailedReportRow(BaseModel):
    date: str
    employee_id: str
    employee_name: str
    shift_name: str
    shift_start: str
    shift_end: str
    in_time: str
    out_time: str
    total_hours: str
    late_minutes: int
    early_out_minutes: int
    overtime_hours: float
    status: str
    paid_hours: float
    unpaid_hours: float
    payable_day_fraction: float
    source: str = "Face"
    remarks: str = "-"

@router.get("/manager/reports/detailed", response_model=List[DetailedReportRow])
async def get_detailed_report(
    start_date_str: str,
    end_date_str: str,
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    return _get_detailed_report_data(session, start_date, end_date)

def _get_detailed_report_data(session: Session, start_date: date, end_date: date) -> List[DetailedReportRow]:
    users = session.exec(select(User)).all()
    
    # Pre-fetch Shift Map if needed, or rely on user.shift_id
    # Pre-fetch Leaves for efficiency
    leaves = session.exec(
        select(Leave).where(
            and_(
                Leave.end_date >= start_date,
                Leave.start_date <= end_date,
                Leave.status == "Approved"
            )
        )
    ).all()
    
    # Map leave by (user_id, date)
    leave_map = {}
    from datetime import timedelta
    for leave in leaves:
        curr = leave.start_date
        while curr <= leave.end_date:
            if start_date <= curr <= end_date:
                leave_map[(leave.user_id, curr)] = leave
            curr += timedelta(days=1)
            
    # Fetch logs
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    logs = session.exec(
        select(AuditLog).where(
            and_(
                AuditLog.timestamp >= start_dt,
                AuditLog.timestamp <= end_dt
            )
        )
    ).all()
    
    logs_map = {}
    for log in logs:
        d = log.timestamp.date()
        key = (log.user_id, d)
        if key not in logs_map:
            logs_map[key] = []
        logs_map[key].append(log)
        
    report = []
    
    curr = start_date
    while curr <= end_date:
        for user in users:
            # 1. Determine Shift
            from backend.models.shift import Shift
            user_shift = None
            if user.shift_id:
                user_shift = session.get(Shift, user.shift_id)
            if not user_shift:
                user_shift = Shift(name="General Shift", start_time=time(9,0), end_time=time(18,0), grace_period_mins=15)
                
            # 2. Get Logs & Stats
            day_logs = logs_map.get((user.id, curr), [])
            from backend.services.attendance import calculate_daily_stats
            stats = calculate_daily_stats(day_logs, shift=user_shift)
            
            # 3. Determine Final Status (Check Leaves/Holidays)
            final_status = stats["attendance_status"]
            remarks = "-"
            
            if (user.id, curr) in leave_map:
                l = leave_map[(user.id, curr)]
                final_status = "Leave" # Or specific type
                remarks = l.leave_type
                # MVP: Assume Paid Leave
                stats["payable_fraction"] = 1.0 
                stats["payable_hours"] = 8.0 # Standard day?
                
            elif curr.weekday() == 6: # Sunday
                final_status = "Week Off"
                remarks = "Sunday"
                stats["payable_fraction"] = 1.0 # If paid week off
            
            shift_duration = 9.0
            unpaid = max(0.0, shift_duration - stats["payable_hours"])
            if final_status in ["Week Off", "Leave"]:
                 unpaid = 0.0 # Don't count as unpaid loss
            
            report.append(DetailedReportRow(
                date=curr.isoformat(),
                employee_id=user.employee_id or "E000",
                employee_name=user.name,
                shift_name=stats["shift_name"],
                shift_start=stats["shift_start"],
                shift_end=stats["shift_end"],
                in_time=stats["first_in"] if stats["first_in"] else "-",
                out_time=stats["last_out"] if stats["last_out"] else "-",
                total_hours=stats["worked_hours"],
                late_minutes=stats["late_minutes"],
                early_out_minutes=stats["early_out_minutes"],
                overtime_hours=stats["overtime_hours"],
                status=final_status,
                paid_hours=stats["payable_hours"],
                unpaid_hours=round(unpaid, 2),
                payable_day_fraction=stats["payable_fraction"],
                source="Face",
                remarks=remarks
            ))
        curr += timedelta(days=1)
        
    return report

from fastapi.responses import StreamingResponse
import csv
import io

@router.get("/manager/reports/export")
async def export_detailed_report(
    start_date_str: str,
    end_date_str: str,
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
        
    data = _get_detailed_report_data(session, start_date, end_date)
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    headers = [
        "Date", "Employee ID", "Employee Name", "Shift Name", "Shift Start", "Shift End",
        "Check-In", "Check-Out", "Total Hrs", "Late Duration", "Early Duration", 
        "Overtime (hrs)", "Status", "Paid Hrs", "Unpaid Hrs", "Payable Fraction", "Source", "Remarks"
    ]
    writer.writerow(headers)
    
    def format_mins(m):
        if not m: return "00:00"
        h, rem = divmod(int(m), 60)
        return f"{h:02d}:{rem:02d}"

    for row in data:
        writer.writerow([
            row.date,
            row.employee_id,
            row.employee_name,
            row.shift_name,
            row.shift_start,
            row.shift_end,
            row.in_time,
            row.out_time,
            row.total_hours,
            format_mins(row.late_minutes),
            format_mins(row.early_out_minutes),
            row.overtime_hours,
            row.status,
            row.paid_hours,
            row.unpaid_hours,
            row.payable_day_fraction,
            row.source,
            row.remarks
        ])
        
    output.seek(0)
    
    filename = f"payroll_report_{start_date_str}_to_{end_date_str}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')), # BOM for Excel
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
