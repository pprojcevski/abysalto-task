from agno.agent import Agent
from agno.knowledge import Knowledge
from agno.knowledge.embedder.fastembed import FastEmbedEmbedder
from agno.models.aws import AwsBedrock
from agno.vectordb.pgvector import PgVector
from agno.vectordb.search import SearchType

from app.core.config import get_config
from app.core.prompts import agent_description


config = get_config()

knowledge_base = Knowledge(
    name="Document Knowledge Base",
    description="Base knowledge base for Document Insight",
    vector_db=PgVector(
        table_name="agno_knowledge_chunks",
        db_url=config.agno_db_url,
        search_type=SearchType.hybrid,
        embedder=FastEmbedEmbedder(),
    ),
)

agent = Agent(
    name="Document Insight Agent",
    model=AwsBedrock(id=config.bedrock_model_name),
    description=agent_description,
    knowledge=knowledge_base,
    markdown=True,
    search_knowledge=True,
    debug_mode=config.agno_debug_mode,
)
