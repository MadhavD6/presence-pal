from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date, time
from sqlmodel import Session, select, and_
from backend.models.audit import AuditLog
from backend.models.shift import Shift, EmployeeShift
from backend.models.user import User

def get_shift_for_date(session: Session, user_id: int, target_date: date) -> tuple[Optional[Shift], bool]:
    """
    Determines the effective shift for a user on a specific date.
    Returns (Shift, is_weekly_off).
    """
    # 1. Check EmployeeShift (Roster)
    # Find assignment active on this date
    assignment = session.exec(
        select(EmployeeShift)
        .where(EmployeeShift.user_id == user_id)
        .where(EmployeeShift.start_date <= target_date)
        .where(
            (EmployeeShift.end_date == None) | (EmployeeShift.end_date >= target_date)
        )
        .order_by(EmployeeShift.start_date.desc())
    ).first()
    
    current_shift = None
    is_off = False
    
    if assignment:
        current_shift = session.get(Shift, assignment.shift_id)
        # Check weekly offs
        offs = [int(x) for x in assignment.weekly_offs.split(",") if x.strip()]
        if target_date.weekday() in offs:
            is_off = True
    else:
        # 2. Fallback to User's default shift
        user = session.get(User, user_id)
        if user and user.shift_id:
            current_shift = session.get(Shift, user.shift_id)
            # Default fallback: Sunday (6) is off if no roster
            if target_date.weekday() == 6:
                is_off = True
    
    # 3. Absolute Fallback
    if not current_shift:
        current_shift = Shift(name="General Shift", start_time=time(9,0), end_time=time(18,0), grace_period_mins=15)
        if target_date.weekday() == 6:
            is_off = True
            
    return current_shift, is_off

def calculate_daily_stats(logs: List[AuditLog], shift: Optional[Shift] = None) -> Dict[str, Any]:
    """
    Robustly calculate worked hours, first in, last out, and status from logs.
    Handles missing punches and respects event_type if available.
    """
    if not logs:
        return {
            "first_in": None,
            "last_out": None,
            "status": "Absent", 
            "attendance_status": "Absent",
            "worked_hours": "0h 0m",
            "punches": [],
            "is_late": False,
            "late_minutes": 0,
            "early_out_minutes": 0,
            "overtime_hours": 0.0,
            "payable_hours": 0.0,
            "payable_fraction": 0.0,
            "shift_name": shift.name if shift else "General Shift",
            "shift_start": shift.start_time.strftime("%I:%M %p") if shift else "09:00 AM",
            "shift_end": shift.end_time.strftime("%I:%M %p") if shift else "06:00 PM",
            "total_hours": 0.0
        }

    # Sort logs just in case
    sorted_logs = sorted(logs, key=lambda x: x.timestamp)
    
    first_in = sorted_logs[0].timestamp
    last_out = sorted_logs[-1].timestamp
    
    punches = []
    
    total_seconds = 0
    current_in_time = None
    
    for log in sorted_logs:
        p_type = log.event_type.capitalize() if log.event_type in ["in", "out"] else "Unknown"
        
        if p_type == "Unknown":
             pass 

        punches.append({
            "id": log.id,
            "time": log.timestamp.strftime("%I:%M %p"),
            "type": p_type,
            "timestamp": log.timestamp
        })

        if log.event_type == "in":
            if current_in_time is None:
                current_in_time = log.timestamp
            else:
                pass 
        elif log.event_type == "out":
            if current_in_time:
                delta = log.timestamp - current_in_time
                total_seconds += delta.total_seconds()
                current_in_time = None
            else:
                pass
    
    # Formatting
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(int(remainder), 60)
    
    if hours == 0 and minutes == 0 and seconds > 0:
        worked_str = f"{seconds}s"
    else:
        worked_str = f"{hours}h {minutes}m"
    
    # Status
    # If total_seconds > 0 or we have punches -> Present
    status = "Present" if total_seconds > 0 or len(sorted_logs) > 0 else "Absent"
    
    # Check if currently strictly IN (for Today status)
    current_status = "In" if current_in_time is not None else "Out"


    # Late Check & Early Out & Overtime
    is_late = False
    late_minutes = 0
    early_out_minutes = 0
    overtime_hours = 0.0
    payable_hours = total_seconds / 3600.0
    payable_fraction = 1.0 if status == "Present" else 0.0
    
    if shift and shift.name != "General Shift" and first_in and status == "Present":
        shift_start_dt = datetime.combine(first_in.date(), shift.start_time)
        shift_end_dt = datetime.combine(first_in.date(), shift.end_time)
        
        # Handle Midnight Crossover
        if shift.crosses_midnight:
             # End time is the NEXT day
             shift_end_dt = shift_end_dt + timedelta(days=1)
             
             # Edge Case: What if I punched in AFTER midnight (e.g. 1 AM for a 10 PM shift)?
             # Then first_in.date() is already Day+1.
             # We need to rely on the "Working Day".
             # For simpler MVP: We assume 'first_in' is 'close' to start time.
             # Better: Use the date passed in context? 
             # For now, 'late check' works if we compare strict times properly.
             
             # If first_in is between 00:00 and EndTime -> It belongs to Previous Day's shift?
             # This complexity is handled by HOW we query logs (the input `logs` list).
             # Assuming `logs` passed to this function are correct for the "Shift Day", we assume start_date is `first_in` roughly.
             # But if I come at 1 AM, `first_in.date()` is Day 2. `shift_start` becomes Day 2 10PM. Late = -21 hours. BAD.
             
             # FIX: We should use the EARLIEST log timestamp or a reference date if available.
             # Since 'calculate_daily_stats' doesn't take 'reference_date' arg, we infer.
             # Standard: If first_in.time < start_time AND crosses_midnight -> We are in the "Next Day" part.
             if first_in.time() < shift.start_time and first_in.time() < shift.end_time:
                 # Shift started yesterday
                 shift_start_dt = shift_start_dt - timedelta(days=1)
                 shift_end_dt = shift_end_dt - timedelta(days=1)
                 # Wait, if I am at 1 AM, shift end is 6 AM TODAY. start was 10 PM YESTERDAY.
                 # shift_end_dt calculation remains: shift_start + duration.
                 # Let's reset purely based on shift start
                 pass

        grace_limit = shift_start_dt + timedelta(minutes=shift.grace_period_mins)
        
        # 1. Late Check
        if first_in > grace_limit:
            is_late = True
            diff = first_in - shift_start_dt 
            late_minutes = int(diff.total_seconds() / 60)
            late_minutes = max(0, late_minutes)

        # 2. Early Out Check: Only if they are NOT currently IN (i.e. they signed out)
        if current_status != "In" and last_out < shift_end_dt:
            diff_early = shift_end_dt - last_out
            early_out_minutes = int(diff_early.total_seconds() / 60)
            early_out_minutes = max(0, early_out_minutes)
            
    # 3. Overtime
    # Assume 9 hours is standard shift duration or calculate from shift
    shift_duration_hours = 9.0 
    if shift:
        d1 = datetime.combine(date.today(), shift.start_time)
        d2 = datetime.combine(date.today(), shift.end_time)
        if shift.crosses_midnight:
            d2 = d2 + timedelta(days=1)
        shift_duration_hours = (d2 - d1).total_seconds() / 3600.0
        
    worked_h = total_seconds / 3600.0
    if worked_h > shift_duration_hours:
        overtime_hours = worked_h - shift_duration_hours

    # Payable logic (Basic for MVP)
    # If worked < 4 hours -> 0.5?
    # For now, let's stick to Present = 1.0
    if status == "Present" and worked_h < 4.5:
        payable_fraction = 0.5

    shift_end_label = shift.end_time.strftime("%I:%M %p") if shift else "06:00 PM"
    if shift and shift.crosses_midnight:
        shift_end_label += " (+1)"

    return {
        "first_in": first_in.strftime("%I:%M %p"),
        "last_out": last_out.strftime("%I:%M %p"),
        "status": current_status, # "In" or "Out"
        "attendance_status": status, # "Present", "Absent"
        "worked_hours": worked_str,
        "classification": status, # "Present", "Absent" - kept for consistency, same as attendance_status
        "punches": punches,
        "is_late": is_late,
        "late_minutes": late_minutes,
        "early_out_minutes": early_out_minutes,
        "overtime_hours": round(overtime_hours, 2),
        "payable_hours": round(payable_hours, 2),
        "payable_fraction": payable_fraction,
        "shift_name": shift.name if shift else "General Shift",
        "shift_start": shift.start_time.strftime("%I:%M %p") if shift else "09:00 AM",
        "shift_end": shift_end_label if shift else "06:00 PM",
        "total_hours": total_seconds / 3600.0
    }
