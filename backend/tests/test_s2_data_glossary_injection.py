# -*- coding: utf-8 -*-
"""S2 — execution 해석 LLM 의미 배선 검증 (2026-06-18).

컨텍스트엔지니어링 ②축 수정: insight_extractor·summary_generator 가 벌거벗은 숫자만 받던 것을
[데이터 사전](단위·함정라벨)과 함께 받도록 배선됐는지 박제. 프롬프트를 LLM 호출 직전 캡처해
사전이 실제로 들어갔는지 + 단위(배수/%/원)가 명시됐는지 단언.

계획: docs/_claude/plans/S1-S3_execution_LLM_의미배선_구현계획_2026-06-18.md
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.shared.col_dictionary import COL_DESC, build_data_glossary


# ── S1: 데이터 사전 SSOT — 단위·함정 명문화 ──
def test_col_dict_units_and_trap():
    """roas=배수, *_pct=%, *_krw=원 단위 + salesAmt 함정 라벨이 사전에 명문화."""
    assert "배수" in COL_DESC["roas"] and "배수" in COL_DESC["mer"]
    assert "%" in COL_DESC["ctr_pct"] and "%" in COL_DESC["tacos_pct"]
    assert "원" in COL_DESC["ad_cost_krw"] and "원" in COL_DESC["total_marketing_cost"]
    # ★함정: ad_cost_krw desc 가 naver salesAmt=비용 을 경고
    assert "salesAmt" in COL_DESC["ad_cost_krw"] and "비용" in COL_DESC["ad_cost_krw"]


def test_build_glossary_filters_to_present_keys():
    """입력에 등장한 키만 사전화 + clumi metric_glossary 합성. '_' 키 제외."""
    g = build_data_glossary(["roas", "total_marketing_cost", "_meta", "unknown_key"], "clumi")
    assert "roas" in g and "배수" in g
    assert "total_marketing_cost" in g and "원" in g
    assert "_meta" not in g                      # underscore 제외
    assert "ROAS" in g                           # clumi metric_glossary([지표 정의]) 합성
    assert "[칼럼 의미·단위]" in g and "[지표 정의]" in g


def test_build_glossary_empty_safe():
    """빈 키 → 안전 fallback (추측 금지 안내)."""
    g = build_data_glossary([], None)
    assert "추측" in g and g                      # 빈 문자열 아님


# ── S1+ : 사전 규약/커버리지 드리프트 가드 (2026-06-18 보강) ──
def test_col_dict_unit_convention():
    """접미사 규약 ↔ desc 단위 일치 (미래 드리프트 가드).

    *_pct→%, *_krw→원, *_x/roas/mer→배수, *_count→정수. 새 키가 규약을 어기면 빨간불.
    """
    for k, desc in COL_DESC.items():
        if k.endswith("_pct"):
            assert "%" in desc, f"{k}: *_pct 인데 desc 에 % 없음"
        if k.endswith("_krw"):
            assert "원" in desc, f"{k}: *_krw 인데 desc 에 원 없음"
        if k.endswith("_x") or k in ("roas", "mer", "promotion_roas"):
            assert "배수" in desc, f"{k}: 배수 지표인데 desc 에 배수 없음"
        if k.endswith("_count"):
            assert "정수" in desc or "수" in desc, f"{k}: *_count 인데 desc 에 정수/수 없음"


def test_col_dict_covers_execution_output_keys():
    """실행 LLM 이 받는 산출 키(top-level + rows[] nested) 전부 desc 보유 — 드리프트 가드.

    근거(실측): daily_performance_totals(total_*), channel_aggregate rows(ctr/cpc/cpa/cvr/roas),
    conversion_funnel rows(pct_of_top/prev), financial headline(mer/cac/total_marketing_cost).
    새 산출 키 추가 시 desc 누락을 잡는다 — 누락 = ②축 할루시 재발 통로.
    """
    required = {
        # daily_performance_totals (top-level)
        "total_impressions", "total_clicks", "total_conversions", "total_ad_cost",
        # financial headline (top-level)
        "total_marketing_cost", "mer", "roas", "cac",
        # channel_aggregate rows[] (nested — 함정 단위 키)
        "channel", "impressions", "clicks", "conversions",
        "ad_cost", "conversion_revenue", "ctr", "cvr", "cpc", "cpa",
        # conversion_funnel rows[] (nested)
        "pct_of_top", "pct_of_prev",
    }
    missing = sorted(k for k in required if k not in COL_DESC)
    assert not missing, f"COL_DESC 누락(실행 LLM 수신 키): {missing}"


def test_build_glossary_scans_nested_keys():
    """★G-B: rows[] 안 중첩 키(ctr/cpc 등 함정 단위)도 1-depth 수집 — top-level만 보던 갭 폐쇄.

    channel_aggregate 산출 형태({rows:[{ctr, cpc, roas, ...}]})를 그대로 줘도 사전이 닿아야 함.
    """
    channel_output = {
        "rows": [
            {"channel": "google", "ad_cost": 1000, "ctr": 1.2, "cpc": 300, "roas": 4.46},
        ],
        "count": 1,
    }
    g = build_data_glossary(channel_output, "clumi")
    assert "ctr" in g and "%" in g, "nested ctr(%) 미수집"
    assert "cpc" in g and "원" in g, "nested cpc(원) 미수집"
    assert "roas" in g and "배수" in g, "nested roas(배수) 미수집"
    assert "ad_cost" in g, "nested ad_cost 미수집"


# ── S2-ext : diagnoser·forecaster·report_writer·qa 의미 주입 (2026-06-18 확장) ──
def test_diagnoser_injects_glossary(monkeypatch):
    """diagnoser 프롬프트에도 [데이터 사전] + roas 배수 단위 주입 (insight 와 동일 패턴)."""
    import app.dream_agent.tools.analysis.llm.diagnoser as dg
    captured = {"p": ""}

    class _Fake:
        async def generate_json(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            captured["p"] = prompt
            return {"diagnosis": []}

    monkeypatch.setattr(dg, "get_llm_client", lambda layer: _Fake())
    tool = object.__new__(dg.Diagnoser)
    tool.spec = SimpleNamespace(name="diagnoser", parameters=[])
    asyncio.run(tool.execute({}, _ctx({"t1": {"roas": 4.46, "total_marketing_cost": 26806923}})))

    p = captured["p"]
    assert "[데이터 사전]" in p, "diagnoser 데이터 사전 블록 미주입"
    assert "roas" in p and "배수" in p, "diagnoser roas 배수 단위 미주입"


def test_forecaster_injects_glossary(monkeypatch):
    """forecaster 프롬프트에도 [데이터 사전] 주입."""
    import app.dream_agent.tools.analysis.llm.forecaster as fc
    captured = {"p": ""}

    class _Fake:
        async def generate_json(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            captured["p"] = prompt
            return {"forecast": []}

    monkeypatch.setattr(fc, "get_llm_client", lambda layer: _Fake())
    tool = object.__new__(fc.Forecaster)
    tool.spec = SimpleNamespace(name="forecaster", parameters=[])
    asyncio.run(tool.execute({}, _ctx({"t1": {"roas": 4.46, "mer": 4.46}})))

    p = captured["p"]
    assert "[데이터 사전]" in p, "forecaster 데이터 사전 블록 미주입"
    assert "배수" in p, "forecaster 배수 단위 미주입"


def test_report_writer_injects_glossary(monkeypatch):
    """report_writer — 입력은 해석된 insights(canonical 키 0)지만 [지표 정의](metric_glossary)는 주입.

    프로즈에서 'ROAS 4.46배'를 %로 둔갑시키지 않도록 지표 정의를 동봉.
    """
    import app.dream_agent.tools.report.report_writer as rw
    captured = {"p": ""}

    class _Fake:
        async def generate(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            captured["p"] = prompt
            return "보고서"

    monkeypatch.setattr(rw, "get_llm_client", lambda layer: _Fake())
    tool = object.__new__(rw.ReportWriter)
    tool.spec = SimpleNamespace(name="report_writer", parameters=[])
    asyncio.run(tool.execute(
        {}, _ctx({"t1": {"insights": [{"title": "ROAS 호조", "description": "ROAS 4.46배"}]}})))

    p = captured["p"]
    assert "[데이터 사전]" in p, "report_writer 데이터 사전 블록 미주입"
    assert "ROAS" in p, "report_writer 지표 정의(metric_glossary) 미주입"


def test_qa_responder_injects_client_glossary(monkeypatch):
    """qa_responder — load_client_glossary 경로버그(과거 빈 채 돌던 것) 회귀 가드.

    clumi metric_glossary(ROAS 정의)가 실제 프롬프트에 들어가야 함.
    """
    import app.dream_agent.tools.qa.llm.qa_responder as qa
    captured = {"p": ""}

    class _Fake:
        async def generate_json(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            captured["p"] = prompt
            return {"answer": "ROAS는 광고수익률", "answer_type": "knowledge"}

    monkeypatch.setattr(qa, "get_llm_client", lambda layer: _Fake())
    tool = object.__new__(qa.QaResponder)
    tool.spec = SimpleNamespace(name="qa_responder", parameters=[])
    asyncio.run(tool.execute({"question": "ROAS가 뭐야?"}, _ctx({})))

    p = captured["p"]
    assert "ROAS" in p, "qa_responder clumi metric_glossary 미주입 (경로버그 재발?)"


# ── S2: 프롬프트 주입 (LLM 호출 직전 캡처) ──
def _ctx(prev):
    return ExecutionContext(session_id="s", plan_id="p", client_id="clumi", previous_results=prev)


def test_insight_extractor_injects_glossary(monkeypatch):
    """insight_extractor 프롬프트에 [데이터 사전] + roas 배수 단위가 주입됨."""
    import app.dream_agent.tools.analysis.llm.insight_extractor as ie
    captured = {"p": ""}

    class _Fake:
        async def generate_json(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            captured["p"] = prompt
            return {"insights": []}

    monkeypatch.setattr(ie, "get_llm_client", lambda layer: _Fake())
    tool = object.__new__(ie.InsightExtractor)
    tool.spec = SimpleNamespace(name="insight_extractor", parameters=[])
    asyncio.run(tool.execute({}, _ctx({"t1": {"roas": 4.46, "total_marketing_cost": 26806923}})))

    p = captured["p"]
    assert "[데이터 사전]" in p, "데이터 사전 블록 미주입"
    assert "roas" in p and "배수" in p, "roas 배수 단위 미주입"
    assert "total_marketing_cost" in p and "원" in p


def test_summary_generator_injects_glossary(monkeypatch):
    """summary_generator 프롬프트에도 [데이터 사전] 주입."""
    import app.dream_agent.tools.report.summary_generator as sg
    captured = {"p": ""}

    class _Fake:
        async def generate(self, prompt, system_prompt=None, **kw):  # noqa: ANN001
            captured["p"] = prompt
            return "요약"

    monkeypatch.setattr(sg, "get_llm_client", lambda layer: _Fake())
    tool = object.__new__(sg.SummaryGenerator)
    tool.spec = SimpleNamespace(name="summary_generator", parameters=[])
    asyncio.run(tool.execute({}, _ctx({"t1": {"mer": 4.46, "total_revenue": 119539660}})))

    p = captured["p"]
    assert "[데이터 사전]" in p
    assert "mer" in p and "배수" in p
