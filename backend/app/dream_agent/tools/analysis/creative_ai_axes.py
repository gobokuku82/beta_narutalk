"""creative_ai_axes — 소재 AI 5축 평균 (C11 radar). ml_model(MockMlModel) 호출.

POC = MockMlModel(data/ml_mock/ai_axes/clumi.json). MVP+ = CV/LLM scorer.

Status: complete — Phase 1 Batch 5 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.ml_models import get_default_ml_model
from app.schemas.inputs.creatives import load_creatives
from app.schemas.outputs.creative import AiAxesRadarOutput

logger = get_logger(__name__)


class CreativeAiAxes(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)

        creatives = load_creatives(self.fetch("creatives", context)).rows
        ml = get_default_ml_model()
        result = await ml.score_ai_axes([c.model_dump() for c in creatives], client=context.client_id)

        return AiAxesRadarOutput(**result.as_axes()).model_dump()
