"""Review Collector — clumi/raw/reviews.csv raw 수집 (helper-B 패턴).

작업 ⑫ (2026-06-01) 재작성 — ADR-027 §1 권한 매트릭스 정합:

  [Tool 권한] (할 일):
    * DataSource 호출 (self.fetch("reviews", context))
    * raw 통째 반환 (raw_reviews 키)

  [Tool 금지] (안 할 일):
    * 파일 경로·파일명 hardcode (load_mock_csv 폐기)
    * client 컬럼명 hardcode (한글 컬럼 hardcode 폐기 — review_normalizer 책임)
    * 도메인 필터링 (brand·source·period·limit — cleaning tool 책임, MVP+ 결정)
    * 다른 Tool 직접 호출 / ml_model 우회

Status: complete — broken (load_mock_csv) → helper-B 재작성.

입력: params (예: brand) 받아도 무시 — POC clumi 단일 client 단일 brand raw.
       filtering = MVP+ 단계에 cleaning tool (cleaning/reviews_filter) 신규 결정.
출력: raw_reviews (list[dict]) — reviews.csv 24 raw 행 통째.
       컬럼 정규화 = review_normalizer 책임 (ADR-014 v2 단일 책임 분리).
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool

logger = get_logger(__name__)

SOURCE_ID = "reviews"           # file.py SOURCE_REGISTRY 등록 키
PRODUCES_KEY = "raw_reviews"    # 다음 tool (review_normalizer) 입력 키 (broken 과 동일)


class ReviewCollector(BaseTool):
    """리뷰 raw 수집 — DataSource 위임 + raw 통째 반환 (ADR-027 권한 정합)."""

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        # helper-B (ADR-022) — client 흐름은 context, source_id 는 tool 책임
        data = self.fetch(SOURCE_ID, context)

        # pandas DataFrame → list[dict] (raw 형태 유지, normalize 위임)
        if hasattr(data, "to_dict"):
            records = data.to_dict(orient="records")
        else:
            records = data if isinstance(data, list) else [data]

        logger.info(
            "review_collector completed",
            source=SOURCE_ID,
            client=context.client_id,
            count=len(records),
        )

        return {
            PRODUCES_KEY: records,
            "count": len(records),
            "source_id": SOURCE_ID,
        }
