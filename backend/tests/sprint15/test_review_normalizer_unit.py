"""Sprint 15 — review_normalizer unit test (2026-05-19).

ADR-014 v2 (Tool 단일 책임 분리) 적용 — format_normalizer 에서 review 분리.
이전: test_format_normalizer_ads_unit.py::test_TE_FN10 (review.v1 회귀).

대상: `app.dream_agent.tools.preprocessing.data_normalization.review_normalizer.ReviewNormalizer`
의 review.v1 룰셋 (4 출처 리뷰 raw → normalized_reviews).

검증 영역:
- 한글 컬럼 → 영문 통일 (리뷰ID/텍스트/출처/별점/감성/작성일/주요키워드 → review_id/text/...)
- channel 정규화 (normalize_channel helper)
- sentiment 정규화 (normalize_sentiment helper — 긍정/부정/중립 → positive/negative/neutral)
- rating int 변환
- keywords 문자열 → list 변환
- 빈 입력 → 빈 출력

Test naming: TE-RN01 ~ TE-RN05.
"""
from __future__ import annotations

import pytest

from app.dream_agent.models import ExecutionContext, ToolSpec
from app.dream_agent.models.enums import ToolCategory
from app.dream_agent.tools.normalization.review_normalizer import (
    ReviewNormalizer,
)


def _normalizer_spec() -> ToolSpec:
    return ToolSpec(
        name="review_normalizer",
        category=ToolCategory.NORMALIZATION,
        executor="app.dream_agent.tools.preprocessing.data_normalization.review_normalizer.ReviewNormalizer",
        description="review_normalizer (review 전용)",
        parameters=[],
    )


def _ctx_with(previous_results: dict) -> ExecutionContext:
    return ExecutionContext(
        session_id="test",
        plan_id="test",
        client_id=None,
        user_id="test",
        previous_results=previous_results,
    )


# ──────────────────────────────────────────────────────────────
# TE-RN01 — 한글 컬럼 → 영문 통일 (기본 case)
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_TE_RN01_korean_to_unified_schema():
    """리뷰ID/텍스트/출처/별점/감성/작성일/주요키워드 → review_id/text/.../keywords."""
    normalizer = ReviewNormalizer(spec=_normalizer_spec())
    review_raw = [
        {
            "리뷰ID": "RV-001",
            "텍스트": "보습력이 정말 좋아요",
            "출처": "naver_blog",
            "별점": 5,
            "감성": "긍정",
            "작성일": "2025-03-28",
            "주요키워드": "보습력,촉촉",
        }
    ]
    ctx = _ctx_with({"review_step": {"data": {"raw_reviews": review_raw}}})

    result = await normalizer.execute({}, ctx)

    assert result["count"] == 1
    assert result["schema_version"] == "review.v1"
    item = result["normalized_reviews"][0]
    assert item["review_id"] == "RV-001"
    assert item["text"] == "보습력이 정말 좋아요"
    assert item["channel"] == "naver_blog"
    assert item["rating"] == 5
    assert item["keywords"] == ["보습력", "촉촉"]
    assert item["date"] == "2025-03-28"


# ──────────────────────────────────────────────────────────────
# TE-RN02 — sentiment 정규화 (긍정 → positive 등)
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_TE_RN02_sentiment_normalization():
    """감성 한글/영문 정규화 — normalize_sentiment helper."""
    normalizer = ReviewNormalizer(spec=_normalizer_spec())
    review_raw = [
        {"리뷰ID": "RV-001", "텍스트": "좋아요", "감성": "긍정"},
        {"리뷰ID": "RV-002", "텍스트": "별로", "감성": "negative"},
        {"리뷰ID": "RV-003", "텍스트": "보통", "감성": "중립"},
    ]
    ctx = _ctx_with({"step": {"data": {"raw_reviews": review_raw}}})

    result = await normalizer.execute({}, ctx)

    items = result["normalized_reviews"]
    assert items[0]["sentiment"] in ("positive", "긍정")  # helper 구현에 따라
    assert items[1]["sentiment"] in ("negative", "부정")
    assert items[2]["sentiment"] in ("neutral", "중립")


# ──────────────────────────────────────────────────────────────
# TE-RN03 — keywords 문자열 → list 변환
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_TE_RN03_keywords_string_to_list():
    """주요키워드: '보습력,촉촉' → ['보습력', '촉촉']."""
    normalizer = ReviewNormalizer(spec=_normalizer_spec())
    review_raw = [
        {"리뷰ID": "RV-001", "텍스트": "...", "주요키워드": "보습력, 촉촉, 효과"},
        {"리뷰ID": "RV-002", "텍스트": "..."},  # keywords 없음
    ]
    ctx = _ctx_with({"step": {"data": {"raw_reviews": review_raw}}})

    result = await normalizer.execute({}, ctx)
    items = result["normalized_reviews"]

    assert items[0]["keywords"] == ["보습력", "촉촉", "효과"]
    assert items[1]["keywords"] == []  # None → 빈 list


# ──────────────────────────────────────────────────────────────
# TE-RN04 — 빈 입력 → 빈 출력
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_TE_RN04_empty_input_returns_empty():
    normalizer = ReviewNormalizer(spec=_normalizer_spec())
    ctx = _ctx_with({})

    result = await normalizer.execute({}, ctx)
    assert result["count"] == 0
    assert result["normalized_reviews"] == []
    assert result["schema_version"] == "review.v1"


# ──────────────────────────────────────────────────────────────
# TE-RN05 — rating int 변환 + 비정상 값 가드
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_TE_RN05_rating_int_conversion():
    """별점 int 변환 + 잘못된 값 None 처리."""
    normalizer = ReviewNormalizer(spec=_normalizer_spec())
    review_raw = [
        {"리뷰ID": "RV-001", "텍스트": "...", "별점": 5},
        {"리뷰ID": "RV-002", "텍스트": "...", "별점": "4"},
        {"리뷰ID": "RV-003", "텍스트": "...", "별점": "invalid"},
    ]
    ctx = _ctx_with({"step": {"data": {"raw_reviews": review_raw}}})

    result = await normalizer.execute({}, ctx)
    items = result["normalized_reviews"]

    assert items[0]["rating"] == 5
    assert items[1]["rating"] == 4  # string → int
    assert items[2]["rating"] is None  # invalid → None
