from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from backend.core.database import get_session
from backend.core.security import get_current_active_user, get_current_admin_user
from backend.models.user import User
from backend.models.payroll import Payslip, PayrollRun
from backend.services.payroll_service import aggregate_daily_attendance, generate_payroll_run

router = APIRouter(prefix="/payroll", tags=["payroll"])

@router.post("/aggregate", response_model=PayrollRun)
def trigger_payroll_run(
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """
    Admin only: Aggregate daily summaries and generate a payroll run.
    """
    # 1. First, refresh daily summaries for all users in range
    # This might be slow for many users; normally background task.
    users = session.exec(select(User)).all()
    delta = end_date - start_date
    
    for user in users:
        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            # Re-calculate summary
            aggregate_daily_attendance(session, user.id, day)
            
    # 2. Generate Run
    run = generate_payroll_run(session, start_date, end_date)
    return run

@router.get("/slips/me", response_model=List[Payslip])
def get_my_payslips(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Get all payslips for current user.
    """
    slips = session.exec(
        select(Payslip)
        .where(Payslip.user_id == current_user.id)
        .order_by(Payslip.id.desc())
    ).all()
    return slips

@router.get("/slips/me/{run_id}", response_model=Payslip)
def get_my_payslip_detail(
    run_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    slip = session.exec(
        select(Payslip)
        .where(Payslip.user_id == current_user.id)
        .where(Payslip.run_id == run_id)
    ).first()
    
    if not slip:
        raise HTTPException(status_code=404, detail="Payslip not found")
        
    return slip
