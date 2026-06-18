"""Signup Conversion — methodology §S067 (가입 전환율).

회귀 (4월): 600 / 24,000 = 2.50%

Composer 패턴:
    - 분자: new_members_monthly (S069)
    - 분모: ga4_session_aggregator (정제 6) session_start_total

Status: complete — 2026-05-23 metrics 마지막 정량 정답.
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.metrics.new_members_monthly import NewMembersMonthly
from app.dream_agent.tools.metrics.ga4_session_aggregator import (
    Ga4SessionAggregator,
)
from app.dream_agent.tools.registry import get_registry

logger = get_logger(__name__)


class SignupConversion(BaseTool):
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM)")
        if "/" in period:
            raise ValueError("signup_conversion 는 단일 월만")

        reg = get_registry()

        # 분자 — new_members_monthly (S069)
        nmm = NewMembersMonthly(reg.get("new_members_monthly"))
        nmm_res = await nmm.execute({"period": period}, context)
        signups = nmm_res["new_members_total"]

        # 분모 — ga4_session_aggregator (정제 6)
        ga4 = Ga4SessionAggregator(reg.get("ga4_session_aggregator"))
        ga4_res = await ga4.execute({}, context)
        sessions = ga4_res["session_start_total"]

        ratio = round(signups / sessions * 100, 2) if sessions else 0.0

        key = f"S067_signup_conversion_{period}.json"
        logger.info(
            "signup_conversion",
            period=period, ratio=ratio, signups=signups, sessions=sessions,
        )
        return {
            "signup_conversion_pct": ratio,
            "signups": signups,
            "sessions": sessions,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "signups / sessions * 100 (round 2자리)"},
        }
