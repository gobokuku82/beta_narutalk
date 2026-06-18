"""System Console API — `/api/system/*` (Postgres System DB 무-SQL 조회/삭제/수정).

사용자가 SQL 없이 클릭으로 테이블 데이터를 보고/지우고/고치는 대시보드의 백엔드.
프론트(`features/system_console/`)가 이 엔드포인트만 호출 → 사용자는 SQL 0줄.

안전 원칙:
- 테이블/컬럼 이름은 information_schema 화이트리스트로 검증 후 식별자 인용 (인젝션 차단).
- 값은 전부 파라미터라이즈드 ($1..).
- 시스템 테이블(checkpoint* = langgraph 체크포인터)은 **읽기 전용** — 삭제/수정 차단
  (실행 중 에이전트 상태 손상 방지).

Status: complete — System 콘솔 (db_console→system_console 개명 2026-06-07). 조회/삭제/수정.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/system", tags=["System Console"])

# 시스템(읽기 전용) 테이블 prefix = langgraph 체크포인터.
_SYSTEM_PREFIXES = ("checkpoint",)

# 편집(수정) 시 text→타입 캐스팅 허용 목록 (information_schema.data_type 값).
_SAFE_CAST_TYPES = {
    "integer", "bigint", "smallint", "boolean", "numeric", "real",
    "double precision", "text", "character varying", "uuid",
    "json", "jsonb", "date",
    "timestamp without time zone", "timestamp with time zone",
}


# ─────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────


def _is_system(table: str) -> bool:
    return table.startswith(_SYSTEM_PREFIXES)


def _pool(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(503, {
            "code": "DB_POOL_UNAVAILABLE",
            "message": "DB 연결 풀이 없습니다 (서버 시작 로그 확인).",
        })
    return pool


def _qi(ident: str) -> str:
    """식별자 인용 (검증된 이름만 전달). 큰따옴표 이스케이프."""
    return '"' + ident.replace('"', '""') + '"'


def _safe(v: Any) -> Any:
    """JSON 직렬화 안전 변환 (UUID/datetime/Decimal/bytes 등)."""
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (bytes, memoryview)):
        return f"<{len(bytes(v))} bytes>"
    if isinstance(v, Decimal):
        return str(v)
    return str(v)


async def _list_tables(pool) -> list[str]:
    rows = await pool.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_type='BASE TABLE' "
        "ORDER BY table_name"
    )
    return [r["table_name"] for r in rows]


async def _pk_columns(pool, table: str) -> list[str]:
    rows = await pool.fetch(
        "SELECT kcu.column_name "
        "FROM information_schema.table_constraints tc "
        "JOIN information_schema.key_column_usage kcu "
        "  ON tc.constraint_name = kcu.constraint_name "
        " AND tc.table_schema = kcu.table_schema "
        "WHERE tc.constraint_type='PRIMARY KEY' "
        "  AND tc.table_schema='public' AND tc.table_name=$1 "
        "ORDER BY kcu.ordinal_position",
        table,
    )
    return [r["column_name"] for r in rows]


async def _columns(pool, table: str) -> list[dict[str, str]]:
    rows = await pool.fetch(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=$1 "
        "ORDER BY ordinal_position",
        table,
    )
    return [{"name": r["column_name"], "type": r["data_type"]} for r in rows]


async def _require_table(pool, table: str) -> None:
    if table not in await _list_tables(pool):
        raise HTTPException(404, {"code": "TABLE_NOT_FOUND", "message": f"테이블 '{table}' 없음"})


def _guard_writable(table: str) -> None:
    if _is_system(table):
        raise HTTPException(403, {
            "code": "READ_ONLY_SYSTEM_TABLE",
            "message": f"'{table}'는 시스템(체크포인터) 테이블이라 읽기 전용입니다.",
        })


async def _pk_where(pool, table: str, pk: dict[str, Any], start: int) -> tuple[str, list[Any]]:
    """기본키 매칭 WHERE 절 + 파라미터. 값은 ::text 비교로 타입 무관."""
    pks = await _pk_columns(pool, table)
    if not pks:
        raise HTTPException(400, {
            "code": "NO_PRIMARY_KEY",
            "message": f"'{table}'에 기본키가 없어 행을 특정할 수 없습니다.",
        })
    if set(pk.keys()) != set(pks):
        raise HTTPException(400, {
            "code": "PK_MISMATCH",
            "message": f"기본키 컬럼 {pks} 값을 모두 보내야 합니다.",
        })
    conds, args, i = [], [], start
    for col in pks:
        conds.append(f"{_qi(col)}::text = ${i}")
        args.append(str(pk[col]))
        i += 1
    return " AND ".join(conds), args


# ─────────────────────────────────────────────────────────────────
# 요청 모델
# ─────────────────────────────────────────────────────────────────


class DeleteRequest(BaseModel):
    pk: dict[str, Any]


class UpdateRequest(BaseModel):
    pk: dict[str, Any]
    updates: dict[str, Any]


# ─────────────────────────────────────────────────────────────────
# 엔드포인트
# ─────────────────────────────────────────────────────────────────


@router.get("/tables", summary="테이블 목록 + 행 수")
async def get_tables(request: Request) -> dict[str, Any]:
    pool = _pool(request)
    names = await _list_tables(pool)
    out = []
    for name in names:
        count = await pool.fetchval(f"SELECT count(*) FROM {_qi(name)}")
        out.append({
            "name": name,
            "row_count": int(count),
            "is_system": _is_system(name),
            "pk_columns": await _pk_columns(pool, name),
        })
    return {"total": len(out), "tables": out}


@router.get("/tables/{table}/rows", summary="행 조회 (페이지/검색)")
async def get_rows(
    request: Request,
    table: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None),
) -> dict[str, Any]:
    pool = _pool(request)
    await _require_table(pool, table)
    cols = await _columns(pool, table)
    qi = _qi(table)

    where, args = "", []
    if q:
        args.append(f"%{q}%")
        ors = " OR ".join(f"CAST({_qi(c['name'])} AS TEXT) ILIKE $1" for c in cols)
        where = f" WHERE ({ors})"

    total = await pool.fetchval(f"SELECT count(*) FROM {qi}{where}", *args)
    rows = await pool.fetch(
        f"SELECT * FROM {qi}{where} ORDER BY 1 LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}",
        *args, limit, offset,
    )
    data = [{k: _safe(v) for k, v in dict(r).items()} for r in rows]
    return {
        "table": table,
        "is_system": _is_system(table),
        "columns": cols,
        "pk_columns": await _pk_columns(pool, table),
        "total": int(total),
        "rows": data,
    }


@router.delete("/tables/{table}/rows", summary="행 삭제 (기본키)")
async def delete_row(request: Request, table: str, body: DeleteRequest) -> dict[str, Any]:
    pool = _pool(request)
    await _require_table(pool, table)
    _guard_writable(table)
    where, args = await _pk_where(pool, table, body.pk, 1)
    result = await pool.execute(f"DELETE FROM {_qi(table)} WHERE {where}", *args)
    return {"deleted": int(result.split()[-1]) if result else 0}


@router.patch("/tables/{table}/rows", summary="행 수정 (기본키)")
async def update_row(request: Request, table: str, body: UpdateRequest) -> dict[str, Any]:
    pool = _pool(request)
    await _require_table(pool, table)
    _guard_writable(table)
    if not body.updates:
        raise HTTPException(400, {"code": "NO_UPDATES", "message": "수정할 값이 없습니다."})

    coltypes = {c["name"]: c["type"] for c in await _columns(pool, table)}
    set_parts, args, i = [], [], 1
    for col, val in body.updates.items():
        if col not in coltypes:
            raise HTTPException(400, {"code": "BAD_COLUMN", "message": f"컬럼 '{col}' 없음"})
        if val is None:
            set_parts.append(f"{_qi(col)} = NULL")
            continue
        dtype = coltypes[col]
        if dtype not in _SAFE_CAST_TYPES:
            raise HTTPException(400, {
                "code": "UNSUPPORTED_TYPE",
                "message": f"'{col}'({dtype}) 타입은 편집 미지원입니다.",
            })
        set_parts.append(f"{_qi(col)} = ${i}::text::{dtype}")
        args.append(str(val))
        i += 1

    where, wargs = await _pk_where(pool, table, body.pk, i)
    args.extend(wargs)
    result = await pool.execute(
        f"UPDATE {_qi(table)} SET {', '.join(set_parts)} WHERE {where}", *args
    )
    return {"updated": int(result.split()[-1]) if result else 0}
