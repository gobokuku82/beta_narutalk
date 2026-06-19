"""DB설계(ERD) 영속 라우트.

시스템 → DB설계 페이지의 설계(JSON)를 서버측에 영속. v1 = 설계 저장/복원만
(실제 dreamagent_data 적용은 범위 외 — 프론트에서 DDL 출력으로 수동).

저장소: <repo_root>/var/erd/<name>.json (파일 기반, DB 마이그레이션 불요).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger

router = APIRouter(prefix="/api/db-design", tags=["DB Design"])
logger = get_logger(__name__)

# <repo_root>/var/erd/  (db_design.py = backend/api/routes/ → parents[3] = repo root)
_STORE_DIR = Path(__file__).resolve().parents[3] / "var" / "erd"


def _safe_name(name: str) -> str:
    """파일명 안전화 — path traversal 차단 (영숫자/_/- 만 허용)."""
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", name).strip("_")
    if not safe:
        raise HTTPException(status_code=400, detail="invalid design name")
    return safe


def _path(name: str) -> Path:
    return _STORE_DIR / f"{_safe_name(name)}.json"


class ErdDesignIn(BaseModel):
    """프론트 store.ErdDesign 과 정합 (tables 는 opaque dict — 프론트 모델 진화 허용)."""
    model_config = ConfigDict(extra="ignore")
    name: str
    tables: list[dict[str, Any]] = Field(default_factory=list)


@router.get("")
async def list_designs() -> dict[str, list[str]]:
    """저장된 설계 이름 목록."""
    if not _STORE_DIR.exists():
        return {"names": []}
    names = sorted(p.stem for p in _STORE_DIR.glob("*.json"))
    return {"names": names}


@router.get("/{name}")
async def get_design(name: str) -> dict[str, Any]:
    """설계 조회 — 없으면 빈 설계(200) 반환(프론트가 신규로 시작)."""
    path = _path(name)
    if not path.exists():
        return {"name": name, "tables": [], "updated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"read failed: {e}") from e


@router.put("/{name}")
async def put_design(name: str, design: ErdDesignIn) -> dict[str, Any]:
    """설계 저장(덮어쓰기). updated_at 갱신 후 저장본 반환."""
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "name": design.name,
        "tables": design.tables,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    try:
        _path(name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"write failed: {e}") from e
    logger.info("db-design saved", name=name, tables=len(design.tables))
    return payload


@router.delete("/{name}", status_code=204)
async def delete_design(name: str) -> None:
    """설계 삭제."""
    path = _path(name)
    if path.exists():
        path.unlink()
