
from sqlmodel import Session, select
from backend.core.database import engine
from backend.models.site import Site
from backend.models.user import User

def seed_test_site():
    with Session(engine) as session:
        site = session.exec(select(Site).where(Site.name == "Bangalore Office")).first()
        if not site:
            print("Creating Bangalore Office...")
            site = Site(
                name="Bangalore Office",
                latitude=12.9716,
                longitude=77.5946,
                radius_meters=100.0,
                is_active=True
            )
            session.add(site)
            session.commit()
            print(f"Created Site: {site.name} (ID: {site.id})")
        else:
            print(f"Site exists: {site.name} (ID: {site.id})")

if __name__ == "__main__":
    seed_test_site()
