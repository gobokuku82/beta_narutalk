# -*- coding: utf-8 -*-
"""preprocessing 2 — member_guest_stats (정제 10) + category_multi_distributor (정제 7).

검증:
  MG1 4월: 회원 1779 / 비회원 140 / 합 1919
  MG2 전체: 회원 3007 / 비회원 258 / 합 3265
  CD1 4월 스킨케어 매출 67,652,216
  CD2 4월 카테고리 5종 (스킨케어·클렌징·마스크팩·자외선차단·기타)
  CD3 method='other' 거부
"""
from __future__ import annotations
import asyncio
import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.metrics.category_multi_distributor import (
    CategoryMultiDistributor,
)
from app.dream_agent.tools.metrics.member_guest_stats import (
    MemberGuestStats,
)
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


# ── member_guest_stats ──
def test_split_april(ctx):
    tool = MemberGuestStats(get_registry().get("member_guest_stats"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["member_count"] == 1779
    assert r["guest_count"] == 140
    assert r["total_active"] == 1919


def test_split_all(ctx):
    tool = MemberGuestStats(get_registry().get("member_guest_stats"))
    r = asyncio.run(tool.execute({}, ctx))
    assert r["member_count"] == 3007
    assert r["guest_count"] == 258
    assert r["total_active"] == 3265


def test_split_share_sum(ctx):
    tool = MemberGuestStats(get_registry().get("member_guest_stats"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert 99.5 <= r["member_share_pct"] + r["guest_share_pct"] <= 100.5


# ── category_multi_distributor ──
def test_category_skincare_revenue(ctx):
    """스킨케어 분배 매출 = 67,652,216 (4월)."""
    tool = CategoryMultiDistributor(get_registry().get("category_multi_distributor"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["by_category"]["스킨케어"]["revenue"] == 67_652_216
    assert r["by_category"]["스킨케어"]["count"] == 1400


def test_category_top_5_match(ctx):
    """5 카테고리 정답값."""
    tool = CategoryMultiDistributor(get_registry().get("category_multi_distributor"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    expected = {
        "스킨케어":   {"count": 1400, "revenue": 67_652_216},
        "클렌징":     {"count": 497,  "revenue": 19_126_163},
        "마스크팩":   {"count": 464,  "revenue": 19_366_323},
        "자외선차단": {"count": 161,  "revenue": 6_864_031},
        "기타":       {"count": 166,  "revenue": 6_530_924},
    }
    for cat, exp in expected.items():
        assert r["by_category"][cat]["count"] == exp["count"], (
            f"{cat} count {r['by_category'][cat]['count']} != {exp['count']}"
        )
        assert r["by_category"][cat]["revenue"] == exp["revenue"], (
            f"{cat} rev {r['by_category'][cat]['revenue']} != {exp['revenue']}"
        )


def test_category_method_invalid(ctx):
    tool = CategoryMultiDistributor(get_registry().get("category_multi_distributor"))
    with pytest.raises(ValueError, match="method"):
        asyncio.run(tool.execute({"period": "2026-04", "method": "other"}, ctx))
