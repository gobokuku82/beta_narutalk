"""작업 ⑫.G — review_collector helper-B 패턴 unit 테스트 (5 cases)

명세서: docs/reports/계획_작업⑫_broken5_폐기_review_재작성_권한명확_2026-05-31.md §3.G
대상: backend/app/dream_agent/tools/collection/review_collector.py (helper-B 재작성)

위치 결정: sprint13 = ws_agent + state + helper-B 통합 e2e 영역 (작업 ⑪ 패턴 정합).
sprint15 = broken collector 격리 영역 (분리).

검증 차원 (ADR-027 §1 Tool 권한 매트릭스 정합):
  RC-01: self.fetch("reviews", context) DataSource 위임
  RC-02: raw_reviews list[dict] 형식 반환
  RC-03: client_id=None 시 BaseTool.fetch ValueError (helper-B fail-fast)
  RC-04: DataFrame → list[dict] 변환 정상
  RC-05: Tool 금지 패턴 자동 검증 (load_mock_csv·한글 컬럼 hardcode 0)
"""

import inspect
from unittest.mock import MagicMock

import pytest


# ──────────────────────────────────────────────────────────────────
# RC-01 self.fetch("reviews", context) DataSource 위임
# ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_RC01_fetch_delegates_to_data_source():
    """신 review_collector 가 self.fetch("reviews", context) 호출."""
    from app.dream_agent.models import ExecutionContext, ToolSpec
    from app.dream_agent.models.enums import ToolCategory
    from app.dream_agent.tools.collection.review_collector import ReviewCollector

    mock_ds = MagicMock()
    mock_ds.get.return_value = [{"review_id": "RV-001", "text": "test"}]

    spec = ToolSpec(
        name="review_collector",
        description="test",
        category=ToolCategory.COLLECTION,
        executor="app.dream_agent.tools.collection.review_collector.ReviewCollector",
    )
    tool = ReviewCollector(spec=spec, data_source=mock_ds)

    ctx = ExecutionContext(session_id="t", plan_id="t", client_id="clumi")
    result = await tool.execute({}, ctx)

    mock_ds.get.assert_called_once_with("clumi", "reviews")
    assert result["source_id"] == "reviews"


# ──────────────────────────────────────────────────────────────────
# RC-02 raw_reviews list[dict] 반환
# ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_RC02_raw_reviews_list_dict_format():
    """raw_reviews 키 list[dict] 형식 반환 + count 정합."""
    from app.dream_agent.models import ExecutionContext, ToolSpec
    from app.dream_agent.models.enums import ToolCategory
    from app.dream_agent.tools.collection.review_collector import ReviewCollector

    mock_ds = MagicMock()
    mock_ds.get.return_value = [
        {"review_id": "RV-001", "text": "a"},
        {"review_id": "RV-002", "text": "b"},
    ]
    spec = ToolSpec(name="review_collector", description="", category=ToolCategory.COLLECTION,
                    executor="x")
    tool = ReviewCollector(spec=spec, data_source=mock_ds)

    ctx = ExecutionContext(session_id="t", plan_id="t", client_id="clumi")
    result = await tool.execute({}, ctx)

    assert "raw_reviews" in result
    assert isinstance(result["raw_reviews"], list)
    assert all(isinstance(r, dict) for r in result["raw_reviews"])
    assert result["count"] == 2


# ──────────────────────────────────────────────────────────────────
# RC-03 client_id=None → BaseTool.fetch ValueError (helper-B fail-fast)
# ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_RC03_fail_fast_on_none_client_id():
    """client_id 미명시 시 ADR-022 helper-B fail-fast (ValueError)."""
    from app.dream_agent.models import ExecutionContext, ToolSpec
    from app.dream_agent.models.enums import ToolCategory
    from app.dream_agent.tools.collection.review_collector import ReviewCollector

    spec = ToolSpec(name="review_collector", description="", category=ToolCategory.COLLECTION,
                    executor="x")
    tool = ReviewCollector(spec=spec)

    ctx = ExecutionContext(session_id="t", plan_id="t", client_id=None)
    with pytest.raises(ValueError, match="client 미지정"):
        await tool.execute({}, ctx)


# ──────────────────────────────────────────────────────────────────
# RC-04 DataFrame → list[dict] 변환 정상
# ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_RC04_dataframe_to_list_dict_conversion():
    """DataSource 가 DataFrame 반환 시 list[dict] 변환."""
    import pandas as pd
    from app.dream_agent.models import ExecutionContext, ToolSpec
    from app.dream_agent.models.enums import ToolCategory
    from app.dream_agent.tools.collection.review_collector import ReviewCollector

    df = pd.DataFrame([
        {"review_id": "RV-001", "rating": 5},
        {"review_id": "RV-002", "rating": 4},
    ])
    mock_ds = MagicMock()
    mock_ds.get.return_value = df

    spec = ToolSpec(name="review_collector", description="", category=ToolCategory.COLLECTION,
                    executor="x")
    tool = ReviewCollector(spec=spec, data_source=mock_ds)

    ctx = ExecutionContext(session_id="t", plan_id="t", client_id="clumi")
    result = await tool.execute({}, ctx)

    assert isinstance(result["raw_reviews"], list)
    assert result["count"] == 2
    assert result["raw_reviews"][0]["review_id"] == "RV-001"


# ──────────────────────────────────────────────────────────────────
# RC-05 ADR-027 Tool 권한 매트릭스 자동 검증 (소스 코드 inspect)
# ──────────────────────────────────────────────────────────────────

def test_RC05_adr_027_tool_permission_compliance():
    """신 review_collector 가 ADR-027 §1 Tool 금지 사항 위반 0 (소스 코드 자동 검증)."""
    from app.dream_agent.tools.collection.review_collector import ReviewCollector

    src = inspect.getsource(ReviewCollector)

    # Tool 금지: 파일 경로 hardcode
    assert "load_mock_csv" not in src, "ADR-027 Tool 금지: 파일 경로 접근"
    assert "MOCK_FILE" not in src, "ADR-027 Tool 금지: 파일명 hardcode"

    # Tool 금지: client 컬럼명 hardcode (한글)
    assert "브랜드" not in src, "ADR-027 Tool 금지: client 컬럼 hardcode (브랜드)"
    assert "출처" not in src, "ADR-027 Tool 금지: client 컬럼 hardcode (출처)"
    assert "작성일" not in src, "ADR-027 Tool 금지: client 컬럼 hardcode (작성일)"

    # Tool 권한: DataSource 호출
    assert "self.fetch" in src, "ADR-027 Tool 권한: DataSource 호출 부재"
