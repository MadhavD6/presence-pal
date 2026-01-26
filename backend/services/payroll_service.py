from datetime import date, datetime, timedelta, time
from typing import List, Optional
from sqlmodel import Session, select, func
from backend.models.user import User
from backend.models.audit import AuditLog
from backend.models.shift import Shift
from backend.models.payroll import PayrollConfig, DailySummary, PayrollRun, Payslip
from backend.services.attendance import calculate_daily_stats

# Defaults
DEFAULT_HOURLY_RATE = 20.0 # MVP default if config missing

def get_or_create_config(session: Session, user_id: int) -> PayrollConfig:
    config = session.exec(select(PayrollConfig).where(PayrollConfig.user_id == user_id)).first()
    if not config:
        config = PayrollConfig(user_id=user_id, base_hourly_rate=DEFAULT_HOURLY_RATE)
        session.add(config)
        session.commit()
        session.refresh(config)
    return config

def aggregate_daily_attendance(session: Session, user_id: int, target_date: date) -> DailySummary:
    """
    Calculates and stores DailySummary for a user/date.
    """
    # 1. Fetch Logs
    logs = session.exec(
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .where(AuditLog.timestamp >= datetime.combine(target_date, datetime.min.time()))
        .where(AuditLog.timestamp <= datetime.combine(target_date, datetime.max.time()))
    ).all()
    
    # 2. Fetch Shift
    user = session.get(User, user_id)
    shift = None
    if user.shift_id:
        shift = session.get(Shift, user.shift_id)
    if not shift:
         shift = Shift(name="General Shift", start_time=time(9,0), end_time=time(18,0), grace_period_mins=15)

    # 3. Calculate Stats
    # calculate_daily_stats returns dict
    stats = calculate_daily_stats(logs, shift=shift)
    
    # 4. Handle Holidays
    from backend.models.holiday import Holiday
    holiday_record = session.exec(select(Holiday).where(Holiday.date == target_date)).first()
    
    # Defaults
    final_status = stats['attendance_status']
    total_hours = stats['total_hours']
    is_late = stats['is_late']
    
    # If Holiday exists
    if holiday_record:
        # Override if Absent or if configured to always override
        # User Pref: "If holiday date + punches exist -> override to Holiday status (paid 8h)"
        # So essentially Holiday > Punches.
        final_status = "Holiday"
        total_hours = 8.0 # Paid 8h
        is_late = False
        # Note: If they worked, we might want to track it elsewhere, but for now we follow preference 'paid 8h'
    else:
        # 5. Handle Missed Punch Logic only if Not Holiday
        if final_status == "Present" and total_hours < 0.1: 
             if len(logs) % 2 != 0:
                 final_status = "MissedPunch"
                 total_hours = 0.0 # No pay for partial
    
    # 6. Create/Update Summary
    # Check if exists
    summary = session.exec(
        select(DailySummary)
        .where(DailySummary.user_id == user_id)
        .where(DailySummary.date == target_date)
    ).first()
    
    if not summary:
        summary = DailySummary(user_id=user_id, date=target_date)
    
    summary.first_in = datetime.strptime(stats['first_in'], "%I:%M %p") if stats['first_in'] else None
    summary.last_out = datetime.strptime(stats['last_out'], "%I:%M %p") if stats['last_out'] else None
    summary.total_hours = total_hours
    
    # Regular vs Overtime (Standard 8h)
    STD_HOURS = 8.0
    if total_hours > STD_HOURS:
        summary.regular_hours = STD_HOURS
        summary.overtime_hours = total_hours - STD_HOURS
    else:
        summary.regular_hours = total_hours
        summary.overtime_hours = 0.0
        
    summary.is_late = is_late
    summary.status = final_status
    
    session.add(summary)
    session.commit()
    session.refresh(summary)
    return summary

def generate_payroll_run(session: Session, start_date: date, end_date: date) -> PayrollRun:
    """
    Generates a full payroll run for all users.
    """
    # Create Run
    run = PayrollRun(start_date=start_date, end_date=end_date)
    session.add(run)
    session.commit()
    session.refresh(run)
    
    users = session.exec(select(User)).all()
    total_payout = 0.0
    
    for user in users:
        config = get_or_create_config(session, user.id)
        
        # Fetch summaries
        summaries = session.exec(
            select(DailySummary)
            .where(DailySummary.user_id == user.id)
            .where(DailySummary.date >= start_date)
            .where(DailySummary.date <= end_date)
        ).all()
        
        total_regular_hours = sum(s.regular_hours for s in summaries if s.status == "Present")
        total_ot_hours = sum(s.overtime_hours for s in summaries if s.status == "Present")
        late_days = sum(1 for s in summaries if s.is_late)
        
        # Calc
        base_pay = total_regular_hours * config.base_hourly_rate
        ot_pay = total_ot_hours * config.base_hourly_rate * config.overtime_multiplier
        
        # Deduction Logic
        # If specific amount set, use it (flat deduction per late occurrence)
        # Else default to 0.5x hourly rate penalty per occurrence
        if config.late_deduction_amount > 0:
            deduction = late_days * config.late_deduction_amount
        else:
            deduction = late_days * (config.base_hourly_rate * 0.5)
        
        gross = base_pay + ot_pay
        net = max(0, gross - deduction)
        
        # Check for Missed Punches or Errors
        warnings = []
        status = "Ready"
        
        missed_punches = [s.date for s in summaries if s.status == "MissedPunch"]

        if missed_punches:
            status = "Blocked"
            for d in missed_punches:
                warnings.append(f"Missed Punch on {d}")
                
        import json
        
        # Create Payslip
        slip = Payslip(
            run_id=run.id,
            user_id=user.id,
            gross_pay=round(gross, 2),
            total_deductions=round(deduction, 2),
            net_pay=round(net, 2),
            total_hours=round(total_regular_hours + total_ot_hours, 2),
            ot_hours=round(total_ot_hours, 2),
            late_days=late_days,
            status=status,
            warnings=json.dumps(warnings),
            details=f'{{"base_rate": {config.base_hourly_rate}, "missed_punches": {len(missed_punches)}}}'
        )
        session.add(slip)
        session.flush() # Force ID gen
        total_payout += net
        
    run.total_payout = round(total_payout, 2)
    session.add(run)
    session.commit()
    session.refresh(run) # Important to return ID
    
    return run
