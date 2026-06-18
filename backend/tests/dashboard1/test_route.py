# -*- coding: utf-8 -*-
"""C:LUMI API route 20 endpoint — HTTP 회귀.

검증:
  H1 20 endpoint 모두 HTTP 200
  H2 정답 17개 HTTP 응답에서 그대로 확인 (S001·S002·S004·S005·S028·S032·S037·S045·S046·S048·S054·S067·S069·정제4·정제7·정제10·M-1)
  H3 period 형식 invalid → 400
  H4 _catalog endpoint 응답
  H5 캐시 hit/miss 동작 (1차 호출 후 2차 호출 = 동일 결과)

계획서: docs/_claude/frontend/clumi_2026_04_대시보드_계획서_2026-05-26.md §2 / §5 DoD Step 2
신설: 2026-05-26 — frontend Step 2.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_v2.routes.dashboard1 import router as dashboard1_router
from app.dream_agent.tools.shared.storage import (
    FileStorage, reset_storage, set_storage,
)


PERIOD = "2026-04"
PERIOD_PREV = "2026-03"


@pytest.fixture
def client(tmp_path) -> TestClient:
    """lifespan 우회 — dashboard1_router 만 단독 마운트."""
    set_storage(FileStorage(tmp_path))
    app = FastAPI()
    app.include_router(dashboard1_router)
    yield TestClient(app)
    reset_storage()


# =========================================================================
# Section 1. KPI 9 — HTTP 200 + 정답값
# =========================================================================


def test_kpi_revenue_119539660(client):
    r = client.get("/api/dashboard1/kpi/revenue", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["revenue_total"] == 119_539_660
    assert body["period"] == PERIOD


def test_kpi_ad_cost_26806923(client):
    r = client.get("/api/dashboard1/kpi/ad-cost", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["total_cost"] == 26_806_923   # 가 결정 A-5.2 google 포함 (원안 18,306,923)
    assert body["by_channel"]["meta"] == 9_235_826
    assert body["by_channel"]["naver_sa"] == 5_999_627
    assert body["by_channel"]["google"] == 8_500_000


def test_kpi_roas_446(client):
    r = client.get("/api/dashboard1/kpi/roas", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["roas"] == 4.46   # 가 결정 A-5.2 google 포함 (원안 6.53)
    assert body["total_revenue"] == 119_539_660
    assert body["total_marketing_cost"] == 26_806_923


def test_kpi_cac_44678(client):
    r = client.get("/api/dashboard1/kpi/cac", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["cac"] == 44_678   # 가 결정 A-5.2 google 포함 (원안 30,512)
    assert body["new_members_count"] == 600


def test_kpi_promotion_revenue_43400360(client):
    r = client.get("/api/dashboard1/kpi/promotion-revenue", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["promotion_revenue"] == 43_400_360
    assert body["promotion_share_pct"] == 36.3


def test_kpi_promotion_roas_162(client):
    r = client.get("/api/dashboard1/kpi/promotion-roas", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["promotion_roas"] == 1.62   # 가 결정 A-5.2 google 포함 (원안 2.37)


def test_kpi_new_members_600(client):
    r = client.get("/api/dashboard1/kpi/new-members", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["new_members_total"] == 600
    assert sum(body["new_members_by_channel"].values()) == 600


def test_kpi_aov_62293(client):
    r = client.get("/api/dashboard1/kpi/aov", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["aov"] == 62_293
    assert body["orders_count"] == 1_919


def test_kpi_signup_conversion_250(client):
    r = client.get("/api/dashboard1/kpi/signup-conversion", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["signup_conversion_pct"] == 2.50
    assert body["signups"] == 600


# =========================================================================
# Section 2. MoM 4
# =========================================================================


def test_mom_revenue_plus_505(client):
    r = client.get("/api/dashboard1/mom/revenue", params={"a": PERIOD_PREV, "b": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["delta_pct"] == 50.5
    assert body["period_b_revenue"] == 119_539_660


def test_mom_repurchase_192_14_28pp(client):
    r = client.get("/api/dashboard1/mom/repurchase", params={"a": PERIOD_PREV, "b": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["delta"]["existing_buyers_pct"] == 19.2
    assert body["delta"]["new_buyers_pct"] == 1.4
    assert body["delta"]["repurchase_rate_pp"] == 2.8
    assert body["period_a_stats"]["repurchase_rate"] == 76.2
    assert body["period_b_stats"]["repurchase_rate"] == 79.0


def test_mom_aov_orders_426(client):
    r = client.get("/api/dashboard1/mom/aov", params={"a": PERIOD_PREV, "b": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["delta"]["orders_pct"] == 42.6
    assert body["delta"]["aov_pct"] == 5.6


def test_mom_new_members_minus_02(client):
    r = client.get("/api/dashboard1/mom/new-members", params={"a": PERIOD_PREV, "b": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["delta_pct"] == -0.2
    assert body["period_b_total"] == 600
    assert body["period_a_total"] == 601


# =========================================================================
# Section 3-8. Segment 7
# =========================================================================


def test_segment_grade_silver_revenue(client):
    r = client.get("/api/dashboard1/segment/grade", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["silver_revenue"] == 65_757_080
    assert body["welcome_member_share"] == 74.5
    assert body["total_members"] == 8_500
    for g in ("VIP", "GOLD", "SILVER", "REGULAR", "WELCOME"):
        assert g in body["table"]


def test_segment_grade_timeseries_4_snapshots(client):
    r = client.get("/api/dashboard1/segment/grade-timeseries", params={"client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    totals = [snap["total"] for snap in body["timeline"]]
    assert totals == [6_680, 7_299, 7_900, 8_500]
    assert body["snapshot_count"] == 4


def test_segment_age_35_44_eq_2884(client):
    r = client.get("/api/dashboard1/segment/age", params={"client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["core_segment_35_44"] == 2_884
    assert body["table"]["40-44"]["count"] == 1_455


def test_segment_category_skincare_67M(client):
    r = client.get("/api/dashboard1/segment/category", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["by_category"]["스킨케어"]["revenue"] == 67_652_216
    assert body["by_category"]["스킨케어"]["count"] == 1_400


def test_segment_channel_unknown_481(client):
    r = client.get("/api/dashboard1/segment/channel", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["by_raw_channel"]["unknown"] == 481
    assert body["by_group"]["Naver"] == 530
    assert body["by_group"]["Meta"] == 388


def test_segment_member_guest_1779_140(client):
    r = client.get("/api/dashboard1/segment/member-guest", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["member_count"] == 1_779
    assert body["guest_count"] == 140
    assert body["total_active"] == 1_919


def test_segment_unknown_share_398(client):
    r = client.get("/api/dashboard1/segment/unknown-share", params={"period": PERIOD, "client": "clumi"})
    assert r.status_code == 200
    body = r.json()
    assert body["unknown_share_pct"] == 39.8
    assert body["total_revenue"] == 119_539_660


# =========================================================================
# H3. period 형식 invalid → 400
# =========================================================================


def test_invalid_period_format_returns_400(client):
    r = client.get("/api/dashboard1/kpi/revenue", params={"period": "2026/04", "client": "clumi"})
    assert r.status_code == 400


def test_missing_period_returns_422(client):
    """period 누락 → FastAPI 422 (Query required)."""
    r = client.get("/api/dashboard1/kpi/revenue")
    assert r.status_code == 422


# =========================================================================
# H4. _catalog
# =========================================================================


def test_catalog_endpoint(client):
    r = client.get("/api/dashboard1/_catalog")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 20
    paths = [ep["path"] for ep in body["endpoints"]]
    assert "/api/dashboard1/kpi/revenue" in paths
    assert "/api/dashboard1/segment/grade-timeseries" in paths


# =========================================================================
# H5. 캐시 hit/miss — 2회 호출 동일 응답
# =========================================================================


def test_cache_consistency_revenue(client):
    """1차 miss (tool 실행 + storage 저장) → 2차 hit (캐시 로드)."""
    r1 = client.get("/api/dashboard1/kpi/revenue", params={"period": PERIOD, "client": "clumi"})
    r2 = client.get("/api/dashboard1/kpi/revenue", params={"period": PERIOD, "client": "clumi"})
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()
    # _storage / _meta 가 응답에 들어가지 않음 (extra='ignore')
    assert "_storage" not in r1.json()
    assert "_meta" not in r1.json()
