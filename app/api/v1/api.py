from fastapi import APIRouter

from app.rest.ask import router as ask_router
from app.rest.upload import router as upload_router

router = APIRouter()

router.include_router(ask_router)
router.include_router(upload_router)
