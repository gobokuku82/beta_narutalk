# -*- coding: utf-8 -*-
"""Phase B — 21 collector 통합 회귀.

검증:
  C1 21 collector 모두 import + 실행 (대용량 #8 GA4 page events 는 import 만)
  C2 핵심 회귀값:
     orders=3420 · customers=8500 · signup=600 · grade_history=30379
     ga4_traffic=38319 · advoost=90 · household=12 · category_sales=155
  C3 thin pattern — Clumi*Collector 가 RawCollectorBase 의 subclass
"""
from __future__ import annotations
import asyncio
import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.collection._base import RawCollectorBase
from app.dream_agent.tools.registry import get_registry


@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(session_id="t", plan_id="t", client_id="clumi")


# ── 회귀값 ──
EXPECTED_COUNTS = {
    "orders_collector": 3420,
    "customers_collector": 8500,
    "signup_events_collector": 600,
    "customer_rfm_collector": 8500,
    "customer_grade_history_collector": 30379,
    "ga4_traffic_source_collector": 38319,
    "naver_advoost_collector": 90,
    "household_structure_collector": 12,
    "category_sales_collector": 155,
}


def test_all_21_collectors_registered():
    """C1: 21 raw collector 모두 catalog 등록 (clumi_ prefix 제거 후 — 2026-05-27)."""
    reg = get_registry()
    # collection/external·internal 의 collector. *_collector 로 끝나면서 다른 카테고리 collector
    # (google_ads·meta·naver_gfa·kakao·naver_sa·review) 와 구분 위해 화이트리스트.
    # 단순화: 21 raw collector 의 source_id 화이트리스트
    RAW_COLLECTORS = {
        "ad_change_history_collector", "category_sales_collector",
        "crm_messages_collector", "customer_grade_history_collector",
        "customer_rfm_collector", "customers_collector",
        "ga4_page_events_collector", "ga4_traffic_source_collector",
        "household_structure_collector", "instagram_engagement_collector",
        "kakao_bizmessage_collector", "meta_ads_by_age_collector",
        "meta_ads_performance_collector", "meta_instagram_inapp_collector",
        "naver_advoost_collector", "naver_interest_alert_collector",
        "naver_searchad_collector", "naver_talktalk_collector",
        "orders_collector", "promotions_collector", "signup_events_collector",
    }
    found = {t.name for t in reg.get_all() if t.name in RAW_COLLECTORS}
    assert found == RAW_COLLECTORS, f"missing: {RAW_COLLECTORS - found}"


@pytest.mark.parametrize("name,expected", EXPECTED_COUNTS.items())
def test_collector_count_regression(ctx, name, expected):
    """C2: 각 collector 의 count 회귀 (실 raw row 수)."""
    reg = get_registry()
    cls = reg.import_tool(name)
    r = asyncio.run(cls(reg.get(name)).execute({}, ctx))
    assert r["count"] == expected, f"{name}: expected {expected}, got {r['count']}"


def test_all_subclass_of_base():
    """C3: 21 raw collector 모두 RawCollectorBase subclass (clumi_ prefix 제거 후)."""
    reg = get_registry()
    # collection/external·internal 의 collector 만 검증 (다른 collector 와 구분)
    from app.dream_agent.tools.collection._base import RawCollectorBase as _Base
    raw_count = 0
    for t in reg.get_all():
        if not t.name.endswith("_collector"):
            continue
        try:
            cls = reg.import_tool(t.name)
        except ImportError:
            continue
        if not issubclass(cls, _Base):
            continue  # 다른 카테고리 collector (google_ads 등)
        assert cls.FILE_NO > 0, f"{t.name} FILE_NO 미설정"
        assert cls.PRODUCES_KEY != "raw", f"{t.name} PRODUCES_KEY 미커스터마이즈"
        raw_count += 1
    assert raw_count == 21, f"expected 21 raw collectors, got {raw_count}"
