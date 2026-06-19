"""Data DB Setup — client 정형 데이터(schema-per-client)를 Postgres에 적재.

`dreamagent_data` DB 생성 + client별 schema + computed 적재 + 네이밍 정합(P5).
computed 적재는 **PostgresWorkspace.save 경유** → 파이프라인과 동일 네이밍(`computed_{key}`)
+ `_workspace` 진실행까지 일관. (이전: 자체 CREATE TABLE 로 prefix 없이 적재 → P5에서 통일)

client 추가 = `data/{client}/computed/` 폴더만 있으면 다음 실행 시 자동 schema 생성·적재.

사용법:
    cd backend
    uv run python -m scripts.setup_data_db

Status: complete — V2 (2026-06-07, P5 정합). computed=PostgresWorkspace 경유 + legacy(prefix없음) 정리.
"""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import psycopg
from psycopg import sql

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.core.config import settings

    DATA_DB_URI = settings.data_db_uri  # CHECKPOINT_DB_URI 자격증명 재사용 (db=dreamagent_data)
except Exception:
    DATA_DB_URI = "postgresql://postgres:postgres@localhost:5432/dreamagent_data"

from app.data_pg_util import connect  # noqa: E402  (data_db_uri 정규화 connection)
from app.data_layer.workspace.postgres import PostgresWorkspace  # noqa: E402

_uri = (
    DATA_DB_URI.replace("postgresql+psycopg", "postgresql").replace(
        "postgresql+asyncpg", "postgresql"
    )
)
_p = urlparse(_uri)
HOST = _p.hostname or "localhost"
PORT = _p.port or 5432
USER = _p.username or "postgres"
PW = _p.password or ""
DB = (_p.path or "/dreamagent_data").lstrip("/") or "dreamagent_data"

ADMIN = f"postgresql://{USER}:{PW}@{HOST}:{PORT}/postgres"
DATA_ROOT = project_root.parent / "data"  # backend/ → repo/ → data/
EXCLUDE = {"pipeline", "mock_api", "description"}  # client 아님
LAYER_SUFFIXES = ("_raw", "_normalized", "_computed", "_blended")  # 접미사 네이밍 (피봇 P1, 2026-06-17: prefix→suffix)


def create_database() -> None:
    print(f"[1] PostgreSQL 연결 ({HOST}:{PORT})")
    try:
        with psycopg.connect(ADMIN, autocommit=True) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB,))
            if cur.fetchone():
                print(f"    DB '{DB}' 이미 존재")
            else:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB)))
                print(f"    DB '{DB}' 생성 완료")
    except psycopg.OperationalError as e:
        print(f"    오류: PostgreSQL 연결 실패 - {e}")
        print("    PostgreSQL 서버 실행 여부를 확인하세요.")
        sys.exit(1)


def load_client_computed(ws: PostgresWorkspace, client: str) -> int:
    """data/{client}/computed/*.json → PostgresWorkspace.save("computed", ...).

    파이프라인과 동일 통로 → `{client}.{stem}_computed` 타입테이블 + `_workspace` 진실행.
    """
    cdir = DATA_ROOT / client / "computed"
    if not cdir.is_dir():
        return 0
    n = 0
    for f in sorted(cdir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            ws.save("computed", f.name, data, client=client)
            n += 1
        except Exception as e:
            print(f"    [skip] {client}/{f.name}: {e}")
    print(f"    schema '{client}': computed {n}건 적재 (*_computed + _workspace)")
    return n


def cleanup_legacy(conn, client: str) -> list[str]:
    """신 규칙(_workspace / *_raw / *_normalized / *_computed) 외 = 옛 적재본(구 prefix orphan 포함) → DROP."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema=%s", (client,)
        )
        names = [r[0] for r in cur.fetchall()]
    legacy = [
        t for t in names if t != "_workspace" and not t.endswith(LAYER_SUFFIXES)
    ]
    for t in legacy:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                    sql.Identifier(client), sql.Identifier(t)
                )
            )
    conn.commit()
    if legacy:
        print(f"    schema '{client}': legacy(prefix없음) {len(legacy)}개 정리")
    return legacy


def main() -> None:
    print("=" * 56)
    print("DreamAgent - Data DB Setup (schema-per-client, P5 네이밍 정합)")
    print("=" * 56)
    create_database()

    clients = [
        d.name
        for d in sorted(DATA_ROOT.iterdir())
        if d.is_dir() and d.name not in EXCLUDE and (d / "computed").is_dir()
    ]
    print(f"[2] clients (폴더=client): {clients}")

    ws = PostgresWorkspace()
    total, dropped = 0, 0
    for c in clients:
        total += load_client_computed(ws, c)
        with connect() as conn:
            dropped += len(cleanup_legacy(conn, c))
    print(
        f"\n완료 — schema {len(clients)}개, computed {total}개 적재 "
        f"(*_computed 일관), legacy {dropped}개 정리. DB={DB}"
    )


if __name__ == "__main__":
    main()
