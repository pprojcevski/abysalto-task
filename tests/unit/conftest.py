import uuid
from datetime import date
from datetime import datetime
from datetime import timezone
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from app.models.api_key import ApiKey


@pytest.fixture
def mock_session():
    """Create a mocked AsyncSession."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def sample_api_key():
    """Create a sample ApiKey for testing."""
    return ApiKey(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        key_hash="fake_hash",
        daily_limit=1000,
        requests_today=0,
        last_reset_date=date.today(),
        active=True,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def exhausted_api_key():
    """Create an ApiKey that has exceeded its daily limit."""
    return ApiKey(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        key_hash="fake_hash",
        daily_limit=100,
        requests_today=100,
        last_reset_date=date.today(),
        active=True,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def stale_api_key():
    """Create an ApiKey whose counter hasn't been reset today."""
    return ApiKey(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        key_hash="fake_hash",
        daily_limit=1000,
        requests_today=50,
        last_reset_date=date(2025, 1, 1),  # old date
        active=True,
        created_at=datetime.now(timezone.utc),
    )
