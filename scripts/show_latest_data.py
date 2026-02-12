from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.audit import AuditLog
from backend.models.gallery import FaceGallery
from backend.models.user import User

def show_data():
    with Session(engine) as session:
        # 1. Get User
        user = session.exec(select(User)).first()
        if not user:
            print("No users found.")
            return

        print(f"\n--- User: {user.name} (ID: {user.id}) ---")

        # 2. Latest Audit Log (The "Clock In" Evidence)
        logs = session.exec(
            select(AuditLog)
            .where(AuditLog.user_id == user.id)
            .order_by(AuditLog.timestamp.desc())
            .limit(3)
        ).all()
        
        print(f"\n[Table: AuditLog] (Latest 3 events)")
        if logs:
            for log in logs:
                print(f" - ID: {log.id} | Type: {log.event_type} | Time: {log.timestamp} | Conf: {log.confidence:.4f}")
                if log.metadata_info:
                    print(f"   Metadata: {log.metadata_info}")
        else:
            print(" - No logs found.")

        # 3. Face Gallery (The Biometric Storage)
        gallery_entries = session.exec(
            select(FaceGallery)
            .where(FaceGallery.user_id == user.id)
            .order_by(FaceGallery.created_at.asc())
        ).all()
        
        print(f"\n[Table: FaceGallery] (Vectors stored for recognition)")
        if gallery_entries:
            for entry in gallery_entries:
                type_str = "ANCHOR (Permanent)" if entry.is_anchor else "DYNAMIC (Adaptive)"
                print(f" - ID: {entry.id} | Type: {type_str} | Date: {entry.created_at} | InitConf: {entry.confidence}")
        else:
            print(" - No gallery entries found.")

if __name__ == "__main__":
    show_data()
