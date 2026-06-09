from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension (needed by Agno's PgVector)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("daily_limit", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("requests_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "last_reset_date",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), server_default="uploaded", nullable=True),
        sa.Column(
            "uploaded_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("api_keys")
    op.drop_table("tenants")
    op.execute("DROP EXTENSION IF EXISTS vector")
