from sqlmodel import SQLModel
from backend.core.database import engine
# Import ALL models so they are registered with SQLModel.metadata
from backend.models.user import User
from backend.models.kiosk import Kiosk
from backend.models.audit import AuditLog
from backend.models.shift import Shift, EmployeeShift
from backend.models.site import Site
from backend.models.leave import Leave
try:
    from backend.models.correction import AttendanceCorrection
except ImportError:
    pass
# from backend.models.holiday import Holiday # Missing

def init_db():
    print("Creating all tables...")
    SQLModel.metadata.create_all(engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()
