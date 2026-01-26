import sys
import os
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Mock Services BEFORE importing main
# We need to mock them to avoid loading heavy models or needing real faces
sys.modules["backend.services.face"] = MagicMock()
sys.modules["backend.services.liveness"] = MagicMock()
sys.modules["backend.services.vector"] = MagicMock()

from backend.services.face import face_service
from backend.services.liveness import liveness_service
from backend.services.vector import vector_service

# Mock methods
face_service.get_embedding.return_value = b'fake_vector'
liveness_service.check_liveness.return_value = True

# Now import main
from backend.main import app
from backend.core.database import get_session
from backend.models.user import User
from backend.models.site import Site

# Setup Test DB
engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
SQLModel.metadata.create_all(engine)

def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

# Setup Data
def setup_data():
    with Session(engine) as session:
        # Create Site
        site = Site(
            name="Test Office",
            latitude=12.9716, # Bangalore coords example
            longitude=77.5946,
            radius_meters=100.0
        )
        session.add(site)
        session.commit()
        session.refresh(site)
        
        # Create User
        user = User(
            name="Mobile Tester",
            employee_id="M001",
            role="user",
            site_id=site.id 
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return user, site

def run_tests():
    client = TestClient(app)
    user, site = setup_data()
    
    # Mock Auth (Dependency Override for get_current_user)
    # Since we can't easily generate valid JWT without full auth setup, 
    # let's override the `get_current_user` dependency directly.
    from backend.core.security import get_current_active_user
    app.dependency_overrides[get_current_active_user] = lambda: user
    
    # Mock Vector Service to return OUR user
    vector_service.find_nearest.return_value = (user.id, 0.95)
    
    print("--- Starting Verification Tests ---")
    
    # Test 1: Success inside Geofence
    print("\nTest 1: Clock-In Inside Geofence (Distance ~0m)")
    response = client.post(
        "/api/v1/attendance/clock-in",
        data={
            "latitude": 12.9716, 
            "longitude": 77.5946,
            "accuracy": 10.0
        },
        files={"file": ("selfie.jpg", b"fake_image_bytes", "image/jpeg")}
    )
    if response.status_code == 200:
        print("✅ SUCCESS:", response.json())
    else:
        print("❌ FAILED:", response.status_code, response.text)

    # Test 2: Success edge of Geofence (Distance ~90m)
    # 0.0008 deg is roughly 88m at equator
    print("\nTest 2: Clock-In at Edge (~90m)")
    response = client.post(
        "/api/v1/attendance/clock-in",
        data={
            "latitude": 12.9716 + 0.0008, 
            "longitude": 77.5946,
            "accuracy": 10.0
        },
        files={"file": ("selfie.jpg", b"fake_image_bytes", "image/jpeg")}
    )
    if response.status_code == 200:
        print("✅ SUCCESS:", response.json())
    else:
        print("❌ FAILED:", response.status_code, response.text)
        
    # Test 3: Fail Outside Geofence (Distance ~200m)
    print("\nTest 3: Clock-In Outside Geofence (~200m)")
    try:
        response = client.post(
            "/api/v1/attendance/clock-in",
            data={
                "latitude": 12.9716 + 0.002, 
                "longitude": 77.5946,
                "accuracy": 10.0
            },
            files={"file": ("selfie.jpg", b"fake_image_bytes", "image/jpeg")}
        )
        if response.status_code == 403:
            print("✅ CORRECTLY REJECTED (403):", response.json()['detail'])
        else:
            print("❌ UNEXPECTED RESPONSE:", response.status_code, response.text)
    except Exception as e:
        print("❌ EXCEPTION:", e)

    # Test 4: Fail Poor GPS Accuracy
    print("\nTest 4: Fail Poor Accuracy (>100m)")
    response = client.post(
        "/api/v1/attendance/clock-in",
        data={
            "latitude": 12.9716, 
            "longitude": 77.5946,
            "accuracy": 150.0
        },
        files={"file": ("selfie.jpg", b"fake_image_bytes", "image/jpeg")}
    )
    if response.status_code == 400:
         print("✅ CORRECTLY REJECTED (400):", response.json()['detail'])
    else:
         print("❌ UNEXPECTED RESPONSE:", response.status_code, response.text)

if __name__ == "__main__":
    run_tests()
