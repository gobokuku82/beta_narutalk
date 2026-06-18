"""review_recent — 최근 리뷰 카드 N건 (O03). 작성일 desc sort + slice.

Status: complete — Phase 1 Batch 4 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.reviews import load_reviews
from app.schemas.outputs.trend import ReviewCardsOutput

logger = get_logger(__name__)


class ReviewRecent(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        n = int(merged.get("n", 6))

        reviews = load_reviews(self.fetch("reviews", context)).rows
        recent = sorted(reviews, key=lambda r: r.date, reverse=True)[:n]
        rows = [r.model_dump() for r in recent]
        return ReviewCardsOutput(rows=rows, count=len(rows)).model_dump()
