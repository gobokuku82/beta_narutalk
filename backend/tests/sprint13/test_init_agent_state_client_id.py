"""작업 ⑪.F — init_agent_state client_id 파라미터 unit 테스트

명세서: docs/reports/계획_작업⑪_client_id_agent_흐름복구_2026-05-31.md §3.A·§3.F
대상: backend/app/dream_agent/states/agent_state.py
  - AgentState client_id 필드 (TypedDict total=False)
  - init_agent_state(client_id: str | None = None) 파라미터
  - is not None 패턴 (require_review 일관)

원칙 박제:
  - default 강제 X (사용자 [기본값은 있으면 안 되는거야])
  - client_id 미명시 → 키 자체 absent (state.get 컨벤션, ADR-022 helper-B fail-fast 단일 책임)
  - 빈 문자열 "" 처리는 BaseTool.fetch 위임 (single source of truth)
"""


# ──────────────────────────────────────────────────────────────────
# CID-01 client_id 명시 → state["client_id"] set
# ──────────────────────────────────────────────────────────────────

def test_CID01_explicit_client_id_set():
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
        client_id="clumi",
    )

    assert state["client_id"] == "clumi"


# ──────────────────────────────────────────────────────────────────
# CID-02 client_id=None → 키 자체 absent (TypedDict total=False)
# ──────────────────────────────────────────────────────────────────

def test_CID02_none_client_id_key_absent():
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
        client_id=None,
    )

    assert "client_id" not in state


# ──────────────────────────────────────────────────────────────────
# CID-03 client_id 미명시 (기본값) → 키 absent
# ──────────────────────────────────────────────────────────────────

def test_CID03_default_omitted_client_id_key_absent():
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
    )

    assert "client_id" not in state
    # state.get 컨벤션 검증
    assert state.get("client_id") is None


# ──────────────────────────────────────────────────────────────────
# CID-04 빈 문자열 "" → 키 set (빈 문자열도 명시로 간주, fail-fast 는 BaseTool.fetch 위임)
# ──────────────────────────────────────────────────────────────────

def test_CID04_empty_string_client_id_set():
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
        client_id="",
    )

    # is not None 패턴 → "" 도 set (require_review 일관)
    # 빈 문자열 처리는 BaseTool.fetch (single source of truth) 위임
    assert state["client_id"] == ""


# ──────────────────────────────────────────────────────────────────
# CID-05 다양한 client_id 값 (clumi 외)
# ──────────────────────────────────────────────────────────────────

def test_CID05_various_client_ids():
    from app.dream_agent.states.agent_state import init_agent_state

    for cid in ["clumi", "blooming", "demo_client_a"]:
        state = init_agent_state(
            user_input="t",
            conversation_id="c",
            turn_id="tn",
            client_id=cid,
        )
        assert state["client_id"] == cid


# ──────────────────────────────────────────────────────────────────
# CID-06 다른 필드와 독립 (require_review 같은 Optional 필드 간섭 0)
# ──────────────────────────────────────────────────────────────────

def test_CID06_client_id_independent_of_require_review():
    from app.dream_agent.states.agent_state import init_agent_state

    state_a = init_agent_state(
        user_input="t", conversation_id="c", turn_id="tn",
        client_id="clumi",
    )
    state_b = init_agent_state(
        user_input="t", conversation_id="c", turn_id="tn",
        client_id="clumi", require_review=False,
    )

    assert state_a["client_id"] == "clumi"
    assert "require_review" not in state_a
    assert state_b["client_id"] == "clumi"
    assert state_b["require_review"] is False
