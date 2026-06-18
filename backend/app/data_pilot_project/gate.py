"""gate.py — data_pilot 산출물 *전체 게이트* 단일 엔트리포인트 (P1 통합).

materialize → 4단 검사 일괄 + 종합 판정. 'verify 통과'를 한 명령으로 정직하게.
  1) run_pilot   : SPEC 정답 대조 (8/8) — 구현이 contract대로 raw 처리했나
  2) verify_outputs: 산출물 독립 재계산 (12/12 critical + crosswalk WARN)
  3) coverage    : 44필드 materialized/tested 매니페스트 (vacuously-green 가시화)
  4) dict_gate   : 사전↔raw↔contract 컬럼 diff (CRITICAL=contract오기 차단 / DRIFT=사전 owner영역 보고)

종합 FAIL 조건: run_pilot 실패 OR verify critical 실패 OR coverage 미정당화 not_attempted OR dict CRITICAL>0.
(crosswalk WARN·dict DRIFT 는 비차단 — 의도적 미해결/오너 영역.)

실행: python backend/app/data_pilot_project/gate.py
"""
from __future__ import annotations

import materialize
import run_pilot
import verify_outputs as vo
import coverage
import dict_gate

LINE = "█" * 72


def main() -> bool:
    print(LINE)
    print("  data_pilot GATE — 산출물 전체 검증 (materialize → 4단 검사)")
    print(LINE)

    # 0) 최신 materialize (검사 대상 신선도 보장)
    materialize.materialize()
    print("[0] materialize ✓ → data/clumi/_canonical/\n")

    results: dict[str, bool] = {}

    print("【1】 run_pilot — SPEC 정답 대조")
    results["run_pilot"] = run_pilot.main()

    print("\n【2】 verify_outputs — 산출물 독립 재계산")
    checks, tested = vo.run()
    results["verify_outputs"] = vo._report(checks, tested)

    print("\n【3】 coverage — 필드 커버리지 매니페스트")
    results["coverage"] = coverage.main()

    print("\n【4】 dict_gate — 사전↔raw↔contract diff")
    results["dict_gate"] = dict_gate.main()

    # 종합
    print("\n" + LINE)
    print("  GATE 종합")
    print(LINE)
    for name, ok in results.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    overall = all(results.values())
    print(LINE)
    print(f"  ★ OVERALL: {'✅ PASS' if overall else '✗ FAIL'}  "
          "(crosswalk WARN·dict DRIFT 는 비차단 — 본문 참조)")
    print(LINE)
    return overall


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
