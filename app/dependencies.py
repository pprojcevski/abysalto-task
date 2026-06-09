import hashlib
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone

from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db import get_session
from app.models.api_key import ApiKey


async def verify_api_key(
    x_api_key: str = Header(...),
    session: AsyncSession = Depends(get_session),
) -> ApiKey:
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()

    result = await session.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.active == True)  # noqa: E712
    )
    api_key = result.scalars().first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or inactive API key.",
        )

    # Rate limiting: reset counter if the day has rolled over
    today = date.today()
    if api_key.last_reset_date < today:
        api_key.requests_today = 0
        api_key.last_reset_date = today

    # Check if daily limit is exceeded
    if api_key.requests_today >= api_key.daily_limit:
        reset_at = datetime.combine(
            today + timedelta(days=1), time.min, tzinfo=timezone.utc
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Resets at {reset_at.isoformat()}.",
        )

    # Increment request count and persist
    api_key.requests_today += 1
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return api_key
