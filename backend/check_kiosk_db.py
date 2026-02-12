import asyncio
import os
import sys

# Add the parent directory to the path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.database import get_async_session
from sqlmodel import select, func
from backend.models.site import Site
from backend.models.kiosk import Kiosk
from backend.models.user import User

async def check_db():
    print("--- Connecting to Database ---")
    try:
        async for session in get_async_session():
            print("Connected!")
            
            # Check Sites
            sites_result = await session.exec(select(func.count(Site.id)))
            site_count = sites_result.one()
            
            active_sites_result = await session.exec(select(func.count(Site.id)).where(Site.is_active == True))
            active_site_count = active_sites_result.one()
            
            print(f"Total Sites: {site_count}")
            print(f"Active Sites: {active_site_count}")
            
            # Check Kiosks
            kiosks_result = await session.exec(select(func.count(Kiosk.id)))
            kiosk_count = kiosks_result.one()
            print(f"Total Kiosks: {kiosk_count}")

            # Check Users
            users_result = await session.exec(select(func.count(User.id)))
            user_count = users_result.one()
            print(f"Total Users: {user_count}")
            
            if site_count == 0:
                print("\n[ALERT] 'Sites' table is empty! This creates a deadlock in Kiosk Setup.")
                print("Action Required: Create a Site manually in the Manager Dashboard or via SQL.")
            else:
                 print("\n[OK] Sites exist. Kiosk Setup should list them.")
                 
            break
            
    except Exception as e:
        print(f"\n[ERROR] Failed to connect or query database: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
