"""슬라이스 1 — period 정직 박제 (2026-06-12, 헌법 19 D2·D3·R2 / DoD=G2).

거짓말 메커니즘(폐지 전): 오염원 tool 이 period 미지정 시 "period": "all" 을 데이터로 방출
→ executor._inject_prev_outputs 가 하류 필수 param 으로 setdefault 주입
→ cac_overall 등이 signup_date.startswith("all") = 0건 → CAC 0원 'COMPLETED' (G2 거짓 숫자).

박제 4겹 (한 겹이 풀려도 다른 겹이 막도록 독립):
  P1 주입 금지     — _inject_prev_outputs 가 SCOPE_PARAMS 를 건너뜀
  P2 경계 거부     — _param_boundary_issue: 필수 누락 missing_param / 'all'·'2026-13' invalid_param
  P3 plan 자가평가 — detect_plan_gaps 스코프 예외 (tests/test_planning_gaps.py 에 박제)
  P4 정직 되묻기   — responder 가 period SKIP 을 "기간을 알려주세요" 로 종착 (숫자 단정 금지)
+ G2 통합: 실제 카탈로그·실제 tool(channel_cac_compare/cac_overall) 경계 SKIP → 되묻기까지.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from app.dream_agent.execution.executor import (
    _inject_prev_outputs,
    _is_valid_period_value,
    _param_boundary_issue,
    execute_phase,
)
from app.dream_agent.models import ExecutionContext
from app.dream_agent.planning.planner import PlannedTodo, _resolved_month
from app.dream_agent.response.responder import (
    Responder,
    build_display_payload,
    build_missing_period_payload,
)
from app.dream_agent.schemas.execution_result import (
    ExecutionResult,
    TodoResult,
    TodoStatus,
)
from app.dream_agent.schemas.structured_query import SCOPE_PARAMS, StructuredQuery


def _tr(tid: str, status: TodoStatus = TodoStatus.COMPLETED, data: dict | None = None,
        tool: str = "x") -> TodoResult:
    now = time.time()
    return TodoResult(
        todo_id=tid, task_type="t", tool=tool, agent="a", status=status,
        data=data or {}, started_at=now, ended_at=now, duration_ms=0.0,
    )


def _exec(*todos: TodoResult) -> ExecutionResult:
    return ExecutionResult(todos={t.todo_id: t for t in todos})


# ── P1: 스코프 param 주입 금지 ──────────────────────────────────────────────

def test_scope_params_not_injected_from_upstream():
    prev = {"t0": _tr("t0", data={"period": "all", "total_cost": 123})}
    merged = _inject_prev_outputs({}, prev)
    assert "period" not in merged, "스코프 param 주입 금지 (R2) — 'all' 오염 경로"
    assert merged["total_cost"] == 123, "일반 artifact 체이닝은 유지돼야"


def test_scope_param_set_means_all_three():
    assert SCOPE_PARAMS == {"period", "period_a", "period_b"}


def test_plan_bound_scope_value_untouched():
    prev = {"t0": _tr("t0", data={"period": "2026-03"})}
    merged = _inject_prev_outputs({"period": "2026-04"}, prev)
    assert merged["period"] == "2026-04", "plan 바인딩 값은 불변"


# ── P2: 실행 경계 — 거부(D2), coerce 금지 ──────────────────────────────────

class _SpecOK:
    def validate_params(self, params):
        return True, []


def test_period_format_contract():
    for ok in ("2026-04", "2026-12", "2026-01", "2026-03/2026-05"):
        assert _is_valid_period_value(ok), ok
    # 공백 표기는 함수 단에선 거부(raw 검증) — 경계가 정규화 후 같은 값을 검증·전달 (리뷰 R-7)
    for bad in ("all", "3months", "2026-13", "2026-00", "2026/04", "26-04", "2026-4",
                " 2026-04", "2026-03 / 2026-05"):
        assert not _is_valid_period_value(bad), bad


def test_boundary_normalizes_whitespace_validation_equals_execution():
    """(리뷰 R-7) 검증값=실행값 — 공백 표기는 lexical 정규화 후 그 값이 tool 로 간다.
    구버전은 strip 한 값으로 통과시키고 원본을 실행 → startswith 0건 silent-0 재발 구멍."""
    params = {"period": "2026-03 / 2026-05"}
    assert _param_boundary_issue({}, _SpecOK(), params) is None
    assert params["period"] == "2026-03/2026-05"

    params2 = {"period": " 2026-04"}
    assert _param_boundary_issue({}, _SpecOK(), params2) is None
    assert params2["period"] == "2026-04"


def test_boundary_missing_required_period():
    issue = _param_boundary_issue({"params_required": ["period"]}, _SpecOK(), {})
    assert issue is not None
    assert issue["reason"] == "missing_param" and issue["param"] == "period"


def test_boundary_rejects_all_and_hallucinated_month():
    for bad in ("all", "3months", "2026-13"):
        issue = _param_boundary_issue({}, _SpecOK(), {"period": bad})
        assert issue is not None and issue["reason"] == "invalid_param", bad
        assert issue["param"] == "period"


def test_boundary_accepts_valid_month_and_range():
    for ok in ("2026-04", "2026-03/2026-05"):
        assert _param_boundary_issue({}, _SpecOK(), {"period": ok}) is None, ok


def test_boundary_wires_toolspec_validate_params():
    """⑷(2026-06-01) 설계 'Executor 가 execute 전 호출'의 실제 배선 — 슬라이스 1-④."""
    class _SpecBad:
        def validate_params(self, params):
            return False, ["Required parameter missing: source_id"]
    issue = _param_boundary_issue({}, _SpecBad(), {})
    assert issue is not None and issue["reason"] == "invalid_param"
    assert "source_id" in issue["detail"]


# ── _resolved_month: 월 범위 + zero-pad 정규화 (슬라이스 1-③ 구멍 보강) ────

def _sq_period(resolved=None, window=None):
    return SimpleNamespace(
        targets=SimpleNamespace(period=SimpleNamespace(resolved=resolved, window=window))
    )


def test_resolved_month_rejects_out_of_range():
    assert _resolved_month(_sq_period(resolved="2026-13")) is None
    assert _resolved_month(_sq_period(resolved="2026-00")) is None


def test_resolved_month_normalizes_zero_padding():
    assert _resolved_month(_sq_period(resolved="2026-4")) == "2026-04"
    assert _resolved_month(_sq_period(window="2026-9")) == "2026-09"


# ── 리뷰 R-1: optional-period tool 의 무언 전체기간 확장 방지 (결정론 바인딩) ──

def test_bind_temporal_fills_optional_period_too():
    """월 쿼리에서 optional-period tool(member_guest_stats 등)이 무언 전체기간으로 넓어지지
    않게 — 폐지된 상류 주입이 우연히 하던 월-정합 전파를 결정론 바인딩이 정공법으로 대체."""
    from app.dream_agent.planning.planner import Plan, bind_temporal_params
    idx = {"member_guest_stats": {
        "params_required": [], "params_optional": ["period"], "produces": [], "consumes": [],
    }}
    plan = Plan(todos=[PlannedTodo(id="t1", task_type="x", tool="member_guest_stats")])
    bind_temporal_params(plan, _sq_period(resolved="2026-04"), idx)
    assert plan.todos[0].tool_params["period"] == "2026-04"


def test_bind_temporal_optional_stays_unbound_without_month():
    """월 없는 쿼리 — optional 은 빈 채 유지 (전체기간 집계는 optional tool 의 정당한 의미)."""
    from app.dream_agent.planning.planner import Plan, bind_temporal_params
    idx = {"member_guest_stats": {
        "params_required": [], "params_optional": ["period"], "produces": [], "consumes": [],
    }}
    plan = Plan(todos=[PlannedTodo(id="t1", task_type="x", tool="member_guest_stats")])
    bind_temporal_params(plan, _sq_period(), idx)
    assert "period" not in plan.todos[0].tool_params


# ── P4: responder 정직 되묻기 (D3 — 자동 기본월 금지) ──────────────────────

def test_period_ask_fires_on_scope_skip():
    er = _exec(_tr("t1", status=TodoStatus.SKIPPED,
                   data={"reason": "missing_param", "param": "period"}, tool="cac_overall"))
    p = build_missing_period_payload(er)
    assert p is not None
    assert "기간을 알려주세요" in p.text
    assert p.meta["reason"] == "missing_period"
    assert p.meta["blocked_tools"] == ["cac_overall"]


def test_period_ask_silent_on_non_scope_or_other_reasons():
    er = _exec(
        _tr("t1", status=TodoStatus.SKIPPED, data={"reason": "missing_param", "param": "source_id"}),
        _tr("t2", status=TodoStatus.SKIPPED, data={"reason": "data_insufficient", "artifact": "rows"}),
        _tr("t3"),
    )
    assert build_missing_period_payload(er) is None


def test_g2_ask_wins_over_partial_numbers():
    """G2 DoD: 기간 없는 질문에는 (전체기간 집계 같은) 부분 완료가 있어도 숫자 단정 금지."""
    er = _exec(
        _tr("t1", data={"rows": [{"channel": "meta", "cpa": 71470}], "count": 1},
            tool="channel_aggregate"),
        _tr("t2", status=TodoStatus.SKIPPED,
            data={"reason": "missing_param", "param": "period"}, tool="channel_cac_compare"),
    )
    payload = asyncio.run(Responder().respond(StructuredQuery.model_construct(), er))
    assert "기간을 알려주세요" in payload.text
    assert "71470" not in payload.text, "기간 없는 질문에 숫자를 단정하면 안 됨 (I1)"


def test_display_no_false_complete_when_nothing_ran():
    """전 단계 SKIP 인데 '분석을 완료했습니다' 로 둔갑 금지 (I1 — 경계 SKIP 도입의 부작용 가드)."""
    er = _exec(_tr("t1", status=TodoStatus.SKIPPED,
                   data={"reason": "missing_param", "param": "source_id"}))
    p = build_display_payload(StructuredQuery.model_construct(), er)
    assert "분석을 완료했습니다" not in p.text


def test_display_no_false_complete_with_collector_only():
    """(리뷰 R-6) collector 만 완료 + 분석 단계 전부 SKIP — '완료' 둔갑 금지 잔존 구멍."""
    er = _exec(
        _tr("c1", data={"raw_reviews": [1, 2]}, tool="orders_collector"),
        _tr("t1", status=TodoStatus.SKIPPED, data={"reason": "missing_param", "param": "source_id"}),
    )
    p = build_display_payload(StructuredQuery.model_construct(), er)
    assert "분석을 완료했습니다" not in p.text


def test_period_ask_yields_to_failure():
    """(리뷰 R-5) FAILED 실행 + period SKIP 공존 — ask 가 실패 사실을 가리면 안 됨 (I1).
    실패 고지(ERROR 경로)가 이기고, 기간 안내는 재시도 시 자연 발동."""
    now = time.time()
    er = ExecutionResult(
        todos={
            "t1": _tr("t1", status=TodoStatus.SKIPPED,
                      data={"reason": "missing_param", "param": "period"}, tool="cac_overall"),
            "t2": TodoResult(todo_id="t2", task_type="t", tool="report_writer", agent="a",
                             status=TodoStatus.FAILED, data={}, error="boom",
                             started_at=now, ended_at=now, duration_ms=0.0),
        },
        overall_status=TodoStatus.FAILED, halted_at="t2", halt_reason="boom",
    )
    assert build_missing_period_payload(er) is None
    payload = asyncio.run(Responder().respond(StructuredQuery.model_construct(), er))
    assert "실패" in payload.text


def test_ctx_previous_results_exclude_non_completed(monkeypatch):
    """(리뷰 R-8) SKIP/FAILED 의 사유 dict 가 ctx.previous_results 로 새어 LLM tool payload 에
    데이터인 척 들어가지 않게 — COMPLETED 만 병합 (_inject_prev_outputs 와 같은 기준)."""
    from app.dream_agent.execution import executor as ex
    seen: dict = {}

    class _EchoTool:
        def validate_params(self, params):
            return True, []

        async def execute(self, params, ctx):
            seen["prev"] = dict(ctx.previous_results or {})
            return {"ok": 1}

    class _Pool:
        def is_tool_stub(self, a, t):
            return False

        def is_tool_implemented(self, a, t):
            return True

        def get_real_tool(self, t):
            return _EchoTool()

        def get_tool_meta(self, a, t):
            return {}

    monkeypatch.setattr(ex, "get_agent_pool", lambda: _Pool())
    prev = {
        "ok1": _tr("ok1", data={"rows": [1]}),
        "sk1": _tr("sk1", status=TodoStatus.SKIPPED,
                   data={"reason": "missing_param", "param": "period"}),
    }
    todo = PlannedTodo(id="t9", task_type="x", tool="echo_tool", agent="a")
    ctx = ExecutionContext(session_id="s", plan_id="p", client_id="clumi")
    asyncio.run(ex._run_single_todo(todo, ctx, prev))
    assert "ok1" in seen["prev"]
    assert "sk1" not in seen["prev"]


# ── 리뷰 R-2: 단일 월 tool 의 범위 period — silent-0 대신 시끄러운 거부 ──

def test_channel_cac_compare_rejects_range_loudly():
    from app.dream_agent.execution.agent_pool import get_agent_pool
    tool = get_agent_pool().get_real_tool("channel_cac_compare")
    ctx = ExecutionContext(session_id="s", plan_id="p", client_id="clumi")
    with pytest.raises(ValueError, match="단일 월"):
        asyncio.run(tool.execute({"period": "2026-03/2026-05"}, ctx))


# ── 리뷰 R-4: 스코프 param 계약 자동 drift 검사 (team_catalog ↔ per-tool yaml) ──

def test_scope_param_contract_two_yaml_sources_agree():
    """06-11 수동 정합 + 슬라이스 1 의 9곳 정합이 다시 썩지 않게 — 두 YAML 진실 소스의
    스코프 param required 선언 일치를 박제 (코드 raise 는 G2 통합 테스트가 커버)."""
    base = Path(__file__).parents[1] / "app" / "dream_agent"
    team = yaml.safe_load(
        (base / "planning" / "catalog" / "team_catalog.yaml").read_text(encoding="utf-8"))
    team_req: dict[str, set] = {}
    for tm in team["teams"].values():
        for ag in tm["agents"].values():
            for t in (ag.get("tools") or []):
                team_req[t["name"]] = set(t.get("params_required") or []) & SCOPE_PARAMS

    mismatches = []
    for yml in (base / "tools" / "catalog").rglob("*.yaml"):
        spec = yaml.safe_load(yml.read_text(encoding="utf-8"))
        name = (spec or {}).get("name")
        if name not in team_req:
            continue
        spec_req = {
            p["name"] for p in (spec.get("parameters") or [])
            if p.get("required") and p["name"] in SCOPE_PARAMS
        }
        if spec_req != team_req[name]:
            mismatches.append(
                f"{name}: per-tool={sorted(spec_req)} vs team_catalog={sorted(team_req[name])}")
    assert not mismatches, "스코프 param required 선언 drift:\n  " + "\n  ".join(mismatches)


# ── G2 통합: 실제 카탈로그 + 실제 tool — 경계 SKIP → 되묻기 종착 ───────────

def test_g2_real_channel_cac_without_period_ends_in_ask():
    """월 없는 '채널별 CAC': 실제 channel_cac_compare 가 경계에서 SKIPPED(missing_param) 되고
    responder 가 '기간을 알려주세요' 로 종착. (구버전: 주입 'all' → CAC 0원 COMPLETED)"""
    ctx = ExecutionContext(session_id="s", plan_id="p", client_id="clumi")
    todo = PlannedTodo(id="t1", task_type="competitor_comparison",
                       tool="channel_cac_compare", agent="comparison_agent", depends_on=[])
    results = asyncio.run(execute_phase([todo], ctx))
    assert results[0].status == TodoStatus.SKIPPED
    assert results[0].data["reason"] == "missing_param"
    assert results[0].data["param"] == "period"

    payload = asyncio.run(Responder().respond(
        StructuredQuery.model_construct(), _exec(*results)))
    assert "기간을 알려주세요" in payload.text


def test_g2_real_cac_overall_rejects_injected_all():
    """'all' 이 (어떤 경로로든) param 에 들어와도 경계가 거부 — startswith('all') 0건 불가."""
    ctx = ExecutionContext(session_id="s", plan_id="p", client_id="clumi")
    todo = PlannedTodo(id="t1", task_type="metric_calculation", tool="cac_overall",
                       agent="metrics_agent", depends_on=[], tool_params={"period": "all"})
    results = asyncio.run(execute_phase([todo], ctx))
    assert results[0].status == TodoStatus.SKIPPED
    assert results[0].data["reason"] == "invalid_param"
    assert results[0].data["param"] == "period"
