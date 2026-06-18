"""Data Console API — `/api/data/*` (Postgres Data DB, schema-per-client 무-SQL 조회/삭제/수정).

client = schema. `octormate_data` DB의 client schema 데이터를 표로 보고/지우고/고친다.
프론트(`/db` 페이지)가 호출. System 콘솔(system_console.py)과 동일 패턴 + schema(client) 차원 추가.

안전: schema/table/column은 화이트리스트 검증 후 식별자 인용, 값은 파라미터라이즈드.
풀: app.state.data_db_pool (octormate_data) — System DB 풀과 별개.

Status: complete — Data 콘솔 V1 (2026-06-07). 조회/삭제/수정 + client(schema) selector.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from api_v2.routes.system_console import _SAFE_CAST_TYPES, _qi, _safe

router = APIRouter(prefix="/api/data", tags=["Data Console"])

_SYS_SCHEMAS = {"information_schema", "pg_catalog", "pg_toast", "public"}


def _pool(request: Request):
    pool = getattr(request.app.state, "data_db_pool", None)
    if pool is None:
        raise HTTPException(503, {
            "code": "DATA_DB_UNAVAILABLE",
            "message": "Data DB 풀이 없습니다 (octormate_data 미구축? `setup_data_db` 실행 확인).",
        })
    return pool


def _qt(schema: str, table: str) -> str:
    return f"{_qi(schema)}.{_qi(table)}"


async def _schemas(pool) -> list[str]:
    rows = await pool.fetch(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name NOT LIKE 'pg_%' ORDER BY schema_name"
    )
    return [r["schema_name"] for r in rows if r["schema_name"] not in _SYS_SCHEMAS]


async def _tables(pool, schema: str) -> list[str]:
    rows = await pool.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema=$1 AND table_type='BASE TABLE' ORDER BY table_name",
        schema,
    )
    return [r["table_name"] for r in rows]


async def _columns(pool, schema: str, table: str) -> list[dict[str, str]]:
    rows = await pool.fetch(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema=$1 AND table_name=$2 ORDER BY ordinal_position",
        schema, table,
    )
    return [{"name": r["column_name"], "type": r["data_type"]} for r in rows]


async def _pk_columns(pool, schema: str, table: str) -> list[str]:
    rows = await pool.fetch(
        "SELECT kcu.column_name FROM information_schema.table_constraints tc "
        "JOIN information_schema.key_column_usage kcu "
        "  ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema "
        "WHERE tc.constraint_type='PRIMARY KEY' AND tc.table_schema=$1 AND tc.table_name=$2 "
        "ORDER BY kcu.ordinal_position",
        schema, table,
    )
    return [r["column_name"] for r in rows]


async def _require_schema(pool, client: str) -> None:
    if client not in await _schemas(pool):
        raise HTTPException(404, {"code": "CLIENT_NOT_FOUND", "message": f"client(schema) '{client}' 없음"})


async def _require_table(pool, schema: str, table: str) -> None:
    if table not in await _tables(pool, schema):
        raise HTTPException(404, {"code": "TABLE_NOT_FOUND", "message": f"{schema}.{table} 없음"})


async def _pk_where(pool, schema: str, table: str, pk: dict[str, Any], start: int) -> tuple[str, list[Any]]:
    pks = await _pk_columns(pool, schema, table)
    if not pks:
        raise HTTPException(400, {"code": "NO_PRIMARY_KEY", "message": f"'{table}'에 기본키가 없어 행을 특정할 수 없습니다."})
    if set(pk.keys()) != set(pks):
        raise HTTPException(400, {"code": "PK_MISMATCH", "message": f"기본키 {pks} 값을 모두 보내야 합니다."})
    conds, args, i = [], [], start
    for col in pks:
        conds.append(f"{_qi(col)}::text = ${i}")
        args.append(str(pk[col]))
        i += 1
    return " AND ".join(conds), args


class DeleteRequest(BaseModel):
    pk: dict[str, Any]


class UpdateRequest(BaseModel):
    pk: dict[str, Any]
    updates: dict[str, Any]


# ── 엔드포인트 ──


@router.get("/clients", summary="client 목록 (= schema)")
async def get_clients(request: Request) -> dict[str, Any]:
    pool = _pool(request)
    out = []
    for s in await _schemas(pool):
        out.append({"name": s, "table_count": len(await _tables(pool, s))})
    return {"total": len(out), "clients": out}


@router.get("/{client}/tables", summary="client(schema) 테이블 목록 + 행 수")
async def get_tables(request: Request, client: str) -> dict[str, Any]:
    pool = _pool(request)
    await _require_schema(pool, client)
    out = []
    for name in await _tables(pool, client):
        count = await pool.fetchval(f"SELECT count(*) FROM {_qt(client, name)}")
        out.append({
            "name": name,
            "row_count": int(count),
            "pk_columns": await _pk_columns(pool, client, name),
        })
    return {"client": client, "total": len(out), "tables": out}


@router.get("/{client}/tables/{table}/rows", summary="행 조회 (페이지/검색)")
async def get_rows(
    request: Request,
    client: str,
    table: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None),
) -> dict[str, Any]:
    pool = _pool(request)
    await _require_schema(pool, client)
    await _require_table(pool, client, table)
    cols = await _columns(pool, client, table)
    qt = _qt(client, table)

    where, args = "", []
    if q:
        args.append(f"%{q}%")
        ors = " OR ".join(f"CAST({_qi(c['name'])} AS TEXT) ILIKE $1" for c in cols)
        where = f" WHERE ({ors})"

    total = await pool.fetchval(f"SELECT count(*) FROM {qt}{where}", *args)
    rows = await pool.fetch(
        f"SELECT * FROM {qt}{where} ORDER BY 1 LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}",
        *args, limit, offset,
    )
    return {
        "client": client,
        "table": table,
        "is_system": False,
        "columns": cols,
        "pk_columns": await _pk_columns(pool, client, table),
        "total": int(total),
        "rows": [{k: _safe(v) for k, v in dict(r).items()} for r in rows],
    }


@router.delete("/{client}/tables/{table}/rows", summary="행 삭제 (기본키)")
async def delete_row(request: Request, client: str, table: str, body: DeleteRequest) -> dict[str, Any]:
    pool = _pool(request)
    await _require_schema(pool, client)
    await _require_table(pool, client, table)
    where, args = await _pk_where(pool, client, table, body.pk, 1)
    result = await pool.execute(f"DELETE FROM {_qt(client, table)} WHERE {where}", *args)
    return {"deleted": int(result.split()[-1]) if result else 0}


@router.patch("/{client}/tables/{table}/rows", summary="행 수정 (기본키)")
async def update_row(request: Request, client: str, table: str, body: UpdateRequest) -> dict[str, Any]:
    pool = _pool(request)
    await _require_schema(pool, client)
    await _require_table(pool, client, table)
    if not body.updates:
        raise HTTPException(400, {"code": "NO_UPDATES", "message": "수정할 값이 없습니다."})

    coltypes = {c["name"]: c["type"] for c in await _columns(pool, client, table)}
    set_parts, args, i = [], [], 1
    for col, val in body.updates.items():
        if col not in coltypes:
            raise HTTPException(400, {"code": "BAD_COLUMN", "message": f"컬럼 '{col}' 없음"})
        if val is None:
            set_parts.append(f"{_qi(col)} = NULL")
            continue
        dtype = coltypes[col]
        if dtype not in _SAFE_CAST_TYPES:
            raise HTTPException(400, {"code": "UNSUPPORTED_TYPE", "message": f"'{col}'({dtype}) 타입은 편집 미지원."})
        set_parts.append(f"{_qi(col)} = ${i}::text::{dtype}")
        args.append(str(val))
        i += 1

    where, wargs = await _pk_where(pool, client, table, body.pk, i)
    args.extend(wargs)
    result = await pool.execute(
        f"UPDATE {_qt(client, table)} SET {', '.join(set_parts)} WHERE {where}", *args
    )
    return {"updated": int(result.split()[-1]) if result else 0}
