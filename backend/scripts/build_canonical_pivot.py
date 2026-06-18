"""Canonical 피봇 정형 테이블 라이브 적재 — {client} schema에 12 테이블(normalized 6 + computed 5 + blended 1).

canonical_translator.execute(순수) → persist_all(write_relational_table, UPSERT) 로
`{client}.{source}_normalized`·`{source}_computed`·`blended_computed` 생성·적재.
ADD-only(CREATE IF NOT EXISTS·UPSERT) — 기존 _workspace/raw/serving 캐시 미접촉.

사용법:
    cd backend
    uv run python -m scripts.build_canonical_pivot --client clumi --period 2026-04 [--cleanup-orphans]

--cleanup-orphans: C-1(옛 prefix orphan typed 테이블 DROP). serving=_workspace라 무해(표시용 정리).
  ⚠ _workspace의 cleaned/computed 행(C-2)은 **건드리지 않음** — 운영 대시보드 라이브 캐시(P2까지 유지).

Status: complete — DB제작 라이브 적재 (2026-06-17).
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data_pg_util import connect  # noqa: E402
from app.dream_agent.models import ExecutionContext  # noqa: E402
from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator  # noqa: E402
from app.dream_agent.tools.registry import get_registry  # noqa: E402


def _table_names(client: str) -> set[str]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema=%s", (client,)
        )
        return {r[0] for r in cur.fetchall()}


def cleanup_orphans(client: str) -> list[str]:
    """C-1: _workspace/*_raw/*_normalized/*_computed/*_blended 외 옛 prefix orphan typed 테이블 DROP.

    serving은 _workspace 블롭을 읽으므로 typed 표시 테이블 DROP은 무해. (setup_data_db.cleanup_legacy와 동일 규칙)
    """
    from psycopg import sql
    from scripts.setup_data_db import LAYER_SUFFIXES

    names = _table_names(client)
    orphans = [t for t in names if t != "_workspace" and not t.endswith(LAYER_SUFFIXES)]
    with connect() as conn:
        for t in orphans:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                    sql.Identifier(client), sql.Identifier(t)))
        conn.commit()
    return orphans


async def build(client: str, period: str, do_cleanup: bool) -> None:
    print("=" * 60)
    print(f"Canonical 피봇 적재 — client={client} period={period}")
    print("=" * 60)
    before = _table_names(client)
    print(f"[0] 적재 전 테이블: {len(before)}개")

    tool = CanonicalTranslator(get_registry().get("canonical_translator"))
    ctx = ExecutionContext(session_id="build", plan_id="canonical_pivot", client_id=client)
    result = await tool.execute({"period": period}, ctx)

    print("[1] persist_all (normalized → computed → blended)")
    counts = tool.persist_all(result, client)
    for tbl, n in counts.items():
        print(f"    {tbl:<42} {n:>6} 행")

    if do_cleanup:
        print("[2] C-1 orphan typed 테이블 정리 (serving=_workspace 무해)")
        dropped = cleanup_orphans(client)
        print(f"    DROP {len(dropped)}개 (옛 prefix). _workspace cleaned/computed 행은 미접촉(C-2=P2).")

    after = _table_names(client)
    new_rel = sorted(t for t in after if t.endswith(("_normalized", "_computed", "_blended")))
    print(f"[3] 적재 후: 총 {len(after)}개 / 정형 {len(new_rel)}개")
    for t in new_rel:
        print(f"    ✓ {t}")
    # blended MER 확인
    mer = result["computed"]["mer"]
    tot = result["computed"]["total_marketing_cost_krw"]
    print(f"[4] blended 검증: total_marketing_cost={tot:,} · MER={mer}")
    print("완료.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", default="clumi")
    ap.add_argument("--period", default="2026-04")
    ap.add_argument("--cleanup-orphans", action="store_true",
                    help="C-1: 옛 prefix orphan typed 테이블 DROP (serving 무해)")
    a = ap.parse_args()
    asyncio.run(build(a.client, a.period, a.cleanup_orphans))


if __name__ == "__main__":
    main()
