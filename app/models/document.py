import uuid
from datetime import datetime
from datetime import timezone

from sqlmodel import Field
from sqlmodel import SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID = Field(nullable=False, foreign_key="tenants.id")
    filename: str = Field(max_length=500, nullable=False)
    storage_path: str = Field(nullable=False)
    mime_type: str | None = Field(default=None, max_length=100)
    status: str = Field(default="uploaded", max_length=50)
    uploaded_at: datetime = Field(default_factory=_utcnow)
