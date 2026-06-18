# -*- coding: utf-8 -*-
"""Phase 1 Batch 3 (Channel) — daily_performance channel 집계 3 pipeline.

신규 데이터 0 (Batch 2 daily_performance 재사용). clumi 방향.

  C05 매체별 막대 (4 채널 집계 + 파생율)
  C06 전환 퍼널 (노출>클릭>전환)
  T05 매체 상세 테이블 (C05 와 cache 공유)
"""
from __future__ import annotations

import asyncio

import pytest

from app.data_sources import reset_data_source
from app.dream_agent.tools.shared.storage import FileStorage, reset_storage, set_storage
from app.pipelines import PipelineRunner, list_pipelines, load_pipeline

CLIENT = {"client": "clumi"}


@pytest.fixture(autouse=True)
def _isolated(tmp_path):
    reset_data_source()
    set_storage(FileStorage(tmp_path))
    yield
    reset_storage()


def _run(name, variables=CLIENT, runner=None):
    runner = runner or PipelineRunner()
    return asyncio.run(runner.run(load_pipeline(name), variables))


def test_c05_channel_bar():
    r = _run("channel_bar_metrics")
    assert r.status == "completed", r.error
    rows = r.output["rows"]
    assert r.output["count"] == 4  # A-5.3 canonical AD: advoost·google·meta·naver_sa (kakao=메시징 제외)
    assert {row["channel"] for row in rows} == {"advoost", "google", "meta", "naver_sa"}
    first = rows[0]
    assert {"channel", "impressions", "clicks", "conversions", "ctr", "cvr",
            "cpc", "cpa", "roas"} <= set(first)


def test_c06_funnel_monotonic():
    r = _run("channel_funnel")
    assert r.status == "completed", r.error
    rows = r.output["rows"]
    assert len(rows) == 3
    vals = [s["value"] for s in rows]
    assert vals[0] > vals[1] > vals[2]  # 노출 > 클릭 > 전환
    assert rows[0]["pct_of_top"] == 100.0


def test_t05_shares_c05_cache():
    """C05 먼저 실행(컴퓨트) → T05 = 동일 key cache hit."""
    runner = PipelineRunner()  # 같은 tmp workspace
    r_c05 = _run("channel_bar_metrics", runner=runner)
    assert r_c05.cache_hit is False
    r_t05 = _run("channel_table_detailed", runner=runner)
    assert r_t05.cache_hit is True
    assert r_t05.output["count"] == 4


def test_catalog_channel_has_3():
    ch = [p for p in list_pipelines() if p.category == "channel"]
    assert len(ch) == 3, sorted(p.name for p in ch)
