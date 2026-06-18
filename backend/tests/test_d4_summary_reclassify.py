"""D4 summary_generator 재분류 — 단순답변 서술 tool (2026-06-08).

계획 Phase 1 / 사용자 결정 D4: summary_generator 를 "단순 쿼리용 짧은 답변 서술 tool"로
재정의(긴 보고서 X). response 가 표시할 한두 문장을 생성 = "단순 쿼리 텍스트 공백" 메움.

catalog 정합(Phase 1 범위):
  - produces: summary_text → summary (코드 반환 키와 일치, drift 0)
  - params_required: [analysis_results] 제거 (생산자 0 orphan — report_writer 와 같은 패턴)
  - description: 역할 명시

(동작 전환 — response 가 단순 쿼리에 summary tool 산출을 *표시* — 은 Phase 2.)

RED → GREEN:
  D4-1 produces == [summary] (코드 정합)
  D4-2 analysis_results orphan 제거 (params_required)
  D4-3 코드(SummaryGenerator) 가 summary 키 반환 (catalog produces 와 일치)
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import yaml

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.report import summary_generator as sg_mod
from app.dream_agent.tools.report.summary_generator import SummaryGenerator

_CATALOG = Path(__file__).parents[1] / "app" / "dream_agent" / "planning" / "catalog" / "team_catalog.yaml"


def _summary_meta() -> dict:
    catalog = yaml.safe_load(_CATALOG.read_text(encoding="utf-8"))
    agents = catalog["teams"]["analysis_team"]["agents"]
    return next(t for t in agents["report_text_agent"]["tools"] if t["name"] == "summary_generator")


# ── D4-1: produces 정합 (summary_text → summary) ──

def test_d4_1_summary_produces_aligned_to_code():
    meta = _summary_meta()
    assert meta.get("produces") == ["summary"], (
        f"D4: catalog produces 를 코드 반환(summary)과 정합. 현재 {meta.get('produces')}"
    )


# ── D4-2: analysis_results orphan 제거 ──

def test_d4_2_summary_orphan_removed():
    meta = _summary_meta()
    assert "analysis_results" not in (meta.get("params_required") or []), (
        "D4: analysis_results(생산자 0 orphan) 를 params_required 에서 제거"
    )


# ── D4-3: 코드가 summary 키 반환 (catalog produces 와 일치) ──

def test_d4_3_summary_code_returns_summary_key(monkeypatch):
    class _Fake:
        async def generate(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            return "4월 ROAS 는 3.2 입니다"

    monkeypatch.setattr(sg_mod, "get_llm_client", lambda layer: _Fake())
    sg = object.__new__(SummaryGenerator)
    sg.spec = SimpleNamespace(name="summary_generator", parameters=[])
    ctx = ExecutionContext(
        session_id="s", plan_id="p",
        previous_results={"t1": {"insights": [{"text": "재구매율 상승"}]}},
    )

    result = asyncio.run(sg.execute({}, ctx))
    assert "summary" in result, "코드가 summary 키 반환 → catalog produces 와 일치"
