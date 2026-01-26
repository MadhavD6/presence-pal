import sys
import os

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.kiosk import Kiosk

def reset_kiosk(device_id: str):
    with Session(engine) as session:
        kiosk = session.exec(select(Kiosk).where(Kiosk.device_id == device_id)).first()
        if not kiosk:
            print(f"Error: Kiosk with Device ID '{device_id}' not found.")
            return
        
        try:
            session.delete(kiosk)
            session.commit()
            print(f"Success: Kiosk '{device_id}' has been removed. You can now re-register it.")
        except Exception as e:
            print(f"Error removing kiosk: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reset_kiosk.py <device_id>")
        sys.exit(1)
    
    reset_kiosk(sys.argv[1])
