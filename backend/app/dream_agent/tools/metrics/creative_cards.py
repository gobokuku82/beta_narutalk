"""creative_cards — 소재 카드 Top-N (O04). sort_by 지표 desc + slice.

Status: complete — Phase 1 Batch 5 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.creatives import load_creatives
from app.schemas.outputs.creative import CreativeCardsOutput

logger = get_logger(__name__)


class CreativeCards(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        n = int(merged.get("n", 9))
        sort_by = merged.get("sort_by", "roas")

        rows = load_creatives(self.fetch("creatives", context)).rows
        top = sorted(rows, key=lambda c: getattr(c, sort_by, 0), reverse=True)[:n]
        return CreativeCardsOutput(rows=[c.model_dump() for c in top], count=len(top)).model_dump()
