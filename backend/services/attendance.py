from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from backend.models.audit import AuditLog
from backend.models.shift import Shift

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
        grace_limit = shift_start_dt + timedelta(minutes=shift.grace_period_mins)
        
        # 1. Late Check
        if first_in > grace_limit:
            is_late = True
            diff = first_in - shift_start_dt 
            late_minutes = int(diff.total_seconds() / 60)
            late_minutes = max(0, late_minutes)

        # 2. Early Out Check
        if last_out < shift_end_dt:
            diff_early = shift_end_dt - last_out
            early_out_minutes = int(diff_early.total_seconds() / 60)
            early_out_minutes = max(0, early_out_minutes)
            
    # 3. Overtime
    # Assume 9 hours is standard shift duration or calculate from shift
    shift_duration_hours = 9.0 
    if shift:
        # naive diff
        d1 = timedelta(hours=shift.start_time.hour, minutes=shift.start_time.minute)
        d2 = timedelta(hours=shift.end_time.hour, minutes=shift.end_time.minute)
        shift_duration_hours = (d2 - d1).total_seconds() / 3600.0
        
    worked_h = total_seconds / 3600.0
    if worked_h > shift_duration_hours:
        overtime_hours = worked_h - shift_duration_hours

    # Payable logic (Basic for MVP)
    # If worked < 4 hours -> 0.5?
    # For now, let's stick to Present = 1.0
    if status == "Present" and worked_h < 4.5:
        payable_fraction = 0.5

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
        "shift_end": shift.end_time.strftime("%I:%M %p") if shift else "06:00 PM",
        "total_hours": total_seconds / 3600.0
    }
