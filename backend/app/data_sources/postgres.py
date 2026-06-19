"""PostgresDataSource — DataSource 의 Postgres 구현 (raw 읽기, dreamagent_data, schema=client).

FileDataSource 와 동일 계약(get/list_sources/has). raw 는 `{client}._workspace`(layer='raw')
에서 읽어 **확장자별로 FileDataSource.get 과 동일한 타입으로 복원** → 하위 도구 불변.

복원 규약 (FileDataSource.get 과 1:1):
    .csv   → pandas.DataFrame   (payload = records list)
    .json  → dict | list        (payload 그대로)
    .jsonl → list[dict]         (payload 그대로)
    .sql   → str                (payload 그대로)

raw 적재 경로 (둘 다 같은 _workspace 테이블에 layer='raw' 로 들어옴):
    - External 수집기: ExternalRawCollectorBase._fetch_from_mock_api → workspace.save("raw", ...)
    - Internal/일괄: scripts/load_raw_to_data_db.py (파일 → dreamagent_data raw 적재)

set_data_source(PostgresDataSource()) 한 번이면 도구·러너가 전부 Postgres raw 를 읽음 (lifespan, P4).

Status: partial — P2 (2026-06-07). raw 읽기. (normalized/computed 산출은 PostgresWorkspace 담당)
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from psycopg import sql

from app.core.logging import get_logger
from app.data_pg_util import STREAM_MARKER_KEY, connect, iter_streamed_rows
from app.data_sources.base import DataSource, DataSourceError, DataSourceNotFound, _PREFIX_OP
from app.data_sources.file import SOURCE_REGISTRY
from app.workspace.postgres import PostgresWorkspace

logger = get_logger(__name__)

_RAW = "raw"


class PostgresDataSource(DataSource):
    """dreamagent_data `{client}._workspace`(layer='raw') 기반 DataSource.

    raw 쓰기는 Workspace(PostgresWorkspace)·수집기·적재 스크립트가 담당.
    본 클래스는 *읽기*(get/list_sources/has)만 — FileDataSource 와 대칭.
    """

    def __init__(self, workspace: PostgresWorkspace | None = None):
        # raw 읽기를 위해 PostgresWorkspace.load/exists/list_keys 재사용 (같은 _workspace 테이블).
        self._ws = workspace or PostgresWorkspace()

    # ── DataSource 구현 ──
    def get(self, client: str, source_id: str) -> Any:
        spec = SOURCE_REGISTRY.get(source_id)
        if spec is None:
            raise DataSourceNotFound(
                f"source_id '{source_id}' not in SOURCE_REGISTRY "
                f"(registered: {sorted(SOURCE_REGISTRY.keys())})"
            )
        try:
            payload = self._ws.load(_RAW, spec.filename, client=client)
        except FileNotFoundError as e:
            raise DataSourceNotFound(
                f"raw not found in postgres: client={client} source_id={source_id} "
                f"key={spec.filename} ({e})"
            ) from e

        # 대용량 스트리밍 적재본 → 행-테이블에서 전체 list[dict] 복원 (.jsonl 계약).
        if isinstance(payload, dict) and payload.get(STREAM_MARKER_KEY):
            data: Any = list(iter_streamed_rows(client, payload[STREAM_MARKER_KEY]))
        else:
            data = self._reconstruct(spec.filename, payload)
        logger.info(
            "data_source.get", backend="postgres", client=client,
            source_id=source_id, key=spec.filename, type=type(data).__name__,
        )
        return data

    def stream_jsonl(self, client: str, source_id: str) -> Any:
        """대용량 jsonl 을 record 단위 yield — FileDataSource.stream_jsonl 대칭 (메모리 일정).

        스트리밍 적재본 → server-side 커서로 한 행씩. 소형 blob 저장본 → payload 순회.
        consumer: kst_timezone_normalizer · ga4_session_aggregator (DATA_BACKEND=postgres 시 필수).
        """
        spec = SOURCE_REGISTRY.get(source_id)
        if spec is None:
            raise DataSourceNotFound(f"source_id '{source_id}' not in SOURCE_REGISTRY")
        try:
            payload = self._ws.load(_RAW, spec.filename, client=client)
        except FileNotFoundError as e:
            raise DataSourceNotFound(
                f"raw not found in postgres: client={client} source_id={source_id}"
            ) from e
        if isinstance(payload, dict) and payload.get(STREAM_MARKER_KEY):
            yield from iter_streamed_rows(client, payload[STREAM_MARKER_KEY])
        elif isinstance(payload, list):
            yield from payload  # 소형 jsonl 은 blob 으로 저장됨
        else:
            raise DataSourceNotFound(
                f"stream_jsonl: '{source_id}' 는 jsonl 형식 아님 (key={spec.filename})"
            )

    def has(self, client: str, source_id: str) -> bool:
        spec = SOURCE_REGISTRY.get(source_id)
        if spec is None:
            return False
        return self._ws.exists(_RAW, spec.filename, client=client)

    def list_sources(self, client: str) -> list[str]:
        keys = set(self._ws.list_keys(_RAW, client=client))
        return sorted(sid for sid, spec in SOURCE_REGISTRY.items() if spec.filename in keys)

    # ── pushdown v1 (ADR-031): 행-테이블 소스만 SQL — blob 은 기본 구현 fallback ──

    def _stream_table(self, client: str, source_id: str) -> tuple[str, list[str] | None] | None:
        """마커 소스면 (테이블명, typed 컬럼목록 | None=generic). 마커 아니면 None (fallback).

        두 모양 인지 (계획 §8 V1 실측): generic `(_id, data jsonb)` / typed (수집·적재 경로별).
        마커가 가리키는 테이블 부재 = 깨진 상태 → 시끄럽게 (V2 침묵 소멸 재발 감지).
        """
        spec = SOURCE_REGISTRY.get(source_id)
        if spec is None:
            raise DataSourceNotFound(f"source_id '{source_id}' not in SOURCE_REGISTRY")
        try:
            payload = self._ws.load(_RAW, spec.filename, client=client)
        except FileNotFoundError:
            return None   # 미존재 — 기본 구현 경로가 동일 에러를 내게 위임
        if not (isinstance(payload, dict) and payload.get(STREAM_MARKER_KEY)):
            return None   # blob — 소형이라 SQL 이득 0 (계획 §1)
        table = payload[STREAM_MARKER_KEY]
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position",
                (client, table),
            )
            cols = [r[0] for r in cur.fetchall()]
        if not cols:
            raise DataSourceNotFound(
                f"stream marker 가 가리키는 행-테이블 부재: {client}.{table} "
                f"(G28 — 마커/테이블 침묵 소멸 의심)"
            )
        return (table, None) if cols == ["_id", "data"] else (table, cols)

    @staticmethod
    def _where_sql(where: dict | None, typed_cols: list[str] | None):
        """where dict → (SQL 조건 list, params, impossible). typed 에서 미지 컬럼 = 불일치(빈 결과)."""
        conds: list[sql.Composable] = []
        params: list[Any] = []
        for k, v in (where or {}).items():
            prefix = k.endswith(_PREFIX_OP)
            col = k[: -len(_PREFIX_OP)] if prefix else k
            if typed_cols is None:   # generic — jsonb 키는 값 바인딩 (인젝션 불가, ::text 로 타입 확정)
                lhs = sql.SQL("data->>(%s::text)")
                params_lhs = [col]
            else:
                if col not in typed_cols:
                    return [], [], True   # Python 의미론: 부재 컬럼은 어떤 조건과도 불일치
                lhs = sql.SQL("{}::text").format(sql.Identifier(col))
                params_lhs = []
            if prefix:
                conds.append(sql.SQL("starts_with(") + lhs + sql.SQL(", %s)"))
            else:
                conds.append(lhs + sql.SQL(" = %s"))
            params.extend(params_lhs + [str(v)])
        return conds, params, False

    def query_iter(
        self, client: str, source_id: str, *,
        where: dict | None = None, columns: list[str] | None = None,
    ):
        """query 의 스트리밍 형태 — 행-테이블이면 server-side 커서로 SQL pushdown (피크 메모리 일정)."""
        st = self._stream_table(client, source_id)
        if st is None:
            yield from super().query_iter(client, source_id, where=where, columns=columns)
            return
        table, typed_cols = st
        conds, params, impossible = self._where_sql(where, typed_cols)
        if impossible:
            return

        target: list[str] | None = None
        if typed_cols is None:
            if columns:
                pairs = sql.SQL(", ").join(sql.SQL("%s::text, data->(%s::text)") for _ in columns)
                select = sql.SQL("jsonb_build_object(") + pairs + sql.SQL(")")
                params = [x for c in columns for x in (c, c)] + params
            else:
                select = sql.SQL("data")
        else:
            target = columns or [c for c in typed_cols if c != "_id"]
            select = sql.SQL(", ").join(
                sql.Identifier(c) if c in typed_cols
                else sql.SQL("NULL AS {}").format(sql.Identifier(c))
                for c in target
            )

        q = sql.SQL("SELECT ") + select + sql.SQL(" FROM {}.{}").format(
            sql.Identifier(client), sql.Identifier(table))
        if conds:
            q = q + sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conds)
        q = q + sql.SQL(" ORDER BY _id")

        logger.info("data_source.query", backend="postgres", client=client,
                    source_id=source_id, table=table, pushdown=True)
        with connect() as conn:
            with conn.cursor(name=f"dsq_{table}") as cur:
                cur.itersize = 2000
                cur.execute(q, params)
                for row in cur:
                    yield row[0] if target is None else dict(zip(target, row))

    def query(
        self, client: str, source_id: str, *,
        where: dict | None = None, columns: list[str] | None = None,
    ) -> list[dict]:
        return list(self.query_iter(client, source_id, where=where, columns=columns))

    def aggregate(
        self, client: str, source_id: str, *,
        op: str = "count", column: str | None = None,
        by: str | None = None, where: dict | None = None,
    ) -> Any:
        if op not in ("count", "sum"):
            raise DataSourceError(f"aggregate: 미지원 op '{op}' (v1 = count/sum)")
        if op == "sum" and not column:
            raise DataSourceError("aggregate: op=sum 은 column 필수")
        st = self._stream_table(client, source_id)
        if st is None:
            return super().aggregate(client, source_id, op=op, column=column, by=by, where=where)
        table, typed_cols = st
        conds, params, impossible = self._where_sql(where, typed_cols)
        if impossible:
            return ({} if by is not None else (0 if op == "count" else 0.0))

        def _val_expr(col: str) -> tuple[sql.Composable, list]:
            if typed_cols is None:
                return sql.SQL("(data->>(%s::text))::numeric"), [col]
            if col not in typed_cols:
                return sql.SQL("NULL::numeric"), []   # 부재 컬럼 = 전부 None → sum 0
            return sql.SQL("{}::numeric").format(sql.Identifier(col)), []

        if op == "count":
            agg = sql.SQL("count(*)")
            agg_params: list = []
        elif by is None:
            expr, agg_params = _val_expr(column)        # type: ignore[arg-type]
            agg = sql.SQL("COALESCE(sum(") + expr + sql.SQL("), 0)")
        else:
            # by-그룹 sum: 전부-NULL 그룹은 그룹 자체가 없어야 함 (Python 의미론 — 0.0 날조 금지).
            expr, agg_params = _val_expr(column)        # type: ignore[arg-type]
            agg = sql.SQL("sum(") + expr + sql.SQL(")")

        if by is None:
            q = sql.SQL("SELECT ") + agg + sql.SQL(" FROM {}.{}").format(
                sql.Identifier(client), sql.Identifier(table))
            all_params = agg_params + params
        else:
            if typed_cols is None:
                grp = sql.SQL("data->>(%s::text)")
                grp_params = [by]
            elif by in typed_cols:
                grp = sql.SQL("{}::text").format(sql.Identifier(by))
                grp_params = []
            else:
                grp = sql.SQL("NULL::text")             # 부재 그룹 컬럼 → 전부 None 그룹
                grp_params = []
            q = (sql.SQL("SELECT ") + grp + sql.SQL(" AS g, ") + agg
                 + sql.SQL(" FROM {}.{}").format(sql.Identifier(client), sql.Identifier(table)))
            all_params = grp_params + agg_params + params

        if conds:
            q = q + sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conds)
        if by is not None:
            q = q + sql.SQL(" GROUP BY 1")

        with connect() as conn, conn.cursor() as cur:
            cur.execute(q, all_params)
            rows = cur.fetchall()
        logger.info("data_source.aggregate", backend="postgres", client=client,
                    source_id=source_id, table=table, op=op, by=by, pushdown=True)

        def _num(v: Any) -> Any:
            if isinstance(v, Decimal):
                v = float(v)
            return int(v) if op == "count" else float(v)

        if by is None:
            return _num(rows[0][0])
        return {g: _num(v) for g, v in rows if v is not None}

    # ── 복원 (확장자 → FileDataSource.get 과 동일 타입) ──
    @staticmethod
    def _reconstruct(filename: str, payload: Any) -> Any:
        ext = Path(filename).suffix.lower()
        if ext == ".csv":
            # payload = records list(jsonable). DataFrame 복원 (빈 경우 빈 프레임).
            return pd.DataFrame(payload if isinstance(payload, list) else [])
        if ext in (".json", ".jsonl"):
            # .json → dict|list, .jsonl → list[dict] — payload 그대로 (jsonb 라운드트립).
            return payload
        if ext == ".sql":
            return payload if isinstance(payload, str) else str(payload)
        raise DataSourceNotFound(f"unsupported extension: {ext} (file={filename})")


__all__ = ["PostgresDataSource"]
