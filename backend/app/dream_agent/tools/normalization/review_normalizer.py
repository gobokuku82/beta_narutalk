"""Review Normalizer — 4 출처 리뷰 raw → 통일 스키마 (review.v1).

Status: complete — 2026-05-19 P1.1 sprint 신규 (format_normalizer 의 review 코드 이식).

ADR-014 Proposed v2 = Tool 단일 책임 분리 패턴 적용.
- Before: format_normalizer 가 ads + review 다도메인 (분기 매개변수 domain)
- After: format_normalizer (ads 전용) + review_normalizer (review 전용)

입력: raw_reviews (list[dict]) — review_collector 의 produces
      (⑱ 2026-06-01: youtube/coupang/oliveyoung stub 3 폐기. MVP+ 실 source 진입 시 helper-B 신규)
출력: normalized_reviews (list[dict]) — 통일 review 스키마 + schema_version=review.v1

매핑 룰: 4 출처 (naver_blog/naver_shopping/naver_cafe/oliveyoung) 의 컬럼명·값
정규화 (review_id / text / channel / rating / sentiment / date / keywords).
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.helpers import (
    find_in_previous,
    normalize_channel,
    normalize_sentiment,
)

logger = get_logger(__name__)

REVIEW_FIELD_ALIASES: dict[str, list[str]] = {
    "review_id":  ["리뷰ID", "review_id", "id"],
    "text":       ["텍스트", "리뷰내용", "content", "review_text", "text"],
    "channel":    ["출처", "source", "media", "channel"],
    "rating":     ["별점", "rating", "score"],
    "sentiment":  ["감성", "sentiment"],
    "date":       ["작성일", "date", "created_at"],
    "keywords":   ["주요키워드", "키워드", "keywords"],
}


class ReviewNormalizer(BaseTool):
    """4 출처 리뷰 raw → 통일 스키마 (review 전용)."""

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        raw = find_in_previous(context.previous_results, "raw_reviews") or []
        normalized = [self._map_review(row) for row in raw]

        logger.info(
            "review_normalizer completed",
            input=len(raw),
            output=len(normalized),
        )

        return {
            "normalized_reviews": normalized,
            "count": len(normalized),
            "schema_version": "review.v1",
        }

    def _map_review(self, row: dict) -> dict:
        item: dict[str, Any] = {}
        for target, aliases in REVIEW_FIELD_ALIASES.items():
            item[target] = self._pick(row, aliases)

        # 값 표준화
        item["channel"] = normalize_channel(item.get("channel"))
        item["sentiment"] = normalize_sentiment(item.get("sentiment"))

        if item.get("rating") is not None:
            try:
                item["rating"] = int(item["rating"])
            except (ValueError, TypeError):
                item["rating"] = None

        # 키워드: "보습력,촉촉" → ["보습력", "촉촉"]
        kw = item.get("keywords")
        if isinstance(kw, str):
            item["keywords"] = [k.strip() for k in kw.split(",") if k.strip()]
        elif kw is None:
            item["keywords"] = []

        # 날짜: ISO 문자열로 유지
        if item.get("date") is not None:
            item["date"] = str(item["date"])

        return item

    @staticmethod
    def _pick(row: dict, aliases: list[str]) -> Optional[Any]:
        """alias 리스트에서 먼저 발견되는 값 반환 (null 제외)."""
        for key in aliases:
            if key in row and row[key] is not None:
                val = row[key]
                # pandas NaN 대응
                try:
                    import math
                    if isinstance(val, float) and math.isnan(val):
                        continue
                except Exception:
                    pass
                return val
        return None
