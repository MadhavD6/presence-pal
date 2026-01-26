from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select, and_
from typing import List, Optional
from datetime import datetime, date, timedelta, time
from backend.core.database import get_session
from backend.core.security import get_current_active_user, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.models.user import User
from backend.models.audit import AuditLog
from backend.models.shift import Shift
from backend.models.site import Site
from backend.models.leave import Leave

router = APIRouter(prefix="/employee", tags=["employee"])

@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    # 1. Fetch User
    # In our system, username = employee_id
    user = session.exec(select(User).where(User.employee_id == form_data.username)).first()
    
    # 2. Verify
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect employee ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Create Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Returns:
    - User Profile (name, id, role)
    - Today's Punch Status (In/Out/Time)
    - Shift Info
    """
    today = date.today()
    now = datetime.now()
    
    # 1. Fetch Today's Logs
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)
    
    logs = session.exec(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .where(AuditLog.timestamp >= start_of_day)
        .where(AuditLog.timestamp <= end_of_day)
        .order_by(AuditLog.timestamp.desc()) # Newest first for "Recent Activity"
    ).all()
    
    # Process Logs for Recent Activity
    recent_punches = []
    for log in logs:
        # Filter only valid punches
        if log.event_type in ['in', 'out']:
            recent_punches.append({
                "type": "In" if log.event_type == 'in' else "Out",
                "time": log.timestamp.strftime("%I:%M %p")
            })

    # Sort logs asc for calculations
    logs_asc = sorted(logs, key=lambda x: x.timestamp)
    
    # 2. Determine Status & Stats
    status = "Absent"
    first_in = None
    last_out = None
    worked_hours_str = "0h 0m"
    is_late = False
    late_minutes = 0
    
    if logs_asc:
        # Find First In
        first_in_log = next((l for l in logs_asc if l.event_type == 'in'), None)
        if first_in_log:
            first_in_dt = first_in_log.timestamp
            first_in = first_in_dt.strftime("%I:%M %p")
            status = "Present"
            
            # Check Late Status (if shift exists)
            if current_user.shift_id:
                shift = session.get(Shift, current_user.shift_id)
                if shift:
                    # Combine today date with shift start time
                    shift_start_dt = datetime.combine(today, shift.start_time)
                    # 15 min grace period
                    grace_time = shift_start_dt + timedelta(minutes=15)
                    
                    if first_in_dt > grace_time:
                        is_late = True
                        diff = first_in_dt - shift_start_dt
                        late_minutes = int(diff.total_seconds() / 60)

        # Find Last Out (or check current status)
        last_log = logs_asc[-1]
        if last_log.event_type == 'in':
            status = "In"
        elif last_log.event_type == 'out':
            status = "Out"
            last_out = last_log.timestamp.strftime("%I:%M %p")
            
        # Calculate Worked Hours (Sum of pairs)
        total_seconds = 0
        in_time = None
        for log in logs_asc:
            if log.event_type == 'in':
                in_time = log.timestamp
            elif log.event_type == 'out' and in_time:
                total_seconds += (log.timestamp - in_time).total_seconds()
                in_time = None
        
        # If still in, add time until now
        if in_time:
            total_seconds += (datetime.now() - in_time).total_seconds()
            
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        worked_hours_str = f"{hours}h {minutes}m"

    # 3. Fetch Shift & Week Schedule
    # For now, generate a 7-day projection based on the assigned shift
    shifts = []
    if current_user.shift_id:
        shift = session.get(Shift, current_user.shift_id)
        if shift:
            # Generate for current week (Mon-Sun) or just next 7 days? 
            # Frontend shows "My Shift Schedule" mostly as upcoming cards.
            # Let's show Today + next 6 days.
            for i in range(7):
                d = today + timedelta(days=i)
                # Simple logic: Work all days except Sunday (WO)
                # You might want a Roster table later.
                is_wo = (d.weekday() == 6) # Sunday
                
                s_name = "WO" if is_wo else "General" 
                # If we have real shift name, use it. But usually "General" implies the standard 9-6.
                # If is_wo, override.
                
                shifts.append({
                    "day": d.strftime("%a"),
                    "date": d.isoformat(),
                    "shift_name": s_name,
                    "start": shift.start_time.strftime("%H:%M") if not is_wo else None,
                    "end": shift.end_time.strftime("%H:%M") if not is_wo else None
                })
    
    # 4. Fetch Site Info
    site_name = None
    if current_user.site_id:
        site = session.get(Site, current_user.site_id)
        if site:
            site_name = site.name
    
    return {
            "name": current_user.name,
            "id": current_user.id,
            "role": current_user.role,
            "employee_id": current_user.employee_id,
            "site_id": current_user.site_id,
            "site_name": site_name,
            "status": status,
            "first_in": first_in,
            "last_out": last_out,
            "worked_hours": worked_hours_str,
            "is_late": is_late,
            "late_minutes": late_minutes,
            "date": today.strftime("%a, %d %b"),
            "recent_punches": recent_punches,
        "shifts": shifts,
        "current_shift": "General Shift" # Placeholder or from Shift object
    }

@router.get("/timesheet")
async def get_my_timesheet(
    month: str = Query(..., description="YYYY-MM"), 
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Returns date-wise status for the requested month.
    """
    try:
        start_date = datetime.strptime(month, "%Y-%m").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
        
    # Calculate end date (first day of next month)
    if start_date.month == 12:
        next_month = start_date.replace(year=start_date.year + 1, month=1)
    else:
        next_month = start_date.replace(month=start_date.month + 1)
    
    end_date = next_month - timedelta(days=1)
    
    # Fetch all logs for the month
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    
    logs = session.exec(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .where(AuditLog.timestamp >= start_dt)
        .where(AuditLog.timestamp <= end_dt)
        .order_by(AuditLog.timestamp.asc())
    ).all()
    
    # Group by Date
    daily_map = {}
    
    for log in logs:
        d_str = log.timestamp.date().isoformat()
        if d_str not in daily_map:
            daily_map[d_str] = {"in": [], "out": []}
        
        daily_map[d_str][log.event_type].append(log.timestamp)
        
    # Transform to list
    results = []
    
    # Iterate through all days in month to fill gaps
    curr = start_date
    while curr <= end_date:
        d_str = curr.isoformat()
        
        status = "Absent" # Default
        if curr.weekday() >= 5: # Sat/Sun
             status = "Weekend"
             
        day_logs = daily_map.get(d_str)
        
        entry = {
            "date": d_str,
            "status": status,
            "first_in": None,
            "last_out": None,
            "total_hours": 0
        }
        
        if day_logs:
            # We have punches
            in_times = sorted(day_logs['in'])
            out_times = sorted(day_logs['out'])
            
            if in_times:
                entry['first_in'] = in_times[0].strftime("%H:%M")
                entry['status'] = "Present" # Basic logic
                
            if out_times:
                entry['last_out'] = out_times[-1].strftime("%H:%M")
                
            # Basic Hours Calc (very rough, just for UI viz)
            if in_times and out_times:
                # Pair simplistic
                 start = in_times[0]
                 end = out_times[-1]
                 if end > start:
                     diff = (end - start).total_seconds() / 3600
                     entry['total_hours'] = round(diff, 1)

        results.append(entry)
        curr += timedelta(days=1)
        
    return results

@router.get("/me/timesheet/day")
async def get_daily_timesheet(
    date_str: str = Query(..., alias="date", description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Detailed timecard for a specific day.
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # 1. Fetch Logs for this day
    start_dt = datetime.combine(target_date, time.min)
    end_dt = datetime.combine(target_date, time.max)
    
    logs = session.exec(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .where(AuditLog.timestamp >= start_dt)
        .where(AuditLog.timestamp <= end_dt)
        .order_by(AuditLog.timestamp.asc())
    ).all()
    
    # 2. Process Statistics
    status = "Absent"
    sub_status = "-"
    first_in = "-"
    last_out = "-"
    worked_hours_str = "0h 0m"
    payable_hours = "-"
    overtime_str = "-"
    breaktime_str = "-"
    punches = []
    
    # Check Shift
    shift_name = "-"
    shift_start = None
    shift_end = None
    if current_user.shift_id:
        shift = session.get(Shift, current_user.shift_id)
        if shift:
            # Handle Sunday logic or Roster
            is_wo = (target_date.weekday() == 6)
            shift_name = "WO" if is_wo else "General" # Simplify
            if not is_wo:
                shift_start = shift.start_time
                shift_end = shift.end_time
    
    if logs:
        # Determine Status
        status = "Present"
        
        # Format Punches
        for log in logs:
            if log.event_type in ['in', 'out']:
                punches.append({
                    "type": "In" if log.event_type == 'in' else "Out",
                    "time": log.timestamp.strftime("%I:%M %p"),
                    "shift": shift_name
                })
        
        # Calculate Times
        valid_ins = [l.timestamp for l in logs if l.event_type == 'in']
        valid_outs = [l.timestamp for l in logs if l.event_type == 'out']
        
        if valid_ins:
            first_in = valid_ins[0].strftime("%I:%M %p")
            
            # Late Check
            if shift_start:
                 # Reconstruct shift datetime
                 s_start = datetime.combine(target_date, shift_start)
                 grace = s_start + timedelta(minutes=15)
                 if valid_ins[0] > grace:
                     sub_status = "Late Entry"
        
        if valid_outs:
            last_out = valid_outs[-1].strftime("%I:%M %p")
            
            # Early Exit Check (simplistic)
            if shift_end:
                s_end = datetime.combine(target_date, shift_end)
                if valid_outs[-1] < s_end:
                     # Only if not late? or append
                     sub_status = "Early Exit" if sub_status == "-" else sub_status + ", Early Exit"

        # Calculate Hours
        total_seconds = 0
        in_time = None
        for log in logs:
            if log.event_type == 'in':
                in_time = log.timestamp
            elif log.event_type == 'out' and in_time:
                total_seconds += (log.timestamp - in_time).total_seconds()
                in_time = None
        
        # If today and still in
        if in_time and target_date == date.today():
             total_seconds += (datetime.now() - in_time).total_seconds()
             status = "In"
        elif in_time:
            status = "Missed Out" # Forgot to punch out yesterday
             
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        worked_hours_str = f"{hours}h {minutes}m"
        payable_hours = worked_hours_str # Simplify for now
        
        # Overtime (if > 9 hours)
        if total_seconds > (9 * 3600):
            ot_seconds = total_seconds - (9 * 3600)
            ot_h = int(ot_seconds // 3600)
            ot_m = int((ot_seconds % 3600) // 60)
            overtime_str = f"{ot_h}h {ot_m}m"

    return {
        "name": current_user.name,
        "id": current_user.employee_id,
        "status": status,
        "inTime": first_in,
        "outTime": last_out,
        "workedHours": worked_hours_str,
        "payableHours": payable_hours,
        "shift": shift_name,
        "overtime": overtime_str,
        "breaktime": breaktime_str,
        "subStatus": sub_status,
        "approvalStatus": "Approved", # Placeholder
        "punches": punches
    }
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from backend.models.leave import Leave

# ... existing code ...

@router.post("/me/leaves")
async def apply_leave(
    leave_type: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    file_path = None
    if file:
        # Save file logic (mock for now or save to disk)
        # For MVP, we just store the filename
        file_path = f"uploads/{file.filename}"
        
    leave = Leave(
        user_id=current_user.id,
        leave_type=leave_type,
        start_date=s_date,
        end_date=e_date,
        reason=reason,
        attachment=file_path,
        status="Pending"
    )
    session.add(leave)
    session.commit()
    session.refresh(leave)
    return {"status": "submitted", "id": leave.id}

@router.get("/me/leaves")
async def get_my_leaves(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    leaves = session.exec(
        select(Leave)
        .where(Leave.user_id == current_user.id)
        .order_by(Leave.start_date.desc())
    ).all()
    return leaves
