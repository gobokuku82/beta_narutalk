"""D5 report 산출 키 정합 — report_text → report_markdown (2026-06-08).

계획 Phase 1 / 사용자 결정 D5: report_writer 코드 실반환을 catalog·다운스트림과 정합.
catalog 는 이미 produces=[report_markdown], pdf_renderer/pptx_generator 도 report_markdown
소비. **코드만 report_text 반환** → drift. 코드를 report_markdown 으로 통일(최소 변경).

소비자(코드 실측): report_writer 반환 / summary_generator._collect_payload / executor.py:101.

RED(현재) → GREEN(정합 후):
  D5-1 report_writer(insights 있음) → report_markdown 키 (report_text 제거)
  D5-2 summary_generator._collect_payload 가 report_markdown 수집
  D5-3 catalog produces 와 코드 키 일치 (report_markdown)
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import yaml

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.report import report_writer as rw_mod
from app.dream_agent.tools.report.report_writer import ReportWriter
from app.dream_agent.tools.report.summary_generator import SummaryGenerator

_CATALOG = Path(__file__).parents[1] / "app" / "dream_agent" / "planning" / "catalog" / "team_catalog.yaml"


# ── D5-1: report_writer 정상 경로 → report_markdown 키 ──

def test_d5_1_report_writer_returns_report_markdown(monkeypatch):
    class _Fake:
        async def generate(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            return "## 리뷰 인사이트 보고서\n핵심: 재구매율 상승..."

    monkeypatch.setattr(rw_mod, "get_llm_client", lambda layer: _Fake())
    rw = object.__new__(ReportWriter)
    rw.spec = SimpleNamespace(name="report_writer", parameters=[])
    ctx = ExecutionContext(
        session_id="s", plan_id="p",
        previous_results={"t1": {"insights": [{"text": "재구매율 상승"}]}},
    )

    result = asyncio.run(rw.execute({}, ctx))

    assert result.get("report_markdown"), "D5: report_writer 는 report_markdown 키로 반환(catalog·다운스트림 정합)"
    assert "report_text" not in result, "D5: 구 키 report_text 제거(drift 해소)"


# ── D5-2: summary_generator 가 report_markdown 을 입력으로 수집 ──

def test_d5_2_summary_collects_report_markdown():
    payload = SummaryGenerator._collect_payload({"t1": {"report_markdown": "## 보고서 본문"}})
    assert "report_markdown" in payload, "summary_generator._collect_payload 가 report_markdown 수집해야"


# ── D5-3: catalog produces 와 코드 키 일치 ──

def test_d5_3_catalog_produces_matches_code_key():
    catalog = yaml.safe_load(_CATALOG.read_text(encoding="utf-8"))
    agents = catalog["teams"]["analysis_team"]["agents"]
    rw_meta = next(t for t in agents["report_text_agent"]["tools"] if t["name"] == "report_writer")
    assert rw_meta.get("produces") == ["report_markdown"], (
        "catalog produces 가 report_markdown 이고 코드도 report_markdown 반환 → drift 0"
    )
