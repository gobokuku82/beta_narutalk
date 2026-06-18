"""I6 — AgentState + init_agent_state 헬퍼 Unit 테스트

명세서: docs/_claude/checkpointer/sprint13_integration_i6_agent_state_spec.md
대상: backend/app/dream_agent/states/agent_state.py
  - AgentState TypedDict (Sprint 13 필드 5개 추가)
  - init_agent_state() 헬퍼 함수 (신규)

9 케이스. Unit only (순수 함수 + TypedDict 검증 불필요).
"""


# ──────────────────────────────────────────────────────────────────
# AS-01 기본 초기화
# ──────────────────────────────────────────────────────────────────

def test_AS01_init_basic():
    from app.dream_agent.states.agent_state import init_agent_state
    from app.core.config import settings

    state = init_agent_state(
        user_input="블루밍글로우 분석",
        conversation_id="conv_123",
        turn_id="turn_abc",
    )

    assert state["user_input"] == "블루밍글로우 분석"
    assert state["conversation_id"] == "conv_123"
    assert state["turn_id"] == "turn_abc"
    assert state["session_id"] == "turn_abc"
    assert state["language"] == "ko"
    assert state["user_id"] == settings.DEFAULT_USER_ID


# ──────────────────────────────────────────────────────────────────
# AS-02 🔴 session_id = turn_id alias 동기화
# ──────────────────────────────────────────────────────────────────

def test_AS02_session_id_alias_sync():
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="unique_turn_xyz",
    )

    assert state["turn_id"] == "unique_turn_xyz"
    assert state["session_id"] == "unique_turn_xyz"
    assert state["turn_id"] == state["session_id"]


# ──────────────────────────────────────────────────────────────────
# AS-03 user_id=None → Settings fallback
# ──────────────────────────────────────────────────────────────────

def test_AS03_default_user_id_from_settings():
    from app.dream_agent.states.agent_state import init_agent_state
    from app.core.config import settings

    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
        user_id=None,
    )

    assert state["user_id"] == settings.DEFAULT_USER_ID
    assert state["user_id"] == "demo"  # 현재 기본값


# ──────────────────────────────────────────────────────────────────
# AS-04 명시적 user_id 우선
# ──────────────────────────────────────────────────────────────────

def test_AS04_explicit_user_id():
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
        user_id="alice",
    )

    assert state["user_id"] == "alice"


# ──────────────────────────────────────────────────────────────────
# AS-05 conversation_history 기본값 []
# ──────────────────────────────────────────────────────────────────

def test_AS05_empty_conversation_history_default():
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
    )

    assert state["conversation_history"] == []
    assert isinstance(state["conversation_history"], list)
    assert state["conversation_history"] is not None


# ──────────────────────────────────────────────────────────────────
# AS-06 history_limit fallback + 명시
# ──────────────────────────────────────────────────────────────────

def test_AS06_history_limit_from_settings():
    from app.dream_agent.states.agent_state import init_agent_state
    from app.core.config import settings

    # None → Settings fallback
    state_default = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
        history_limit=None,
    )
    assert state_default["history_limit"] == settings.DEFAULT_HISTORY_LIMIT
    assert state_default["history_limit"] == 3

    # 명시 값 우선
    state_explicit = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t2",
        history_limit=5,
    )
    assert state_explicit["history_limit"] == 5


# ──────────────────────────────────────────────────────────────────
# AS-07 trace 기본값 + optional 필드 미포함
# ──────────────────────────────────────────────────────────────────

def test_AS07_trace_and_optional_fields():
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
    )

    # trace 기본 []
    assert state["trace"] == []
    assert isinstance(state["trace"], list)

    # 노드 산출 필드는 초기엔 미설정
    assert "plan" not in state
    assert "error" not in state
    assert "execution_progress" not in state
    assert "structured_query" not in state
    assert "execution_result" not in state
    assert "response" not in state


# ──────────────────────────────────────────────────────────────────
# AS-08 빈 문자열 pass-through (X1 보정)
# ──────────────────────────────────────────────────────────────────

def test_AS08_empty_string_pass_through():
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="",
        conversation_id="",
        turn_id="",
    )

    # init은 방어 안 함 — 호출자 책임 (ws_agent.run_turn D-3/D-4 정책)
    assert state["user_input"] == ""
    assert state["conversation_id"] == ""
    assert state["turn_id"] == ""
    assert state["session_id"] == ""  # alias 여전히 동기화


# ──────────────────────────────────────────────────────────────────
# AS-09 conversation_history list 참조 pass-through (Y5 보정)
# ──────────────────────────────────────────────────────────────────

def test_AS09_conversation_history_pass_through():
    from app.dream_agent.states.agent_state import init_agent_state

    history = [{"turn_index": 1, "user_input": "q1", "response_summary": "a1"}]
    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
        conversation_history=history,
    )

    # pass-through (defensive copy 안 함)
    assert state["conversation_history"] == history

    # 원본 list 수정이 state에 전파됨 (같은 참조)
    history.append({"turn_index": 2, "user_input": "q2", "response_summary": "a2"})
    assert len(state["conversation_history"]) == 2
    assert state["conversation_history"][1]["turn_index"] == 2
