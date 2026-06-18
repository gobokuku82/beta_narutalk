"""복합쿼리 planning stage3 크래시 — 원인 가설 검증 (2026-06-06).

원인분석: docs/_claude/4layer_system/stage3_truncation_rootcause_260606_v1.md
가설: stage3 출력이 max_tokens=2500 에서 잘려(truncation) json.loads 실패 → generate_json
      이 ValueError(복구·재시도 0) → planner None → "stage3 todo_builder failed".

여기선 결정론으로 메커니즘을 못박는다 (LLM mock — 키 불필요):
  H1 truncated/invalid 출력 → ValueError("Invalid JSON") (복구 0)
  H2 단발 — 재시도 없음 (truncation 시 즉시 총체 실패)
  H3 planning 캡 = 2500 (복합 plan 엔 부족 = 트리거)
  (대조) 정상 JSON 은 통과 — 잘림만 문제.
H4(복합 plan 출력이 2500 초과)는 비결정·LLM 이라 repro/하니스 라이브 입증(문서 §2).
"""
from __future__ import annotations

import asyncio

import pytest

from app.dream_agent.llm_manager.client import LLMClient
from app.dream_agent.llm_manager.config import LAYER_CONFIGS


def _planning_client() -> LLMClient:
    """__init__(provider client 생성=키 필요) 우회 — generate_json 은 config+generate 만 씀."""
    c = object.__new__(LLMClient)
    c.config = LAYER_CONFIGS["planning"]
    return c


# ── H3: 캡 (root trigger 였음). F1(2026-06-06)으로 2500→12000 상향 ──

def test_h3_planning_max_tokens_raised_for_complex_plans():
    # 원인: 2500 캡이 복합 plan 출력을 잘랐다. F1 수정: 12000 으로 상향 → 복합 plan 이 캡 안에 듦.
    # (H1/H2 = truncation *시* 동작은 불변 — 캡을 더 키워도 복구·재시도는 별도 안건 F2.)
    assert LAYER_CONFIGS["planning"].max_tokens >= 12000, \
        "F1: planning 캡을 2500→12000 상향(복합 plan truncation 방지). 회귀 시 여기서 잡힘."


# ── H1: 잘린 출력 → ValueError, 복구 없음 ──

def test_h1_truncated_output_raises_invalid_json():
    c = _planning_client()
    # repro 재현: stage3 가 긴 plan 을 쓰다 char 경계에서 끊긴 모양
    truncated = '{"todos": [{"id": "todo_001", "tool": "meta_ads_performance_collector", "rationale": "광고성과 원천 수집'

    async def fake_generate(prompt, system_prompt=None, **kw):  # noqa: ANN001
        return truncated

    c.generate = fake_generate  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="Invalid JSON"):
        asyncio.run(c.generate_json("p", system_prompt="s"))


# ── H2: 단발 — 재시도/복구 없음 ──

def test_h2_no_retry_single_attempt():
    c = _planning_client()
    calls = {"n": 0}

    async def fake_generate(prompt, system_prompt=None, **kw):  # noqa: ANN001
        calls["n"] += 1
        return "{ this is not valid json"

    c.generate = fake_generate  # type: ignore[method-assign]
    with pytest.raises(ValueError):
        asyncio.run(c.generate_json("p"))
    assert calls["n"] == 1, "재시도가 있었다면 >1. 단발이라 truncation = 즉시 총체 실패."


# ── 대조: 정상 JSON 은 통과 (파서 자체는 멀쩡 — 잘림만 문제) ──

def test_valid_complete_json_passes():
    c = _planning_client()

    async def fake_generate(prompt, system_prompt=None, **kw):  # noqa: ANN001
        return '{"todos": [], "dag": {}, "plan_notes": "ok"}'

    c.generate = fake_generate  # type: ignore[method-assign]
    out = asyncio.run(c.generate_json("p"))
    assert out["plan_notes"] == "ok"
