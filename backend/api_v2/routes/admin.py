"""Admin Routes — 시스템 메타 노출 (개발자·workflow palette 용).

API path = /api/admin/...
client 무관 (시스템 차원).

Endpoints:
    GET /api/admin/catalog  — 90 tool 카탈로그 dump (workflow tool palette 의 데이터 source)
    GET /api/admin/clients  — 데이터 디렉토리 스캔 → 사용 가능 client 목록

spec: docs/_claude/architecture/frontend_dashboard1_2026-05-26.md §5 Step F7
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.core.logging import get_logger
from app.dream_agent.tools.registry import get_registry

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# repo root = backend/../
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _tool_to_dict(spec) -> dict[str, Any]:
    """ToolSpec → frontend 용 dict (가벼움)."""
    return {
        "name": spec.name,
        "description": spec.description,
        "category": str(spec.category.value) if hasattr(spec.category, "value") else str(spec.category),
        "parameters": [
            {
                "name": p.name,
                "type": str(p.type.value) if hasattr(p.type, "value") else str(p.type),
                "required": p.required,
                "default": p.default,
                "description": p.description,
            }
            for p in (spec.parameters or [])
        ],
        "produces": list(spec.produces or []),
        "dependencies": list(spec.dependencies or []),
        "timeout_sec": spec.timeout_sec,
        "requires_approval": spec.requires_approval,
        "has_cost": spec.has_cost,
    }


@router.get("/catalog", summary="90 tool 카탈로그 dump (workflow palette)")
async def get_catalog() -> dict[str, Any]:
    """전체 tool 메타 dump.

    frontend ToolPalette 가 본 endpoint 1회 호출 → 검색·필터·그룹.
    카테고리별 count + tools list.
    """
    reg = get_registry()
    tools = reg.get_all()
    tool_dicts = [_tool_to_dict(t) for t in tools]

    by_category: Counter = Counter(t["category"] for t in tool_dicts)
    # name 기준 정렬 (예측 가능)
    tool_dicts.sort(key=lambda t: (t["category"], t["name"]))

    return {
        "total": len(tool_dicts),
        "by_category": dict(by_category.most_common()),
        "tools": tool_dicts,
    }


@router.get("/clients", summary="data/ 디렉토리 스캔 → 사용 가능 client 목록")
async def get_clients() -> dict[str, Any]:
    """data/{client}/raw/ 가 존재하는 client 디렉토리 목록.

    frontend TopBar 드롭다운이 본 endpoint 호출 → AVAILABLE_CLIENTS 동적화 (POC 다음 단계).
    """
    data_dir = _REPO_ROOT / "data"
    if not data_dir.exists():
        return {"clients": [], "count": 0}

    clients = []
    for child in data_dir.iterdir():
        if not child.is_dir():
            continue
        # data/{name}/raw/ 가 있어야 사용 가능 client
        raw_dir = child / "raw"
        if raw_dir.exists() and raw_dir.is_dir():
            raw_count = sum(1 for _ in raw_dir.iterdir() if _.is_file())
            clients.append({
                "id": child.name,
                "name": child.name,
                "raw_count": raw_count,
            })

    clients.sort(key=lambda c: c["name"])
    return {"clients": clients, "count": len(clients)}
