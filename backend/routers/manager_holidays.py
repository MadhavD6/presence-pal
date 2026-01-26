from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from backend.core.database import get_session
from backend.core.security import get_current_manager_user
from backend.models.user import User
from backend.models.holiday import Holiday
from backend.services.payroll_service import aggregate_daily_attendance

router = APIRouter(prefix="/manager/holidays", tags=["manager-holidays"])

@router.get("/", response_model=List[Holiday])
async def get_holidays(
    current_user: User = Depends(get_current_manager_user),
    session: Session = Depends(get_session)
):
    return session.exec(select(Holiday).order_by(Holiday.date.desc())).all()

@router.post("/", response_model=Holiday)
async def create_holiday(
    holiday: Holiday,
    current_user: User = Depends(get_current_manager_user),
    session: Session = Depends(get_session)
):
    # Check uniqueness
    existing = session.exec(select(Holiday).where(Holiday.date == holiday.date)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Holiday already exists on this date")
    
    session.add(holiday)
    session.commit()
    session.refresh(holiday)
    
    # Optional: Re-aggregate for all users on this date?
    # This ensures stats stay in sync immediately.
    # Might be slow if 1000 users, but for MVP reasonable.
    users = session.exec(select(User)).all()
    for user in users:
        aggregate_daily_attendance(session, user.id, holiday.date)
        
    return holiday

@router.delete("/{holiday_id}")
async def delete_holiday(
    holiday_id: int,
    current_user: User = Depends(get_current_manager_user),
    session: Session = Depends(get_session)
):
    holiday = session.get(Holiday, holiday_id)
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
        
    target_date = holiday.date
    session.delete(holiday)
    session.commit()
    
    # Re-aggregate to revert to Absent/Punch
    users = session.exec(select(User)).all()
    for user in users:
        aggregate_daily_attendance(session, user.id, target_date)
        
    return {"status": "success"}
