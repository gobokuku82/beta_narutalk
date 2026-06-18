"""ab_test_table — AB 테스트 테이블 (T06). winner·lift_pct tool 파생.

Status: complete — Phase 1 Batch 5 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.ab_tests import load_ab_tests
from app.schemas.outputs.creative import AbTestTableOutput

logger = get_logger(__name__)


class AbTestTable(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)

        tests = load_ab_tests(self.fetch("ab_tests", context)).rows
        rows: list[dict[str, Any]] = []
        for t in tests:
            d = t.model_dump()
            hi, lo = max(t.a_value, t.b_value), min(t.a_value, t.b_value)
            d["winner"] = "A" if t.a_value >= t.b_value else "B"
            d["lift_pct"] = round((hi / lo - 1) * 100, 1) if lo else 0.0
            rows.append(d)
        return AbTestTableOutput(rows=rows, count=len(rows)).model_dump()
