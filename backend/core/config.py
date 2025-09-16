"""
Configuration management for the backend
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o"  # Using GPT-4o as default

    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./pharma_chatbot.db")
    DATABASE_ECHO: bool = False  # Set to True for SQL debugging

    # LangGraph Configuration
    USE_SQLITE_CHECKPOINTER: bool = False
    CHECKPOINT_DB_PATH: str = "checkpoints.db"

    # Cache Configuration
    CACHE_TTL_INTENT: int = 300  # 5 minutes
    CACHE_TTL_PLANNING: int = 300  # 5 minutes
    CACHE_TTL_DATA: int = 600  # 10 minutes

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Security Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # HuggingFace Configuration (if needed)
    HUGGINGFACE_TOKEN: Optional[str] = os.getenv("HUGGINGFACE_TOKEN")

    # Worker Configuration
    MAX_WORKERS: int = 4
    WORKER_TIMEOUT: int = 120  # seconds

    # LangGraph Node Timeouts
    TIMEOUT_INTENT_ANALYSIS: int = 30
    TIMEOUT_PLANNING: int = 30
    TIMEOUT_EXECUTION: int = 120
    TIMEOUT_EVALUATION: int = 20
    TIMEOUT_ITERATION: int = 10

    # Iteration Configuration
    MAX_ITERATIONS: int = 3
    QUALITY_THRESHOLD: float = 0.8

    # Mock Database Configuration
    MOCK_DB_ENABLED: bool = os.getenv("MOCK_DB_ENABLED", "true").lower() == "true"
    MOCK_DB_SEED_DATA: bool = os.getenv("MOCK_DB_SEED_DATA", "true").lower() == "true"

    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


# Helper functions
def get_openai_config():
    """Get OpenAI configuration"""
    return {
        "api_key": settings.OPENAI_API_KEY,
        "model": settings.OPENAI_MODEL,
        "temperature": 0
    }


def get_database_url():
    """Get database URL"""
    return settings.DATABASE_URL


def get_cache_config():
    """Get cache configuration"""
    return {
        "intent_analysis": {"ttl": settings.CACHE_TTL_INTENT},
        "planning": {"ttl": settings.CACHE_TTL_PLANNING},
        "data_analysis": {"ttl": settings.CACHE_TTL_DATA}
    }


def get_timeout_config():
    """Get timeout configuration"""
    return {
        "intent_analysis": settings.TIMEOUT_INTENT_ANALYSIS,
        "planning": settings.TIMEOUT_PLANNING,
        "execution": settings.TIMEOUT_EXECUTION,
        "evaluation": settings.TIMEOUT_EVALUATION,
        "iteration": settings.TIMEOUT_ITERATION
    }


# Export settings
__all__ = [
    "settings",
    "get_openai_config",
    "get_database_url",
    "get_cache_config",
    "get_timeout_config"
]