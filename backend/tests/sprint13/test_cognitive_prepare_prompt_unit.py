"""I8 — cognitive_stage prepare_cognitive_prompt Unit 테스트

명세서: docs/_claude/checkpointer/sprint13_integration_i8_cognitive_prepare_prompt_spec.md
대상: backend/app/dream_agent/cognitive/cognitive_stage.py 의 prepare_cognitive_prompt

7 케이스 (순수 함수 Unit).
"""

from pathlib import Path


# ──────────────────────────────────────────────────────────────────
# CS-01 빈 history → 빈 context_summary
# ──────────────────────────────────────────────────────────────────

def test_CS01_empty_history_produces_empty_context():
    from app.dream_agent.cognitive.cognitive_stage import prepare_cognitive_prompt
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="블루밍글로우 분석",
        conversation_id="c1",
        turn_id="t1",
    )
    template = "Input: {user_input}\nLang: {language}\nCtx: {context_summary}"

    result = prepare_cognitive_prompt(state, template)

    assert "Input: 블루밍글로우 분석" in result
    assert "Lang: ko" in result
    assert "Ctx: " in result


# ──────────────────────────────────────────────────────────────────
# CS-02 🔴 history 있을 때 주입
# ──────────────────────────────────────────────────────────────────

def test_CS02_history_injected_when_present():
    from app.dream_agent.cognitive.cognitive_stage import prepare_cognitive_prompt
    from app.dream_agent.states.agent_state import init_agent_state

    history = [
        {"turn_index": 1, "user_input": "안녕", "response_summary": "반갑습니다"},
        {"turn_index": 2, "user_input": "블루밍글로우 뭐야?", "response_summary": "화장품 브랜드"},
    ]
    state = init_agent_state(
        user_input="그럼 분석해줘",
        conversation_id="c1",
        turn_id="t3",
        conversation_history=history,
        history_limit=3,
    )
    template = "Ctx: {context_summary}\nInput: {user_input}\nLang: {language}"

    result = prepare_cognitive_prompt(state, template)

    assert "[T1]" in result
    assert "[T2]" in result
    assert "안녕" in result
    assert "블루밍글로우 뭐야?" in result
    assert "반갑습니다" in result
    assert "그럼 분석해줘" in result  # user_input 자리


# ──────────────────────────────────────────────────────────────────
# CS-03 history_limit 적용 (tail slicing)
# ──────────────────────────────────────────────────────────────────

def test_CS03_history_limit_applied():
    from app.dream_agent.cognitive.cognitive_stage import prepare_cognitive_prompt
    from app.dream_agent.states.agent_state import init_agent_state

    history = [
        {"turn_index": 1, "user_input": "q1", "response_summary": "a1"},
        {"turn_index": 2, "user_input": "q2", "response_summary": "a2"},
        {"turn_index": 3, "user_input": "q3", "response_summary": "a3"},
    ]
    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t4",
        conversation_history=history,
        history_limit=1,
    )
    template = "{context_summary}"

    result = prepare_cognitive_prompt(state, template)

    assert "[T3]" in result
    assert "[T1]" not in result
    assert "[T2]" not in result


# ──────────────────────────────────────────────────────────────────
# CS-04 language pass-through
# ──────────────────────────────────────────────────────────────────

def test_CS04_language_passed_through():
    from app.dream_agent.cognitive.cognitive_stage import prepare_cognitive_prompt
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="hello",
        conversation_id="c1",
        turn_id="t1",
        language="en",
    )
    template = "Language: {language}"

    result = prepare_cognitive_prompt(state, template)

    assert result == "Language: en"


# ──────────────────────────────────────────────────────────────────
# CS-05 template에 context_summary placeholder 없는 경우
# ──────────────────────────────────────────────────────────────────

def test_CS05_template_without_context_summary_placeholder():
    from app.dream_agent.cognitive.cognitive_stage import prepare_cognitive_prompt
    from app.dream_agent.states.agent_state import init_agent_state

    template = "Only: {user_input}"
    state = init_agent_state(user_input="x", conversation_id="c1", turn_id="t1")

    result = prepare_cognitive_prompt(state, template)

    assert result == "Only: x"


# ──────────────────────────────────────────────────────────────────
# CS-06 실제 cognitive.yaml 호환
# ──────────────────────────────────────────────────────────────────

def test_CS06_actual_cognitive_yaml_integration():
    import yaml
    from app.dream_agent.cognitive.cognitive_stage import prepare_cognitive_prompt
    from app.dream_agent.states.agent_state import init_agent_state

    # 테스트 파일 위치 기준 (V3 보정)
    # backend/tests/sprint13/test_X.py → parents[3] = 프로젝트 루트
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    yaml_path = PROJECT_ROOT / "backend/app/dream_agent/llm_manager/prompts/cognitive.yaml"
    assert yaml_path.exists(), f"cognitive.yaml 없음: {yaml_path}"

    config = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    template = config["user_template"]

    state = init_agent_state(
        user_input="블루밍글로우 분석",
        conversation_id="c1",
        turn_id="t1",
        language="ko",
    )

    # 예외 없이 실행되어야 함 (placeholder 누락 시 KeyError)
    result = prepare_cognitive_prompt(state, template)

    assert "블루밍글로우 분석" in result


# ──────────────────────────────────────────────────────────────────
# CS-07 순수 함수 — state 불변성
# ──────────────────────────────────────────────────────────────────

def test_CS07_pure_function_no_side_effects():
    from app.dream_agent.cognitive.cognitive_stage import prepare_cognitive_prompt
    from app.dream_agent.states.agent_state import init_agent_state

    state = init_agent_state(
        user_input="test",
        conversation_id="c1",
        turn_id="t1",
        conversation_history=[
            {"turn_index": 1, "user_input": "a", "response_summary": "b"}
        ],
        history_limit=5,
    )
    snapshot = dict(state)
    snapshot_history_copy = list(state["conversation_history"])

    prepare_cognitive_prompt(state, "{context_summary}")

    # 상위 dict 변동 없음
    assert state == snapshot
    # history list 내용 변동 없음
    assert state["conversation_history"] == snapshot_history_copy
    assert state["history_limit"] == 5
