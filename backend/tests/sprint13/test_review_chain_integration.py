"""작업 ⑫.G — review_collector → review_normalizer chain integration (1 case)

명세서: docs/reports/계획_작업⑫_broken5_폐기_review_재작성_권한명확_2026-05-31.md §3.G

검증 (RCI-01): clumi/raw/reviews.csv 24 raw → review_collector → review_normalizer
              → normalized_reviews 24 (channel/sentiment/keywords = None 박제)

POC 박제 의도:
  reviews.csv 5컬럼 (review_id/date/product/rating/text) vs
  review_normalizer aliases (channel/sentiment/keywords) gap = silent None.
  미래 raw 확장 (channel/sentiment 추가) 시 = 자연 trigger.
"""

import pytest


@pytest.mark.asyncio
async def test_RCI01_review_collector_normalizer_chain_clumi():
    """clumi/raw/reviews.csv → review_collector → review_normalizer 전 chain (real DataSource)."""
    from app.dream_agent.models import ExecutionContext, ToolSpec
    from app.dream_agent.models.enums import ToolCategory
    from app.dream_agent.tools.collection.review_collector import ReviewCollector
    from app.dream_agent.tools.normalization.review_normalizer import ReviewNormalizer

    # 1. review_collector (real DataSource = file.py FileDataSource)
    collector_spec = ToolSpec(
        name="review_collector", description="", category=ToolCategory.COLLECTION,
        executor="app.dream_agent.tools.collection.review_collector.ReviewCollector",
    )
    collector = ReviewCollector(spec=collector_spec)

    ctx = ExecutionContext(session_id="rci_test", plan_id="rci_test", client_id="clumi")
    collect_out = await collector.execute({}, ctx)

    # reviews.csv = 24 raw 행 (1 header + 24 data)
    assert collect_out["count"] == 24, f"clumi raw count={collect_out['count']} != 24"
    assert collect_out["source_id"] == "reviews"

    # 2. review_normalizer (chain — previous_results 전달)
    normalizer_spec = ToolSpec(
        name="review_normalizer", description="", category=ToolCategory.NORMALIZATION,
        executor="app.dream_agent.tools.normalization.review_normalizer.ReviewNormalizer",
    )
    normalizer = ReviewNormalizer(spec=normalizer_spec)

    ctx_normalize = ExecutionContext(
        session_id="rci_test", plan_id="rci_test", client_id="clumi",
        previous_results={"collect_step": {"data": collect_out}},
    )
    normalize_out = await normalizer.execute({}, ctx_normalize)

    # 3. normalized_reviews 검증
    normalized = normalize_out["normalized_reviews"]
    assert len(normalized) == 24
    assert normalize_out["schema_version"] == "review.v1"

    # 4. POC reviews.csv 5컬럼 vs alias gap 박제 — silent None 자연 출력
    #    review_normalizer alias 가 한글+영문 둘 다 처리 → 영문 review_id 매칭 OK
    assert normalized[0]["review_id"] == "RV-001"

    # text 컬럼 매핑 OK (review.v1 schema)
    assert normalized[0]["text"] is not None

    # POC 박제 — channel/sentiment/keywords = silent None
    # (MVP+ raw 확장 시 = 본 assert 자연 trigger)
    assert normalized[0]["channel"] is None, \
        "POC reviews.csv 5컬럼 = channel alias 부재. MVP+ raw 확장 시 fail = 자연 trigger."
    assert normalized[0]["sentiment"] is None, \
        "POC reviews.csv = sentiment alias 부재. MVP+ ML sentiment 분석 도입 시 fail = trigger."
    assert normalized[0]["keywords"] == [], \
        "POC reviews.csv = keywords alias 부재. MVP+ keyword_extractor 도입 시 fail = trigger."
