from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional, List
from backend.services.face import face_service
from backend.services.vector import vector_service
from backend.services.audit import audit_service
from backend.services.liveness import liveness_service
from sqlmodel import Session
from backend.core.database import get_session
from backend.models.user import User
from backend.models.kiosk import Kiosk
from backend.core.security import get_current_kiosk, get_password_hash

router = APIRouter()

# identify_user moved to backend/routers/kiosk.py

@router.post("/admin/enroll")
async def enroll_user(
    name: str = Form(...),
    employee_id: str = Form(...),
    password: str = Form(None), # Optional for backward compatibility but recommended
    files: List[UploadFile] = File(...), # Changed from file to files
    session: Session = Depends(get_session)
):
    """
    Admin only: Enroll new user.
    Multi-Reference Registration: Stores each frame as individual embedding.
    """
    image_contents = []
    for f in files:
        content = await f.read()
        image_contents.append(content)
    
    # Generate individual embeddings for each frame
    individual_embeddings = []
    for img_bytes in image_contents:
        vec = face_service.get_embedding(img_bytes)
        if vec:
            individual_embeddings.append(vec)
    
    if not individual_embeddings:
        raise HTTPException(status_code=400, detail="No face detected in any of the frames")
    
    # Use averaged embedding for duplicate check only
    import numpy as np
    avg_vector = np.mean(np.array(individual_embeddings), axis=0)
    norm = np.linalg.norm(avg_vector)
    if norm > 0:
        avg_vector = (avg_vector / norm).tolist()
    else:
        avg_vector = avg_vector.tolist()
         
    # Check for duplicate face
    existing_user_id, confidence = vector_service.find_nearest(avg_vector)
    if existing_user_id and confidence > 0.4:
        raise HTTPException(status_code=400, detail="This face is already registered.")

    # Create User
    from sqlalchemy.exc import IntegrityError
    
    hashed_password = None
    if password:
        hashed_password = get_password_hash(password)

    try:
        user = User(
            name=name, 
            employee_id=employee_id, 
            role="user",
            hashed_password=hashed_password
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="User with this ID already exists")
    
    # Add EACH embedding as separate anchor (Multi-Reference)
    for idx, embedding in enumerate(individual_embeddings):
        vector_service.add_embedding(user.id, embedding, session, is_anchor=True)
    
    print(f"✅ Enrolled {name} with {len(individual_embeddings)} reference embeddings")
    
    return {
        "status": "enrolled", 
        "user_id": user.id,
        "embeddings_stored": len(individual_embeddings)
    }
