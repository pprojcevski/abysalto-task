import hashlib
import os
import uuid
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import httpx
from testcontainers.postgres import PostgresContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy
import pytest


# ---------------------------------------------------------------------------
# Agno mock — MUST be patched at module level BEFORE app.core.agent is imported.
# ---------------------------------------------------------------------------


class FakeAgentResponse:
    """Mimics the response object returned by Agent.arun()."""

    def __init__(self, content: str = "This is a mocked agent response."):
        self.content = content


_mock_arun = AsyncMock(return_value=FakeAgentResponse())
_mock_ainsert = AsyncMock(return_value=None)

_mock_agent_instance = MagicMock()
_mock_agent_instance.arun = _mock_arun

_mock_knowledge_instance = MagicMock()
_mock_knowledge_instance.ainsert = _mock_ainsert

# Patch agno constructors at module level
_patches = [
    patch("agno.agent.Agent", return_value=_mock_agent_instance),
    patch("agno.knowledge.Knowledge", return_value=_mock_knowledge_instance),
    patch("agno.models.aws.AwsBedrock", return_value=MagicMock()),
    patch("agno.vectordb.pgvector.PgVector", return_value=MagicMock()),
    patch("agno.vectordb.search.SearchType", new=MagicMock(hybrid="hybrid")),
]

for _p in _patches:
    _p.start()

# ---------------------------------------------------------------------------
# Agno fixtures (for per-test customization)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def mock_agent_response():
    """Access the mocked agent to customize responses per-test if needed."""
    return {"arun": _mock_arun, "ainsert": _mock_ainsert}


# ---------------------------------------------------------------------------
# Testcontainers: PostgreSQL with pgvector
# ---------------------------------------------------------------------------


PG_USER = "postgres"
PG_PASSWORD = "postgres"
PG_DB = "abysalto_test"


@pytest.fixture(scope="session")
def pg_container():
    """Start a PostgreSQL container with pgvector extension."""
    with (
        PostgresContainer(
            image="pgvector/pgvector:pg16",
            username=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DB,
        )
        .with_env("POSTGRES_USER", PG_USER)
        .with_env("POSTGRES_PASSWORD", PG_PASSWORD)
        .with_env("POSTGRES_DB", PG_DB)
        .with_env("POSTGRES_HOST_AUTH_METHOD", "trust")
        .waiting_for(
            LogMessageWaitStrategy("database system is ready to accept connections")
        )
    ) as pg:
        yield pg


@pytest.fixture(scope="session")
def pg_connection_url(pg_container):
    """Return the asyncpg connection URL for the test database."""
    host = pg_container.get_container_host_ip()
    port = pg_container.get_exposed_port(5432)
    return f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{host}:{port}/{PG_DB}"


@pytest.fixture(scope="session")
def pg_sync_url(pg_container):
    """Return the synchronous psycopg2 connection URL (for alembic
    migrations)."""
    host = pg_container.get_container_host_ip()
    port = pg_container.get_exposed_port(5432)
    return f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{host}:{port}/{PG_DB}"


# ---------------------------------------------------------------------------
# Database setup: run migrations + seed data
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _run_migrations(pg_sync_url, pg_connection_url):
    """Run alembic migrations against the test PostgreSQL container."""
    os.environ["DATABASE_URL"] = pg_connection_url
    os.environ["AGNO_DB_URL"] = pg_connection_url.replace("+asyncpg", "+psycopg")

    from app.core.config import get_config

    get_config.cache_clear()

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", pg_sync_url)
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
def _seed_data(_run_migrations, pg_sync_url):
    """Seed test tenant and API key using a sync connection (no event loop
    issues)."""
    import sqlalchemy as sa

    engine = sa.create_engine(pg_sync_url)

    tenant_id = uuid.uuid4()
    raw_key = "integration-test-key"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    with engine.begin() as conn:
        conn.execute(
            sa.text("INSERT INTO tenants (id, name) VALUES (:id, :name)"),
            {"id": tenant_id, "name": "Test Tenant"},
        )
        conn.execute(
            sa.text(
                "INSERT INTO api_keys (id, tenant_id, key_hash, daily_limit, requests_today, last_reset_date, active) "
                "VALUES (:id, :tenant_id, :key_hash, :daily_limit, :requests_today, CURRENT_DATE, true)"
            ),
            {
                "id": uuid.uuid4(),
                "tenant_id": tenant_id,
                "key_hash": key_hash,
                "daily_limit": 1000,
                "requests_today": 0,
            },
        )

    engine.dispose()
    return {"raw_key": raw_key, "tenant_id": tenant_id}


@pytest.fixture(scope="session")
def test_api_key(_seed_data):
    """Return (raw_key, tenant_id) for authenticated requests."""
    return _seed_data["raw_key"], _seed_data["tenant_id"]


# ---------------------------------------------------------------------------
# In-process FastAPI test client — FUNCTION-scoped for clean isolation
# ---------------------------------------------------------------------------


@pytest.fixture
async def async_client(_seed_data, pg_connection_url):
    """Function-scoped async HTTP client.

    Each test gets a fresh client with a properly isolated DB session.
    """
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from app.db import get_session
    from app.main import app

    engine = create_async_engine(pg_connection_url, echo=False, pool_pre_ping=True)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()
