import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import router as v1_router
from app.core.config import get_config

config = get_config()


app = FastAPI(
    title=os.environ.get("APP_NAME", "MLS Api"),
    version=os.environ.get("APP_VERSION", "0.0.1"),
)

# CORS
allowed_origins = [origin.strip() for origin in config.cors_allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(v1_router, prefix="/api/v1")


# Health and root endpoints
@app.get("/", tags=["meta"])
def read_root():
    return {"status": "ok", "service": config.app_name, "version": config.version}


@app.get("/health", tags=["meta"])
def health():
    return {"status": "healthy"}


def main():
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
        log_level=config.log_level,
        workers=config.workers,
    )


if __name__ == "__main__":
    main()
