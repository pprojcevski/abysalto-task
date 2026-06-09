import pymupdf
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.knowledge import insert_document
from app.db import get_session
from app.dependencies import verify_api_key
from app.models.api_key import ApiKey
from app.models.document import Document

router = APIRouter()


@router.post("/upload", response_model=Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    api_key: ApiKey = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
) -> Document:
    """Upload a PDF file, persist metadata, and index content in the knowledge
    base."""

    if file.content_type not in ("application/pdf",):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported.",
        )

    # Read file bytes
    content = await file.read()

    # Extract text from PDF
    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
        text_content = "\n".join(page.get_text() for page in doc)
        doc.close()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text from PDF: {exc}",
        )

    if not text_content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PDF contains no extractable text.",
        )

    # Create document record in DB
    document = Document(
        tenant_id=api_key.tenant_id,
        filename=file.filename or "untitled.pdf",
        mime_type=file.content_type,
        status="processed",
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)

    # Insert into Agno knowledge base
    await insert_document(
        name=str(document.id),
        text_content=text_content,
        metadata={
            "document_id": str(document.id),
            "tenant_id": str(document.tenant_id),
            "filename": document.filename,
        },
    )

    return document
