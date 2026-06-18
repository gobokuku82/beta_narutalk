# -*- coding: utf-8 -*-
"""test_dimension_normalizer_prototype.py — Step3 프로토타입 검증 (2026-06-16).

★증명할 설계 명제: 단일 **contract-driven dimension translator**(data_pilot_project/dimensions.py,
config 외부화)가 production 의 *하드코딩 normalizer 3종*을 동일 결과로 흡수 가능한가.
  - channel_attribution_normalizer (CHANNEL_GROUP_MAP) → channel_group
  - grade_system_unifier (STANDARD_ORDER)              → membership_grade
  - utm_normalizer (normalize_utm 규칙)                → utm_source/medium

측정값(test_normalized_pivot_baseline.py)에 이은 *차원* 교차세계 동치. 통과 = 피봇 §3.2 의
"normalization REPLACE → canonical translator 흡수" 가 차원에서도 실증됨 (Step4 표의 근거).

실행: uv run pytest backend/tests/test_dimension_normalizer_prototype.py -v
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
_DP = BACKEND / "app" / "data_pilot_project"
if str(_DP) not in sys.path:
    sys.path.insert(0, str(_DP))

PERIOD = "2026-04"


def _ctx():
    from app.dream_agent.models import ExecutionContext
    return ExecutionContext(session_id="t", plan_id="t", client_id="clumi")


@pytest.fixture(autouse=True)
def isolated_storage():
    from app.dream_agent.tools.shared.storage import FileStorage, reset_storage, set_storage
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        set_storage(FileStorage(Path(tmp)))
        yield
        reset_storage()


# ── World B: production normalizer ──
def _prod_channel_group():
    from app.dream_agent.tools.registry import get_registry
    from app.dream_agent.tools.normalization.channel_attribution_normalizer import ChannelAttributionNormalizer
    t = ChannelAttributionNormalizer(get_registry().get("channel_attribution_normalizer"))
    return asyncio.run(t.execute({"period": PERIOD}, _ctx()))["by_group"]


def _prod_grade():
    from app.dream_agent.tools.registry import get_registry
    from app.dream_agent.tools.normalization.grade_system_unifier import GradeSystemUnifier
    t = GradeSystemUnifier(get_registry().get("grade_system_unifier"))
    return asyncio.run(t.execute({}, _ctx()))["standard_grade_dist"]


def _prod_utm():
    from app.dream_agent.tools.registry import get_registry
    from app.dream_agent.tools.normalization.utm_normalizer import UtmNormalizer
    t = UtmNormalizer(get_registry().get("utm_normalizer"))
    r = asyncio.run(t.execute({"period": PERIOD}, _ctx()))
    return r["source_dist"], r["medium_dist"]


# ── 교차세계 동치 ──
def test_channel_group_equivalent():
    """프로토타입 channel_group == production channel_attribution_normalizer.by_group."""
    import dimensions as proto
    proto_d = proto.channel_group(PERIOD)
    prod_d = _prod_channel_group()
    assert proto_d == prod_d, f"channel_group 불일치:\n proto={proto_d}\n prod ={prod_d}"
    assert sum(proto_d.values()) > 0


def test_membership_grade_equivalent():
    """프로토타입 membership_grade == production grade_system_unifier.standard_grade_dist."""
    import dimensions as proto
    proto_d = proto.membership_grade()
    prod_d = _prod_grade()
    assert proto_d == prod_d, f"membership_grade 불일치:\n proto={proto_d}\n prod ={prod_d}"
    assert sum(proto_d.values()) > 0


def test_utm_equivalent():
    """프로토타입 utm == production utm_normalizer.source_dist/medium_dist."""
    import dimensions as proto
    proto_d = proto.utm(PERIOD)
    prod_src, prod_med = _prod_utm()
    assert proto_d["source"] == prod_src, f"utm source 불일치:\n proto={proto_d['source']}\n prod ={prod_src}"
    assert proto_d["medium"] == prod_med, f"utm medium 불일치:\n proto={proto_d['medium']}\n prod ={prod_med}"


def test_absorption_design_proof():
    """설계 명제: 1 config-driven translator 가 3 production normalizer 를 흡수.

    dimensions.py 는 하드코딩 dict 없이 dimension_maps.yaml(외부화)로 3 차원 산출.
    위 3 동치 테스트가 통과하면 'normalization REPLACE → canonical translator' 가 차원에서 실증됨.
    """
    import dimensions as proto
    out = proto.run_dimensions(PERIOD)
    assert set(out) == {"channel_group", "membership_grade", "utm"}
    # 하드코딩 매핑이 모듈 코드가 아니라 config 에서 옴 (외부화 확인)
    assert proto.CFG["channel_group"]["map"]["meta_facebook"] == "Meta"
    assert proto.CFG["membership_grade"]["order"][0] == "WELCOME"
