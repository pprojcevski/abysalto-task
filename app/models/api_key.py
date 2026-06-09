import uuid
from datetime import datetime, date, timezone

from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID = Field(nullable=False, foreign_key="tenants.id")
    key_hash: str = Field(max_length=255, nullable=False, unique=True)
    daily_limit: int = Field(default=1000, nullable=False)
    requests_today: int = Field(default=0, nullable=False)
    last_reset_date: date = Field(default_factory=date.today, nullable=False)
    active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)

