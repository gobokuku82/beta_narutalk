"""C2 — ②축(데이터 의미 전달) 할루시 측정 하네스 (2026-06-18).

라이브 4레이어(cognitive→planning→execution→response)를 헤드리스로 돌려,
응답이 canonical 정답을 *단위·의미* 틀리지 않고 전달하는지(②축)를 측정한다.
- 패턴: scripts/agent_lang_diagnostics/probe_qa_e2e.py (build_graph + ainvoke, LLM 실호출 + postgres canonical).
- 측정 대상 = ROADMAP §0.1 ②축: roas/mer=배수(%아님)·*_krw=원·함정라벨(salesAmt=비용).

판정(deterministic v1 — 보수적, 전체 trace도 저장해 수동 검토 가능):
  - exec_value     : execution_result 산출값 (= canonical ground truth, tool이 계산)
  - truth_in_resp  : 응답 텍스트에 정답 수치가 들어갔나
  - right_unit     : 응답에 올바른 단위 표기(배수/원/%)가 있나
  - wrong_unit     : 응답에 틀린 단위(예: roas를 %/원)로 표기했나  ← ②축 할루시 핵심
  - verdict        : OK / UNIT_HALLUCINATION / NUMBER_MISSING / EXEC_FAILED

사용: uv run python scripts/c2_hallucination_measure.py [N]   (N=앞에서 N개만, 기본 전체)
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.dream_agent.system_graph.builder import build_graph  # noqa: E402
from app.dream_agent.states.agent_state import init_agent_state  # noqa: E402

# ── ②축 코퍼스: canonical 정답이 명확하고 단위 함정이 있는 지표 ──
# truth = 문서·canonical 기준값(clumi.yaml glossary / re-baseline). unit = 올바른 단위.
# wrong_units = 이 지표에 쓰면 ②축 할루시인 단위 토큰.
CORPUS = [
    {"q": "clumi 4월 ROAS 알려줘", "metric": "roas", "truth": 4.46, "unit": "배수",
     "truth_strs": ["4.46", "4.5", "446%"], "right_unit": ["배", "배수"], "wrong_unit": ["%", "퍼센트", "원"]},
    {"q": "4월 MER 얼마야?", "metric": "mer", "truth": 4.46, "unit": "배수",
     "truth_strs": ["4.46", "4.5"], "right_unit": ["배", "배수"], "wrong_unit": ["%", "퍼센트", "원"]},
    {"q": "clumi 4월 CAC 알려줘", "metric": "cac", "truth": 44678, "unit": "원",
     "truth_strs": ["44,678", "44678", "44,700", "4.4만", "44.7"], "right_unit": ["원"], "wrong_unit": ["%", "배"]},
    {"q": "4월 총 광고비 얼마야?", "metric": "ad_cost", "truth": 26806923, "unit": "원",
     "truth_strs": ["26,806,923", "26806923", "2,680", "2680", "2,681", "26.8", "2680만", "2,681만"],
     "right_unit": ["원"], "wrong_unit": ["%", "배"]},
]


def _digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


def _extract_exec_values(exec_result: dict) -> dict:
    """execution_result.todos 의 data 에서 스칼라 수치 키만 추출 (ground truth 대조용)."""
    out: dict = {}
    todos = exec_result.get("todos") if isinstance(exec_result, dict) else None
    if not isinstance(todos, dict):
        return out
    for tid, r in todos.items():
        if not isinstance(r, dict):
            continue
        d = r.get("data")
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out[f"{r.get('tool')}.{k}"] = v
    return out


def _judge(case: dict, out: dict) -> dict:
    sq = out.get("structured_query") or {}
    intent = sq.get("intent") or {}
    plan = out.get("plan") or {}
    tools = [t.get("tool") for t in plan.get("todos", [])]
    exec_result = out.get("execution_result") or {}
    payload = out.get("response") or {}
    text = (payload.get("text") if isinstance(payload, dict) else str(payload)) or ""
    err = out.get("error")

    exec_vals = _extract_exec_values(exec_result)
    truth_in_resp = any(s in text for s in case["truth_strs"])

    # ★단위 판정 = 정답 수치 *바로 뒤* 인접 단위만 검사 (전역 등장 아님 — "원"이 매출용으로
    #   정당하게 나오는 false-positive 차단). 지표값에 붙은 단위가 맞나/틀리나가 ②축 핵심.
    right_unit, wrong_unit = False, []
    for ts in case["truth_strs"]:
        idx = text.find(ts)
        while idx >= 0:
            after = text[idx + len(ts): idx + len(ts) + 4]
            if any(after.lstrip().startswith(u) for u in case["right_unit"]):
                right_unit = True
            for u in case["wrong_unit"]:
                if after.lstrip().startswith(u):
                    wrong_unit.append(f"{ts}{u}")
            idx = text.find(ts, idx + 1)

    # verdict
    if err or (not exec_vals and not truth_in_resp):
        verdict = "EXEC_FAILED"
    elif not truth_in_resp:
        verdict = "NUMBER_MISSING"
    elif wrong_unit and not right_unit:
        verdict = "UNIT_HALLUCINATION"   # ★②축: 맞는 숫자인데 틀린 단위로 둔갑
    else:
        verdict = "OK"

    return {
        "query": case["q"], "metric": case["metric"], "truth": case["truth"], "unit": case["unit"],
        "op": intent.get("operation"), "domain": intent.get("domain"), "plan_tools": tools,
        "exec_values": exec_vals, "truth_in_resp": truth_in_resp,
        "right_unit": right_unit, "wrong_unit": wrong_unit, "error": err,
        "response_text": text, "verdict": verdict,
    }


async def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(CORPUS)
    cases = CORPUS[:limit]
    graph = build_graph()
    results = []
    for i, case in enumerate(cases):
        state = init_agent_state(
            user_input=case["q"], conversation_id="c2", turn_id=f"c2_{i}",
            client_id="clumi", require_review=False,
        )
        try:
            out = await graph.ainvoke(state)
        except Exception as e:  # noqa: BLE001
            results.append({"query": case["q"], "metric": case["metric"],
                            "verdict": "CRASH", "error": f"{type(e).__name__}: {e}"})
            print(f"[{i+1}/{len(cases)}] {case['q']}  → CRASH: {type(e).__name__}: {e}")
            continue
        j = _judge(case, out)
        results.append(j)
        print(f"[{i+1}/{len(cases)}] {case['q']}")
        print(f"    op={j['op']} domain={j['domain']} tools={j['plan_tools']}")
        print(f"    exec_values={j['exec_values']}")
        print(f"    verdict={j['verdict']} (truth_in_resp={j['truth_in_resp']} right_unit={j['right_unit']} wrong_unit={j['wrong_unit']})")
        print(f"    response: {j['response_text'][:240]}")

    # 요약
    from collections import Counter
    tally = Counter(r["verdict"] for r in results)
    print("\n=== ②축 할루시 측정 요약 ===")
    print(dict(tally))
    n_ok = tally.get("OK", 0)
    print(f"OK {n_ok}/{len(results)}  (②축 할루시 = UNIT_HALLUCINATION {tally.get('UNIT_HALLUCINATION',0)})")

    out_dir = _BACKEND.parent / "docs" / "_claude" / "4layer_system" / "diag_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "c2_hallucination_baseline.json"
    out_path.write_text(json.dumps({"results": results, "tally": dict(tally)},
                                   ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n저장: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
