#!/bin/bash
set -e

echo "==> Waiting for database to be ready..."
# The depends_on healthcheck handles this, but belt-and-suspenders:
python -c "
import asyncio, asyncpg, sys

async def wait():
    for i in range(30):
        try:
            conn = await asyncpg.connect('postgresql://postgres:postgres@db:5432/abysalto')
            await conn.close()
            return
        except Exception:
            await asyncio.sleep(1)
    print('ERROR: Database not reachable after 30s', file=sys.stderr)
    sys.exit(1)

asyncio.run(wait())
"

echo "==> Running Alembic migrations..."
alembic upgrade head

echo "==> Verifying pgvector extension..."
python -c "
import asyncio, asyncpg, sys

async def check():
    conn = await asyncpg.connect('postgresql://postgres:postgres@db:5432/abysalto')
    row = await conn.fetchrow(\"SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'\")
    await conn.close()
    if row is None:
        print('ERROR: pgvector extension is not installed!', file=sys.stderr)
        sys.exit(1)
    print(f'pgvector v{row[\"extversion\"]} confirmed.')

asyncio.run(check())
"

echo "==> Verifying all migrations are applied..."
python -c "
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:postgres@db:5432/abysalto')
with engine.connect() as conn:
    context = MigrationContext.configure(conn)
    current_rev = context.get_current_revision()

alembic_cfg = Config('alembic.ini')
script = ScriptDirectory.from_config(alembic_cfg)
head_rev = script.get_current_head()

if current_rev != head_rev:
    print(f'WARNING: DB at revision {current_rev}, head is {head_rev}')
else:
    print(f'All migrations applied (revision: {current_rev})')
"

echo "==> Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --proxy-headers
