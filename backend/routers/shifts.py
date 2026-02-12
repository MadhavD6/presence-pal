from typing import List, Optional
from datetime import time, date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from backend.core.database import get_session
from backend.models.shift import Shift, EmployeeShift
from backend.models.user import User
from pydantic import BaseModel

router = APIRouter()

# --- Schemas ---
class ShiftCreate(BaseModel):
    name: str
    start_time: str # HH:MM
    end_time: str # HH:MM
    grace_period_mins: int = 15
    crosses_midnight: bool = False # True for night shifts where end_time < start_time

class ShiftRead(BaseModel):
    id: int
    name: str
    start_time: time
    end_time: time
    grace_period_mins: int
    crosses_midnight: bool = False

class RosterAssign(BaseModel):
    user_ids: List[int]
    shift_id: int
    weekly_offs: Optional[str] = "6" # Comma-separated weekday numbers (0=Mon, 6=Sun). Default Sunday.
    is_permanent: bool = True 

# --- Endpoints ---

@router.get("/manager/shifts", response_model=List[ShiftRead])
def get_shifts(session: Session = Depends(get_session)):
    shifts = session.exec(select(Shift)).all()
    return shifts

@router.post("/manager/shifts", response_model=ShiftRead)
def create_shift(
    shift_data: ShiftCreate,
    session: Session = Depends(get_session)
):
    try:
        # Parse times
        st = datetime.strptime(shift_data.start_time, "%H:%M").time()
        et = datetime.strptime(shift_data.end_time, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    shift = Shift(
        name=shift_data.name,
        start_time=st,
        end_time=et,
        grace_period_mins=shift_data.grace_period_mins,
        crosses_midnight=shift_data.crosses_midnight
    )
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift

@router.delete("/manager/shifts/{shift_id}")
def delete_shift(shift_id: int, session: Session = Depends(get_session)):
    shift = session.get(Shift, shift_id)
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
        
    # Check usage?
    # If users are assigned, maybe prevent delete or set to null.
    # For now, simple delete (might fail FK constraints if strict).
    try:
        session.delete(shift)
        session.commit()
    except Exception as e:
         raise HTTPException(status_code=400, detail=f"Cannot delete shift: {str(e)}")
         
    return {"status": "success"}

@router.put("/manager/shifts/{shift_id}", response_model=ShiftRead)
def update_shift(
    shift_id: int,
    shift_data: ShiftCreate,
    session: Session = Depends(get_session)
):
    shift = session.get(Shift, shift_id)
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
        
    try:
        st = datetime.strptime(shift_data.start_time, "%H:%M").time()
        et = datetime.strptime(shift_data.end_time, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    shift.name = shift_data.name
    shift.start_time = st
    shift.end_time = et
    shift.grace_period_mins = shift_data.grace_period_mins
    shift.crosses_midnight = shift_data.crosses_midnight
    
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift

@router.post("/manager/roster/assign")
def assign_roster(
    data: RosterAssign,
    session: Session = Depends(get_session)
):
    """
    Bulk assign shift to users with History Tracking.
    1. Close current active EmployeeShift (end_date = yesterday).
    2. Create new active EmployeeShift (start_date = today).
    3. Update User.shift_id (Cache).
    """
    shift = session.get(Shift, data.shift_id)
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
        
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    count = 0
    try:
        for uid in data.user_ids:
            user = session.get(User, uid)
            if not user: continue
                
            # 1. Close active shift if exists
            # Find active shift for user
            active_assignment = session.exec(
                select(EmployeeShift)
                .where(EmployeeShift.user_id == uid)
                .where(EmployeeShift.is_active == True)
                .where(EmployeeShift.end_date == None)
            ).first()
            
            if active_assignment:
                # If assigning same shift, skip? Or force re-assign?
                # Let's force re-assign date boundary for cleanliness, 
                # OR simple check:
                if active_assignment.shift_id == shift.id:
                    # Same shift, do nothing
                    count += 1
                    continue
                    
                active_assignment.end_date = yesterday
                # If start_date > end_date (e.g. assigned today, closed today), handle?
                # If start_date == today, then we just overwrite/delete it?
                if active_assignment.start_date > yesterday:
                    # It was started today or future. Delete it to prevent conflict/bad data.
                    session.delete(active_assignment)
                else:
                     session.add(active_assignment)
            
            # 2. Create new assignment
            new_assignment = EmployeeShift(
                user_id=uid,
                shift_id=shift.id,
                start_date=today,
                is_active=True,
                end_date=None,
                weekly_offs=data.weekly_offs or "6"
            )
            session.add(new_assignment)
            
            # 3. Update Cache
            user.shift_id = shift.id
            session.add(user)
            count += 1
                
        session.commit()
        return {"status": "success", "updated_count": count}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Roster assignment failed: {str(e)}")
