"""① cleaned 필드 — cognitive 3겹 전달(raw/cleaned/intent) 중 'cleaned' 추가 (2026-06-06).

cleaned = 에이전트가 재평가한 "사용자가 원하는 것" 평어 재진술 (관측·진단·원문안전망).
intent 가 실행 canonical, cleaned 는 진단용. LLM 산출 품질은 100쿼리 하니스(③)로 보고,
여기선 결정론으로 못박는다: (a) 스키마 additive 안전성(회귀 0), (b) 프롬프트가 cleaned 를
가르치는지(doc-code 계약 — 프롬프트가 비면 LLM 이 cleaned 를 안 채움).
"""
from __future__ import annotations

from pathlib import Path

import yaml

from app.dream_agent.schemas.structured_query import (
    Goal,
    GoalType,
    OutputFormat,
    QueryMeta,
    StructuredQuery,
    Targets,
)

_PROMPTS = Path(__file__).parents[1] / "app" / "dream_agent" / "llm_manager" / "prompts"
_COG = _PROMPTS / "cognitive.yaml"
_CLUMI = _PROMPTS / "clients" / "clumi.yaml"


# ── 스키마 additive 안전성 (기존 깨지지 않음) ──

def test_querymeta_cleaned_defaults_empty():
    # cleaned 없는 기존 JSON 도 그대로 검증 + default="" → 회귀 0
    assert QueryMeta().cleaned == ""
    assert QueryMeta.model_validate({"raw_input": "x"}).cleaned == ""


def test_querymeta_cleaned_roundtrips():
    m = QueryMeta(
        raw_input="전체 로아스는 어떻게 나온거야?",
        cleaned="전체 ROAS 값 + 그 값이 어떻게 유도되었는지(provenance) 설명을 원함",
    )
    dumped = m.model_dump(mode="json")
    assert "cleaned" in dumped
    assert QueryMeta.model_validate(dumped).cleaned == m.cleaned


def test_structured_query_carries_cleaned_to_planning():
    # planning 은 SQ 전체를 model_dump 해 프롬프트에 주입 → cleaned 가 동봉돼야 전달됨
    sq = StructuredQuery(
        targets=Targets(),
        goal=Goal(type=GoalType.METRIC, output_format=OutputFormat.TEXT),
        meta=QueryMeta(cleaned="진단용 재진술"),
    )
    assert sq.model_dump(mode="json")["meta"]["cleaned"] == "진단용 재진술"


# ── doc-code 계약: 프롬프트가 cleaned 를 가르치는가 ──

def test_cognitive_prompt_teaches_cleaned():
    cfg = yaml.safe_load(_COG.read_text(encoding="utf-8"))
    assert "cleaned" in cfg["system_prompt"], "meta 설명에 cleaned 지침 없음 → LLM 이 안 채움"
    for ex in cfg.get("examples", []):
        assert "cleaned" in ex["output"]["meta"], f"범용 예시 cleaned 누락: {ex['input']}"


def test_clumi_fewshot_all_have_cleaned():
    # clumi(POC client)는 few_shot 이 공용 examples 보다 우선 사용됨 → 여기 없으면 POC 에서 cleaned 안 채워짐
    cfg = yaml.safe_load(_CLUMI.read_text(encoding="utf-8"))
    fs = cfg.get("few_shot", [])
    assert fs, "clumi few_shot 비어있으면 안 됨"
    for ex in fs:
        assert ex["output"]["meta"].get("cleaned"), f"clumi cleaned 누락: {ex['input']}"
