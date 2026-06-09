from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Config(BaseSettings, extra="ignore", env_file=".env"):
    app_name: str = "API"
    version: str = "0.0.1"
    cors_allowed_origins: str = "*"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/abysalto"

class LogConfig(BaseModel):
    """Logging configuration."""

    LOGGER_NAME: str = "main_logger"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "INFO"

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers: dict = {
        "main_logger": {"handlers": ["default"], "level": LOG_LEVEL},
    }


@lru_cache
def get_config():
    return Config()
