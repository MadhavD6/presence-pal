import sys
import os

# Add project root to path
sys.path.append("/home/karthik/test face app/presence-pal")

try:
    print("Checking imports...")
    from backend.models import user, kiosk, audit
    print("Models imported.")
    
    from backend.core import security
    print("Security imported.")
    
    from backend.services import vector, liveness
    print("Services imported.")
    
    from backend.routers import kiosk as kiosk_router
    print("Routers imported.")
    
    print("ALL CHECKS PASSED")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)
