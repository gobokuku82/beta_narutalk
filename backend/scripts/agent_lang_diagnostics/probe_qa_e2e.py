"""QA end-to-end 프로브 — 질의응답 카테고리 구동 확인 (2026-06-10, 임시).

build_graph() 로 cognitive→planning→execution→response 전체를 헤드리스로 돌려,
Q&A 쿼리가 실제 답을 내고(데이터 파이프 우회) 데이터 쿼리는 그대로인지 확인.
require_review=False 로 HITL interrupt 우회. LLM 호출함.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.dream_agent.system_graph.builder import build_graph  # noqa: E402

QUERIES = [
    ("Q&A 정의", "ROAS가 뭐야?"),
    ("Q&A 시스템메타", "넌 뭐 할 수 있어?"),
    ("데이터(회귀)", "4월 매출 알려줘"),
]


async def main() -> None:
    graph = build_graph()
    for label, q in QUERIES:
        state = {
            "user_input": q, "language": "ko", "client_id": "clumi",
            "session_id": "probe_qa", "conversation_history": [], "history_limit": 5,
            "require_review": False,
        }
        try:
            out = await graph.ainvoke(state)
        except Exception as e:  # noqa: BLE001
            print(f"\n[{label}] {q}\n  ERROR: {type(e).__name__}: {e}")
            continue

        sq = out.get("structured_query") or {}
        intent = sq.get("intent") or {}
        tasks = [t.get("id") for t in sq.get("tasks", [])]
        plan = out.get("plan") or {}
        tools = [t.get("tool") for t in plan.get("todos", [])]
        payload = out.get("response") or out.get("response_payload") or {}
        text = payload.get("text") if isinstance(payload, dict) else None
        print(f"\n[{label}] {q}")
        print(f"  state keys: {list(out.keys())}")
        print(f"  op={intent.get('operation')} domain={intent.get('domain')} tasks={tasks}")
        print(f"  plan tools={tools}")
        exec_res = out.get("execution_result") or out.get("exec_result") or {}
        todos = exec_res.get("todos") if isinstance(exec_res, dict) else None
        if isinstance(todos, dict):
            for tid, r in todos.items():
                d = r.get("data") if isinstance(r, dict) else {}
                dkeys = list(d.keys()) if isinstance(d, dict) else d
                print(f"    todo {r.get('tool')}: status={r.get('status')} err={r.get('error')} data_keys={dkeys}")
                if isinstance(d, dict) and "answer" in d:
                    print(f"      answer={str(d.get('answer'))[:160]}")
        print(f"  response text: {str(text)[:200]}")


if __name__ == "__main__":
    asyncio.run(main())
