import asyncio
import os
import sys

# Add the parent directory to the path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.database import get_async_session
from sqlmodel import select

# Import all models
from backend.models.user import User
from backend.models.site import Site
from backend.models.kiosk import Kiosk
from backend.models.audit import AuditLog
from backend.models.correction import AttendanceCorrection
from backend.models.gallery import FaceGallery
from backend.models.holiday import Holiday
from backend.models.leave import Leave
from backend.models.payroll import PayrollConfig, DailySummary, PayrollRun, Payslip
from backend.models.shift import Shift

async def dump_data():
    print("--- Database Content Dump ---")
    try:
        async for session in get_async_session():
            models = [
                ("Site", Site),
                ("Kiosk", Kiosk),
                ("User", User),
                ("Shift", Shift),
                ("Holiday", Holiday),
                ("LeaveRequest", Leave),
                ("CorrectionRequest", AttendanceCorrection),
                ("AuditLog", AuditLog),
                ("Gallery", FaceGallery),
                ("PayrollConfig", PayrollConfig),
                ("DailySummary", DailySummary),
                ("PayrollRun", PayrollRun),
                ("Payslip", Payslip)
            ]

            for name, model in models:
                print(f"\n=== Table: {name} ===")
                try:
                    # Fetch first 5 rows
                    result = await session.exec(select(model).limit(5))
                    rows = result.all()
                    
                    if not rows:
                        print("  [Empty]")
                    else:
                        for row in rows:
                            # Convert to dict for cleaner printing if possible, or just print object
                            print(f"  {row}")
                            
                    # Count total
                    from sqlmodel import func
                    count_res = await session.exec(select(func.count(model.id)))
                    total = count_res.one()
                    print(f"  [Total Records: {total}]")
                    
                except Exception as e:
                    print(f"  [Error reading table: {e}]")
            
            break
            
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(dump_data())
