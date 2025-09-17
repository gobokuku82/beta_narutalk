"""
Health Check Routes
시스템 상태 확인 엔드포인트
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
import logging
import os

from backend.api.core.config import settings
from backend.api.core.dependencies import (
    get_supervisor_service,
    get_cache_manager,
    get_database_client,
    verify_dependencies
)
from backend.api.services.supervisor_service import SupervisorService
from backend.api.services.cache_manager import SQLiteMemoryCache
from backend.api.services.database_client import DatabaseAPIClient

logger = logging.getLogger(__name__)

# Router 생성
router = APIRouter(tags=["Health"])


@router.get("")
async def health_check():
    """
    기본 헬스 체크

    서비스가 실행 중인지 확인합니다.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/detailed")
async def detailed_health_check(
    supervisor: SupervisorService = Depends(get_supervisor_service),
    cache: SQLiteMemoryCache = Depends(get_cache_manager),
    db_client: DatabaseAPIClient = Depends(get_database_client)
):
    """
    상세 헬스 체크

    모든 시스템 컴포넌트의 상태를 확인합니다.
    """
    health_status = {
        "overall": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    # Supervisor 체크
    try:
        if supervisor:
            stats = supervisor.get_statistics()
            health_status["components"]["supervisor"] = {
                "status": "healthy",
                "active_sessions": stats["active_sessions"],
                "total_requests": stats["service_stats"].get("total_requests", 0)
            }
        else:
            health_status["components"]["supervisor"] = {
                "status": "unhealthy",
                "error": "Supervisor not initialized"
            }
            health_status["overall"] = "degraded"
    except Exception as e:
        health_status["components"]["supervisor"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "degraded"

    # Cache 체크
    try:
        if cache and settings.CACHE_ENABLED:
            cache_stats = cache.get_stats()
            health_status["components"]["cache"] = {
                "status": "healthy",
                "entries": cache_stats.get("total_entries", 0),
                "hit_rate": cache_stats.get("hit_rate", "0%")
            }
        else:
            health_status["components"]["cache"] = {
                "status": "disabled" if not settings.CACHE_ENABLED else "unhealthy"
            }
    except Exception as e:
        health_status["components"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "degraded"

    # Database API 체크
    try:
        if db_client:
            db_healthy = await db_client.health_check()
            health_status["components"]["database_api"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "url": settings.DATABASE_API_URL
            }
            if not db_healthy:
                health_status["overall"] = "degraded"
        else:
            health_status["components"]["database_api"] = {
                "status": "unhealthy",
                "error": "Database client not initialized"
            }
            health_status["overall"] = "degraded"
    except Exception as e:
        health_status["components"]["database_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "degraded"

    # Checkpoint 디렉토리 체크
    try:
        checkpoint_dir = os.path.dirname(settings.CHECKPOINT_PATH)
        if os.path.exists(checkpoint_dir):
            health_status["components"]["checkpoint"] = {
                "status": "healthy",
                "path": settings.CHECKPOINT_PATH
            }
        else:
            health_status["components"]["checkpoint"] = {
                "status": "unhealthy",
                "error": f"Directory not found: {checkpoint_dir}"
            }
            health_status["overall"] = "degraded"
    except Exception as e:
        health_status["components"]["checkpoint"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    return health_status


@router.get("/ready")
async def readiness_check():
    """
    준비 상태 체크

    서비스가 요청을 처리할 준비가 되었는지 확인합니다.
    """
    try:
        # 의존성 검증
        results = await verify_dependencies()

        all_ready = all(results.values())

        if all_ready:
            return {
                "ready": True,
                "status": "Service is ready",
                "components": results,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 일부 컴포넌트가 준비되지 않음
            return {
                "ready": False,
                "status": "Service is not fully ready",
                "components": results,
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "status": "Readiness check failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/live")
async def liveness_check():
    """
    생존 상태 체크

    서비스가 살아있는지 확인합니다.
    """
    return {
        "alive": True,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/cache/stats")
async def cache_statistics(
    cache: SQLiteMemoryCache = Depends(get_cache_manager)
):
    """
    캐시 통계 조회

    캐시 성능 및 사용 통계를 반환합니다.
    """
    if not cache or not settings.CACHE_ENABLED:
        return {
            "enabled": False,
            "message": "Cache is disabled"
        }

    try:
        stats = cache.get_stats()
        return {
            "enabled": True,
            "stats": stats,
            "config": {
                "ttl": settings.CACHE_TTL,
                "max_size": settings.CACHE_MAX_SIZE
            }
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "enabled": True,
            "error": str(e)
        }


@router.post("/cache/clear")
async def clear_cache(
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    캐시 초기화

    모든 캐시 항목을 삭제합니다.
    """
    try:
        await supervisor.clear_cache()
        return {
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }