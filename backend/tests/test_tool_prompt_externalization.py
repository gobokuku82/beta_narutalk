"""LLM-tool 프롬프트 외부화 — 프롬프트(콘텐츠)를 tool 로직(.py)에서 분리.

agent 레이어가 llm_manager/prompts/*.yaml 로 분리한 것과 같은 콘텐츠/로직 분리(spec 16 §1,
spec 40 OS/콘텐츠). LLM 호출 tool(insight_extractor/report_writer/summary_generator)의
프롬프트를 tools/prompts/<name>.yaml 로 빼고 tools/shared/prompt_loader 로 로드.
프롬프트=자주 바뀌는 콘텐츠 → 코드 밖, 비전공자 튜닝·client overlay(추후) 가능.
"""
from __future__ import annotations

from app.dream_agent.tools.shared.prompt_loader import load_tool_prompt

# tool 별 user_template 가 가진 .format() 플레이스홀더 (이 집합으로 format 성공해야 함)
_EXPECTED_PLACEHOLDERS = {
    "insight_extractor": ["max_insights", "glossary", "analysis"],   # +glossary (S2 데이터사전 주입)
    "diagnoser": ["max_causes", "glossary", "analysis"],             # +glossary (S2-ext)
    "forecaster": ["max_items", "glossary", "analysis"],             # +glossary (S2-ext)
    "report_writer": ["glossary", "sentiment", "keywords", "insights"],  # +glossary (S2-ext)
    "summary_generator": ["max_length", "glossary", "payload"],      # +glossary (S2)
    "qa_responder": ["question", "glossary", "capabilities", "retrieved"],
}


def test_load_tool_prompts_keys_and_placeholders():
    for name, fields in _EXPECTED_PLACEHOLDERS.items():
        cfg = load_tool_prompt(name)
        assert cfg.get("system_prompt", "").strip(), f"{name}: system_prompt 비어있음"
        ut = cfg.get("user_template", "")
        assert ut.strip(), f"{name}: user_template 비어있음"
        # 선언한 플레이스홀더로 format 성공해야 함 (누락=KeyError / 미선언 placeholder=KeyError)
        ut.format(**{f: "X" for f in fields})


def test_prompt_content_moved_intact():
    assert "인사이트" in load_tool_prompt("insight_extractor")["user_template"]
    assert "보고서" in load_tool_prompt("report_writer")["user_template"]
    assert "요약" in load_tool_prompt("summary_generator")["user_template"]


def test_insight_json_braces_preserved():
    # insight 프롬프트의 JSON 예시 {{ }} 이스케이프가 보존돼야 format 후 단일 {} 로 나옴
    cfg = load_tool_prompt("insight_extractor")
    out = cfg["user_template"].format(max_insights=5, glossary="", analysis="{}")
    assert '"insights"' in out  # JSON 예시 살아있음
