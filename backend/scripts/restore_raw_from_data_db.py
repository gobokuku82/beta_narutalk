"""data/clumi/raw 복구 — octormate_data `{client}._workspace`(layer='raw') → 파일 역직렬화.

2026-06-12 사고 복구용: worktree junction 정리 중 data/clumi/raw 가 삭제됨.
load_raw_to_data_db.py(항목①) 가 적재해 둔 Postgres 진실원천에서 역으로 파일을 재구성한다.

역변환 (FileDataSource.get 의 역):
  .csv  : payload(list[record]) → DataFrame → to_csv(utf-8-sig, index=False)
  .json : payload(dict/list)    → json.dump(ensure_ascii=False, indent=2)
  .jsonl: payload(list)         → 줄당 json.dumps
  .sql  : payload(str)          → 텍스트 그대로
  스트림 마커({__stream_table__}) : {client}.{stem}_raw 행 테이블 → 줄당 jsonl (server-side cursor)

주의: jsonb 는 키 순서를 보존하지 않으므로 CSV 컬럼 순서는 원본과 다를 수 있음.
      소비자는 전부 컬럼명 접근(pd.read_csv) — 기능 동등.

사용법: cd backend && python -m scripts.restore_raw_from_data_db [client]
"""
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd  # noqa: E402
import psycopg  # noqa: E402
from psycopg import sql  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.data_pg_util import STREAM_MARKER_KEY  # noqa: E402

REPO_ROOT = project_root.parent
# 삭제를 면한 원본 파일 — 덮어쓰지 않음 (원본이 비트 단위로 더 정확)
SKIP_EXISTING = True


def restore_client(conn: psycopg.Connection, client: str) -> None:
    raw_dir = REPO_ROOT / "data" / client / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("SELECT key, payload FROM {}.{} WHERE layer='raw' ORDER BY key").format(
                sql.Identifier(client), sql.Identifier("_workspace")
            )
        )
        rows = cur.fetchall()

    for key, payload in rows:
        path = raw_dir / key
        if SKIP_EXISTING and path.exists():
            print(f"  [keep]    {key} (원본 생존 — 건너뜀)")
            continue
        suffix = path.suffix.lower()
        if isinstance(payload, dict) and STREAM_MARKER_KEY in payload:
            table = payload[STREAM_MARKER_KEY]
            n = _restore_stream(conn, client, table, path)
            print(f"  [stream]  {key} ← {client}.{table} ({n} rows)")
        elif suffix == ".csv":
            df = pd.DataFrame(payload)
            df.to_csv(path, index=False, encoding="utf-8-sig")
            print(f"  [csv]     {key} ({len(df)} rows, {len(df.columns)} cols)")
        elif suffix == ".json":
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  [json]    {key}")
        elif suffix == ".jsonl":
            with path.open("w", encoding="utf-8") as f:
                for rec in payload:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"  [jsonl]   {key} ({len(payload)} lines)")
        elif suffix == ".sql":
            path.write_text(str(payload), encoding="utf-8")
            print(f"  [sql]     {key}")
        else:
            print(f"  [skip-??] {key} (unknown suffix {suffix})")


def _restore_stream(conn: psycopg.Connection, client: str, table: str, path: Path) -> int:
    n = 0
    with conn.cursor(name=f"restore_{table}") as cur, path.open("w", encoding="utf-8") as f:
        cur.itersize = 5000
        cur.execute(
            sql.SQL("SELECT data FROM {}.{} ORDER BY _id").format(
                sql.Identifier(client), sql.Identifier(table)
            )
        )
        for (data,) in cur:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
            n += 1
    return n


def main() -> None:
    client = sys.argv[1] if len(sys.argv) > 1 else "clumi"
    print(f"복구 시작: data/{client}/raw ← octormate_data {client}._workspace(raw)")
    with psycopg.connect(settings.data_db_uri) as conn:
        restore_client(conn, client)
    print("복구 완료")


if __name__ == "__main__":
    main()
