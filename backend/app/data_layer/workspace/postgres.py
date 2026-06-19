"""PostgresWorkspace — WorkspaceBackend의 Postgres 구현 (dreamagent_data, schema=client).

FileWorkspace와 동일 계약(save/load/exists/list_keys). sync psycopg 사용(ABC가 sync).

저장 구조:
  - 진실원천: {client}._workspace(layer, key, payload jsonb) — save한 dict 그대로 load (라운드트립 정확)
  - 표시용: {client}.{stem}_{layer} 타입 테이블 (접미사, 피봇 P1) (best-effort, /db 콘솔 표시)

도구·러너·DirectAPI는 get_default_workspace()로 가져다 쓰므로, set_workspace(PostgresWorkspace())
한 번이면 전체 파이프라인이 Postgres로 전환됨 (lifespan, P4).

Status: partial — P1. normalized/computed/raw payload 저장. (cleaned→normalized rename 2026-06-17)
"""
from __future__ import annotations

from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Json

from app.core.logging import get_logger
from app.data_pg_util import (
    STREAM_MARKER_KEY,
    connect,
    ensure_schema,
    ensure_workspace_table,
    extract_rows,
    jsonable,
    sanitize,
    stem,
    typed_table_name,
    write_jsonl_rows_streaming,
    write_typed_table,
)
from app.data_layer.workspace.base import Layer, WorkspaceBackend

logger = get_logger(__name__)

_WS = "_workspace"

# G28 (ADR-031-5): 이 크기 이상의 record 목록 save 는 blob 이 아니라 save_stream 으로 —
# blob 덮어쓰기가 기존 `__streamed__` 마커를 삼키고 행-테이블을 typed 콘솔 테이블로
# DROP/재생성해 pushdown 경로를 침묵 소멸시킨 실사고(2026-06-11 20:47, GA4 traffic) 재발 방지.
STREAM_ROUTE_THRESHOLD = 10_000


class PostgresWorkspace(WorkspaceBackend):
    def save(self, layer: Layer, key: str, data: Any, meta: dict | None = None, *, client: str) -> str:
        # G28: 마커 보존 라우팅 — ⓐ 대용량 record 목록 ⓑ 기존 항목이 스트리밍 마커.
        if isinstance(data, list) and data:
            route = len(data) >= STREAM_ROUTE_THRESHOLD
            if not route:
                try:
                    existing = self.load(layer, key, client=client)
                    route = isinstance(existing, dict) and STREAM_MARKER_KEY in existing
                except FileNotFoundError:
                    pass
            if route:
                logger.info("postgres workspace save → save_stream (G28 마커 보존)",
                            layer=layer, key=key, rows=len(data))
                return self.save_stream(layer, key, iter(data), client=client, meta=meta)
        with connect() as conn:
            ensure_schema(conn, client)
            ensure_workspace_table(conn, client)
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        "INSERT INTO {}.{} (layer, key, payload, meta) VALUES (%s, %s, %s, %s) "
                        "ON CONFLICT (layer, key) DO UPDATE SET "
                        "payload = EXCLUDED.payload, meta = EXCLUDED.meta, updated_at = now()"
                    ).format(sql.Identifier(client), sql.Identifier(_WS)),
                    (layer, key, Json(jsonable(data)), Json(jsonable(meta)) if meta else None),
                )
            conn.commit()
            # 표시용 타입 테이블 (실패해도 저장은 성립)
            try:
                rows = extract_rows(data)
                if rows:
                    write_typed_table(conn, client, typed_table_name(layer, key), rows)
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.warning("postgres workspace typed-table skip", layer=layer, key=key, error=str(e))
        return f"{client}.{_WS}[{layer}/{key}]"

    def save_stream(
        self, layer: Layer, key: str, records, *, client: str,
        batch_size: int = 2000, meta: dict | None = None,
    ) -> str:
        """대용량 record 스트림을 행-테이블로 배치 적재 (메모리 일정 — "호스" 방식).

        실데이터 → `{client}.{stem}_{layer}(_id, data jsonb)` 행별 저장.
        `_workspace` 에는 표식(marker)만 → load/get 시 이 테이블을 가리킴.
        FileWorkspace 엔 없는 Postgres 전용 메서드 (파일은 이미 스트리밍 가능).
        """
        table = typed_table_name(layer, key)
        with connect() as conn:
            ensure_schema(conn, client)
            ensure_workspace_table(conn, client)
            count = write_jsonl_rows_streaming(conn, client, table, records, batch_size)
            marker = {STREAM_MARKER_KEY: table, "format": "jsonl", "count": count}
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        "INSERT INTO {}.{} (layer, key, payload, meta) VALUES (%s, %s, %s, %s) "
                        "ON CONFLICT (layer, key) DO UPDATE SET "
                        "payload = EXCLUDED.payload, meta = EXCLUDED.meta, updated_at = now()"
                    ).format(sql.Identifier(client), sql.Identifier(_WS)),
                    (layer, key, Json(marker), Json(jsonable(meta)) if meta else None),
                )
            conn.commit()
        logger.info("postgres workspace save_stream", layer=layer, key=key, table=table, rows=count)
        return f"{client}.{table}[streamed {count} rows]"

    def load(self, layer: Layer, key: str, *, client: str) -> Any:
        try:
            with connect() as conn, conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT payload FROM {}.{} WHERE layer=%s AND key=%s").format(
                        sql.Identifier(client), sql.Identifier(_WS)
                    ),
                    (layer, key),
                )
                row = cur.fetchone()
        except psycopg.Error as e:
            raise FileNotFoundError(f"{client}/{layer}/{key}: {e}") from e
        if row is None:
            raise FileNotFoundError(f"{client}/{layer}/{key}")
        return row[0]

    def exists(self, layer: Layer, key: str, *, client: str) -> bool:
        try:
            with connect() as conn, conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT 1 FROM {}.{} WHERE layer=%s AND key=%s").format(
                        sql.Identifier(client), sql.Identifier(_WS)
                    ),
                    (layer, key),
                )
                return cur.fetchone() is not None
        except psycopg.Error:
            return False  # 스키마/테이블 미생성 = 캐시 미스로 취급 (파이프라인 안 막음)

    def list_keys(self, layer: Layer, prefix: str | None = None, *, client: str) -> list[str]:
        try:
            with connect() as conn, conn.cursor() as cur:
                base = sql.SQL("SELECT key FROM {}.{} WHERE layer=%s").format(
                    sql.Identifier(client), sql.Identifier(_WS)
                )
                if prefix:
                    cur.execute(base + sql.SQL(" AND key LIKE %s ORDER BY key"), (layer, f"{prefix}%"))
                else:
                    cur.execute(base + sql.SQL(" ORDER BY key"), (layer,))
                return [r[0] for r in cur.fetchall()]
        except psycopg.Error:
            return []
