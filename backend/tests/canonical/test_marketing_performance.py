# -*- coding: utf-8 -*-
"""Canonical Read API — /api/canonical/marketing-performance 검증.

새 World-A 정형 테이블(clumi.blended_computed·*_normalized)을 직접 SELECT·집계해 서빙하는지.
★ 신뢰 게이트: KPI total_marketing_cost=26,806,923·MER 4.46 (가 결정 A-5.2 google 포함).
+ 채널 집계(Σrev/Σcost roas)·메시징 분리(C6.3)·일별 추이·KPI↔채널합 정합.

lifespan(LangGraph/checkpointer) 우회 — asyncpg 풀 직접 생성해 최소 app.state에 주입.
실행: uv run pytest tests/canonical/test_marketing_performance.py -v
"""
from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

PERIOD = "2026-04"
CLIENT = "clumi"
# 가 결정 A-5.2(2026-06-17): google 광고 매체 포함 re-baseline (18.3M/6.53 → 26.8M/4.46).
EXPECT_TOTAL = 26_806_923
EXPECT_MER = 4.46
AD = {"meta", "naver_sa", "advoost", "google"}
MSG = {"kakao", "talktalk"}


async def _client_and_pool():
    """canonical 라우터만 올린 최소 app + 실 asyncpg 풀. DB 미가용 시 skip."""
    import asyncpg
    from fastapi import FastAPI
    from app.data_pg_util import data_dsn
    from api_v2.routes.canonical import router
    try:
        pool = await asyncpg.create_pool(data_dsn(), min_size=1, max_size=2)
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"data DB 미가용: {e}")
    app = FastAPI()
    app.state.data_db_pool = pool
    app.include_router(router)
    ac = httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t")
    return ac, pool


async def _get():
    ac, pool = await _client_and_pool()
    try:
        async with ac:
            r = await ac.get("/api/canonical/marketing-performance",
                             params={"client": CLIENT, "period": PERIOD})
        return r
    finally:
        await pool.close()


async def test_kpi_reproduces_cross_world_answer():
    """blended KPI = 교차세계 정답 (새 테이블이 옛 답 재현)."""
    r = await _get()
    assert r.status_code == 200, r.text
    kpi = r.json()["kpi"]
    assert kpi["total_marketing_cost_krw"] == EXPECT_TOTAL
    assert abs(kpi["mer"] - EXPECT_MER) <= 0.05
    assert kpi["total_ad_cost_krw"] + kpi["total_msg_cost_krw"] == kpi["total_marketing_cost_krw"]


async def test_ad_channels_aggregated_and_msg_separated():
    """광고 채널 ROAS=Σrev/Σcost·메시징은 ad_channels에 섞이지 않음(C6.3)."""
    r = await _get()
    data = r.json()
    ad_names = {c["channel"] for c in data["ad_channels"]}
    msg_names = {c["channel"] for c in data["msg_channels"]}
    assert ad_names == AD, ad_names
    assert msg_names == MSG, msg_names
    assert ad_names.isdisjoint(msg_names)               # 광고·메시징 분리
    for c in data["ad_channels"]:
        if c["ad_cost_krw"]:
            assert c["roas_x"] == round(c["conversion_revenue_krw"] / c["ad_cost_krw"], 2)
        assert "msg_roi_pct" not in c                    # 메시징 지표 누설 없음


async def test_kpi_matches_channel_sums():
    """KPI 총광고비/총메시징비 == 채널 집계 합 (정합)."""
    data = (await _get()).json()
    kpi = data["kpi"]
    assert sum(c["ad_cost_krw"] for c in data["ad_channels"]) == kpi["total_ad_cost_krw"]
    assert sum(c["msg_cost_krw"] for c in data["msg_channels"]) == kpi["total_msg_cost_krw"]


async def test_daily_present_and_sums_to_total_ad_cost():
    """일별 추이 존재 + 일별 광고비 합 == 총광고비."""
    data = (await _get()).json()
    daily = data["daily"]
    assert daily, "일별 추이 비어있음"
    assert all("report_date" in d and "roas_x" in d for d in daily)
    assert sum(d["ad_cost_krw"] for d in daily) == data["kpi"]["total_ad_cost_krw"]


async def test_campaigns_drilldown_consistent():
    """캠페인 드릴다운 — 광고 채널만·캠페인 광고비 합 == 채널 광고비 합·파생 결정성."""
    data = (await _get()).json()
    campaigns = data["campaigns"]
    assert campaigns, "캠페인 드릴다운 비어있음"
    assert {c["channel"] for c in campaigns} <= AD            # 광고 채널만 (메시징 제외)
    # 캠페인 광고비 총합 == 채널 광고비 총합 (집계 정합)
    assert sum(c["ad_cost_krw"] for c in campaigns) == data["kpi"]["total_ad_cost_krw"]
    # 채널별로도 정합
    by_ch: dict[str, int] = {}
    for c in campaigns:
        by_ch[c["channel"]] = by_ch.get(c["channel"], 0) + c["ad_cost_krw"]
    for ch in data["ad_channels"]:
        assert by_ch.get(ch["channel"], 0) == ch["ad_cost_krw"], ch["channel"]
    # roas 재계산 결정성 + meta·google campaign_name 보유
    for c in campaigns:
        if c["ad_cost_krw"]:
            assert c["roas_x"] == round(c["conversion_revenue_krw"] / c["ad_cost_krw"], 2)
    assert any(c["campaign_name"] for c in campaigns if c["channel"] == "meta")
    assert any(c["campaign_name"] for c in campaigns if c["channel"] == "google")
