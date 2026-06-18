"""review_keywords — 리뷰 키워드 랭킹 Top-N (C12). ml_model(MockMlModel) 호출.

POC = MockMlModel(data/ml_mock/keywords/clumi.json). MVP+ = 진짜 NLP.

Status: complete — Phase 1 Batch 4 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.ml_models import get_default_ml_model
from app.schemas.inputs.reviews import load_reviews
from app.schemas.outputs.trend import KeywordsTopNOutput

logger = get_logger(__name__)


class ReviewKeywords(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        n = int(merged.get("n", 10))

        reviews = load_reviews(self.fetch("reviews", context)).rows
        ml = get_default_ml_model()
        result = await ml.extract_keywords([r.text for r in reviews], client=context.client_id, top_n=n)

        rows = [{"keyword": k.keyword, "count": k.count} for k in result.keywords]
        return KeywordsTopNOutput(rows=rows, count=len(rows)).model_dump()
