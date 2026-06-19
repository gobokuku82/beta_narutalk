"""Health Check Routes (v2)

최소 health 엔드포인트. v1 의존성 없음.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter(prefix="/health", tags=["Health"])
logger = get_logger(__name__)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@router.get("/")
async def health() -> dict[str, Any]:
    """기본 health check (서버 응답 확인용)"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": "2.0.0-alpha",
        "timestamp": _iso_now(),
    }


@router.get("/detail")
async def health_detail() -> dict[str, Any]:
    """상세 health — 4-Layer 그래프 컴파일 가능 여부 확인"""
    checks: dict[str, Any] = {}

    # Graph compile check
    try:
        from app.dream_agent.system_graph.builder import build_graph
        build_graph()  # compile 성공하면 OK
        checks["graph"] = {"status": "ok", "message": "4-layer graph compiled"}
    except Exception as e:
        checks["graph"] = {"status": "error", "message": str(e)}

    # LLM client check
    try:
        from app.dream_agent.llm_manager import get_llm_client

        client = get_llm_client("cognitive")
        if client:
            checks["llm"] = {"status": "ok", "message": "LLM client available"}
        else:
            checks["llm"] = {"status": "error", "message": "LLM client not initialized"}
    except Exception as e:
        checks["llm"] = {"status": "error", "message": str(e)}

    # AgentPool check
    try:
        from app.dream_agent.execution.agent_pool import get_agent_pool

        pool = get_agent_pool()
        checks["agent_pool"] = {
            "status": "ok",
            "teams": len(pool.list_teams()),
            "agents": len(pool.list_agents()),
        }
    except Exception as e:
        checks["agent_pool"] = {"status": "error", "message": str(e)}

    overall = "ok" if all(c.get("status") == "ok" for c in checks.values()) else "error"

    return {
        "status": overall,
        "timestamp": _iso_now(),
        "checks": checks,
    }
