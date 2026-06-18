"""stub 처분 2차 — creative_team·excel/word 렌더 stub 폐기 회귀 (2026-06-12).

(구 파일명 유지 — D1 excel 분리(2026-06-08) 특성화 테스트였으나, 오너 결정
"구현 가능한 건 구현하면서 줄이자"로 excel_agent 자체가 폐기되어 의도적으로 반전.
구 D1-1~D1-4 단언은 git 히스토리 참조.)

새 박제(폐기 상태가 회귀로 깨지지 않게):
  S2-1 creative_team 이 catalog 에 없음 (팀 3: analysis/qa/decision)
  S2-2 excel_agent 부재 + 폐기 tool 16종이 어느 agent 에도 없음
  S2-3 report_generation 힌트 = 3갈래 (excel_agent 제외)
  S2-4 stub 0 — stub 제도 자체 폐지 (2026-06-12 오너 최종 처분: chart_generator 실구현,
       chart_to_slide 폐기[소비자 0·pptx_generator 가 흡수], slide_designer 폐기[D10 확보 시
       재채용]. mock_tools "되는 척" 경로 삭제 — 비구현 tool 은 카탈로그 등재 금지)
"""
from __future__ import annotations

from pathlib import Path

import yaml

_CATALOG = Path(__file__).parents[1] / "app" / "dream_agent" / "planning" / "catalog" / "team_catalog.yaml"

_RETIRED_TOOLS = {
    # 렌더 확장 (2026-06-12 폐기)
    "word_template_filler", "excel_template_filler",
    # 렌더 확장 3차 (2026-06-12 폐기 — template_choice 소비자 0, R6)
    "template_selector",
    # 렌더 확장 4차 (2026-06-12 폐기 — stub 0 처분: chart_slides 소비자 0·pptx_generator 흡수 / D10 대기)
    "chart_to_slide", "slide_designer",
    # 크리에이티브 9 (2026-06-12 폐기)
    "image_generator", "image_resizer", "thumbnail_creator",
    "storyboard_creator", "video_image_generator",
    "slogan_writer", "copy_generator", "material_modifier", "variation_generator",
    # 분석 stub 2 (2026-06-12 폐기 — 도메인 정의는 spec 32 §7.1)
    "trend_analyzer", "competitor_comparator",
}


def _catalog() -> dict:
    return yaml.safe_load(_CATALOG.read_text(encoding="utf-8"))


def _all_tools() -> list[dict]:
    return [
        t
        for team in _catalog()["teams"].values()
        for agent in team["agents"].values()
        for t in (agent.get("tools") or [])
    ]


def test_s2_1_creative_team_retired():
    teams = set(_catalog()["teams"].keys())
    assert "creative_team" not in teams, "creative_team 은 2026-06-12 폐기 — 재등장은 헌법 §7 채용 3문항 통과 후"
    assert teams == {"analysis_team", "qa_team", "decision_team"}, f"팀 구성 drift: {teams}"


def test_s2_2_retired_tools_absent_everywhere():
    names = {t["name"] for t in _all_tools()}
    leaked = _RETIRED_TOOLS & names
    assert not leaked, f"폐기 tool 이 catalog 에 재등장: {leaked}"
    agents = {
        a for team in _catalog()["teams"].values() for a in team["agents"].keys()
    }
    assert "excel_agent" not in agents, "excel_agent 는 2026-06-12 폐기"


def test_s2_3_report_generation_hint_three_way():
    rg = _catalog()["task_agent_hints"]["report_generation"]
    assert "excel_agent" not in rg, f"폐기된 excel_agent 가 힌트에 잔존: {rg}"
    assert set(rg) == {"report_text_agent", "pdf_agent", "ppt_agent"}, f"3갈래여야: {rg}"


def test_s2_4_zero_stubs_all_implemented():
    """stub 제도 폐지 박제 — 카탈로그 전 tool implemented. stub 재등장 = mock "되는 척"
    경로가 없으므로 executor 시끄러운 실패 → 등재 전 구현 또는 폐기를 강제."""
    statuses = {t["name"]: t.get("status") for t in _all_tools()}
    non_impl = {n: s for n, s in statuses.items() if s != "implemented"}
    assert not non_impl, f"비구현 tool 이 카탈로그에 등재됨 (stub 제도 폐지, 2026-06-12): {non_impl}"
