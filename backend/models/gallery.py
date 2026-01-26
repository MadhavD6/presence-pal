from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, LargeBinary

class FaceGallery(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    vector: bytes = Field(sa_column=Column(LargeBinary))
    is_anchor: bool = Field(default=False, description="True if this is the original registration photo")
    confidence: float = Field(default=1.0, description="Confidence score when captured")
    model_version: str = Field(default="arcface_v1", description="Embedding model version for future migrations")
    created_at: datetime = Field(default_factory=datetime.utcnow)

