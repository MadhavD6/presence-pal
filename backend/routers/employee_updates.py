
from backend.models.correction import AttendanceCorrection

@router.post("/me/corrections")
def apply_correction(
    original_date: str = Form(...),
    corrected_in: Optional[str] = Form(None), # HH:MM
    corrected_out: Optional[str] = Form(None), # HH:MM
    reason: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    try:
        o_date = datetime.strptime(original_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    c_in = None
    c_out = None
    
    if corrected_in:
        try:
             # Combine with original date
             t_in = datetime.strptime(corrected_in, "%H:%M").time()
             c_in = datetime.combine(o_date, t_in)
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid time format")

    if corrected_out:
        try:
             t_out = datetime.strptime(corrected_out, "%H:%M").time()
             c_out = datetime.combine(o_date, t_out)
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid time format")

    correction = AttendanceCorrection(
        user_id=current_user.id,
        original_date=o_date,
        corrected_in=c_in,
        corrected_out=c_out,
        reason=reason,
        status="Pending"
    )
    session.add(correction)
    session.commit()
    session.refresh(correction)
    return {"status": "submitted", "id": correction.id}

@router.get("/me/corrections")
def get_my_corrections(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    start_dt = date.today() - timedelta(days=60)
    corrections = session.exec(
        select(AttendanceCorrection)
        .where(AttendanceCorrection.user_id == current_user.id)
        .where(AttendanceCorrection.original_date >= start_dt)
        .order_by(AttendanceCorrection.created_at.desc())
    ).all()
    return corrections
