"""PMAL intent → tasks[TaskType] shim (W2, 2026-06-04).

intent(새 PMAL 칸, W1) → tasks(옛 TaskType 칸) 기계 파생. intent=canonical 진실, tasks=그림자.
목적: 기존 planning 3-stage·subject-coherence 게이트(TaskType 기반)를 안 깨고 계속 작동시킴
      (혼재 아님 — tasks 는 독립 저작 X, 순수 파생. B2 에 tasks 제거).

규칙:
  1. domain∋reviews → sentiment_analysis  (operation 무관·최우선)
  2. diagnose→causal_analysis(diagnoser) / forecast→trend_analysis(forecaster) / attribute→insight_generation(insight_extractor)
     (2026-06-10 분석레이어 v2 — 구 DEGRADE 대신 실제 분석 tool 로 라우팅. 분석 사다리 깊은 층)
  3. operation=compare → competitor_comparison
  4. 그 외(measure/breakdown/rank/trend/기본) → metric_calculation

Status: complete — 순수 함수. 흐름 연결(cognitive 가 호출)=W3. metric 세부는 intent.metric 에 남아 planning(W4)이 소비.
"""
from __future__ import annotations

from app.dream_agent.schemas.structured_query import Intent, Task, TaskType


def intent_to_tasks(intent: Intent) -> list[Task]:
    """intent → tasks[]. intent 가 진실, tasks 는 호환용 파생."""
    op = (intent.operation or "measure").lower()
    domain = {d.lower() for d in (intent.domain or [])}

    if "reviews" in domain:          # 1. 리뷰 주제 = 텍스트 분석 (최우선)
        return [Task(id=TaskType.SENTIMENT_ANALYSIS)]
    # 2. 분석 사다리 깊은 층 (2026-06-10 분석레이어 v2 — 구 DEGRADE → 실제 분석 tool)
    if op == "diagnose":             # 진단 '왜' → diagnoser
        return [Task(id=TaskType.CAUSAL_ANALYSIS)]
    if op == "forecast":             # 예측 '앞으로' → forecaster
        return [Task(id=TaskType.TREND_ANALYSIS)]
    if op == "attribute":            # 추론 '함의·기여' → insight_extractor
        return [Task(id=TaskType.INSIGHT_GENERATION)]
    if op == "recommend":            # 의사결정 '뭘 해야' → recommender (2026-06-10 의사결정 카테고리)
        return [Task(id=TaskType.RECOMMENDATION)]
    if op == "compare":              # 3. 비교
        return [Task(id=TaskType.COMPETITOR_COMPARISON)]
    return [Task(id=TaskType.METRIC_CALCULATION)]   # 4. 그 외 숫자
