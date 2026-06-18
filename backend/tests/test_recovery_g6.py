"""G6 데이터 없음 → HITL 복구: 변경 용이 구조의 *순수 코어* 테스트 (2026-06-07).

설계: docs/_claude/4layer_system/silent0_g6_hitl복구_설계_260607_v1.md
코어 = actions.yaml(바뀌는 메뉴) + 그걸 읽는 순수 함수. 그래프 wiring(interrupt)은 별도(다음 단계).

RED 먼저: recovery 모듈이 없으니 import 실패 → 구현하면 GREEN.
  RC-1 load_actions: actions.yaml 읽힘(런타임) + message·options(id·action)
  RC-2 is_blocked True: report SKIPPED(data_insufficient) + 다른 산출 없음
  RC-3 is_blocked False: 다른 tool COMPLETED(부분 성공)
  RC-4 is_blocked False: data_insufficient SKIP 없음
  RC-5 build_recovery_payload: type=data_recovery + 메뉴 from config
  RC-6 resolve_choice: option_id→verb+params; 모르면 end
"""
from __future__ import annotations

from app.dream_agent.workflow_managers.recovery import (
    build_recovery_payload,
    detect_recovery,
    is_blocked,
    load_actions,
    resolve_choice,
)


def _skipped(tool: str, reason: str = "data_insufficient") -> dict:
    return {"status": "skipped", "tool": tool, "data": {"reason": reason, "detail": f"{tool} 0건"}}


def _completed(tool: str, data: dict | None = None) -> dict:
    return {"status": "completed", "tool": tool, "data": data or {}}


# ── RC-1: 설정 로드 (런타임 read) ──

def test_rc1_load_actions_has_message_and_options():
    cfg = load_actions()
    assert cfg.get("message"), "actions.yaml 에 message 필요"
    options = cfg.get("options")
    assert isinstance(options, list) and len(options) >= 1
    for o in options:
        assert o.get("id") and o.get("action"), "각 옵션은 id + action(verb) 필수"


# ── RC-2: 막힘 — report SKIPPED(data_insufficient) + 다른 산출 없음 ──

def test_rc2_is_blocked_true_when_report_skipped_no_output():
    cfg = load_actions()
    todos = {"t1": _skipped("report_writer")}
    assert is_blocked(todos, cfg) is True


# ── RC-3: 막힘 아님 — 다른 tool COMPLETED(부분 성공) ──

def test_rc3_is_blocked_false_when_other_output_present():
    cfg = load_actions()
    todos = {
        "t1": _skipped("report_writer"),
        "t2": _completed("revenue_total", {"revenue": 100}),
    }
    assert is_blocked(todos, cfg) is False


# ── RC-4: 막힘 아님 — data_insufficient SKIP 없음 ──

def test_rc4_is_blocked_false_when_no_insufficient():
    cfg = load_actions()
    todos = {"t1": _completed("revenue_total", {"revenue": 100})}
    assert is_blocked(todos, cfg) is False


# ── RC-5: interrupt 페이로드 — type + 메뉴 from config ──

def test_rc5_build_recovery_payload_from_config():
    cfg = load_actions()
    p = build_recovery_payload(cfg, context={"missing": "insights"})
    assert p["type"] == "data_recovery"
    assert p["message"] == cfg["message"]
    assert [o["id"] for o in p["options"]] == [o["id"] for o in cfg["options"]]
    assert p["context"]["missing"] == "insights"


# ── RC-6: dispatcher — option_id → verb+params; 모르면 end ──

def test_rc6_resolve_choice_maps_verb_and_unknown_to_end():
    cfg = load_actions()
    first = cfg["options"][0]
    r = resolve_choice(first["id"], cfg)
    assert r["verb"] == first["action"]
    assert r["option_id"] == first["id"]
    # 모르는 선택 → 안전하게 end
    r2 = resolve_choice("__nonexistent__", cfg)
    assert r2["verb"] == "end"


# ── detect_recovery: execution_stage wiring 의 *실제* 통합 단위 (감지+메뉴+가드 적골레이션) ──
# 그동안 RC-2~5 는 손으로 만든 dict 로만 검증 → 여기서 *실제 ExecutionResult.model_dump* 형태로
# 닫고, config 오류 시 never-raise(정상 실행 보호, 적대검증 RISK 지적)까지 박는다.

def _exec_result_dict(todos: list) -> dict:
    """실제 ExecutionResult 를 model_dump(mode='json') — execution_stage 가 만드는 그 형태."""
    from app.dream_agent.schemas.execution_result import ExecutionResult
    er = ExecutionResult(todos={t.todo_id: t for t in todos})
    return er.model_dump(mode="json")


def _todo(tool: str, status, data: dict):
    from app.dream_agent.schemas.execution_result import TodoResult
    return TodoResult(
        todo_id=f"t_{tool}", task_type="x", tool=tool, status=status,
        data=data, started_at=0.0, ended_at=0.0, duration_ms=0.0,
    )


# RC-7: 실제 model_dump(막힘) → 메뉴 반환 (status enum→str 변환 형태 통과 확인)
def test_rc7_detect_recovery_returns_menu_on_real_blocked_result():
    from app.dream_agent.schemas.execution_result import TodoStatus
    blocked = _exec_result_dict([
        _todo("report_writer", TodoStatus.SKIPPED,
              {"reason": "data_insufficient", "artifact": "insights", "detail": "insights 부재"}),
    ])
    menu = detect_recovery(blocked)
    assert menu is not None and menu["type"] == "data_recovery"
    assert len(menu["options"]) >= 1


# RC-8: 실제 model_dump(부분 성공) → None
def test_rc8_detect_recovery_none_on_partial_success():
    from app.dream_agent.schemas.execution_result import TodoStatus
    ok = _exec_result_dict([
        _todo("report_writer", TodoStatus.SKIPPED, {"reason": "data_insufficient"}),
        _todo("revenue_total", TodoStatus.COMPLETED, {"revenue": 100}),
    ])
    assert detect_recovery(ok) is None


# RC-9: config 로드 실패해도 detect_recovery 는 None (절대 raise X → 정상 실행 보호)
def test_rc9_detect_recovery_safe_on_config_error(monkeypatch):
    import app.dream_agent.workflow_managers.recovery.manager as mgr
    from app.dream_agent.schemas.execution_result import TodoStatus

    def _boom(*a, **k):
        raise RuntimeError("broken actions.yaml")

    monkeypatch.setattr(mgr, "load_actions", _boom)
    blocked = _exec_result_dict([
        _todo("report_writer", TodoStatus.SKIPPED, {"reason": "data_insufficient"}),
    ])
    # config 가 터져도 None 반환(안전 강등) — execution_stage 가 안 죽는다
    assert detect_recovery(blocked) is None
