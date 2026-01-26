from datetime import date, timedelta, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from backend.core.database import get_session
from backend.core.security import get_current_manager_user # Ensuring role check
from backend.models.user import User
from backend.models.payroll import Payslip, PayrollRun, PayrollConfig
from backend.services.payroll_service import aggregate_daily_attendance, generate_payroll_run, get_or_create_config
from pydantic import BaseModel
import json

router = APIRouter(prefix="/manager/payroll", tags=["manager-payroll"])

class PayrollConfigUpdate(BaseModel):
    base_hourly_rate: float
    currency: str = "USD"
    overtime_multiplier: float = 1.5
    late_deduction_amount: float = 0.0

@router.get("/config/{user_id}", response_model=PayrollConfig)
async def get_user_payroll_config(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_manager_user)
):
    return get_or_create_config(session, user_id)

@router.put("/config/{user_id}", response_model=PayrollConfig)
async def update_user_payroll_config(
    user_id: int,
    data: PayrollConfigUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_manager_user)
):
    config = get_or_create_config(session, user_id)
    config.base_hourly_rate = data.base_hourly_rate
    config.currency = data.currency
    config.overtime_multiplier = data.overtime_multiplier
    config.late_deduction_amount = data.late_deduction_amount
    
    session.add(config)
    session.commit()
    session.refresh(config)
    return config

@router.post("/generate", response_model=PayrollRun)
async def generate_payroll(
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_manager_user),
    session: Session = Depends(get_session)
):
    """
    Manager: Aggregate daily summaries and generate/preview a payroll run.
    """
    # 1. Refresh Aggregations (Batch)
    users = session.exec(select(User)).all()
    delta = end_date - start_date
    
    # Optimization: Only process needed? For now, brute force for safety.
    for user in users:
        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            aggregate_daily_attendance(session, user.id, day)
            
    # 2. Generate Run
    run = generate_payroll_run(session, start_date, end_date)
    return run

@router.get("/runs", response_model=List[PayrollRun])
async def list_payroll_runs(
    current_user: User = Depends(get_current_manager_user),
    session: Session = Depends(get_session)
):
    return session.exec(select(PayrollRun).order_by(PayrollRun.id.desc())).all()

@router.get("/run/{run_id}")
async def get_payroll_run_detail(
    run_id: int,
    current_user: User = Depends(get_current_manager_user),
    session: Session = Depends(get_session)
):
    run = session.get(PayrollRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    # Get Slips with User Info
    # Ideally join, but simple loop fine for MVP
    slips = session.exec(select(Payslip).where(Payslip.run_id == run_id)).all()
    
    slips_data = []
    for s in slips:
        u = session.get(User, s.user_id)
        slips_data.append({
            **s.dict(),
            "user_name": u.name if u else "Unknown",
            "employee_id": u.employee_id if u else "Unknown"
        })
        
    return {
        "run": run,
        "slips": slips_data
    }

@router.post("/run/{run_id}/finalize")
async def finalize_payroll_run(
    run_id: int,
    current_user: User = Depends(get_current_manager_user),
    session: Session = Depends(get_session)
):
    run = session.get(PayrollRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    if run.is_finalized:
        return {"status": "already_finalized"}
        
    # Validation
    slips = session.exec(select(Payslip).where(Payslip.run_id == run_id)).all()
    blocked = [s for s in slips if s.status == "Blocked"]
    
    if blocked:
        # Collect errors
        msg = f"Cannot finalize. {len(blocked)} payslips are blocked."
        raise HTTPException(status_code=400, detail=msg)
        
    run.is_finalized = True
    session.add(run)
    session.commit()
    
    return {"status": "success", "run_id": run.id}
