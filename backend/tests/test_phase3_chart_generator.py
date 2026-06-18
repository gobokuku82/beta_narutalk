"""chart_generator 실구현 회귀 (2026-06-12, stub 0 처분 — 오너 결정).

산출 *형태* 기반 결정론 차트 선택 + 정직(차트화 불가 → data_insufficient, 스텁 비차트화).
pptx_generator 차트 슬라이드 첨부(구 chart_to_slide stub 의 책임 흡수)도 여기서 회귀.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from app.dream_agent.execution.agent_pool import get_agent_pool
from app.dream_agent.models import ExecutionContext


def _ctx(**kw):
    return ExecutionContext(session_id="t", plan_id="t", client_id="clumi", **kw)


def _chart_tool():
    tool = get_agent_pool().get_real_tool("chart_generator")
    assert tool is not None, "chart_generator 가 registry 에서 로드돼야 (implemented 전환)"
    return tool


# ── 형태별 차트 선택 ─────────────────────────────────────────────────────

def test_c1_by_channel_dict_renders_hbar(tmp_path):
    r = asyncio.run(_chart_tool().execute(
        {"by_channel": {"meta": 9_235_826, "naver_sa": 5_999_627, "kakao": 59_020},
         "output_dir": str(tmp_path)}, _ctx()))
    assert r["chart_count"] == 1
    p = Path(r["chart_image_paths"][0])
    assert p.exists() and p.stat().st_size > 1_000, "실제 PNG 파일이 생성돼야"
    assert r["charts"][0]["title"].startswith("채널별")


def test_c2_date_rows_render_line(tmp_path):
    rows = [{"date": f"2026-04-{d:02d}", "ad_cost": d * 1_000, "conversion_revenue": d * 5_000}
            for d in range(1, 11)]
    r = asyncio.run(_chart_tool().execute({"rows": rows, "output_dir": str(tmp_path)}, _ctx()))
    assert r["chart_count"] == 1
    assert Path(r["chart_image_paths"][0]).exists()
    assert "추이" in r["charts"][0]["title"]


def test_c3_categorical_rows_prefer_roas(tmp_path):
    rows = [{"channel": "meta", "roas": 320.5, "clicks": 100},
            {"channel": "naver", "roas": 510.0, "clicks": 80}]
    r = asyncio.run(_chart_tool().execute({"rows": rows, "output_dir": str(tmp_path)}, _ctx()))
    assert r["chart_count"] == 1
    assert "roas" in r["charts"][0]["title"]


def test_c4_korean_labels_and_nested_dict(tmp_path):
    """한국어 라벨 + by_category 류 {cat: {count, revenue}} 중첩 — 첫 숫자키로 통일."""
    r = asyncio.run(_chart_tool().execute(
        {"by_category": {"의류": {"count": 10, "revenue": 1_200_000},
                         "잡화": {"count": 5, "revenue": 300_000}},
         "output_dir": str(tmp_path)}, _ctx()))
    assert r["chart_count"] == 1
    assert Path(r["chart_image_paths"][0]).exists()
    assert "(" in r["charts"][0]["title"], "수치명이 제목에 표기돼야 (어떤 숫자인지 정직 라벨)"


def test_c5_chains_from_previous_results(tmp_path):
    ctx = _ctx(previous_results={"t1": {"by_group": {"Meta": 10, "CRM": 4}}})
    r = asyncio.run(_chart_tool().execute({"output_dir": str(tmp_path)}, ctx))
    assert r["chart_count"] == 1


# ── 정직 — 빈/장식 차트 금지 ─────────────────────────────────────────────

def test_c6_nothing_chartable_is_honest_insufficient(tmp_path):
    r = asyncio.run(_chart_tool().execute(
        {"note": "텍스트뿐", "output_dir": str(tmp_path)}, _ctx()))
    assert r["reason"] == "data_insufficient"   # executor 가 SKIPPED 로 표시 (silent-0 convention)
    assert r["chart_image_paths"] == []


def test_c7_dataref_stub_not_charted(tmp_path):
    ctx = _ctx(previous_results={"t1": {"orders_raw": {"_dataref": True, "count": 3420}}})
    r = asyncio.run(_chart_tool().execute({"output_dir": str(tmp_path)}, ctx))
    assert r.get("reason") == "data_insufficient", "참조 스텁(모형)을 차트화하면 안 됨"


# ── pptx 차트 첨부 (구 chart_to_slide 흡수) ──────────────────────────────

def test_p1_pptx_attaches_chart_slides(tmp_path):
    chart = asyncio.run(_chart_tool().execute(
        {"by_channel": {"a": 3, "b": 1}, "output_dir": str(tmp_path)}, _ctx()))
    pptx_tool = get_agent_pool().get_real_tool("pptx_generator")
    ctx = _ctx(previous_results={
        "t1": {"report_markdown": "# 보고서\n\n## 섹션\n- 불릿\n"},
        "t2": chart,
    })
    r = asyncio.run(pptx_tool.execute({"output_dir": str(tmp_path)}, ctx))
    assert r["slide_count"] == 3   # 타이틀 1 + 섹션 1 + 차트 1

    from pptx import Presentation
    prs = Presentation(r["pptx_file_path"])
    assert len(prs.slides) == 3


def test_p2_pptx_skips_missing_chart_file(tmp_path):
    pptx_tool = get_agent_pool().get_real_tool("pptx_generator")
    ctx = _ctx(previous_results={
        "t1": {"report_markdown": "# t\n\n## s\n- b\n",
               "chart_image_paths": [str(tmp_path / "없는파일.png")]},
    })
    r = asyncio.run(pptx_tool.execute({"output_dir": str(tmp_path)}, ctx))
    assert r["slide_count"] == 2, "없는 파일을 빈 차트 슬라이드로 꾸미지 않는다 (I1)"
