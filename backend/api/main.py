"""
Chat API Main Application
FastAPI application for Chat and Supervisor services
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.api.core.config import settings, validate_settings
from backend.api.core.middleware import setup_middleware
from backend.api.core.dependencies import (
    get_supervisor_service,
    cleanup_dependencies
)
from backend.api.routes import (
    chat_router,
    sessions_router,
    health_router
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    try:
        # Validate settings
        validate_settings()
        logger.info("Configuration validated successfully")

        # Initialize supervisor service
        supervisor = await get_supervisor_service()
        logger.info("Supervisor service initialized")

        logger.info(f"Chat API started on port {settings.PORT}")
        logger.info(f"Database API URL: {settings.DATABASE_API_URL}")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Chat API...")

    try:
        await cleanup_dependencies()
        logger.info("Dependencies cleaned up successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

    logger.info("Chat API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Setup middleware
setup_middleware(app)

# Include routers
app.include_router(
    chat_router,
    prefix=f"{settings.API_PREFIX}/chat",
    tags=["Chat"]
)

app.include_router(
    sessions_router,
    prefix=f"{settings.API_PREFIX}/sessions",
    tags=["Sessions"]
)

app.include_router(
    health_router,
    prefix=f"{settings.API_PREFIX}/health",
    tags=["Health"]
)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint
    Returns basic API information
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health"
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "path": str(request.url),
            "method": request.method
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    """
    Run the application directly
    For development only - use uvicorn for production
    """
    import uvicorn

    logger.info(f"Running Chat API in development mode on port {settings.PORT}")

    uvicorn.run(
        "backend.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )