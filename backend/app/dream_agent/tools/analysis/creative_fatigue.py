"""creative_fatigue — 피로 소재 수 (K21). ml_model(MockMlModel) 호출.

POC = MockMlModel(data/ml_mock/fatigue/clumi.json). MVP+ = anomaly model.

Status: complete — Phase 1 Batch 5 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.ml_models import get_default_ml_model
from app.schemas.inputs.creatives import load_creatives
from app.schemas.outputs.dashboard_v1 import MetricScalarOutput

logger = get_logger(__name__)


class CreativeFatigue(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)

        creatives = load_creatives(self.fetch("creatives", context)).rows
        ml = get_default_ml_model()
        result = await ml.diagnose_fatigue([c.model_dump() for c in creatives], client=context.client_id)

        logger.info("creative_fatigue", total=result.total, fatigue=result.fatigue_count)
        return MetricScalarOutput(
            value=float(result.fatigue_count), op="fatigue_count",
            field="is_fatigue", label="피로 소재 수",
        ).model_dump()
