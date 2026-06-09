from app.core.agent import knowledge_base


async def insert_document(
    name: str,
    text_content: str,
    metadata: dict | None = None,
) -> None:
    """Insert PDF text content into the knowledge base."""
    await knowledge_base.ainsert(
        name=name,
        text_content=text_content,
        metadata=metadata or {},
        upsert=True,
    )
