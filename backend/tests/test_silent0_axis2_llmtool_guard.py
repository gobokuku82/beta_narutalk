"""silent-0 축2(근본수정) + 축1(정직메시지 배선) — RED 테스트 (2026-06-08).

배경(데이터흐름맵 §4·8, compact 복구문서 §1):
  R1(575aa84)이 report_writer 만 빈가드+게이트로 막았다. 그러나 *상류* insight_extractor /
  summary_generator 는 여전히 빈 입력에 LLM 을 불러 환각을 만든다(문2). 특히:

  ★ R1 무력화 체인(실측): reviews=0 → insight_extractor(게이트·가드 없음)가 가짜 insights
    (non-empty) 생성 → report_writer 게이트(consumes=[insights])가 "insights 있음"으로 *통과*
    → 가짜 보고서. = 문2 수정은 '미래 대비'가 아니라 R1 실효성의 전제조건.

축2 설계(선례=RawCollectorBase): tools/llm_tool.py 에 LLMTool(BaseTool) Template Method —
  execute() = collect_inputs() → [전부 빔 검사: data_insufficient] → run_llm().
  가드가 base 소유 → 새 LLM tool 이 구조적으로 가드 못 건너뜀(자동 안전).

여기는 *수정 후* 기대 동작을 박는다 — 현재 RED, 구현하면 GREEN:
  A2-1 insight_extractor 빈 입력 → LLM 0 + insights 없음 + data_insufficient
  A2-2 summary_generator 빈 입력 → LLM 0 + summary 없음 + data_insufficient
  A2-3 insight_extractor catalog consumes 선언 → 게이트가 빈 입력 SKIP
  A2-4 ★체인: insight_extractor 빈 입력 산출이 report_writer 게이트를 못 뚫음(R1 완성)
  A2-5 LLMTool base 가 임의 신규 subclass 에 가드 자동 적용(run_llm 미호출)
  A2-6 3 LLM tool 이 LLMTool subclass 로 이전됨(구조 박제)
  축1-1 insight_extractor 의 data_insufficient SKIP → 정직메시지 발동(배선 확인)

테스트 전략: unit-level 직접 구성(previous_results 직접 주입 + LLM mock).
  test_d4 / test_silent0_fix_r1 패턴 재사용(object.__new__ + SimpleNamespace spec).
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import yaml

from app.dream_agent.execution.data_gate import check_consume_sufficiency
from app.dream_agent.models import ExecutionContext
from app.dream_agent.planning.planner import _build_tool_index

_CATALOG = Path(__file__).parents[1] / "app" / "dream_agent" / "planning" / "catalog" / "team_catalog.yaml"


def _meta(tool_name: str) -> dict:
    catalog = yaml.safe_load(_CATALOG.read_text(encoding="utf-8"))
    return _build_tool_index(catalog).get(tool_name, {})


def _spec(name: str) -> SimpleNamespace:
    # execute 가드 경로는 spec.name(로그) + spec.parameters(merge_params)만 씀.
    return SimpleNamespace(name=name, parameters=[])


# ── A2-1: insight_extractor 빈 입력 → LLM 호출 0 + 가짜 insights 없음 ──

def test_a2_1_insight_extractor_guards_empty_input(monkeypatch):
    """빈 sentiment/keywords → LLM 호출 *전* 정직 degrade. 가짜 insights 생성 안 함.
    현재: 가드 없음 → generate_json 1회 호출 + insights 환각. (RED)"""
    from app.dream_agent.tools.analysis.llm import insight_extractor as ie_mod
    from app.dream_agent.tools.analysis.llm.insight_extractor import InsightExtractor

    calls = {"n": 0}

    class _FakeClient:
        async def generate_json(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            calls["n"] += 1
            return {"insights": [{"title": "지어낸 인사이트", "description": "빈 입력 환각"}]}

    monkeypatch.setattr(ie_mod, "get_llm_client", lambda layer: _FakeClient())
    tool = object.__new__(InsightExtractor)
    tool.spec = _spec("insight_extractor")
    ctx = ExecutionContext(session_id="s", plan_id="p", previous_results={})  # ★ 빈 입력

    result = asyncio.run(tool.execute({}, ctx))

    assert calls["n"] == 0, "빈 입력에 LLM 호출되면 환각 경로(가드 미적용). 수정 후 0 이어야."
    assert not result.get("insights"), "빈 입력에 insights 생성 = silent-0 상류 환각. 수정 후 없어야."
    assert result.get("reason") == "data_insufficient", (
        "빈 입력은 *구조화된* data_insufficient 신호여야(게이트·responder 가 소비)."
    )


# ── A2-2: summary_generator 빈 입력 → LLM 호출 0 + 가짜 summary 없음 ──

def test_a2_2_summary_generator_guards_empty_input(monkeypatch):
    """빈 입력(4 후보 키 전부 부재) → LLM 호출 전 degrade. 가짜 요약 없음.
    현재: 가드 없음 → generate 1회 호출 + summary 환각. (RED)"""
    from app.dream_agent.tools.report import summary_generator as sg_mod
    from app.dream_agent.tools.report.summary_generator import SummaryGenerator

    calls = {"n": 0}

    class _FakeClient:
        async def generate(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            calls["n"] += 1
            return "4월 종합 요약: 매출 견조하게 성장(빈 입력에서 지어냄)"

    monkeypatch.setattr(sg_mod, "get_llm_client", lambda layer: _FakeClient())
    tool = object.__new__(SummaryGenerator)
    tool.spec = _spec("summary_generator")
    ctx = ExecutionContext(session_id="s", plan_id="p", previous_results={})  # ★ 빈 입력

    result = asyncio.run(tool.execute({}, ctx))

    assert calls["n"] == 0, "빈 입력에 LLM 호출되면 환각 경로. 수정 후 0 이어야."
    assert not result.get("summary"), "빈 입력에 summary 생성 = 환각. 수정 후 없어야."
    assert result.get("reason") == "data_insufficient"


# ── A2-3: insight_extractor catalog consumes 선언 → 게이트가 빈 입력 SKIP ──

def test_a2_3_insight_extractor_no_consumes_domain_agnostic():
    """insight_extractor 도메인무관化(2026-06-10): consumes 미선언 — metric·리뷰 OR-입력이라
    catalog consumes(AND-게이트)에 안 맞음. silent-0 은 in-tool LLMTool 가드가 막음(A2-1 참조,
    summary_generator 와 동일 패턴 — OR-입력은 게이트 대신 in-tool 가드)."""
    consumes = _meta("insight_extractor").get("consumes") or []
    assert not consumes, (
        f"도메인무관 insight 는 consumes 미선언(OR-입력, summary_generator 동일). "
        f"silent-0 은 in-tool 가드(A2-1)가 담당. got consumes={consumes}"
    )


# ── A2-4: ★체인 — insight_extractor 빈 산출이 report_writer 게이트를 못 뚫음(R1 완성) ──

def test_a2_4_insight_empty_does_not_defeat_report_gate(monkeypatch):
    """R1 무력화 차단의 핵심 회귀.
    수정 후 insight_extractor(빈) → 가짜 insights 없음 → 그 산출을 받은 report_writer 게이트가
    insights 부재로 SKIP. 현재: insight 가 가짜 insights 생성 → report 게이트 통과(=무력화). (RED)"""
    from app.dream_agent.tools.analysis.llm import insight_extractor as ie_mod
    from app.dream_agent.tools.analysis.llm.insight_extractor import InsightExtractor

    class _FakeClient:
        async def generate_json(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            return {"insights": [{"title": "환각", "description": "빈 입력"}]}

    monkeypatch.setattr(ie_mod, "get_llm_client", lambda layer: _FakeClient())
    tool = object.__new__(InsightExtractor)
    tool.spec = _spec("insight_extractor")
    ctx = ExecutionContext(session_id="s", plan_id="p", previous_results={})

    insight_out = asyncio.run(tool.execute({}, ctx))
    assert not insight_out.get("insights"), "수정 후 insight_extractor 는 가짜 insights 를 안 만들어야"

    # 그 산출을 다음 todo 결과로 넣고 report_writer 게이트 검사
    previous = {"t_insight": insight_out}
    rw_consumes = _meta("report_writer").get("consumes") or ["insights"]
    gate = check_consume_sufficiency(rw_consumes, previous)
    assert gate is not None and gate.get("reason") == "data_insufficient", (
        "insight 가 가짜 insights 를 안 만드니 report_writer 게이트가 insights 부재로 SKIP 해야 "
        "(= R1 이 더 이상 무력화되지 않음)."
    )


# ── A2-5: LLMTool base 가 임의 신규 subclass 에 가드 자동 적용 ──

def test_a2_5_llmtool_base_auto_guards_new_subclass():
    """신규 LLM tool 이 가드를 *직접 안 써도* base.execute 가 빈 입력을 막는다(구조적 자동 안전).
    현재: tools/llm_tool.py 부재. (RED — ImportError)"""
    from app.dream_agent.tools.llm_tool import LLMTool

    ran = {"llm": False}

    class _DummyLLM(LLMTool):
        def collect_inputs(self, params, context):
            return {"x": (context.previous_results or {}).get("x")}

        async def run_llm(self, inputs, params, context):
            ran["llm"] = True
            return {"out": "fabricated"}

    tool = object.__new__(_DummyLLM)
    tool.spec = _spec("dummy")

    # 빈 입력 → run_llm 미호출 + data_insufficient (subclass 가 가드를 안 짰는데도)
    ctx_empty = ExecutionContext(session_id="s", plan_id="p", previous_results={})
    r = asyncio.run(tool.execute({}, ctx_empty))
    assert ran["llm"] is False, "빈 입력에 run_llm 호출되면 base 가드 미작동(자동 안전 깨짐)."
    assert r.get("reason") == "data_insufficient"

    # 입력 있음 → run_llm 정상 호출 (과차단 방지)
    ctx_full = ExecutionContext(session_id="s", plan_id="p", previous_results={"x": [1, 2]})
    r2 = asyncio.run(tool.execute({}, ctx_full))
    assert ran["llm"] is True and r2.get("out") == "fabricated", "입력 있으면 run_llm 정상 실행돼야."


# ── A2-6: 3 LLM tool 이 LLMTool subclass 로 이전됨 (구조 박제) ──

def test_a2_6_llm_tools_migrated_to_llmtool_base():
    """report_writer / insight_extractor / summary_generator 가 LLMTool 을 상속.
    현재: 셋 다 BaseTool 직접 상속 + llm_tool.py 부재. (RED)"""
    from app.dream_agent.tools.llm_tool import LLMTool
    from app.dream_agent.tools.analysis.llm.insight_extractor import InsightExtractor
    from app.dream_agent.tools.report.report_writer import ReportWriter
    from app.dream_agent.tools.report.summary_generator import SummaryGenerator

    for cls in (ReportWriter, InsightExtractor, SummaryGenerator):
        assert issubclass(cls, LLMTool), f"{cls.__name__} 은 LLMTool 을 상속해 가드 자동 상속해야."


# ── 축1-1: insight_extractor 의 data_insufficient SKIP → 정직메시지 발동 (배선 확인) ──

def test_axis1_insight_insufficient_triggers_honest_message():
    """축2 신호(insight_extractor data_insufficient SKIP)를 기존 responder 정직 degrade 가
    그대로 받는지 확인. report_writer 뿐 아니라 상류 신호도 동일 배선(거의 공짜)."""
    from app.dream_agent.response.responder import build_insufficient_data_payload
    from app.dream_agent.schemas.execution_result import ExecutionResult, TodoResult, TodoStatus

    exec_result = ExecutionResult(todos={
        "t1": TodoResult(
            todo_id="t1", task_type="insight_generation", tool="insight_extractor",
            status=TodoStatus.SKIPPED,
            data={"reason": "data_insufficient", "artifact": "top_keywords", "detail": "top_keywords 부재"},
            started_at=0.0, ended_at=0.0, duration_ms=0.0,
        )
    })

    payload = build_insufficient_data_payload(exec_result)

    assert payload is not None, "insight 가 data_insufficient SKIP + 다른 산출 없으면 정직 degrade 발동."
    assert payload.meta.get("degraded") is True
    assert payload.meta.get("reason") == "data_insufficient"
