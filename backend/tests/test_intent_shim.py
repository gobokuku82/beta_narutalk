"""PMAL W2 — intent→tasks shim 결정론 단위테스트 (2026-06-04).

목적: intent(새 칸, W1) → tasks[TaskType](옛 칸) 기계 파생. intent=canonical, tasks=그림자.
그래야 기존 planning/게이트(TaskType 기반)가 안 깨지고 계속 작동 (혼재 아님 — 한쪽이 진실).

검증(wf_7235ece5 fix-B) 핵심 규칙: shim 은 (operation, domain) *복합* 키.
  - domain∋reviews → sentiment_analysis (operation 무관, *최우선*). operation 어휘엔 sentiment 없으니 domain 이 가름.
  - diagnose→causal_analysis / forecast→trend_analysis / attribute→insight_generation (2026-06-10 분석레이어 v2: 구 degrade 대신 실제 분석 tool 라우팅).
  - compare → competitor_comparison.
  - 그 외 숫자(measure/breakdown/rank/trend/기본) → metric_calculation.

순수 함수, LLM 없음. 아직 흐름 연결 안 함(연결=W3). 여기선 변환 규칙만 못박음.
"""
from __future__ import annotations

from app.dream_agent.cognitive.intent_shim import intent_to_tasks
from app.dream_agent.schemas.structured_query import Intent, TaskType


def _ids(intent: Intent) -> list[TaskType]:
    return [t.id for t in intent_to_tasks(intent)]


# ── reviews 우선 (fix-B 핵심) ──

def test_reviews_domain_to_sentiment():
    assert _ids(Intent(operation="measure", domain=["reviews"])) == [TaskType.SENTIMENT_ANALYSIS]


def test_reviews_priority_over_numeric_operation():
    # domain=reviews 면 operation=measure 여도 sentiment (metric_calculation 으로 새지 않음)
    assert _ids(Intent(operation="breakdown", domain=["reviews"])) == [TaskType.SENTIMENT_ANALYSIS]


# ── 숫자 도메인 → metric_calculation ──

def test_numeric_measure_to_metric():
    assert _ids(Intent(operation="measure", domain=["revenue"], metric=["revenue"])) == [TaskType.METRIC_CALCULATION]


def test_numeric_ops_to_metric():
    for op in ("breakdown", "rank", "trend"):
        assert _ids(Intent(operation=op, domain=["ad_performance"])) == [TaskType.METRIC_CALCULATION]


def test_default_measure_no_domain_to_metric():
    # operation 기본 measure + domain 없음 → metric_calculation (숫자 기본)
    assert _ids(Intent()) == [TaskType.METRIC_CALCULATION]


# ── compare → competitor_comparison ──

def test_compare_to_competitor_comparison():
    assert _ids(Intent(operation="compare", domain=["revenue"])) == [TaskType.COMPETITOR_COMPARISON]


# ── diagnose/forecast/attribute → 분석 사다리 깊은 층 (2026-06-10 분석레이어 v2, 구 degrade 해소) ──

def test_diagnose_forecast_attribute_route_to_analysis():
    # 구: shim 안 함 → [](degrade). 현: 실제 분석 tool task 로 라우팅 (diagnoser/forecaster/insight_extractor).
    assert _ids(Intent(operation="diagnose", domain=["revenue"])) == [TaskType.CAUSAL_ANALYSIS]
    assert _ids(Intent(operation="forecast", domain=["revenue"])) == [TaskType.TREND_ANALYSIS]
    assert _ids(Intent(operation="attribute", domain=["revenue"])) == [TaskType.INSIGHT_GENERATION]


# ── 산출 타입 ──

def test_returns_task_objects():
    from app.dream_agent.schemas.structured_query import Task
    out = intent_to_tasks(Intent(operation="measure", domain=["customers"]))
    assert all(isinstance(t, Task) for t in out)
