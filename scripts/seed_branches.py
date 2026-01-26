
from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.site import Site

def seed_branches():
    branches = [
        "Sangareddy",
        "Hastinapuram",
        "Kompally",
        "Lal Bungalow",
        "D K Road",
        "Leela Nagar",
        "Nizamabad",
        "Ameerpet",
        "Corporate Office"
    ]
    
    # Default approx coords for Hyderabad region to avoid 0,0
    default_lat = 17.3850
    default_lon = 78.4867
    
    with Session(engine) as session:
        count = 0
        for name in branches:
            site = session.exec(select(Site).where(Site.name == name)).first()
            if not site:
                print(f"Creating {name}...")
                site = Site(
                    name=name,
                    latitude=default_lat,
                    longitude=default_lon,
                    radius_meters=100.0,
                    is_active=True
                )
                session.add(site)
                count += 1
            else:
                print(f"Skipping {name} (Already exists)")
        
        session.commit()
        print(f"Successfully added {count} new branches.")

if __name__ == "__main__":
    seed_branches()
