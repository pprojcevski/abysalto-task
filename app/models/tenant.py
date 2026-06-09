import uuid
from datetime import datetime
from datetime import timezone

from sqlmodel import Field
from sqlmodel import SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow)
