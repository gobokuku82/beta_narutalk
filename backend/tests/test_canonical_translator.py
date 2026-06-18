# -*- coding: utf-8 -*-
"""test_canonical_translator.py — 피봇 P2 격리: canonical_translator production tool 검증.

★증명 명제: production tool `normalization/canonical_translator` 가 raw 를
self.fetch(DataSource) 독립 경로로 normalize → 채널별·합 26,806,923 · MER 4.46 산출.
(가 결정 A-5.2: google 광고 매체 포함 re-baseline — 종전 5매체 18,306,923·6.53.)

ad_cost_total 도 canonical 소비로 전환됨(A3) → 본 테스트의 동치 검증은 두 canonical 경로
(translator ↔ ad_cost_total)의 일관성 확인. (옛 ad_cost_helper World-B 는 A-5.1 폐기.)

실행: uv run pytest backend/tests/test_canonical_translator.py -v
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

PERIOD = "2026-04"
# 가 결정 A-5.2(2026-06-17): google 광고 매체 포함 re-baseline (18.3M/6.53 → 26.8M/4.46).
EXPECT_CHANNEL = {"meta": 9_235_826, "naver_sa": 5_999_627, "advoost": 3_000_000, "google": 8_500_000,
                  "kakao": 59_020, "talktalk": 12_450}
EXPECT_TOTAL = 26_806_923
EXPECT_MER = 4.46
AD_CHANNELS = ("meta", "naver_sa", "advoost", "google")
MSG_CHANNELS = ("kakao", "talktalk")


def _ctx():
    from app.dream_agent.models import ExecutionContext
    return ExecutionContext(session_id="t", plan_id="t", client_id="clumi")


@pytest.fixture(scope="module")
def translated():
    """canonical_translator (registry 로드) 실행 결과."""
    from app.dream_agent.tools.registry import get_registry
    from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator
    tool = CanonicalTranslator(get_registry().get("canonical_translator"))
    return asyncio.run(tool.execute({"period": PERIOD}, _ctx()))


@pytest.fixture(scope="module")
def world_b():
    """production ad_cost_total (canonical 소비 경로, A3 전환) — 동치 대조."""
    from app.dream_agent.tools.metrics.ad_cost_total import AdCostTotal
    from app.dream_agent.tools.registry import get_registry
    from app.dream_agent.tools.shared.storage import FileStorage, reset_storage, set_storage
    with tempfile.TemporaryDirectory() as tmp:
        set_storage(FileStorage(Path(tmp)))
        try:
            tool = AdCostTotal(get_registry().get("ad_cost_total"))
            r = asyncio.run(tool.execute({"period": PERIOD}, _ctx()))
        finally:
            reset_storage()
    return r


# ── 등록 ──
def test_tool_registered():
    from app.dream_agent.tools.registry import get_registry
    assert get_registry().get("canonical_translator") is not None


# ── 정답 재현 ──
def test_total_marketing_cost(translated):
    assert translated["computed"]["total_marketing_cost_krw"] == EXPECT_TOTAL


def test_mer(translated):
    assert abs(translated["computed"]["mer"] - EXPECT_MER) <= 0.05


def test_ad_channels(translated):
    by = translated["computed"]["ad_cost_by_channel"]
    for c in AD_CHANNELS:
        assert by[c] == EXPECT_CHANNEL[c], f"{c}: {by[c]:,} != {EXPECT_CHANNEL[c]:,}"


def test_msg_channels(translated):
    by = translated["computed"]["msg_cost_by_channel"]
    for c in MSG_CHANNELS:
        assert by[c] == EXPECT_CHANNEL[c], f"{c}: {by[c]:,} != {EXPECT_CHANNEL[c]:,}"


# ── ★교차세계 동치: 신 production tool == 기존 production tool ──
def test_equivalent_to_ad_cost_total(translated, world_b):
    """canonical_translator total == ad_cost_total total (독립 경로, 동일 raw)."""
    assert translated["computed"]["total_marketing_cost_krw"] == world_b["total_cost"]
    a = translated["computed"]["ad_cost_by_channel"]
    m = translated["computed"]["msg_cost_by_channel"]
    merged = {**a, **m}
    for c in (*AD_CHANNELS, *MSG_CHANNELS):
        assert merged[c] == world_b["by_channel"][c], f"{c} 불일치"


# ── lineage 무결 (신뢰 동반) ──
def test_lineage_present(translated):
    lin = translated["lineage"]
    assert len(lin) > 0
    for l in lin:
        assert {"channel", "canonical", "source", "value", "transform"} <= set(l)


# ── storage 계약 (P1 rename tripwire 대비) ──
def test_storage_contract(translated):
    st = translated["_storage"]
    assert st["layer"] == "normalized"        # P1 normalized rename 시 본 assert 동반 갱신
    assert st["key"].startswith("canonical_normalized_")
