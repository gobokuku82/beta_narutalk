"""ai_recommendation — AI 추천 카드 (O05, 베타 0.001). ml_model.generate_recommendation.

ADR-027/028: ml_model adapter. POC = MockMlModel(data/ml_mock/recommendations/clumi.json),
MVP+ = LlmMlModel(현 LLM 인프라) swap (DI 1 줄). 단순 1-shot 추천.

Status: complete — Phase 1 Batch 6 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.ml_models import get_default_ml_model
from app.schemas.outputs.cost import RecommendationOutput

logger = get_logger(__name__)


class AiRecommendation(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)

        # context = 이전 step 산출(budget·keyword 요약) 흡수 가능 (POC mock 은 무시).
        ctx_summary: dict[str, Any] = {
            "client": context.client_id,
            "previous": context.previous_results,
            "methodology": merged.get("methodology", "광고 최적화 추천 (베타 0.001)"),
        }
        ml = get_default_ml_model()
        result = await ml.generate_recommendation(ctx_summary, client=context.client_id)

        rows = [
            {"priority": r.priority, "title": r.title, "detail": r.detail}
            for r in result.recommendations
        ]
        logger.info("ai_recommendation", cards=len(rows))
        return RecommendationOutput(rows=rows, count=len(rows)).model_dump()
