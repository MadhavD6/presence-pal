from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, LargeBinary

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    employee_id: str = Field(unique=True, index=True)
    shift_id: Optional[int] = Field(default=None, foreign_key="shift.id")
    role: str = Field(default="user") # "admin" or "user"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    email: Optional[str] = Field(default=None, index=True)
    hashed_password: Optional[str] = Field(default=None)
    site_id: Optional[int] = Field(default=None, foreign_key="site.id")
    # Embedding is stored in a separate table or just not loaded here?
    # We need to persist it. Let's make a separate Embedding table 
    # so we can fetch all embeddings at startup strictly.

class Embedding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    vector: bytes = Field(sa_column=Column(LargeBinary))
    created_at: datetime = Field(default_factory=datetime.utcnow)
