from typing import Optional
from sqlmodel import Field, SQLModel

class Site(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    latitude: float
    longitude: float
    radius_meters: float = Field(default=100.0)
    is_active: bool = Field(default=True)
