import hashlib
from datetime import date
from datetime import timedelta
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.dependencies import verify_api_key


pytestmark = pytest.mark.unit


class TestVerifyApiKeySuccess:
    """Tests for successful API key verification."""

    async def test_valid_key_returns_api_key(self, mock_session, sample_api_key):
        """A valid, active key with remaining quota should return the
        ApiKey."""
        raw_key = "my-secret-key"
        sample_api_key.key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Mock the DB query result
        scalars_mock = MagicMock()
        scalars_mock.first.return_value = sample_api_key
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await verify_api_key(x_api_key=raw_key, session=mock_session)

        assert result == sample_api_key
        assert result.requests_today == 1
        mock_session.add.assert_called_once_with(sample_api_key)
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(sample_api_key)

    async def test_increments_request_count(self, mock_session, sample_api_key):
        """Each call should increment requests_today by 1."""
        raw_key = "another-key"
        sample_api_key.key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        sample_api_key.requests_today = 42

        scalars_mock = MagicMock()
        scalars_mock.first.return_value = sample_api_key
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await verify_api_key(x_api_key=raw_key, session=mock_session)

        assert result.requests_today == 43


class TestVerifyApiKeyForbidden:
    """Tests for invalid/inactive API keys (403)."""

    async def test_invalid_key_raises_403(self, mock_session):
        """An unrecognized key should raise HTTP 403."""
        scalars_mock = MagicMock()
        scalars_mock.first.return_value = None
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(x_api_key="bad-key", session=mock_session)

        assert exc_info.value.status_code == 403
        assert "Invalid or inactive" in exc_info.value.detail

    async def test_inactive_key_not_found(self, mock_session):
        """An inactive key should not be returned by the query (returns
        None)."""
        scalars_mock = MagicMock()
        scalars_mock.first.return_value = None
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(x_api_key="inactive-key", session=mock_session)

        assert exc_info.value.status_code == 403


class TestVerifyApiKeyRateLimit:
    """Tests for rate limiting (429)."""

    async def test_exhausted_limit_raises_429(self, mock_session, exhausted_api_key):
        """A key at its daily limit should raise HTTP 429."""
        raw_key = "rate-limited-key"
        exhausted_api_key.key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        scalars_mock = MagicMock()
        scalars_mock.first.return_value = exhausted_api_key
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(x_api_key=raw_key, session=mock_session)

        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in exc_info.value.detail

    async def test_429_detail_contains_reset_time(
        self, mock_session, exhausted_api_key
    ):
        """The 429 response should indicate when the limit resets."""
        raw_key = "rate-limited-key"
        exhausted_api_key.key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        scalars_mock = MagicMock()
        scalars_mock.first.return_value = exhausted_api_key
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(x_api_key=raw_key, session=mock_session)

        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        assert tomorrow in exc_info.value.detail


class TestVerifyApiKeyDayRollover:
    """Tests for daily counter reset logic."""

    async def test_resets_counter_on_new_day(self, mock_session, stale_api_key):
        """If last_reset_date is in the past, requests_today should reset to 0
        then increment."""
        raw_key = "stale-key"
        stale_api_key.key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        scalars_mock = MagicMock()
        scalars_mock.first.return_value = stale_api_key
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await verify_api_key(x_api_key=raw_key, session=mock_session)

        assert result.requests_today == 1  # reset to 0, then incremented
        assert result.last_reset_date == date.today()

    async def test_stale_exhausted_key_resets_and_succeeds(
        self, mock_session, stale_api_key
    ):
        """A key that was exhausted yesterday should work today after reset."""
        raw_key = "was-exhausted"
        stale_api_key.key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        stale_api_key.requests_today = stale_api_key.daily_limit  # was maxed out

        scalars_mock = MagicMock()
        scalars_mock.first.return_value = stale_api_key
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_session.execute = AsyncMock(return_value=result_mock)

        result = await verify_api_key(x_api_key=raw_key, session=mock_session)

        # Should reset and allow the request
        assert result.requests_today == 1
        assert result.last_reset_date == date.today()
