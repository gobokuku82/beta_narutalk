"""Cognitive provenance / client 프로필 — 결정론적 단위테스트 (2026-06-04, Q1).

원칙: silent fallback 금지. 어떤 client 프로필로 cognitive 가 돌았는지 항상 명시.
  - client_id 명시 + 프로필 없음 → fail-fast (조용한 generic 금지).
  - 프로필 로더는 사실만 (clumi 로드, 미존재 None).

fail-fast 경로는 LLM 호출 *전* 반환하므로 API 없이 결정론적으로 검증 가능.
"""
from __future__ import annotations

from langgraph.graph import END

from app.dream_agent.cognitive.cognitive_stage import (
    _build_client_block,
    _load_client_profile,
    cognitive_stage,
)
from app.dream_agent.states.agent_state import init_agent_state


async def test_failfast_when_client_set_but_profile_missing():
    # 명시된 client 인데 프로필 없음 → generic fallback 안 하고 에러 (LLM 호출 전 반환)
    st = init_agent_state(
        user_input="4월 매출 알려줘", conversation_id="c", turn_id="t1", client_id="bogus_xyz",
    )
    cmd = await cognitive_stage(st)
    assert cmd.goto == END
    err = (cmd.update or {}).get("error", "")
    assert "bogus_xyz" in err and "프로필 없음" in err


def test_profile_loader_facts():
    assert _load_client_profile("clumi") is not None      # 실제 프로필 존재
    assert _load_client_profile("bogus_xyz") is None       # 미존재 → None (caller 가 fail-fast 결정)
    assert _load_client_profile(None) is None               # client_id 없음 → None (generic)


def test_clumi_profile_block_contains_brand_and_sources():
    profile = _load_client_profile("clumi")
    block = _build_client_block(profile)
    assert "C:LUMI" in block            # brand_context 주입
    assert "보유 데이터 소스" in block    # available_sources 주입
    assert "KPI" in block                # metric_glossary 주입
