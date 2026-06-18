"""T4 — Cognitive history_injector Unit 테스트

명세서: docs/_claude/checkpointer/sprint13_test_t4_history_injector_spec.md
대상: backend/app/dream_agent/cognitive/history_injector.py (신규)

7 케이스. 순수 함수라 Unit only.
"""


# ──────────────────────────────────────────────────────────────────
# CH-01
# ──────────────────────────────────────────────────────────────────

def test_CH01_empty_history():
    from app.dream_agent.cognitive.history_injector import build_context_summary

    result = build_context_summary([], limit=3)

    assert result == ""


# ──────────────────────────────────────────────────────────────────
# CH-02
# ──────────────────────────────────────────────────────────────────

def test_CH02_none_history():
    from app.dream_agent.cognitive.history_injector import build_context_summary

    result = build_context_summary(None, limit=3)

    assert result == ""


# ──────────────────────────────────────────────────────────────────
# CH-03
# ──────────────────────────────────────────────────────────────────

def test_CH03_limit_zero():
    from app.dream_agent.cognitive.history_injector import build_context_summary

    history = [{"turn_index": 1, "user_input": "안녕", "response_summary": "반갑습니다"}]
    result = build_context_summary(history, limit=0)

    assert result == ""


# ──────────────────────────────────────────────────────────────────
# CH-04
# ──────────────────────────────────────────────────────────────────

def test_CH04_history_within_limit():
    from app.dream_agent.cognitive.history_injector import build_context_summary

    history = [
        {"turn_index": 1, "user_input": "안녕", "response_summary": "반갑습니다"},
        {"turn_index": 2, "user_input": "분석해줘", "response_summary": "완료"},
    ]
    result = build_context_summary(history, limit=3)

    assert "[T1]" in result
    assert "[T2]" in result
    assert "안녕" in result
    assert "분석해줘" in result
    assert "반갑습니다" in result
    assert "완료" in result
    # 각 turn 별도 라인 (개행 1개 이상)
    assert result.count("\n") >= 1


# ──────────────────────────────────────────────────────────────────
# CH-05 🔴 핵심 — tail slicing
# ──────────────────────────────────────────────────────────────────

def test_CH05_history_exceeds_limit():
    from app.dream_agent.cognitive.history_injector import build_context_summary

    history = [
        {"turn_index": i, "user_input": f"q{i}", "response_summary": f"a{i}"}
        for i in range(1, 6)   # 1~5
    ]
    result = build_context_summary(history, limit=3)

    # 최근 3개 (turn_3, turn_4, turn_5)
    assert "[T3]" in result
    assert "[T4]" in result
    assert "[T5]" in result

    # 과거 2개는 제외
    assert "[T1]" not in result
    assert "[T2]" not in result


# ──────────────────────────────────────────────────────────────────
# CH-06 — MAX_HISTORY_LIMIT clip
# ──────────────────────────────────────────────────────────────────

def test_CH06_max_history_limit_clip(monkeypatch):
    """limit 요청이 MAX 초과 시 자동 clip.

    Settings 오버라이드 대신 직접 max 주입 가능한 API 사용.
    """
    from app.dream_agent.cognitive.history_injector import build_context_summary

    # MAX_HISTORY_LIMIT을 10으로 고정
    monkeypatch.setattr(
        "app.dream_agent.cognitive.history_injector._get_max_history_limit",
        lambda: 10,
    )

    history = [
        {"turn_index": i, "user_input": f"q{i}", "response_summary": f"a{i}"}
        for i in range(1, 16)  # 15개
    ]
    result = build_context_summary(history, limit=20)  # MAX=10 초과 요청

    # MAX=10으로 clip → 최근 10개 (turn_6 ~ turn_15)
    assert "[T6]" in result
    assert "[T15]" in result
    # 이전 5개 제외
    assert "[T1]" not in result
    assert "[T5]" not in result

    # 포함된 turn 수 == 10개 (각 turn은 `[T{n}]` 패턴)
    import re
    matches = re.findall(r"\[T\d+\]", result)
    assert len(matches) == 10


# ──────────────────────────────────────────────────────────────────
# CH-07 — 누락 필드 안전 처리
# ──────────────────────────────────────────────────────────────────

def test_CH07_missing_fields_safe():
    from app.dream_agent.cognitive.history_injector import build_context_summary

    history = [{"turn_index": 1}]  # user_input, response_summary 누락
    result = build_context_summary(history, limit=1)

    # 예외 없이 반환
    assert isinstance(result, str)
    # turn_index는 살아있음
    assert "[T1]" in result
