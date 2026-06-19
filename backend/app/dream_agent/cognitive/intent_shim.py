"""PMAL intent → tasks[str] shim.

intent(PMAL 칸) → tasks(작업 어휘) 기계 파생. intent=canonical 진실, tasks=호환 그림자.
목적: planning 3-stage·게이트(작업 어휘 기반)를 안 깨고 작동시킴.

프레임 추출(2026-06-19): 마케팅 전용 매핑(reviews→sentiment 등) 제거 → 도메인 무관 generic 매핑.
operation 만으로 프레임 기본 작업을 고른다. 도메인별 세부는 intent.domain/metric/dimensions 에 남아
planning(카탈로그 라우팅)이 소비한다.

규칙(generic):
  compare              → comparison
  diagnose / forecast  → analysis
  attribute            → insight_generation
  recommend            → recommendation
  그 외(measure 등)    → metric_calculation
"""
from __future__ import annotations

from app.dream_agent.schemas.structured_query import Intent, Task, TaskType


def intent_to_tasks(intent: Intent) -> list[Task]:
    """intent → tasks[]. intent 가 진실, tasks 는 호환용 파생 (open-vocab str id)."""
    op = (intent.operation or "measure").lower()

    if op == "compare":
        return [Task(id=TaskType.COMPARISON.value)]
    if op in ("diagnose", "forecast"):
        return [Task(id=TaskType.ANALYSIS.value)]
    if op == "attribute":
        return [Task(id=TaskType.INSIGHT_GENERATION.value)]
    if op == "recommend":
        return [Task(id=TaskType.RECOMMENDATION.value)]
    return [Task(id=TaskType.METRIC_CALCULATION.value)]
