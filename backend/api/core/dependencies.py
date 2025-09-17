"""
Dependency Injection for FastAPI
"""

from typing import Optional
import logging
from functools import lru_cache

from .config import settings

logger = logging.getLogger(__name__)

# Global instances (singleton pattern)
_supervisor_service = None
_cache_manager = None
_database_client = None


@lru_cache()
async def get_supervisor_service():
    """
    Get or create Supervisor Service instance (singleton)

    Returns:
        SupervisorService instance
    """
    global _supervisor_service

    if _supervisor_service is None:
        from backend.api.services.supervisor_service import SupervisorService

        _supervisor_service = SupervisorService(
            llm_provider=settings.LLM_PROVIDER,
            model_name=settings.LLM_MODEL,
            checkpoint_path=settings.CHECKPOINT_PATH,
            enable_cache=settings.CACHE_ENABLED,
            cache_ttl=settings.CACHE_TTL
        )

        await _supervisor_service.initialize()
        logger.info("SupervisorService initialized")

    return _supervisor_service


@lru_cache()
def get_cache_manager():
    """
    Get or create Cache Manager instance (singleton)

    Returns:
        SQLiteMemoryCache instance
    """
    global _cache_manager

    if _cache_manager is None and settings.CACHE_ENABLED:
        from backend.api.services.cache_manager import SQLiteMemoryCache

        _cache_manager = SQLiteMemoryCache(
            default_ttl=settings.CACHE_TTL,
            max_size=settings.CACHE_MAX_SIZE
        )
        logger.info("Cache Manager initialized")

    return _cache_manager


@lru_cache()
def get_database_client():
    """
    Get or create Database API Client instance (singleton)

    Returns:
        DatabaseAPIClient instance
    """
    global _database_client

    if _database_client is None:
        from backend.api.services.database_client import DatabaseAPIClient

        _database_client = DatabaseAPIClient(
            base_url=settings.DATABASE_API_URL,
            timeout=settings.DATABASE_API_TIMEOUT,
            max_retries=settings.MAX_RETRIES
        )
        logger.info(f"Database API Client initialized: {settings.DATABASE_API_URL}")

    return _database_client


async def verify_dependencies():
    """
    Verify all dependencies are working

    Returns:
        Dict with verification results
    """
    results = {
        "supervisor": False,
        "cache": False,
        "database_api": False
    }

    try:
        # Check Supervisor
        supervisor = await get_supervisor_service()
        if supervisor:
            results["supervisor"] = True
    except Exception as e:
        logger.error(f"Supervisor verification failed: {e}")

    try:
        # Check Cache
        if settings.CACHE_ENABLED:
            cache = get_cache_manager()
            if cache:
                await cache.set("test_key", "test_value", ttl=10)
                value = await cache.get("test_key")
                results["cache"] = value == "test_value"
                await cache.delete("test_key")
        else:
            results["cache"] = True  # Cache is disabled, so mark as OK
    except Exception as e:
        logger.error(f"Cache verification failed: {e}")

    try:
        # Check Database API
        db_client = get_database_client()
        if db_client:
            health = await db_client.health_check()
            results["database_api"] = health
    except Exception as e:
        logger.error(f"Database API verification failed: {e}")

    return results


async def cleanup_dependencies():
    """
    Cleanup all dependencies on shutdown
    """
    global _supervisor_service, _cache_manager, _database_client

    if _supervisor_service:
        await _supervisor_service.shutdown()
        _supervisor_service = None
        logger.info("SupervisorService shutdown")

    if _cache_manager:
        _cache_manager.close()
        _cache_manager = None
        logger.info("Cache Manager closed")

    if _database_client:
        await _database_client.close()
        _database_client = None
        logger.info("Database API Client closed")