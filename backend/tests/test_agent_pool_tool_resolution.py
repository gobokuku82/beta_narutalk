"""execution tool 해석 robustness — by-name fallback 결정론 단위테스트 (2026-06-04, W3-fix).

발견(end-to-end): planning Stage3 LLM 이 (agent, tool) 쌍에서 *agent 를 틀리게 추측*하면
(예: review_normalizer 를 channel_normalizing_agent 가 아닌 text_preprocessing_agent 에 배정)
agent_pool.get_tool_meta(틀린agent, tool)=None → executor 가 'neither implemented nor stub' → 실행 실패.
근데 get_real_tool(tool_name) 은 이미 *이름만으로* tool 을 만든다(agent 불필요). 카탈로그상 tool명 유일.

fix: get_tool_meta 가 (agent,tool) 못 찾으면 *모든 agent* 에서 tool명으로 복구 → planning 의 agent 추측에 execution 이 안 깨짐. (작동 robustness, 검증단계 아님.)
"""
from __future__ import annotations

from app.dream_agent.execution.agent_pool import get_agent_pool


def test_tool_meta_by_name_fallback_when_agent_wrong():
    pool = get_agent_pool()
    # review_normalizer 는 channel_normalizing_agent 소속. 틀린 agent 로 조회해도 by-name 복구.
    meta = pool.get_tool_meta("text_preprocessing_agent", "review_normalizer")
    assert meta is not None
    assert pool.is_tool_implemented("text_preprocessing_agent", "review_normalizer") is True


def test_tool_meta_correct_agent_still_works():
    pool = get_agent_pool()
    assert pool.is_tool_implemented("metrics_agent", "revenue_total") is True


def test_tool_meta_nonexistent_tool_still_none():
    pool = get_agent_pool()
    assert pool.get_tool_meta("any_agent", "nonexistent_tool_xyz") is None
    assert pool.is_tool_implemented("any_agent", "nonexistent_tool_xyz") is False
