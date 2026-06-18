"""복합쿼리 DAG 토폴로지 프로브 — task 수·병렬/직렬 모양·tool 재사용 실측 (2026-06-11).

사용자 질문(병렬-직렬-병렬-병렬 + tool 재등장 가능한가?)을 실측으로 답하기 위해,
각 쿼리를 cognitive→planning 돌려 *실제 plan DAG 모양*을 덤프:
  - n_todos / n_unique_tools / 재사용 tool(>1회)
  - 레벨별 폭(Kahn 위상정렬) = 병렬 폭, 레벨 수 = 직렬 깊이
  - cycle 여부
각 쿼리 2회 실행(LLM 비결정 노출). 실행만(execution 안 함) — plan 구조가 관심사.

실행 (backend/): python -m scripts.agent_lang_diagnostics.probe_dag_topology
"""
from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.dream_agent.cognitive.cognitive_stage import cognitive_stage  # noqa: E402
from app.dream_agent.planning.planner import Planner  # noqa: E402
from app.dream_agent.schemas.structured_query import StructuredQuery  # noqa: E402

_HERE = Path(__file__).resolve().parent


def _levels(todos: list, dag: dict) -> list[int]:
    """Kahn 위상정렬 레벨별 폭. depends_on 기반. cycle 이면 [] (불가)."""
    ids = [t.id for t in todos]
    deps = {t.id: [d for d in (t.depends_on or []) if d in ids] for t in todos}
    level: dict[str, int] = {}
    remaining = set(ids)
    guard = 0
    while remaining and guard < 200:
        guard += 1
        ready = [i for i in remaining if all(d in level for d in deps[i])]
        if not ready:
            return []   # cycle / unresolved
        lv = max((max((level[d] for d in deps[i]), default=-1) + 1 for i in ready), default=0)
        for i in ready:
            level[i] = max((level[d] for d in deps[i]), default=-1) + 1
        remaining -= set(ready)
    if not level:
        return []
    width = Counter(level.values())
    return [width[k] for k in sorted(width)]


async def _run_one(q: str, client: str, planner: Planner) -> dict:
    state = {"user_input": q, "language": "ko", "client_id": client,
             "session_id": "topo", "conversation_history": [], "history_limit": 5}
    cmd = await cognitive_stage(state)
    upd = getattr(cmd, "update", None) or {}
    if "structured_query" not in upd:
        return {"error": upd.get("error", "no sq")}
    sq = StructuredQuery.model_validate(upd["structured_query"])
    n_sub = len(sq.intent.sub_intents) if sq.intent else 0
    plan, issues = await planner.plan(sq)
    if plan is None:
        return {"error": f"plan None: {issues}"}
    tools = [t.tool for t in plan.todos]
    counts = Counter(t for t in tools if t)
    reused = {t: c for t, c in counts.items() if c > 1}
    shape = _levels(plan.todos, plan.dag)
    return {
        "op": sq.intent.operation if sq.intent else None,
        "n_sub": n_sub,
        "n_todos": len(plan.todos),
        "n_unique_tools": len(counts),
        "reused_tools": reused,
        "shape": shape,                       # 레벨별 폭: [3,1,2,1]=병렬3→1→병렬2→1
        "depth": len(shape),                  # 직렬 깊이
        "max_width": max(shape) if shape else 0,   # 최대 병렬 폭
        "cycle": shape == [] and len(plan.todos) > 0,
        "issues": issues,
        "tools": tools,
    }


async def main() -> None:
    corpus = yaml.safe_load((_HERE / "corpus_stress_topology.yaml").read_text(encoding="utf-8"))
    client = corpus.get("client", "clumi")
    planner = Planner()
    print(f"[topo] {len(corpus['queries'])} queries x2 runs, client={client}\n", flush=True)
    for item in corpus["queries"]:
        q, kind = item["q"], item.get("kind", "?")
        print(f"━━ {kind} ━━\n  Q: {q}")
        for run in (1, 2):
            rec = await _run_one(q, client, planner)
            if rec.get("error"):
                print(f"  run{run}: ERROR {rec['error'][:60]}")
                continue
            print(f"  run{run}: op={rec['op']} sub={rec['n_sub']} todos={rec['n_todos']} "
                  f"unique={rec['n_unique_tools']} 재사용={rec['reused_tools'] or '없음'}")
            print(f"        모양(레벨별폭)={rec['shape']} 깊이={rec['depth']} 최대병렬={rec['max_width']} "
                  f"{'⚠CYCLE' if rec['cycle'] else ''}{' ⚠'+str(rec['issues']) if rec['issues'] else ''}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
