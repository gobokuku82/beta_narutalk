"""keyword_top_roas — 키워드 ROI Top-N + 경쟁 Badge (T07).

competition 컬럼이 그대로 Badge (high/mid/low). raw 정렬·slice 만.

Status: complete — Phase 1 Batch 6 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.keyword_performance import load_keyword_performance
from app.schemas.outputs.cost import KeywordTableOutput

logger = get_logger(__name__)


class KeywordTopRoas(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        n = int(merged.get("n", 12))

        rows = load_keyword_performance(self.fetch("keyword_performance", context)).rows
        top = sorted(rows, key=lambda r: r.roas, reverse=True)[:n]
        return KeywordTableOutput(rows=[r.model_dump() for r in top], count=len(top)).model_dump()
