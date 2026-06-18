"""D3 선행조사 — adjust_query(기간 조정 재실행) 가설 박제 (2026-06-08).

C(재실행)의 핵심 난관 D3 를 코드로 확정:
  H1 cognitive 는 user_input 만 읽고 structured_query 를 *무조건 재생성* → goto=cognitive
     재진입 시 period 조정이 덮어쓰임. (재진입은 planning 으로 가거나 user_input 수정 필요)
  H3 거의 모든 metric 도구는 *단일월 전용*("/" 범위 → ValueError) → "기간 확대(범위)"는
     도구 한계로 막힘. "다른 단일월 변경"만 가능.

함의(계획서 D3 난이도 재평가): D3 는 'Period.resolved 동기화'만의 문제가 아니라
  (1) 재진입 경로(cognitive 우회) + (2) 도구 입력형식(단일월) 두 구조 제약.
  → "기간 확대(+3months 범위)" 헤드라인 예시는 현 도구로 *불가*. adjust_query 는
    "다른 단일 기간으로 변경"으로 재정의해야 현 도구와 정합.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from app.dream_agent.models import ExecutionContext

_AGENT = Path(__file__).parents[1] / "app" / "dream_agent"
_TOOLS = _AGENT / "tools"


# ── H1: cognitive 는 user_input 으로 재생성, 기존 structured_query 재사용 안 함 ──
#   → goto=cognitive 재진입은 period 조정을 덮어씀 (재진입 경로가 D3 의 급소)

def test_h1_cognitive_rebuilds_from_user_input_overwrites_period():
    src = (_AGENT / "cognitive" / "cognitive_stage.py").read_text(encoding="utf-8")
    assert 'state.get("user_input"' in src, "cognitive 는 user_input 을 읽어 재생성"
    assert "generate_json" in src and "goto=\"planning\"" in src.replace("'", '"'), \
        "cognitive 는 LLM 으로 structured_query 새로 만들어 planning 으로 넘김"
    # 기존 structured_query 를 *입력으로* 읽거나 재사용/스킵하는 분기가 없음
    # → 재진입(goto=cognitive) 시 우리가 바꾼 period 가 LLM 재파싱으로 덮어쓰임 (= D3 급소)
    assert 'state.get("structured_query")' not in src, (
        "현재 cognitive 는 기존 structured_query 를 안 읽음 → period 조정 보존 불가. "
        "C 재진입은 planning 으로 가거나(우회) user_input 을 바꿔야 함. "
        "(이 assert 가 깨지면 = cognitive 에 재사용 분기가 생긴 것 = C 설계 변화 신호)"
    )


# ── H3: metric 도구는 단일월 전용 — 범위("/") period 거부 (행동 테스트) ──
#   → "기간 확대(범위)"는 도구 한계로 불가. fetch *전* 에 raise 하므로 데이터 불요.

def test_h3_metric_tool_rejects_period_range_behavioral():
    from app.dream_agent.tools.metrics.cac_overall import CacOverall

    tool = object.__new__(CacOverall)          # __init__ 우회
    tool.spec = SimpleNamespace(parameters=[])  # merge_params 가 self.spec.parameters 만 씀
    ctx = ExecutionContext(session_id="s", plan_id="p", client_id="clumi")

    raised_single_month_only = False
    try:
        asyncio.run(tool.execute({"period": "2026-02/2026-04"}, ctx))  # 3개월 범위
    except ValueError as e:
        raised_single_month_only = "단일 월" in str(e)

    assert raised_single_month_only, (
        "cac_overall 이 범위 period('YYYY-MM/YYYY-MM')를 거부해야 함(단일월 전용). "
        "= '기간 확대(범위)' adjust_query 가 metric 도구 한계로 막힘."
    )


# ── H3b: 단일월 제약은 metric 전반 / cleaning 만 범위 지원 (비대칭) ──

def test_h3b_single_month_constraint_breadth_and_asymmetry():
    metrics_dir = _TOOLS / "metrics"
    single_month_tools = [
        p.name for p in metrics_dir.glob("*.py")
        if "단일 월만" in p.read_text(encoding="utf-8")
    ]
    assert len(single_month_tools) >= 5, (
        f"다수 metric 도구가 단일월 전용이어야(범위 확대 불가 입증). 발견: {single_month_tools}"
    )
    # 대조: cleaning 의 active_orders_filter 는 범위(start/end) 지원 → 데이터 계층은 범위 가능,
    #       metric 계층이 단일월로 막는 비대칭. (C 의 범위확대는 metric 도구 확장이 선행)
    aof = (_TOOLS / "cleaning" / "active_orders_filter.py").read_text(encoding="utf-8")
    assert 'period.split("/")' in aof, "active_orders_filter 는 범위(YYYY-MM/YYYY-MM) 지원해야(비대칭 입증)"
