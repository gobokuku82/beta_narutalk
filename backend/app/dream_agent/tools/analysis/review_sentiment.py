"""review_sentiment — 리뷰 감성 분포 (C08). ml_model(MockMlModel) 호출.

ADR-027: Tool=production / ml_model 구현체 swap. 여기선 get_default_ml_model() 주입.
POC = MockMlModel(data/ml_mock/sentiment/clumi.json). MVP+ = ProductionMlModel.

Status: complete — Phase 1 Batch 4 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.ml_models import get_default_ml_model
from app.schemas.inputs.reviews import load_reviews
from app.schemas.outputs.trend import SentimentDistributionOutput

logger = get_logger(__name__)


class ReviewSentiment(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)

        reviews = load_reviews(self.fetch("reviews", context)).rows
        ml = get_default_ml_model()
        result = await ml.analyze_sentiment([r.text for r in reviews], client=context.client_id)

        logger.info("review_sentiment", n=len(reviews), total=result.total)
        return SentimentDistributionOutput(
            positive=result.positive,
            neutral=result.neutral,
            negative=result.negative,
            total=result.total,
        ).model_dump()
