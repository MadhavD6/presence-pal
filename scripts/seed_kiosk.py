import sys
import os
import secrets

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.kiosk import Kiosk
from backend.core.security import get_password_hash

def seed_kiosk():
    with Session(engine) as session:
        device_id = "TEST_KIOSK_01"
        
        # Check if exists
        existing = session.exec(select(Kiosk).where(Kiosk.device_id == device_id)).first()
        if existing:
            print("Kiosk already exists. Cannot retrieve original secret key.")
            print(f"Delete it first if you need a new key: DELETE FROM kiosk WHERE device_id='{device_id}';")
            return

        secret = secrets.token_urlsafe(32)
        api_key_hash = get_password_hash(secret)
        
        kiosk = Kiosk(
            device_id=device_id,
            location="Test Location",
            building="Test Building",
            api_key_hash=api_key_hash
        )
        session.add(kiosk)
        session.commit()
        session.refresh(kiosk)
        
        full_key = f"kiosk:{device_id}:{secret}"
        print(f"Kiosk Created!")
        print(f"Device ID: {device_id}")
        print(f"API Key: {full_key}")
        print("-" * 20)
        print("Run this in browser console:")
        print(f"localStorage.setItem('kiosk_api_key', '{full_key}')")

if __name__ == "__main__":
    seed_kiosk()
