import sys
import os
import argparse
import numpy as np
import cv2
from typing import List
from sqlmodel import Session, select

# Add project root
sys.path.append(os.getcwd())

from backend.core.database import engine
from backend.models.user import User
from backend.models.site import Site
from backend.models.shift import Shift
from backend.services.face import face_service
from backend.services.vector import vector_service

def register_user_robust(name: str, employee_id: str, image_paths: List[str]):
    """
    Robust Registration Pipeline:
    1. Load 5-10 images.
    2. Ensure High Confidence (>0.99) on ALL.
    3. Compute 'Centroid' (Average Vector).
    4. Check Variance (Consistency).
    5. Save Centroid as Anchor.
    """
    print(f"\n🚀 Starting Robust Registration for '{name}' ({employee_id})")
    print(f"📸 Image Count: {len(image_paths)}")
    
    # 1. Validation
    if len(image_paths) < 3:
        print("❌ Error: Minimum 3 images required for robust registration.")
        return

    vectors = []
    confidences = []
    
    # 2. Process Each Image
    for path in image_paths:
        if not os.path.exists(path):
            print(f"⚠️ Warning: File not found: {path}")
            continue
            
        print(f"   Processing: {os.path.basename(path)}...", end=" ")
        
        # Read file as bytes
        with open(path, "rb") as f:
            content = f.read()
            
        # Get Embedding (using sync helper or async wrapper)
        # Since this is a script, we can call the internal sync method or manipulate the loop
        # But face_service.get_embedding is async. Let's use asyncio.run or simpler:
        # We'll use the threadpool executor directly if possible, or just call _get_embedding_sync
        
        result = face_service._get_embedding_sync(content)
        
        if not result:
            print("FAILED (No Face)")
            continue
            
        conf = result["confidence"]
        vec = result["embedding"]
        
        print(f"Confidence: {conf:.4f}")
        
        if conf < 0.99:
            print(f"      ❌ REJECTED: Low Quality (Need >0.99, Got {conf:.4f})")
            continue
            
        vectors.append(vec)
        confidences.append(conf)

    # 3. Quality Check
    valid_count = len(vectors)
    print(f"\n📊 Valid Faces: {valid_count}/{len(image_paths)}")
    
    if valid_count < 3:
        print("❌ FAILED: Not enough high-quality faces. Please retake photos in better lighting.")
        return

    # 4. Compute Centroid
    matrix = np.array(vectors)
    centroid = np.mean(matrix, axis=0) # Simple mean is fine for anchors (already high conf)
    
    # Normalize!
    norm = np.linalg.norm(centroid)
    centroid = centroid / norm
    
    # 5. Check Variance/Consistency (Optional but good)
    # Calculate average distance of each vector from centroid
    distances = []
    for v in vectors:
        # Cosine Distance = 1 - Dot Product (since normalized)
        # Note: 'v' is from DeepFace, usually normalized? DeepFace outputs normalized vectors?
        # Typically yes, but let's Ensure 'v' is normalized first.
        v_norm = v / np.linalg.norm(v)
        sim = np.dot(v_norm, centroid)
        dist = 1 - sim
        distances.append(dist)
        
    avg_dist_variance = np.mean(distances)
    max_dist = np.max(distances)
    
    print(f"📉 Identity Variance (Avg): {avg_dist_variance:.4f}")
    print(f"📉 Max Outlier Dist: {max_dist:.4f}")
    
    if max_dist > 0.30: # Threshold for outlier (0.30 dist = 0.70 similarity to centroid)
        print(f"❌ FAILED: One or more images are inconsistent (Max Dist: {max_dist:.4f} > 0.30). Remove outliers.")
        return

    if avg_dist_variance > 0.20: # Keep overall consistency check
        print("❌ FAILED: Images appear to be strictly different people or extreme angles!")
        return

    print("✅ Quality Check PASSED. Robust Anchor Generated.")

    # 6. Save to DB
    with Session(engine) as session:
        # Create/Update User
        user = session.exec(select(User).where(User.employee_id == employee_id)).first()
        if not user:
            user = User(name=name, employee_id=employee_id, role="employee")
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"👤 Created New User: ID {user.id}")
        else:
            print(f"👤 Updating Existing User: ID {user.id}")
            
        # Add Anchor to Gallery
        vector_service.add_embedding(user.id, centroid.tolist(), session, is_anchor=True)
        session.commit()
        
    print(f"\n🎉 SUCCESS! {name} is now registered with a ROBUST anchor.")
    print("   This user will now have significantly better recognition accuracy.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Robust Face Registration")
    parser.add_argument("--name", required=True, help="User Name")
    parser.add_argument("--id", required=True, help="Employee ID")
    parser.add_argument("--images", nargs="+", required=True, help="List of image paths")
    
    args = parser.parse_args()
    
    register_user_robust(args.name, args.id, args.images)
