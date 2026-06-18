"""campaigns_table — 캠페인 행 목록 (T04 테이블). 선택적 columns projection.

Status: complete — Phase 1 Batch 2 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.campaigns import load_campaigns
from app.schemas.outputs.dashboard_v1 import CampaignsTableOutput

logger = get_logger(__name__)


class CampaignsTable(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        columns = merged.get("columns")  # None = 전 컬럼

        rows = load_campaigns(self.fetch("campaigns", context)).rows
        out_rows: list[dict[str, Any]] = []
        for r in rows:
            d = r.model_dump()
            out_rows.append({c: d.get(c) for c in columns} if columns else d)

        return CampaignsTableOutput(rows=out_rows, count=len(out_rows)).model_dump()
