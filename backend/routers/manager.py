from datetime import date, datetime, time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func, col, and_
from pydantic import BaseModel
from backend.core.database import get_session
from backend.core.security import get_current_manager_user, get_current_kiosk, get_optional_current_user
from backend.models.user import User
from backend.models.audit import AuditLog
from backend.models.leave import Leave
from backend.models.shift import EmployeeShift, Shift

from backend.models.kiosk import Kiosk

router = APIRouter()

@router.get("/manager/kiosks")
def get_kiosks(
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    kiosks = session.exec(select(Kiosk)).all()
    # Mask secrets? Maybe no need to send hash.
    return kiosks

class KioskUpdate(BaseModel):
    device_id: Optional[str] = None
    location: Optional[str] = None
    building: Optional[str] = None
    site_id: Optional[int] = None

@router.put("/manager/kiosks/{kiosk_id}")
def update_kiosk(
    kiosk_id: int,
    data: KioskUpdate,
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk) # Any authenticated kiosk can update
):
    kiosk = session.get(Kiosk, kiosk_id)
    if not kiosk:
        raise HTTPException(status_code=404, detail="Kiosk not found")
        
    if data.device_id:
        # Check uniqueness if changing ID
        if data.device_id != kiosk.device_id:
            existing = session.exec(select(Kiosk).where(Kiosk.device_id == data.device_id)).first()
            if existing:
                 raise HTTPException(status_code=400, detail="Device ID already exists")
            kiosk.device_id = data.device_id
            
    if data.location:
        kiosk.location = data.location
    if data.building:
        kiosk.building = data.building
    if data.site_id is not None:
        # Verify site exists
        site = session.get(Site, data.site_id)
        if not site:
             raise HTTPException(status_code=404, detail="Site not found")
        kiosk.site_id = data.site_id
        
    session.add(kiosk)
    session.commit()
    session.refresh(kiosk)
    return {"status": "success", "kiosk": kiosk}


from backend.models.site import Site

class AssignSiteRequest(BaseModel):
    user_ids: List[int]
    site_id: Optional[int]

@router.get("/manager/employees")
def get_employees(
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
def get_sites(
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk)
):
    return session.exec(select(Site).where(Site.is_active == True)).all()

@router.post("/manager/employees/assign-site")
def assign_site(
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
    password: Optional[str] = None  # No default password - must be set explicitly or left empty

@router.post("/manager/employees")
def create_employee(
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
def update_employee(
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
def get_manager_stats(
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
def get_timesheet(
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
    
    # Pre-fetch Holidays in range
    from backend.models.holiday import Holiday
    holidays_in_range = session.exec(
        select(Holiday)
        .where(Holiday.date >= start_date)
        .where(Holiday.date <= end_date)
    ).all()
    holiday_set = {h.date for h in holidays_in_range}
    holiday_name_map = {h.date: h.name for h in holidays_in_range}

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
            applicable_employee_shift = None # EmployeeShift record
            for rec in history:
                if rec.start_date <= curr_d and (rec.end_date is None or rec.end_date >= curr_d):
                    applicable_shift = all_shifts.get(rec.shift_id, default_shift)
                    applicable_employee_shift = rec
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
            
            # Check weekday for WO (Dynamic from EmployeeShift or fallback to Sunday)
            weekly_off_days = [6] # Default Sunday
            if applicable_employee_shift and applicable_employee_shift.weekly_offs:
                try:
                    weekly_off_days = [int(x.strip()) for x in applicable_employee_shift.weekly_offs.split(",")]
                except:
                    pass
                    
            if curr_d.weekday() in weekly_off_days:
                status = "WO"
                current_shift_code = "WO"
                current_shift_tooltip = "Weekly Off"
            
            # Check for Holiday
            if curr_d in holiday_set:
                status = "HD"
                current_shift_code = "HD"
                current_shift_tooltip = f"Holiday: {holiday_name_map.get(curr_d, '')}"
            
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
            "dept": user.department or "General",
            "avatar": "".join([n[0] for n in user.name.split(" ")[:2]]),
            "stats": { "payable": worked_str, "worked": worked_str }, # Payable logic can be complex
            "days": days_status
        })

    return timesheet_data

@router.get("/manager/daily-log")
def get_daily_log(
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
                end_time = last_event.timestamp if last_event.event_type == 'out' else datetime.now()
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
def get_pending_leaves(
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
def approve_leave(
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
def get_pending_corrections(
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
def approve_correction(
    correction_id: int,
    action: str, # "approve" or "reject"
    session: Session = Depends(get_session),
    _auth: Any = Depends(get_current_kiosk),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    correction = session.get(AttendanceCorrection, correction_id)
    if not correction:
        raise HTTPException(status_code=404, detail="Correction not found")
        
    # Set resolver for audit trail (if user is logged in via bearer token)
    if current_user:
        correction.resolver_id = current_user.id
        
    if action == "approve":
        correction.status = "Approved"
        correction.resolved_at = datetime.now()
        
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
        
        # Conflict Handling: Find and mark OLD logs for this day as overridden
        start_of_day = datetime.combine(correction.original_date, time.min)
        end_of_day = datetime.combine(correction.original_date, time.max)
        
        # We need to query logs for this user on this day
        # Filter for existing valid punches (in/out)
        existing_logs = session.exec(
            select(AuditLog)
            .where(AuditLog.user_id == correction.user_id)
            .where(AuditLog.timestamp >= start_of_day)
            .where(AuditLog.timestamp <= end_of_day)
            .where(AuditLog.match_type != "overridden") # Avoid double processing
        ).all()
        
        for log in existing_logs:
            # Mark them as overridden so strict calculation ignores them
            # Ideally we preserve them for audit but exclude from stats
            # Update metadata to track who/why (BEFORE changing match_type)
            if not log.metadata_info: log.metadata_info = {}
            log.metadata_info["original_match_type"] = log.match_type # Save before overwrite
            log.metadata_info["overridden_by_correction"] = correction.id
            log.match_type = "overridden"
            session.add(log)
            
        # Now insert the NEW corrected punches
        corrected_in_ts = correction.corrected_in
        corrected_out_ts = correction.corrected_out
        
        # Handle Cross-Day (Night Shift) Corrections:
        # If corrected_out time is BEFORE corrected_in time (e.g., In=22:00, Out=06:00),
        # it means out is on the NEXT day.
        if corrected_in_ts and corrected_out_ts:
            if corrected_out_ts.time() < corrected_in_ts.time():
                # Out is on the next calendar day
                corrected_out_ts = corrected_out_ts + timedelta(days=1)
        
        if corrected_in_ts:
            log_in = AuditLog(
                user_id=correction.user_id,
                timestamp=corrected_in_ts,
                event_type="in",
                confidence=1.0,
                match_type="manual_correction", 
                metadata_info={"verification_method": "manual_correction", "correction_id": correction.id}
            )
            session.add(log_in)
            
        if corrected_out_ts:
            log_out = AuditLog(
                user_id=correction.user_id,
                timestamp=corrected_out_ts,
                event_type="out",
                confidence=1.0,
                match_type="manual_correction",
                metadata_info={"verification_method": "manual_correction", "correction_id": correction.id}
            )
            session.add(log_out)
            
    elif action == "reject":
        correction.status = "Rejected"
        correction.resolved_at = datetime.now()
    else:
         raise HTTPException(status_code=400, detail="Invalid action")
         
    session.add(correction)
    session.commit()
    return {"status": "success"}

@router.get("/manager/approvals/history")
def get_approval_history(
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
    # Enhanced Fields
    warnings: str = "-"
    avg_confidence: float = 0.0
    correction_note: str = "-"
    is_manual: bool = False
    pairing_status: str = "Ok"

@router.get("/manager/reports/detailed", response_model=List[DetailedReportRow])
def get_detailed_report(
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
            
    # Fetch logs (Extend by 1 day to fetch overnight OUT punches)
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date + timedelta(days=1), time.max)
    logs = session.exec(
        select(AuditLog).where(
            and_(
                AuditLog.timestamp >= start_dt,
                AuditLog.timestamp <= end_dt
            )
        ).order_by(AuditLog.timestamp) # Ensure chronological order
    ).all()
    
    # Track consumed logs to prevent double-counting across days
    processed_log_ids = set()
    
    # Organize logs by user for easier access
    usage_map = {} # user_id -> list of logs
    for log in logs:
        if log.user_id not in usage_map:
            usage_map[log.user_id] = []
        usage_map[log.user_id].append(log)
        
    report = []
    
    curr = start_date
    while curr <= end_date:
        for user in users:
            # 1. Determine Shift & Weekly Off
            from backend.services.attendance import calculate_daily_stats, get_shift_for_date
            user_shift, is_weekly_off = get_shift_for_date(session, user.id, curr)
            
            # 2. Identify candidate logs for this "Shift Day"
            # Default Window: 00:00 to 23:59:59 of current day
            w_start = datetime.combine(curr, time.min)
            w_end = datetime.combine(curr, time.max)
            
            # Smart Window for Night Shifts
            if user_shift and user_shift.crosses_midnight:
                # Extend window to next day noon (covering the overnight shift)
                # But start time should be close to shift start (e.g. shift start - 4h)
                # For simplicity/robustness: Just look at [curr 00:00 -> curr+1 12:00]
                # And relies on 'processed_log_ids' to ignore logs claimed by previous day.
                w_end = datetime.combine(curr + timedelta(days=1), time(12, 0)) 
            
            # Fetch all available logs for this user in this window
            candidates = []
            if user.id in usage_map:
                for log in usage_map[user.id]:
                    if log.id in processed_log_ids:
                        continue # Skip already consumed punch (e.g. OUT from yesterday)
                    if w_start <= log.timestamp <= w_end:
                         candidates.append(log)
            
            # 3. Calculate Stats
            stats = calculate_daily_stats(candidates, user_shift)
            
            # 4. Mark "Used" logs as processed
            # Which logs did calculate_daily_stats ACTUALLY use?
            # It uses ALL of them to determine First-In/Last-Out.
            # But wait, if we passed [Jan 1 20:00, Jan 2 05:00, Jan 2 09:00]
            # It might use Jan 2 09:00 as "Last Out" for Jan 1 shift? YES. Risk.
            # FIX: verification logic.
            # If shift is 20:00-05:00.
            # We should filtering candidates: ONLY logs that "belong" to this shift.
            # Heuristic: A log belongs to this shift if it is within (Start - 4h) and (End + 6h).
            
            refined_candidates = []
            if user_shift:
                # Construct absolute shift times
                s_start_dt = datetime.combine(curr, user_shift.start_time)
                s_end_dt = datetime.combine(curr, user_shift.end_time)
                if user_shift.crosses_midnight:
                    s_end_dt += timedelta(days=1)
                
                # Tolerances: 
                # Earliest IN: 4 hours before start?
                # Latest OUT: 6 hours after end? (or until next shift start)
                # Let's say: [Start - 4h, End + 8h]
                lower_bound = s_start_dt - timedelta(hours=4)
                upper_bound = s_end_dt + timedelta(hours=8)
                
                for cand in candidates:
                    if lower_bound <= cand.timestamp <= upper_bound:
                        refined_candidates.append(cand)
                
                # Re-calculate with refined
                if refined_candidates:
                    stats = calculate_daily_stats(refined_candidates, user_shift)
                    # Mark refined candidates as processed
                    for rc in refined_candidates:
                        processed_log_ids.add(rc.id)
            else:
                 # General Shift / No Shift -> Use whatever falls in the day (Standard behavior)
                 # Mark all day candidates as processed
                 for c in candidates:
                     processed_log_ids.add(c.id)
            
            # Define day_logs for downstream analytics (Avg Confidence, Manual check)
            day_logs = refined_candidates if refined_candidates else candidates
            
            final_status = stats["attendance_status"]
            remarks = "-"
            
            stats["payable_fraction"] = 0.0 # Default
            
            if (user.id, curr) in leave_map:
                l = leave_map[(user.id, curr)]
                final_status = "Leave" # Or specific type
                remarks = l.leave_type
                stats["payable_fraction"] = 1.0 # Assume paid leave for now
                stats["payable_hours"] = 8.0 
                
            elif is_weekly_off:
                final_status = "Week Off"
                remarks = "Weekly Off"
                if stats["total_hours"] > 0:
                     final_status = "Worked on WO" # Special status?
                     # Add extra pay logic here if needed
                stats["payable_fraction"] = 1.0 # WO is usually paid salary
            
            elif final_status == "Present":
                 stats["payable_fraction"] = 1.0

            # Calculate Overtime (Simple logic: Worked > Shift Duration)
            shift_duration = 0.0
            if user_shift:
                # Naive duration calc
                dummy_date = date(2000, 1, 1)
                start_dt = datetime.combine(dummy_date, user_shift.start_time)
                end_dt = datetime.combine(dummy_date, user_shift.end_time)
                if user_shift.crosses_midnight:
                    end_dt += timedelta(days=1)
                shift_duration = (end_dt - start_dt).total_seconds() / 3600.0
            
            if not shift_duration: shift_duration = 9.0 # Fallback

            unpaid = 0.0
            if final_status == "Absent":
                 unpaid = shift_duration
            
            # Update stats with refined calculations
            ot_hours = max(0, stats["total_hours"] - shift_duration) if final_status == "Present" else 0.0
            
            # Match logic and warnings
            warnings = []
            pairing_status = "Ok"
            avg_conf = 0.0
            is_man = False
            c_note = "-"
            
            if final_status == "Present":
                 # Check for single punch
                 if stats["first_in"] == stats["last_out"] or not stats["last_out"]:
                     warnings.append("Single Punch (In only)")
                     pairing_status = "Unpaired"
                 
                 # Calc Avg Confidence
                 if day_logs:
                     total_conf = sum([l.confidence for l in day_logs])
                     avg_conf = round(total_conf / len(day_logs), 2)
                     
                     # Check Manual
                     if any(l.match_type == "manual_correction" for l in day_logs):
                         is_man = True
                         c_note = "Manual Correction Applied"
                         
            elif final_status == "Absent" and not is_weekly_off and not (user.id, curr) in leave_map:
                 warnings.append("Missing Attendance")
                 pairing_status = "Missing"

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
                source="Manual" if is_man else "Face",
                remarks=remarks,
                warnings="; ".join(warnings) if warnings else "-",
                avg_confidence=avg_conf,
                correction_note=c_note,
                is_manual=is_man,
                pairing_status=pairing_status
            ))
        curr += timedelta(days=1)
        
    return report

from fastapi.responses import StreamingResponse
import csv
import io

@router.get("/manager/reports/export")
def export_detailed_report(
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
        "Overtime (hrs)", "Status", "Paid Hrs", "Unpaid Hrs", "Payable Fraction", "Source", "Remarks",
        "Warnings", "Pairing Status", "Avg Confidence", "Correction Notes"
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
            row.remarks,
            row.warnings,
            row.pairing_status,
            row.avg_confidence,
            row.correction_note
        ])
        
    output.seek(0)
    
    filename = f"payroll_report_{start_date_str}_to_{end_date_str}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')), # BOM for Excel
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
