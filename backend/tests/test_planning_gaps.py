"""② planning 자가평가 — detect_plan_gaps (실행 전 미바인딩 param 등 결정론 탐지, 2026-06-06).

목적: Run #1("전체 로아스") 처럼 roas_overall 이 period 없이 스케줄돼 *실행 중* 크래시
(Missing required param: period)하던 걸, **실행 전** plan.gaps 로 잡아 진단/정직 degrade 씨앗.
순수 함수 — LLM 없이 결정론 검증. (catalog drift 수정[roas_overall params_required=[period]]도 같이 확인.)
"""
from __future__ import annotations

from pathlib import Path

import yaml

from app.dream_agent.planning.planner import (
    Plan,
    PlannedTodo,
    _build_tool_index,
    detect_plan_gaps,
)

_CATALOG = Path(__file__).parents[1] / "app" / "dream_agent" / "planning" / "catalog" / "team_catalog.yaml"


def _idx(**tools: dict) -> dict[str, dict]:
    return {
        name: {"params_required": m.get("req", []), "produces": m.get("prod", [])}
        for name, m in tools.items()
    }


def _todo(tid: str, tool: str, params: dict | None = None, deps: list[str] | None = None) -> PlannedTodo:
    return PlannedTodo(id=tid, task_type="x", tool=tool, tool_params=params or {}, depends_on=deps or [])


# ── 핵심 동작 ──

def test_gap_when_required_param_unbound():
    plan = Plan(todos=[_todo("t1", "roas_overall")])
    gaps = detect_plan_gaps(plan, _idx(roas_overall={"req": ["period"]}))
    assert len(gaps) == 1
    assert "period" in gaps[0] and "roas_overall" in gaps[0]


def test_no_gap_when_param_in_tool_params():
    plan = Plan(todos=[_todo("t1", "roas_overall", params={"period": "2026-04"})])
    assert detect_plan_gaps(plan, _idx(roas_overall={"req": ["period"]})) == []


def test_no_gap_when_param_produced_upstream():
    # 직속 upstream 이 그 param 을 artifact 로 산출하면(executor _inject_prev_outputs) 만족으로 본다(보수적)
    # ※ 스코프 param(period 류)은 예외 — 아래 test_scope_param_not_satisfied_by_upstream.
    plan = Plan(todos=[
        _todo("t0", "collector"),
        _todo("t1", "needs_sid", deps=["t0"]),
    ])
    idx = _idx(collector={"prod": ["source_id"]}, needs_sid={"req": ["source_id"]})
    assert detect_plan_gaps(plan, idx) == []


def test_scope_param_not_satisfied_by_upstream():
    # (슬라이스 1, 헌법 R2) period 류 스코프 param 은 주입 금지 — 상류가 'period' artifact 를
    # 산출해도 충족 아님. 구버전은 ad_cost_total 의 produces[period]('all' 라벨) 때문에
    # gap 탐지가 눈멀어 CAC 0원 silent-0 로 흘렀음 (G2).
    plan = Plan(todos=[
        _todo("t0", "budget_totals"),
        _todo("t1", "needs_period", deps=["t0"]),
    ])
    idx = _idx(budget_totals={"prod": ["period"]}, needs_period={"req": ["period"]})
    gaps = detect_plan_gaps(plan, idx)
    assert len(gaps) == 1 and "period" in gaps[0]


def test_no_required_params_no_gap():
    plan = Plan(todos=[_todo("t1", "foo")])
    assert detect_plan_gaps(plan, _idx(foo={})) == []


def test_empty_plan_no_gap():
    assert detect_plan_gaps(Plan(todos=[]), _idx()) == []


# ── catalog drift 수정 확인 (roas_overall params_required=[period] = 코드 정합) ──

def test_roas_overall_catalog_declares_period():
    idx = _build_tool_index(yaml.safe_load(_CATALOG.read_text(encoding="utf-8")))
    assert "period" in idx["roas_overall"]["params_required"], \
        "catalog drift: roas_overall 코드는 period 필수인데 catalog 미선언 → gap-check 가 못 잡음"


# ── ★ Run #1 재현: '전체 로아스'(기간 없음) plan 이 실행 전에 잡히는가 ──

def test_run1_shape_flags_roas_period_gap_before_crash():
    """Run #1 모양(collect→roas_overall, period 없음)을 실제 카탈로그로 평가 →
    roas_overall period gap 이 *실행 전* 잡혀야 한다 (=크래시 'Missing required param' 예방).

    (A-5: 광고 지표 tool 은 canonical_translator 내부 소비 → 별도 ads normalize step 없음. 옛 format_normalizer 노드 제거.)"""
    idx = _build_tool_index(yaml.safe_load(_CATALOG.read_text(encoding="utf-8")))
    plan = Plan(todos=[
        _todo("c1", "meta_ads_performance_collector"),
        _todo("m1", "roas_overall", deps=["c1"]),   # period 미바인딩
    ])
    gaps = detect_plan_gaps(plan, idx)
    assert any("roas_overall" in g and "period" in g for g in gaps), \
        f"Run #1 의 period gap 을 실행 전에 못 잡음: {gaps}"
