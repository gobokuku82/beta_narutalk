"""Grade Timeseries — methodology §S045 (등급별 회원수 4시점 시계열).

회귀 (#21 customer_grade_history):
    2026-01-31: 6,680
    2026-02-28: 7,299
    2026-03-31: 7,900
    2026-04-30: 8,500 (= customers 전체)

Status: complete — 2026-05-25.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_str

logger = get_logger(__name__)

GRADE_ORDER = ["WELCOME", "REGULAR", "SILVER", "GOLD", "VIP"]


class GradeTimeseries(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        df = self.fetch("grade_history", context)

        by_snap: dict[str, dict] = defaultdict(lambda: {g: 0 for g in GRADE_ORDER})
        for _, row in df.iterrows():
            snap = safe_str(row["snapshot_date"])
            grade = safe_str(row["grade"])
            if grade in by_snap[snap]:
                by_snap[snap][grade] += 1

        # timeline 정렬
        timeline = []
        for snap in sorted(by_snap.keys()):
            counts = by_snap[snap]
            total = sum(counts.values())
            timeline.append({
                "snapshot_date": snap,
                "grade_counts": counts,
                "total": total,
            })

        latest = timeline[-1] if timeline else None
        first = timeline[0] if timeline else None

        # 등급별 증가율 (latest vs first)
        growth_rates: dict[str, float] = {}
        if first and latest:
            for g in GRADE_ORDER:
                a = first["grade_counts"][g]; b = latest["grade_counts"][g]
                growth_rates[g] = round((b - a) / a * 100, 1) if a else None

        key = "S045_grade_timeseries.json"
        logger.info("grade_timeseries",
                    snapshots=len(timeline),
                    latest=latest["total"] if latest else 0)
        return {
            "timeline": timeline,
            "latest_snapshot": latest,
            "growth_rates": growth_rates,
            "snapshot_count": len(timeline),
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "COUNT(member_id) GROUP BY snapshot_date, grade"},
        }
