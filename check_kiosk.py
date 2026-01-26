from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.kiosk import Kiosk

with Session(engine) as session:
    kiosks = session.exec(select(Kiosk)).all()
    print(f"Total Kiosks: {len(kiosks)}")
    for k in kiosks:
        print(f"ID: {k.id}, Device: {k.device_id}, Hash: {k.api_key_hash[:10]}...")
