"""PMAL W1 — Intent 스키마 (쪽지의 '주제 칸') 결정론 단위테스트 (2026-06-04).

기준(criteria_map §2 ①, spec 37 §2): cognitive 출력 쪽지에 *주제(WHAT)*를 담는 1급 칸이 있어야 한다.
  intent{ operation(HOW, authored, 기본 measure) × domain(WHAT 영역, SET) × metric(open) × dimensions }

W1 = 칸만 만든다 (cognitive 가 채우는 건 W3). 그래서 여기선:
  - Intent 모델이 존재·기본값
  - StructuredQuery 가 intent 없이도 (기존 쪽지) 그대로 작동 (backward compat) + intent 있으면 round-trip
  - Period.resolved 필드 (B1 = field only)
  - F2 케이스("왜 매출 늘었어?")의 주제가 domain=['revenue'] 로 *결정적으로* 담겨 reviews 와 구분됨

검증단계(operation/domain 유효성 강제)는 B1 안 함 — 자유 string. (baseline §3: 검증≠품질)
LLM 호출 없음 — 순수 Pydantic, 결정론.
"""
from __future__ import annotations

from app.dream_agent.schemas.structured_query import (
    Goal,
    GoalType,
    Intent,
    OutputFormat,
    Period,
    QueryMeta,
    StructuredQuery,
    Targets,
)


def _sq(**overrides) -> StructuredQuery:
    base = dict(
        targets=Targets(),
        goal=Goal(type=GoalType.METRIC, output_format=OutputFormat.TEXT),
        tasks=[],
        meta=QueryMeta(raw_input="x"),
    )
    base.update(overrides)
    return StructuredQuery(**base)


# ── Intent 모델 ──

def test_intent_defaults():
    # operation 미언급 → measure (authored 기본). 나머지 빈 SET.
    i = Intent()
    assert i.operation == "measure"
    assert i.domain == [] and i.metric == [] and i.dimensions == []


def test_intent_with_values():
    i = Intent(operation="diagnose", domain=["revenue"], metric=["revenue"], dimensions=["member_grade"])
    assert i.operation == "diagnose"
    assert i.domain == ["revenue"]
    assert i.dimensions == ["member_grade"]


def test_intent_domain_is_set_multi():
    # ROAS 처럼 다중 도메인 (revenue ∩ ad_performance) — domain 은 SET (스칼라 아님)
    i = Intent(operation="measure", domain=["revenue", "ad_performance"], metric=["ROAS"])
    assert set(i.domain) == {"revenue", "ad_performance"}


# ── StructuredQuery 통합 (backward compat 필수) ──

def test_sq_backward_compat_without_intent():
    # 기존 쪽지(intent 없음)도 그대로 파싱 — intent 는 Optional, 기본 None
    sq = _sq()
    assert sq.intent is None


def test_sq_with_intent_roundtrip():
    sq = _sq(intent=Intent(operation="diagnose", domain=["revenue"], metric=["revenue"]))
    dumped = sq.model_dump(mode="json")
    assert dumped["intent"]["operation"] == "diagnose"
    assert dumped["intent"]["domain"] == ["revenue"]
    # 재구성 round-trip
    assert StructuredQuery.model_validate(dumped).intent.domain == ["revenue"]


# ── Period.resolved (B1 = field only) ──

def test_period_resolved_field():
    assert Period(raw="4월", resolved="2026-04").resolved == "2026-04"
    assert Period(raw="4월").resolved is None   # 기본 None (절대화는 B2)


# ── 핵심: 주제가 domain 으로 결정적 인코딩 (W1 존재 이유, F2 anchor) ──

def test_f2_subject_encoded_in_domain():
    # "왜 4월 매출이 늘었는지" → 주제=revenue 가 domain 한 칸에 박힘
    revenue_q = _sq(intent=Intent(operation="diagnose", domain=["revenue"], metric=["revenue"]))
    review_q = _sq(intent=Intent(operation="measure", domain=["reviews"]))
    # 매출 질문과 리뷰 질문이 domain 으로 *결정적으로* 구분됨 (planning 이 추측 불요)
    assert "revenue" in revenue_q.intent.domain
    assert "reviews" not in revenue_q.intent.domain
    assert "reviews" in review_q.intent.domain
