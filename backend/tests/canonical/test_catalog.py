# -*- coding: utf-8 -*-
"""Canonical Catalog API — /api/canonical/catalog 검증.

canonical 정형 테이블(정규화/계산/통합)을 소스별로 묶어 메타·컬럼 사전·행수를 반환하는지.
raw 제외 · 알려진 소스 그룹핑 · 컬럼 desc(데이터 사전) 채움 · 행수 일치.
실행: uv run pytest tests/canonical/test_catalog.py -v
"""
from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

CLIENT = "clumi"
EXPECT_ROWS = {
    "meta_ads_performance_normalized": 90, "naver_searchad_normalized": 180,
    "naver_advoost_normalized": 90, "kakao_bizmessage_normalized": 2,
    "naver_talktalk_normalized": 2, "orders_normalized": 1919, "blended_computed": 1,
}


async def _get_catalog():
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
    try:
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            return await ac.get("/api/canonical/catalog", params={"client": CLIENT})
    finally:
        await pool.close()


async def test_catalog_groups_canonical_only():
    """소스별 그룹 + canonical 테이블만(raw 제외) + 알려진 소스 등장."""
    r = await _get_catalog()
    assert r.status_code == 200, r.text
    data = r.json()
    all_tables = [t["table"] for s in data["sources"] for t in s["tables"]]
    # canonical 접미사만
    assert all(t.endswith(("_normalized", "_computed", "_blended")) for t in all_tables)
    # raw 테이블 없음
    assert not any("_raw" in t for t in all_tables)
    # 주요 소스 등장
    srcs = {s["source"] for s in data["sources"]}
    assert {"meta_ads_performance", "orders", "blended"} <= srcs


def _find(data, table):
    for s in data["sources"]:
        for t in s["tables"]:
            if t["table"] == table:
                return s, t
    return None, None


async def test_catalog_row_counts_and_dict():
    """행수 일치 + 컬럼 사전(desc) 채움 + layer 라벨."""
    data = (await _get_catalog()).json()
    for table, n in EXPECT_ROWS.items():
        s, t = _find(data, table)
        assert t is not None, f"{table} 카탈로그에 없음"
        assert t["row_count"] == n, f"{table}: {t['row_count']} != {n}"
        assert t["columns"], f"{table} 컬럼 없음"
        # 핵심 컬럼은 의미(desc) 보유
        named = {c["name"]: c["desc"] for c in t["columns"]}
        if table == "blended_computed":
            assert named.get("mer")            # MER 의미 채움
        if table == "meta_ads_performance_normalized":
            assert named.get("ad_cost_krw")    # 광고비 의미 채움


async def test_catalog_groups_have_labels():
    """소스 그룹/라벨 한글 — 메뉴얼 표시용."""
    data = (await _get_catalog()).json()
    groups = {s["group"] for s in data["sources"]}
    assert {"광고", "커머스", "통합"} <= groups
    # 정규화 테이블이 계산보다 먼저 (정렬)
    for s in data["sources"]:
        layers = [t["layer"] for t in s["tables"]]
        if "normalized" in layers and "computed" in layers:
            assert layers.index("normalized") < layers.index("computed")
