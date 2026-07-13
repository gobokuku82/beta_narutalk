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

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger
from app.db_design.erd_build import build_sqlite, run_query

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


def _db_path(name: str) -> Path:
    return _STORE_DIR / f"{_safe_name(name)}.db"


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
async def delete_design(name: str):
    """설계 삭제 (빌드된 SQLite 도 함께 정리)."""
    for path in (_path(name), _db_path(name)):
        if path.exists():
            path.unlink()
    return Response(status_code=204)


# ── 실제 DB 빌드 & 검증 (SQLite) ──────────────────────────────────────────────
class BuildIn(BaseModel):
    """설계 + 엑셀에서 추출한 행 데이터. datasets 없는 테이블(차원 추출 마스터)은 DISTINCT 로 채움."""
    model_config = ConfigDict(extra="ignore")
    name: str
    tables: list[dict[str, Any]] = Field(default_factory=list)
    datasets: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class QueryIn(BaseModel):
    sql: str
    max_rows: int = 200


@router.post("/{name}/build")
async def build_design(name: str, body: BuildIn) -> dict[str, Any]:
    """설계 + 데이터 → SQLite(var/erd/<name>.db) 빌드 + 무결성 리포트."""
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        report = build_sqlite(
            {"name": body.name, "tables": body.tables}, body.datasets, str(_db_path(name))
        )
    except Exception as e:  # noqa: BLE001 — 빌드 실패는 사용자 메시지로
        logger.warning("db-design build failed", name=name, error=str(e))
        raise HTTPException(status_code=400, detail=f"build failed: {e}") from e
    logger.info("db-design built", name=name, tables=len(report.get("tables", [])))
    return report


@router.post("/{name}/query")
async def query_design(name: str, body: QueryIn) -> dict[str, Any]:
    """빌드된 DB 에 SELECT 쿼리 — '조립(JOIN)' 미리보기/탐색용."""
    db = _db_path(name)
    if not db.exists():
        raise HTTPException(status_code=404, detail="DB 가 아직 빌드되지 않았습니다")
    try:
        return run_query(str(db), body.sql, max_rows=max(1, min(body.max_rows, 1000)))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
