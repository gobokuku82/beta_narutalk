"""Postgres 데이터 영속화 공용 헬퍼 (sync psycopg).

Workspace/DataSource ABC가 sync 메서드라 **sync psycopg** 사용
(asyncpg는 async 콘솔 라우트 /api/data 전용 — 별개).

대상: `octormate_data` DB, schema = client.
진실원천: `{client}._workspace(layer, key, payload jsonb, meta jsonb)` — 라운드트립 정확.
추가: `{client}.{stem}_{layer}` 타입 테이블(best-effort, 접미사) — /db 콘솔 표시용.

Status: partial — P1 (2026-06-07). Workspace/DataSource 공용.
"""
from __future__ import annotations

import json
import math
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable, Iterator

import psycopg
from psycopg import sql
from psycopg.types.json import Json

from app.core.config import settings

# 대용량(스트리밍) 적재 표식 — _workspace.payload 에 이 키가 있으면 실데이터는 별도 행-테이블에 있음.
# {STREAM_MARKER_KEY: "raw_xxx"(테이블명), "format": "jsonl", "count": N}
STREAM_MARKER_KEY = "__streamed__"


def data_dsn() -> str:
    """data_db_uri를 psycopg가 받는 평범한 postgresql:// 로 정규화."""
    return (
        settings.data_db_uri.replace("postgresql+psycopg", "postgresql").replace(
            "postgresql+asyncpg", "postgresql"
        )
    )


def connect():
    return psycopg.connect(data_dsn())


def jsonable(v: Any) -> Any:
    """pandas/np/datetime/Decimal/NaN 등을 JSON 직렬화 가능 형태로."""
    if v is None or isinstance(v, (str, bool, int)):
        return v
    if isinstance(v, float):
        return None if math.isnan(v) else v
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, dict):
        return {str(k): jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    try:
        import pandas as pd

        if isinstance(v, pd.DataFrame):
            return [jsonable(r) for r in v.to_dict("records")]
        if pd.isna(v):  # numpy NaN/NaT scalar
            return None
    except Exception:
        pass
    return str(v)


def ensure_schema(conn, client: str) -> None:
    with conn.cursor() as cur:
        cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(client)))


def ensure_workspace_table(conn, client: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                "CREATE TABLE IF NOT EXISTS {}.{} ("
                "layer text, key text, payload jsonb, meta jsonb, "
                "updated_at timestamptz NOT NULL DEFAULT now(), "
                "PRIMARY KEY (layer, key))"
            ).format(sql.Identifier(client), sql.Identifier("_workspace"))
        )


_SAFE = re.compile(r"[^0-9a-zA-Z_]")


def sanitize(name: str) -> str:
    return _SAFE.sub("_", name) or "t"


def stem(key: str) -> str:
    return key.rsplit(".", 1)[0] if "." in key else key


def typed_table_name(layer: str, key: str) -> str:
    """typed/표시 테이블명 = {stem}_{layer} 접미사 (오너 규칙, 2026-06-17).

    예: layer='normalized', key='meta_ads_performance.json' → 'meta_ads_performance_normalized'.
    이전 prefix({layer}_{stem})에서 전환. read 측은 save_stream 마커가 테이블명을
    자기참조하므로 새 데이터는 코드 수정 0으로 정합 (단일 지점 SSOT).
    """
    return f"{sanitize(stem(key))}_{layer}"


# ── 정형(relational) 테이블 경계 — write_relational_table 전담, write_typed_table DROP 금지 (ADR-032 D1) ──
RELATIONAL_LAYERS = ("normalized", "computed", "blended")


def is_relational_table(table: str) -> bool:
    """정형 테이블(명시 스키마·UPSERT, write_relational_table 소유) 판정 — 접미사 규칙.

    True면 write_typed_table(추론타입·DROP+CREATE)이 건너뜀 → 정형 스키마/PK/lineage 보존.
    convention 판정(feedback_convention_over_hardcoding): layer 접미사 normalized/computed/blended.
    """
    return any(table.endswith("_" + lyr) for lyr in RELATIONAL_LAYERS)


def extract_rows(data: Any) -> list[dict]:
    """data → 표(rows) 추출. {rows:[...]}·list[dict]·DataFrame·flat dict 처리."""
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return [r for r in data["rows"] if isinstance(r, dict)]
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            return [jsonable(r) for r in data.to_dict("records")]
    except Exception:
        pass
    if isinstance(data, dict):
        return [data]
    return []


def infer_types(rows: list[dict]):
    cols, seen = [], set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                cols.append(k)
    types = {}
    for c in cols:
        vals = [r.get(c) for r in rows if r.get(c) is not None]
        if any(isinstance(v, (dict, list)) for v in vals):
            types[c] = "jsonb"
        elif vals and all(isinstance(v, bool) for v in vals):
            types[c] = "boolean"
        elif vals and all(isinstance(v, int) and not isinstance(v, bool) for v in vals):
            types[c] = "bigint"
        elif vals and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
            types[c] = "double precision"
        else:
            types[c] = "text"
    return cols, types


def _adapt(v: Any, t: str):
    if v is None:
        return None
    if t == "jsonb":
        return Json(jsonable(v))
    if t == "text":
        if isinstance(v, str):
            return v
        return json.dumps(jsonable(v), ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    if t in ("bigint", "double precision"):
        return None if (isinstance(v, float) and math.isnan(v)) else v
    return v


def write_typed_table(conn, client: str, table: str, rows: list[dict]) -> None:
    """rows를 타입 추론해 {client}.{table} 로 적재 (_id PK). /db 콘솔 표시용. (best-effort)"""
    if not rows:
        return
    if is_relational_table(table):   # ADR-032 D1 가드: 정형 테이블은 write_relational_table 전담 — DROP+추론 금지
        return
    cols, types = infer_types(rows)
    if not cols:
        return
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("DROP TABLE IF EXISTS {}.{}").format(sql.Identifier(client), sql.Identifier(table))
        )
        coldefs = sql.SQL(", ").join(
            [sql.SQL("_id bigint generated always as identity primary key")]
            + [sql.SQL("{} {}").format(sql.Identifier(c), sql.SQL(types[c])) for c in cols]
        )
        cur.execute(
            sql.SQL("CREATE TABLE {}.{} ({})").format(
                sql.Identifier(client), sql.Identifier(table), coldefs
            )
        )
        ins = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
            sql.Identifier(client),
            sql.Identifier(table),
            sql.SQL(", ").join(sql.Identifier(c) for c in cols),
            sql.SQL(", ").join(sql.Placeholder() for _ in cols),
        )
        for r in rows:
            cur.execute(ins, [_adapt(r.get(c), types[c]) for c in cols])


# ── 정형 relational 테이블 적재 (명시 스키마 + UPSERT, DROP 금지 — ADR-032 D1) ──

_REL_SQL_TYPE = {
    "int": "bigint", "float": "double precision", "text": "text",
    "date": "date", "datetime": "timestamptz", "jsonb": "jsonb",
}


def _rel_adapt(v: Any, t: str):
    """col_type별 값 어댑트 (UPSERT 파라미터). 결측 → None, jsonb → Json, 그 외 캐스팅."""
    if t == "jsonb":
        return Json(jsonable(v)) if v is not None else None
    if v is None or (isinstance(v, float) and math.isnan(v)) or v == "":
        return None
    if t == "int":
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None
    if t == "float":
        try:
            return float(v)
        except (ValueError, TypeError):
            return None
    return str(v)   # text/date/datetime — 문자열로 (psycopg 캐스팅)


def write_relational_table(
    conn, client: str, table: str, rows: list[dict], *,
    pk_cols: list[str], col_types: dict[str, str],
) -> int:
    """정형 relational 테이블 — 명시 스키마 CREATE IF NOT EXISTS + ON CONFLICT(pk) UPSERT.

    ADR-032 D1: DROP 절대 안 함(추론타입 write_typed_table과 namespace 분리). 소스별 상이 PK 파라미터화.
      rows      : list[dict] (행 단위)
      pk_cols   : PRIMARY KEY 컬럼 (소스별 상이 — meta=[campaign_id, report_date] 등)
      col_types : {col: 'int'|'float'|'text'|'date'|'datetime'|'jsonb'} — ERD를 SSOT로 선언
    반환: upsert 행수. (commit 포함 — 직접호출 패턴)
    """
    if not rows:
        return 0
    cols = list(col_types.keys())
    coldefs = sql.SQL(", ").join(
        sql.SQL("{} {}").format(sql.Identifier(c), sql.SQL(_REL_SQL_TYPE[col_types[c]])) for c in cols
    )
    pk = sql.SQL(", ").join(sql.Identifier(c) for c in pk_cols)
    non_pk = [c for c in cols if c not in pk_cols]
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("CREATE TABLE IF NOT EXISTS {}.{} ({}, PRIMARY KEY ({}))").format(
                sql.Identifier(client), sql.Identifier(table), coldefs, pk
            )
        )
        if non_pk:
            conflict = sql.SQL("ON CONFLICT ({}) DO UPDATE SET {}").format(
                pk, sql.SQL(", ").join(
                    sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(c), sql.Identifier(c)) for c in non_pk
                ),
            )
        else:
            conflict = sql.SQL("ON CONFLICT ({}) DO NOTHING").format(pk)
        ins = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({}) {}").format(
            sql.Identifier(client), sql.Identifier(table),
            sql.SQL(", ").join(sql.Identifier(c) for c in cols),
            sql.SQL(", ").join(sql.Placeholder() for _ in cols),
            conflict,
        )
        for r in rows:
            cur.execute(ins, [_rel_adapt(r.get(c), col_types[c]) for c in cols])
    conn.commit()
    return len(rows)


# ── 대용량 스트리밍 적재/조회 ("호스" 방식) ──
# 한 번에 전부 메모리에 올리지 않고, batch_size 만큼씩만 읽어 INSERT → 일정 메모리로 대용량 처리.

def write_jsonl_rows_streaming(
    conn, client: str, table: str, records: Iterable[dict], batch_size: int = 2000
) -> int:
    """records(반복가능 dict)를 `{client}.{table}(_id, data jsonb)` 에 배치로 스트리밍 적재.

    레코드 1개 = 행 1개(data jsonb). 메모리에는 최대 batch_size 개만 상주 → 252MB+ 파일도 OK.
    반환: 적재된 행 수.
    """
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("DROP TABLE IF EXISTS {}.{}").format(sql.Identifier(client), sql.Identifier(table))
        )
        cur.execute(
            sql.SQL(
                "CREATE TABLE {}.{} "
                "(_id bigint generated always as identity primary key, data jsonb)"
            ).format(sql.Identifier(client), sql.Identifier(table))
        )
        ins = sql.SQL("INSERT INTO {}.{} (data) VALUES (%s)").format(
            sql.Identifier(client), sql.Identifier(table)
        )
        count = 0
        batch: list[tuple] = []
        for rec in records:
            batch.append((Json(jsonable(rec)),))
            if len(batch) >= batch_size:
                cur.executemany(ins, batch)
                count += len(batch)
                batch.clear()
        if batch:
            cur.executemany(ins, batch)
            count += len(batch)
    return count


def iter_streamed_rows(client: str, table: str, itersize: int = 2000) -> Iterator[Any]:
    """`{client}.{table}.data` 를 server-side 커서로 한 행씩 yield (조회도 일정 메모리).

    별도 connection 을 열어 generator 수명 동안 유지 → 소비 측이 끝까지 돌면 자동 정리.
    """
    with connect() as conn:
        with conn.cursor(name=f"stream_{table}") as cur:
            cur.itersize = itersize
            cur.execute(
                sql.SQL("SELECT data FROM {}.{} ORDER BY _id").format(
                    sql.Identifier(client), sql.Identifier(table)
                )
            )
            for (rec,) in cur:
                yield rec
