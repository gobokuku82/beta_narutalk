# -*- coding: utf-8 -*-
"""ad_cost_total — 마케팅비 라인 진입.

검증 (가 결정 A-5.2 2026-06-17: google 광고 매체 포함 re-baseline 18,306,923 → 26,806,923):
  AC1 4월 total = 26,806,923                ← §S003 + google (원안 5매체 18,306,923)
  AC2 매체별 정답 6개 (meta/naver_sa/advoost/google/kakao/talktalk)
  AC3 by_channel 합 = total
  AC4 period=None (전체) 도 동작
  ※ AC5·AC6(tool-save 단언) — ②-b contract B 후 삭제: tool 은 더는 저장하지 않음.
     entry-save(dashboard1 _cached_or_run) 동작은 test_route 가 검증.

  ※ H1/H2(ad_cost_helper unit) 제거 — A-5.1(2026-06-17): ad_cost_helper 폐기(canonical 전환·소비처 0).
"""
from __future__ import annotations
import asyncio

import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.metrics.ad_cost_total import AdCostTotal
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.storage import (
    FileStorage, reset_storage, set_storage,
)


@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(session_id="t", plan_id="t", client_id="clumi")


@pytest.fixture
def tool() -> AdCostTotal:
    return AdCostTotal(get_registry().get("ad_cost_total"))


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    set_storage(FileStorage(tmp_path))
    yield tmp_path
    reset_storage()


# ── 회귀 ──
def test_april_total_26806923(tool, ctx):
    """AC1: 4월 6매체 합 = 26,806,923 (가 결정 A-5.2 google 포함)."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["total_cost"] == 26_806_923, (
        f"expected 26,806,923 got {r['total_cost']:,}"
    )


def test_by_channel_match_methodology(tool, ctx):
    """AC2: 매체별 정답."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    expected = {
        "meta": 9_235_826,
        "naver_sa": 5_999_627,
        "advoost": 3_000_000,
        "google": 8_500_000,
        "kakao": 59_020,
        "talktalk": 12_450,
    }
    for ch, exp in expected.items():
        assert r["by_channel"][ch] == exp, f"{ch}: expected {exp:,} got {r['by_channel'][ch]:,}"


def test_by_channel_sum_equals_total(tool, ctx):
    """AC3: by_channel 합 = total_cost."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert sum(r["by_channel"].values()) == r["total_cost"]


def test_period_optional(tool, ctx):
    """AC4: period 없이도 동작 (mock 은 4월 단일이라 결과 동일).

    (슬라이스 1, 2026-06-12) 구버전은 period 미지정 시 데이터에 "period": "all" 을 방출 —
    하류 param 으로 주입돼 startswith('all') silent-0 의 오염원이었음. 이제 미방출을 박제.
    """
    r = asyncio.run(tool.execute({}, ctx))
    assert "period" not in r, "period 미지정 시 'all' 라벨 데이터 방출 금지 (헌법 D3·R2)"
    # mock 단일 월 — 4월과 결과 일치
    assert r["total_cost"] == 26_806_923


def test_period_passthrough_when_given(tool, ctx):
    """period 지정 시에는 실제 값이 데이터에 표기 (정직 라벨 — 'all' 만 금지)."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["period"] == "2026-04"

# (H1/H2 ad_cost_helper unit 테스트 제거 — A-5.1 2026-06-17: ad_cost_helper 폐기(소비처 0, canonical 전환 완료).
#  값 검증은 위 AC1~AC4가 canonical 경로로 동일 보장.)
