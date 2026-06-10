from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from app.core.agent import agent
from app.core.prompts import ask_prompt_template
from app.dependencies import verify_api_key
from app.models.api_key import ApiKey
from app.models.ask import AskRequest
from app.models.ask import AskResponse

router = APIRouter()


@router.post("/ask", response_model=AskResponse, status_code=status.HTTP_200_OK)
async def ask_question(
    body: AskRequest,
    api_key: ApiKey = Depends(verify_api_key),
) -> AskResponse:
    """Ask a question against the tenant's knowledge base."""

    prompt = ask_prompt_template.format(question=body.question)

    response = await agent.arun(
        input=prompt,
        knowledge_filters={"tenant_id": str(api_key.tenant_id)},
        stream=False,
    )

    return AskResponse(message=response.content or "")
