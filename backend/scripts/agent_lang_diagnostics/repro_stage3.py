"""stage3 todo_builder failed 원인 재현 — 삼켜진 실제 예외/프롬프트 크기 드러내기 (디버그용).

planner._build_todos 가 except 로 예외를 삼키고 None 반환(planner.py:535-537)하므로,
여기서 stage3 LLM 호출을 *그대로 복제*하되 예외를 traceback 으로 노출한다.
실행: python -m scripts.agent_lang_diagnostics.repro_stage3
"""
from __future__ import annotations

import asyncio
import json
import sys
import traceback
from pathlib import Path

_B = Path(__file__).resolve().parents[2]
if str(_B) not in sys.path:
    sys.path.insert(0, str(_B))
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.dream_agent.cognitive.cognitive_stage import cognitive_stage  # noqa: E402
from app.dream_agent.planning.planner import (  # noqa: E402
    Planner,
    Plan,
    _build_prompt,
    _get_agent_tools,
    _load_stage_prompt,
)
from app.dream_agent.schemas.structured_query import StructuredQuery  # noqa: E402

FAILING = [
    "4월 종합 성과 보고서 만들어줘",
    "모든 채널 수집해서 4월 모든 지표 분석하고 각각 ROAS 뽑고 소재별로 다시 표시한 다음 보고서로 써줘",
]


async def probe(q: str) -> None:
    print("\n" + "=" * 70 + f"\nQ: {q}")
    state = {"user_input": q, "language": "ko", "client_id": "clumi",
             "session_id": "repro", "conversation_history": [], "history_limit": 5}
    cmd = await cognitive_stage(state)
    sq = StructuredQuery.model_validate(cmd.update["structured_query"])
    p = Planner()
    sq_json = json.dumps(sq.model_dump(mode="json"), ensure_ascii=False, indent=2)
    teams = await p._select_teams(sq_json)
    agents = await p._select_agents(sq_json, teams)
    print(f"  teams={teams} agents={agents}")

    config = _load_stage_prompt("planning_stage3_todo.yaml")
    allow = p._has_text_intent(sq)
    agent_tools = _get_agent_tools(p._catalog, agents, allow_text=allow)
    sysp, usrp = _build_prompt(config, {
        "structured_query_json": sq_json,
        "agent_tools_json": json.dumps(agent_tools, ensure_ascii=False, indent=2),
    })
    print(f"  PROMPT len: system={len(sysp)} user={len(usrp)} (합={len(sysp)+len(usrp)})  agent_tools={len(agent_tools)}개")

    try:
        result = await p.client.generate_json(prompt=usrp, system_prompt=sysp)
        print(f"  generate_json OK — type={type(result).__name__} keys={list(result)[:8] if isinstance(result, dict) else 'N/A'}")
        raw = json.dumps(result, ensure_ascii=False)
        print(f"  result len={len(raw)}  head={raw[:400]}")
        try:
            Plan.model_validate(result)
            print("  Plan.model_validate OK")
        except Exception as e:  # noqa: BLE001
            print(f"  ★ Plan.model_validate FAILED: {type(e).__name__}: {str(e)[:300]}")
    except Exception as e:  # noqa: BLE001
        print(f"  ★ generate_json RAISED: {type(e).__name__}: {str(e)[:400]}")
        traceback.print_exc()


async def main() -> None:
    for q in FAILING:
        try:
            await probe(q)
        except Exception as e:  # noqa: BLE001
            print(f"  probe outer error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
