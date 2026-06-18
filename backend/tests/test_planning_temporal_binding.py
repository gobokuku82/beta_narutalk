"""R3 — 시간 param 결정론 바인딩 (period / period_a·period_b MoM) (2026-06-09).

문제: stage3 LLM 이 period_a/period_b(MoM 두 기간)·일부 period 를 안 채워 → mom_revenue 등이
      실행 시 ValueError("Missing required params"). detect_plan_gaps 가 미바인딩으로 잡던 그 gap.
해결: bind_temporal_params 가 쿼리 절대월에서 period(단일)·period_b(당월)·period_a(전월) 결정론 도출.
      (날짜 산술은 LLM 보다 결정론이 정확 — MoM=정의상 전월 대비.)
"""
from __future__ import annotations

from types import SimpleNamespace

from app.dream_agent.planning.planner import (
    Plan,
    PlannedTodo,
    _prev_month,
    _resolved_month,
    bind_temporal_params,
    detect_plan_gaps,
)

# 최소 tool_index (실제 카탈로그 대신 — 결정론·격리)
_INDEX = {
    "mom_revenue": {"params_required": ["period_a", "period_b"], "produces": [], "consumes": []},
    "channel_cac_compare": {"params_required": ["period"], "produces": [], "consumes": []},
}


def _sq(resolved=None, window=None):
    return SimpleNamespace(targets=SimpleNamespace(period=SimpleNamespace(resolved=resolved, window=window)))


def _todo(tool, **params):
    return PlannedTodo(id="todo_001", task_type="comparison", tool=tool, tool_params=dict(params))


def _plan(*todos):
    return Plan(teams_selected=[], todos=list(todos), dag={}, gaps=[])


# ── _prev_month ──

def test_prev_month_basic_and_year_boundary():
    assert _prev_month("2026-04") == "2026-03"
    assert _prev_month("2026-01") == "2025-12"   # 연 경계
    assert _prev_month("2026-13") is None        # 잘못된 월
    assert _prev_month("4월") is None            # 형식 아님


# ── _resolved_month ──

def test_resolved_month_prefers_resolved_then_window():
    assert _resolved_month(_sq(resolved="2026-04")) == "2026-04"
    assert _resolved_month(_sq(window="2026-04")) == "2026-04"
    assert _resolved_month(_sq(window="3months")) is None   # 절대월 아님
    assert _resolved_month(SimpleNamespace(targets=SimpleNamespace(period=None))) is None


# ── bind: MoM 두 기간 (period_b=당월, period_a=전월) ──

def test_bind_mom_period_a_b_from_query_month():
    plan = bind_temporal_params(_plan(_todo("mom_revenue")), _sq(resolved="2026-04"), _INDEX)
    assert plan.todos[0].tool_params == {"period_b": "2026-04", "period_a": "2026-03"}


# ── bind: 단일 period ──

def test_bind_single_period():
    plan = bind_temporal_params(_plan(_todo("channel_cac_compare")), _sq(resolved="2026-04"), _INDEX)
    assert plan.todos[0].tool_params == {"period": "2026-04"}


# ── 멱등: LLM 이 이미 채운 값은 안 덮음 ──

def test_bind_idempotent_does_not_override():
    plan = bind_temporal_params(_plan(_todo("mom_revenue", period_a="2025-12")), _sq(resolved="2026-04"), _INDEX)
    assert plan.todos[0].tool_params["period_a"] == "2025-12"   # 보존
    assert plan.todos[0].tool_params["period_b"] == "2026-04"   # 빈 것만 채움


# ── 기간 없으면 바인딩 X → gap 유지(정직 degrade 씨앗) ──

def test_no_month_keeps_gap():
    plan = bind_temporal_params(_plan(_todo("mom_revenue")), _sq(), _INDEX)   # period 없음
    assert plan.todos[0].tool_params == {}
    assert detect_plan_gaps(plan, _INDEX)   # gap 존재


# ── 바인딩 후 gap 해소 (실행 ValueError 방지) ──

def test_gap_cleared_after_binding():
    plan = _plan(_todo("mom_revenue"))
    assert detect_plan_gaps(plan, _INDEX)               # 바인딩 전 = gap
    bind_temporal_params(plan, _sq(resolved="2026-04"), _INDEX)
    assert not detect_plan_gaps(plan, _INDEX)           # 바인딩 후 = gap 0
