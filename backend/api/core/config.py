"""
API Configuration Settings
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Pharma Chat API"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Chat and Supervisor API for Medical Domain"
    API_PREFIX: str = "/api/v1"

    # Server
    HOST: str = Field(default="0.0.0.0", env="API_HOST")
    PORT: int = Field(default=8001, env="API_PORT")
    WORKERS: int = Field(default=1, env="API_WORKERS")

    # Database API
    DATABASE_API_URL: str = Field(
        default="http://localhost:8002/api/v1",
        env="DATABASE_API_URL"
    )
    DATABASE_API_TIMEOUT: float = Field(default=30.0, env="DATABASE_API_TIMEOUT")

    # Cache Configuration
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")
    CACHE_MAX_SIZE: int = Field(default=10000, env="CACHE_MAX_SIZE")

    # Supervisor Configuration
    CHECKPOINT_PATH: str = Field(
        default="database/checkpointer/checkpoint.db",
        env="CHECKPOINT_PATH"
    )
    LLM_PROVIDER: str = Field(default="openai", env="LLM_PROVIDER")
    LLM_MODEL: Optional[str] = Field(default=None, env="LLM_MODEL")

    # Session Configuration
    SESSION_TIMEOUT: int = Field(default=3600, env="SESSION_TIMEOUT")
    MAX_SESSION_HISTORY: int = Field(default=20, env="MAX_SESSION_HISTORY")

    # Security
    API_KEY: Optional[str] = Field(default=None, env="API_KEY")
    ENABLE_CORS: bool = Field(default=True, env="ENABLE_CORS")
    CORS_ORIGINS: list = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )

    # Performance
    REQUEST_TIMEOUT: float = Field(default=60.0, env="REQUEST_TIMEOUT")
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES")
    RETRY_DELAY: float = Field(default=1.0, env="RETRY_DELAY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()


# Validate critical settings
def validate_settings():
    """Validate critical settings on startup"""
    errors = []

    # Check if checkpoint directory exists
    checkpoint_dir = os.path.dirname(settings.CHECKPOINT_PATH)
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir, exist_ok=True)

    # Check LLM provider
    if settings.LLM_PROVIDER not in ["openai", "anthropic"]:
        errors.append(f"Invalid LLM_PROVIDER: {settings.LLM_PROVIDER}")

    # Check port conflicts
    if settings.PORT == 8002:
        errors.append("Chat API port conflicts with Database API port (8002)")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    return True