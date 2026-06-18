# -*- coding: utf-8 -*-
"""마케팅비 라인 4 metrics 회귀 — S002·S004·S032·S005.

검증 (모두 4월 · 가 결정 A-5.2 2026-06-17: google 포함 re-baseline):
  P1 S002 promotion_revenue = 43,400,360 (share 36.3%)
  R1 S004 roas              = 4.46  (6.53 → google 포함)
  C1 S032 cac               = 44,678 (30,512 → google 포함)
  PR1 S005 promotion_roas   = 1.62  (2.37 → google 포함)
  + 각 tool 의 입력 일관성 (총매출 119,539,660 · 총마케팅비 26,806,923 · 신규 600)
"""
from __future__ import annotations
import asyncio
import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.metrics.cac_overall import CacOverall
from app.dream_agent.tools.metrics.promotion_revenue import PromotionRevenue
from app.dream_agent.tools.metrics.promotion_roas import PromotionRoas
from app.dream_agent.tools.metrics.roas_overall import RoasOverall
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.storage import (
    FileStorage, reset_storage, set_storage,
)


@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(session_id="t", plan_id="t", client_id="clumi")


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    set_storage(FileStorage(tmp_path))
    yield
    reset_storage()


# ── S002 ──
def test_promotion_revenue_43400360(ctx):
    tool = PromotionRevenue(get_registry().get("promotion_revenue"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["promotion_revenue"] == 43_400_360
    assert r["promotion_share_pct"] == 36.3
    assert r["total_revenue"] == 119_539_660


# ── S004 ──
def test_roas_446(ctx):
    tool = RoasOverall(get_registry().get("roas_overall"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["roas"] == 4.46
    assert r["total_revenue"] == 119_539_660
    assert r["total_marketing_cost"] == 26_806_923


# ── S032 ──
def test_cac_44678(ctx):
    tool = CacOverall(get_registry().get("cac_overall"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["cac"] == 44_678
    assert r["total_marketing_cost"] == 26_806_923
    assert r["new_members_count"] == 600


# ── S005 ──
def test_promotion_roas_162(ctx):
    tool = PromotionRoas(get_registry().get("promotion_roas"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["promotion_roas"] == 1.62
    assert r["promotion_revenue"] == 43_400_360
    assert r["total_marketing_cost"] == 26_806_923


# ── 일관성: ROAS·CAC·promo_ROAS 의 입력 동일성 ──
def test_consistency_across_tools(ctx):
    """4 tool 의 마케팅비·매출·신규 값이 정확히 일치 (다른 라인 산출 X)."""
    reg = get_registry()
    r1 = asyncio.run(RoasOverall(reg.get("roas_overall")).execute({"period": "2026-04"}, ctx))
    r2 = asyncio.run(CacOverall(reg.get("cac_overall")).execute({"period": "2026-04"}, ctx))
    r3 = asyncio.run(PromotionRoas(reg.get("promotion_roas")).execute({"period": "2026-04"}, ctx))
    # 같은 마케팅비
    assert r1["total_marketing_cost"] == r2["total_marketing_cost"] == r3["total_marketing_cost"] == 26_806_923
    # 같은 프로모션 매출
    r4 = asyncio.run(PromotionRevenue(reg.get("promotion_revenue")).execute({"period": "2026-04"}, ctx))
    assert r3["promotion_revenue"] == r4["promotion_revenue"] == 43_400_360


# ── 입력 검증 ──
def test_invalid_period_all(ctx):
    """4 tool 모두 단일 월 강제 + period 누락 거부."""
    reg = get_registry()
    for name, cls in [
        ("promotion_revenue", PromotionRevenue),
        ("roas_overall", RoasOverall),
        ("cac_overall", CacOverall),
        ("promotion_roas", PromotionRoas),
    ]:
        tool = cls(reg.get(name))
        with pytest.raises(ValueError, match="period"):
            asyncio.run(tool.execute({}, ctx))
        with pytest.raises(ValueError, match="단일 월"):
            asyncio.run(tool.execute({"period": "2026-03/2026-04"}, ctx))
