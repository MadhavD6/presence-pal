from typing import Optional
from datetime import date as dt_date
from sqlmodel import SQLModel, Field

class Holiday(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: dt_date = Field(unique=True, index=True)
    name: str = Field(index=True)
    is_national: bool = Field(default=True)
    description: Optional[str] = Field(default=None)
