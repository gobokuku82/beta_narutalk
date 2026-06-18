"""Sprint 14 A3 D-14 — NL 편집 LLM 성공률 측정 스크립트.

Status: complete — Sprint 14 A3 Phase 5.

실행:
  OPENAI_API_KEY=sk-... uv run python backend/scripts/a3_nl_success_rate.py

결과:
  logs/a3_nl_success_rate_<timestamp>.jsonl
  - 필드: {input, parsed_action, success, latency_ms, error_type}

판정 trigger (plan v0.4 Phase 9):
  - 실패율 < 3%: Y-a 유지
  - 실패율 ≥ 3%: γ (multi-turn) 재평가 trigger
  - 실패율 ≥ 10%: A3 범위 재설계 (Y-a → Y-c)

입력 케이스 (다양한 표현 10종 × 10회 = 100회):
  1. "4번 삭제"
  2. "3-4 순서 바꿔"
  3. "첫 번째 Todo 의 task 를 X 로 수정"
  4. "마지막에 Y 추가"
  5. "todo_002 를 삭제해주세요"
  6. "2번이랑 3번 자리 바꿔"
  7. "첫 번째 작업의 priority 를 10 으로"
  8. "3번 뒤에 새 작업 insert"
  9. "2번 제거"
  10. "agent를 sentiment_analyzer 로 변경"
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# backend path 추가
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.dream_agent.planning.planner import Plan, PlannedTodo
from app.dream_agent.workflow_managers.hitl_manager.plan_editor import PlanEditor


# 10종 입력 × 10회 반복
INPUT_CASES = [
    "4번 삭제",
    "3-4 순서 바꿔",
    "첫 번째 Todo 의 task 를 요약으로 수정",
    "마지막에 PDF 렌더링 추가",
    "todo_002 를 삭제해주세요",
    "2번이랑 3번 자리 바꿔",
    "첫 번째 작업의 priority 를 10 으로",
    "3번 뒤에 리포트 작성 작업 insert",
    "2번 제거",
    "agent 를 sentiment_analyzer 로 변경",
]


def _build_test_plan() -> Plan:
    """5개 Todo 가 있는 테스트 Plan (planner.Plan / PlannedTodo)."""
    return Plan(
        teams_selected=["test_team"],
        todos=[
            PlannedTodo(
                id=f"todo_{i+1:03d}",
                task_type="demo",
                agent=f"agent_{i+1}",
                tool=f"tool_{i+1}",
                priority=5,
                rationale=f"작업 {i+1}",
            )
            for i in range(5)
        ],
        dag={f"todo_{i+1:03d}": [] for i in range(5)},
    )


async def _measure_one(editor: PlanEditor, instruction: str, plan: Plan) -> dict:
    """단일 측정 — latency + action."""
    t0 = time.perf_counter()
    error_type = None
    parsed_action = None
    success = False
    try:
        result = await editor.parse_instruction(instruction, plan)
        parsed_action = result.get("action", "unknown")
        success = parsed_action != "unknown"
    except Exception as e:
        error_type = type(e).__name__
    t1 = time.perf_counter()
    return {
        "input": instruction,
        "parsed_action": parsed_action,
        "success": success,
        "latency_ms": int((t1 - t0) * 1000),
        "error_type": error_type,
    }


async def main(iterations: int = 10):
    """10종 × iterations 회 = 총 10 * iterations 측정."""
    editor = PlanEditor()
    plan = _build_test_plan()

    out_dir = ROOT / "logs"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"a3_nl_success_rate_{ts}.jsonl"

    results: list[dict] = []
    total = len(INPUT_CASES) * iterations

    print(f"🔬 NL 편집 성공률 측정 — 총 {total}회, 결과: {out_path}")
    with open(out_path, "w", encoding="utf-8") as f:
        for iter_idx in range(iterations):
            for case in INPUT_CASES:
                r = await _measure_one(editor, case, plan)
                results.append(r)
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                f.flush()
                sym = "✓" if r["success"] else "✗"
                print(f"  [{len(results):3d}/{total}] {sym} {r['latency_ms']:4d}ms | {case[:30]:30s} → {r['parsed_action']}")

    # Summary
    total_n = len(results)
    success_n = sum(1 for r in results if r["success"])
    fail_n = total_n - success_n
    fail_rate = fail_n / total_n * 100 if total_n else 0.0
    latencies = sorted(r["latency_ms"] for r in results)
    p50 = latencies[len(latencies) // 2] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0

    summary = {
        "total": total_n,
        "success": success_n,
        "failure": fail_n,
        "failure_rate_pct": round(fail_rate, 2),
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
        "nfr_11_p95_under_3000ms": p95 < 3000,
        "trigger": (
            "Y-a 유지 (실패율 < 3%)" if fail_rate < 3
            else "γ 재평가 필요 (실패율 ≥ 3%)" if fail_rate < 10
            else "Y-a 범위 재설계 (실패율 ≥ 10%)"
        ),
    }
    print("\n" + "=" * 60)
    print("📊 요약:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("=" * 60)

    summary_path = out_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n📄 Summary: {summary_path}")


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    asyncio.run(main(iterations=iters))
