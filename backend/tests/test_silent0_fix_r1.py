"""silent-0 R1 수정 — "수정 후 기대 동작" RED 테스트 (2026-06-07).

계획: docs/_claude/4layer_system/silent0_수정_실행계획_260607_v1.md
원인·repro(버그 박제, 현재 PASS): test_d4_silent0_rootcause.py / test_agent_language_holes_baseline.py

여기는 *수정 후* 기대 동작을 박는다 — **현재 FAIL(RED)**, G1·G2·G3 구현하면 PASS(GREEN):
  T1(G2): report_writer 의 consumes(=[insights]) 가 빈 입력에서 게이트 SKIP 판정
  T2(G1): report_writer.execute 가 빈 입력이면 LLM 호출 0 + 거짓 report_text 없음 + data_insufficient 신호
  T4(G3): catalog 에 analysis_results orphan 없음 + produces 가 실반환(report_text)과 일치
  T5(회귀): insights 있으면 기존대로 보고서 작성 (과차단 방지 — 현재도 PASS)

테스트 전략: unit-level 직접 구성 (previous_results 직접 주입 + LLM mock). e2e 재현 불가
(intent_shim 이 report task 를 안 만듦). test_d4 패턴(object.__new__ + 빈 ctx) 재사용.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import yaml

from app.dream_agent.execution.data_gate import check_consume_sufficiency
from app.dream_agent.models import ExecutionContext
from app.dream_agent.planning.planner import _build_tool_index
from app.dream_agent.tools.report import report_writer as rw_mod
from app.dream_agent.tools.report.report_writer import ReportWriter

_CATALOG = Path(__file__).parents[1] / "app" / "dream_agent" / "planning" / "catalog" / "team_catalog.yaml"


def _report_writer_meta() -> dict:
    catalog = yaml.safe_load(_CATALOG.read_text(encoding="utf-8"))
    return _build_tool_index(catalog).get("report_writer", {})


# ── T1 (G2): report_writer consumes 가 빈 입력에서 게이트 SKIP 판정 ──

def test_t1_gate_skips_report_writer_when_inputs_empty():
    """G3 가 consumes(실제 읽는 키)를 선언하면, B2.1 게이트가 빈 입력을 SKIP 한다.
    현재: consumes=[] → 게이트 무검사 → silent-0. (RED)"""
    consumes = _report_writer_meta().get("consumes") or []
    result = check_consume_sufficiency(consumes, {})  # 빈 previous_results
    assert result is not None and result.get("reason") == "data_insufficient", (
        f"report_writer consumes={consumes} — 비었으면 게이트 무검사(silent-0). "
        "G3 가 consumes=[insights] 선언하면 빈 입력에서 data_insufficient 판정돼야 함."
    )


# ── T2 (G1): 빈 입력 → LLM 호출 0 + 거짓 보고서 없음 + 구조화 신호 ──

def test_t2_report_writer_no_llm_and_no_fabrication_when_empty(monkeypatch):
    """G1 빈 가드: 입력 전부 빔 → LLM 호출 *전에* 정직 degrade. 거짓 보고서 생성 안 함.
    현재: 빈 입력에도 LLM 1회 호출 + report_text 생성(환각). (RED)"""
    calls = {"n": 0}

    class _FakeClient:
        async def generate(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            calls["n"] += 1
            return "## 4월 종합 성과 보고서\n핵심 성과: 매출 견조...(빈 입력에서 지어냄)"

    monkeypatch.setattr(rw_mod, "get_llm_client", lambda layer: _FakeClient())
    rw = object.__new__(ReportWriter)  # __init__ 우회 (execute 는 spec/ds 안 씀)
    ctx = ExecutionContext(session_id="s", plan_id="p", previous_results={})  # ★ 빈 입력

    result = asyncio.run(rw.execute({}, ctx))

    assert calls["n"] == 0, "빈 입력에 LLM 호출되면 환각 경로(G1 미적용). 수정 후 0 이어야."
    assert not result.get("report_markdown"), "빈 입력에 report 생성 = silent-0 환각. 수정 후 없어야(D5: report_markdown)."
    assert result.get("reason") == "data_insufficient", (
        "빈 입력은 *구조화된* data_insufficient 신호여야(텍스트 메시지 아님) — G6(HITL)가 받아 씀."
    )


# ── T4 (G3): catalog 정합 — orphan 제거 + consumes(코드가 읽는 키) 선언 ──
# 주: produces drift(report_markdown vs 실반환 report_text)는 다운스트림(pdf 등)이
#     report_markdown 을 소비해 별도 정합 작업 → R1 스코프 밖(후속 TODO).

def test_t4_catalog_no_orphan_and_consumes_declared():
    """G3: analysis_results(생산자 0 orphan) 제거 + 코드가 읽는 insights 를 consumes 선언.
    현재: params_required=[analysis_results], consumes 없음. (RED)"""
    meta = _report_writer_meta()
    params_required = meta.get("params_required") or []
    consumes = meta.get("consumes") or []
    assert "analysis_results" not in params_required, (
        "analysis_results = 생산자 0 orphan(죽은 선언). G3 가 params_required 에서 제거해야."
    )
    assert "insights" in consumes, (
        f"report_writer.py:32 는 insights 를 읽음. consumes={consumes} 에 선언해야 "
        "B2.1 게이트가 빈 입력을 SKIP(silent-0 차단)."
    )


# ── T3 (G5): report_writer 가 SKIPPED(data_insufficient)면 responder 정직 degrade ──
# G2 로 report_writer 가 SKIP 되면, 기존 build_insufficient_data_payload 가 그대로 처리한다
# (더 이상 hollow-COMPLETED 가 아니므로) → 별도 G5 *코드 변경 불요* 를 증명.

def test_t3_responder_degrades_when_report_skipped():
    from app.dream_agent.response.responder import build_insufficient_data_payload
    from app.dream_agent.schemas.execution_result import ExecutionResult, TodoResult, TodoStatus

    exec_result = ExecutionResult(todos={
        "t1": TodoResult(
            todo_id="t1", task_type="report_generation", tool="report_writer",
            status=TodoStatus.SKIPPED,
            data={"reason": "data_insufficient", "artifact": "insights", "detail": "insights 부재"},
            started_at=0.0, ended_at=0.0, duration_ms=0.0,
        )
    })

    payload = build_insufficient_data_payload(exec_result)

    assert payload is not None, (
        "report 가 data_insufficient 로 SKIP 됐고 다른 산출 없으면 정직 degrade 발동해야 "
        "(거짓 보고서 대신). 기존 responder 로직 재사용 → G5 코드 불요."
    )
    assert payload.meta.get("degraded") is True
    assert payload.meta.get("reason") == "data_insufficient"
    assert not payload.text or "보고서" not in payload.text or "데이터" in payload.text, (
        "degrade 텍스트는 거짓 보고서가 아니라 '데이터 없음' 안내여야."
    )


# ── T5 (회귀): insights 있으면 기존대로 보고서 작성 (과차단 방지) ──

def test_t5_report_writer_works_when_insights_present(monkeypatch):
    """수정이 정상 경로를 막지 않는지. insights 있으면 보고서 작성. (현재도 PASS — 회귀 가드)"""
    class _FakeClient:
        async def generate(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            return "## 리뷰 인사이트 보고서\n핵심: 재구매율 상승..."

    monkeypatch.setattr(rw_mod, "get_llm_client", lambda layer: _FakeClient())
    rw = object.__new__(ReportWriter)
    ctx = ExecutionContext(
        session_id="s", plan_id="p",
        previous_results={"t1": {"insights": [{"text": "재구매율 상승"}]}},
    )

    result = asyncio.run(rw.execute({}, ctx))

    assert result.get("report_markdown"), "insights 있으면 정상 보고서 작성돼야(과차단 방지, D5: report_markdown)."
