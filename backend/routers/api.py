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
    employee_id: Optional[str] = Form(None), # Made optional
    password: str = Form(None), 
    files: List[UploadFile] = File(...), 
    session: Session = Depends(get_session)
):
    """
    Admin only: Enroll new user.
    Auto-generates Employee ID if not provided (EMP-XXX).
    """
    image_contents = []
    best_image_bytes = None
    best_confidence = 0.0
    for f in files:
        content = await f.read()
        image_contents.append(content)
        
    # Validation: Check image quality (Blur Score)
    from backend.core.config import get_settings
    import cv2
    import numpy as np
    
    settings = get_settings()
    passed_quality_check = 0
    
    for img_bytes in image_contents:
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        if img is not None:
            variance = cv2.Laplacian(img, cv2.CV_64F).var()
            if variance >= settings.ENROLLMENT_MIN_BLUR_SCORE:
                passed_quality_check += 1
            else:
                print(f"Enrollment Reject: Blur {variance:.2f} < {settings.ENROLLMENT_MIN_BLUR_SCORE}")

    if passed_quality_check < len(image_contents) // 2:
        # Require at least half of the frames to be high quality
        raise HTTPException(
            status_code=400, 
            detail=f"Image quality too low (Blurry). Please hold still and ensure good lighting. (Score: <{settings.ENROLLMENT_MIN_BLUR_SCORE})"
        )
    
    # Generate individual embeddings for each frame
    individual_embeddings = []
    for img_bytes in image_contents:
        result = await face_service.get_embedding(img_bytes)
        if result:
            # InsightFace Quality Check
            # InsightFace Quality Check
            conf = result.get("confidence", 0.0)
            if conf < 0.99:
                print(f"Enrollment Reject: Low Face Confidence {conf:.4f} < 0.99")
                continue
                
            individual_embeddings.append(result["embedding"])
            
            # Track best image for saving
            if conf > best_confidence:
                best_confidence = conf
                best_image_bytes = img_bytes
    
    if not individual_embeddings:
        raise HTTPException(status_code=400, detail="No high-quality face detected (Confidence < 0.99)")

    # Consistency Check (Variance)
    emb_matrix = np.array(individual_embeddings)
    centroid = np.mean(emb_matrix, axis=0)
    
    # Calculate distances from centroid
    dists = []
    from scipy.spatial.distance import cosine
    for vec in individual_embeddings:
        # Cosine distance (0..2)
        d = cosine(vec, centroid)
        dists.append(d)
        
    variance = np.mean(dists)
    print(f"📉 Enrollment Consistency Variance: {variance:.4f}")
    
    if variance > 0.20:
         raise HTTPException(
            status_code=400, 
            detail=f"Inconsistent Faces. Please hold still. (Variance {variance:.2f} > 0.20)"
        )
    
    # Check for duplicate face (using averaged vector)
    import numpy as np
    avg_vector = np.mean(np.array(individual_embeddings), axis=0)
    norm = np.linalg.norm(avg_vector)
    if norm > 0:
        avg_vector = (avg_vector / norm).tolist()
    else:
        avg_vector = avg_vector.tolist()
         
    existing_user_id, confidence = vector_service.find_nearest(avg_vector)
    if existing_user_id:
        # Fetch name for better error message
        existing_user_name = "Unknown"
        existing_employee_id = "Unknown"
        try:
            ex_user = session.get(User, existing_user_id)
            if ex_user:
                existing_user_name = ex_user.name
                existing_employee_id = ex_user.employee_id
        except:
            pass
            
        print(f"Enrollment Duplicate Detected: Matches User {existing_user_id} ({existing_user_name}) with Score {confidence:.4f}")
        
        # Only block if confidence is significantly high
        if confidence > 0.65: # Use same threshold as recognition
             raise HTTPException(
                status_code=400, 
                detail=f"This face is already registered as {existing_user_name} ({existing_employee_id}). Score: {confidence:.2f}"
            )

    # Prepare user data
    from sqlalchemy.exc import IntegrityError
    from sqlmodel import select
    
    hashed_password = None
    if password:
        hashed_password = get_password_hash(password)

    # Concurrency Handling: Retry Loop for ID Generation
    max_retries = 3
    final_user = None
    
    for attempt in range(max_retries):
        try:
            # 1. Determine Employee ID
            final_emp_id = employee_id
            
            if not final_emp_id:
                # Auto-generate: Find max EMP-XXX
                # This is simple string matching, ideal for MVP. 
                # Production would use a sequence or atomic counter in Redis/DB.
                statement = select(User.employee_id).where(User.employee_id.like("EMP-%"))
                existing_ids = session.exec(statement).all()
                
                max_num = 100
                for eid in existing_ids:
                    try:
                        num = int(eid.split("-")[1])
                        if num > max_num:
                            max_num = num
                    except:
                        pass
                
                final_emp_id = f"EMP-{max_num + 1}"
            
            # 2. Try to Create User
            user = User(
                name=name, 
                employee_id=final_emp_id, 
                role="user",
                hashed_password=hashed_password
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            final_user = user
            break # Success!
            
        except IntegrityError:
            session.rollback()
            if employee_id:
                # If user provided a specific ID and it failed, don't retry -> it's a real duplicate
                raise HTTPException(status_code=400, detail="User with this Employee ID already exists")
            else:
                # If auto-generated, it means race condition on EMP-XXX. Retry will fetch new max.
                continue
                
    if not final_user:
        raise HTTPException(status_code=500, detail="System busy: Could not generate unique ID after retries. Please try again.")
    
    # Add EACH embedding as separate anchor (Multi-Reference)
    for idx, embedding in enumerate(individual_embeddings):
        vector_service.add_embedding(final_user.id, embedding, session, is_anchor=True)
        
    # Save the best image (highest confidence)
    if best_image_bytes and final_user:
        try:
            filename = f"registered_faces/{final_user.id}_{final_user.employee_id}.jpg"
            
            from backend.services.storage import storage_service
            file_url = storage_service.upload_file(best_image_bytes, filename)
            
            if file_url:
                print(f"📸 Saved registration photo to S3: {file_url}")
            else:
                print(f"⚠️ Failed to upload registration photo to S3")
                
        except Exception as e:
            print(f"⚠️ Failed to save registration photo: {e}")
    
    print(f"✅ Enrolled {name} ({final_user.employee_id}) with {len(individual_embeddings)} vectors")
    
    return {
        "status": "enrolled", 
        "user_id": final_user.id,
        "employee_id": final_user.employee_id,
        "embeddings_stored": len(individual_embeddings)
    }
