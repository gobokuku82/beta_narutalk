"""Phase 2b(재설계) — planning 프롬프트가 단순 답에 말단 summary_generator 를 chain하도록 가이드.

사용자 결정(2026-06-08): response 뷰 전환의 '텍스트 보장'은 강제 코드(revert 된 compose_terminal_narration)
가 아니라 **의도-주도**여야 한다 — planning 프롬프트가 output_format=text 단순 답에 metric→summary 를
compose 하게. flow 는 분기(metric→summary | analysis | excel)이므로 LLM 이 의도로 결정.
cognitive 는 이미 operation=measure + output_format=text 시그널을 줌(무변경 — 객관 확인).

이 테스트 = 프롬프트 가이드/예시가 사라지지 않게 박제(회귀 가드) + 프롬프트 yaml 유효성.
(실제 LLM 동작은 헤드리스 진단 하니스로 별도 검증 — 본 테스트는 결정론 content 가드.)
"""
from __future__ import annotations

from pathlib import Path

import yaml

_P3 = (
    Path(__file__).parents[1]
    / "app" / "dream_agent" / "llm_manager" / "prompts" / "planning_stage3_todo.yaml"
)


def test_stage3_prompt_yaml_valid():
    cfg = yaml.safe_load(_P3.read_text(encoding="utf-8"))
    assert isinstance(cfg, dict), "planning_stage3 프롬프트가 유효한 yaml 이어야"
    assert "user_template" in cfg or "system_prompt" in cfg


def test_prompt_guides_terminal_summary_for_text_answer():
    txt = _P3.read_text(encoding="utf-8")
    assert "답변 텍스트 보장" in txt, "단순 답에 말단 summary 가이드가 프롬프트에 있어야(의도-주도)"
    assert "summary_generator" in txt and "말단" in txt
    assert "operation=measure" in txt, "단순 계산/조회도 답변 텍스트화 규칙 적용 명시"


def test_metric_example_ends_with_summary_not_number():
    txt = _P3.read_text(encoding="utf-8")
    assert "summary_generation" in txt, (
        "metric 예시(⑰.D)가 summary_generation todo 로 끝나야 — 숫자에서 멈추지 않고 답변 텍스트화"
    )
