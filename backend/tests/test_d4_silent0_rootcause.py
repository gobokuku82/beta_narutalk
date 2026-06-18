"""D4 silent-0 (데이터 없이 거짓 보고서) — 원인 가설 검증 (2026-06-07).

원인분석: docs/_claude/4layer_system/d4_silent0_rootcause_260606_v1.md
"환각"은 결과. 근본 = 깨진 데이터 계약(R1~R4). 여기서 새 가설 2개를 결정론으로 박는다:
  H1 report_writer 는 빈 입력에도 LLM 호출(가드 0) → 환각 경로 열림.
  H4 report_writer 가 읽는 키는 리뷰/텍스트 분석만 생산 → 비-리뷰 보고서는 굶음(R1).
(H2 consumes 미선언 / H3 analysis_results orphan / H5 responder degrade 안 함 =
 test_agent_language_holes_baseline.py 에 이미 있음 — 재사용.)
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import yaml

from app.dream_agent.models import ExecutionContext
from app.dream_agent.planning.planner import _build_producer_index, _build_tool_index
from app.dream_agent.tools.report import report_writer as rw_mod
from app.dream_agent.tools.report.report_writer import ReportWriter

_CATALOG = Path(__file__).parents[1] / "app" / "dream_agent" / "planning" / "catalog" / "team_catalog.yaml"


# ── H1(수정 반전 2026-06-07, G1): 빈 입력 → LLM 호출 안 함 ──
# 원래 가설(빈 입력에도 LLM 호출 = 환각 경로)은 git history 참조. G1 빈 가드로 차단됨.
# canonical 수정 테스트: test_silent0_fix_r1.py::test_t2_*

def test_h1_report_writer_no_llm_with_empty_inputs_after_fix(monkeypatch):
    calls = {"n": 0}

    class _FakeClient:
        async def generate(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            calls["n"] += 1
            return "(불려선 안 됨)"

    monkeypatch.setattr(rw_mod, "get_llm_client", lambda layer: _FakeClient())
    rw = object.__new__(ReportWriter)  # __init__ 우회 — execute 는 self.spec/ds 안 씀
    ctx = ExecutionContext(session_id="s", plan_id="p", previous_results={})  # ★ 빈 입력

    result = asyncio.run(rw.execute({}, ctx))

    # G1: 빈 입력엔 LLM 호출 안 함 (환각 차단) + 거짓 보고서 없음 + 구조화 신호
    assert calls["n"] == 0, "G1: 빈 입력엔 LLM 호출 안 함(환각 차단)."
    assert not result.get("report_markdown"), "빈 입력엔 거짓 보고서 없음(D5: report_markdown)."
    assert result.get("reason") == "data_insufficient", "구조화된 data_insufficient 신호(G6 소비)."


# ── H4: report_writer 입력은 리뷰/텍스트 분석만 생산 → 비-리뷰 보고서는 굶음 (R1) ──

def test_h4_report_writer_inputs_only_from_review_analysis():
    catalog = yaml.safe_load(_CATALOG.read_text(encoding="utf-8"))
    prod = _build_producer_index(_build_tool_index(catalog))
    # report_writer.py:30-32 가 실제로 읽는 키
    review_analysis = {"sentiment_analyzer", "keyword_extractor", "insight_extractor"}
    for key in ("sentiment_distribution", "top_keywords", "insights"):
        producer = prod.get(key)
        assert producer in review_analysis, \
            (f"'{key}' 생산자={producer} — 리뷰/텍스트 분석 tool 만 만든다. "
             f"비-리뷰 보고서(매출/ROAS)는 이 생산자가 plan 에 없어 report_writer 가 빈 입력으로 굶음(R1).")


def test_h4_general_metric_tools_do_not_feed_report_writer():
    # 대조: 일반 성과 지표 tool(roas_overall/revenue_total)은 report_writer 의 입력 3키를 안 만든다
    catalog = yaml.safe_load(_CATALOG.read_text(encoding="utf-8"))
    idx = _build_tool_index(catalog)
    report_inputs = {"sentiment_distribution", "top_keywords", "insights"}
    for metric_tool in ("roas_overall", "revenue_total", "channel_aggregate"):
        produces = set(idx.get(metric_tool, {}).get("produces", []))
        assert not (produces & report_inputs), \
            f"{metric_tool} 가 report 입력을 만들면 가설 반증. 현재는 안 만듦 → 종합 보고서 = 빈 입력."
