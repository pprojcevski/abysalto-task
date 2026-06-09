import uuid
from datetime import datetime, timezone
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeChunk(SQLModel, table=True):
    __tablename__ = "knowledge_chunks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID = Field(nullable=False, foreign_key="tenants.id")
    document_id: uuid.UUID = Field(nullable=False, foreign_key="documents.id")
    chunk_index: int = Field(nullable=False)
    content: str = Field(nullable=False)
    embedding: Any = Field(default=None, sa_column=Column(Vector(1536)))
    chunk_metadata: dict | None = Field(
        default=None, sa_column=Column("metadata", JSONB)
    )
    created_at: datetime = Field(default_factory=_utcnow)

    __table_args__ = (
        Index(
            "knowledge_chunks_embedding_idx",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

