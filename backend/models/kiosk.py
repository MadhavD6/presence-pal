from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class Kiosk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(unique=True, index=True)
    location: str
    building: str
    ip_address: Optional[str] = None
    status: str = Field(default="active") # active, disabled, maintenance
    api_key_hash: str
    site_id: Optional[int] = Field(default=None, foreign_key="site.id")
    last_heartbeat: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
