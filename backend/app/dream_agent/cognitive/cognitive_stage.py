"""Cognitive Stage — 자연어 → StructuredQuery 번역

4-Layer 파이프라인의 첫 단계. 사용자 입력을 Agent가 이해할 수 있는
정형 쿼리(StructuredQuery)로 변환한다.

개념 서브 단계:
  ① input_normalizer    (프롬프트 silent 처리)
  ② intent_classifier   (goal.type + original_domain)
  ③ entity_extractor    (targets.brand/source/period 등)
  ④ query_completer     (goal.depth + tasks[])
  ⑤ cognitive_validator (Pydantic 파싱)

Reference: docs/agent_specs/system_architecture_spec_v1.5.md §2.2
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from langgraph.graph import END
from langgraph.types import Command
from pydantic import ValidationError

from app.core.logging import get_logger
from app.dream_agent.cognitive.history_injector import build_context_summary
from app.dream_agent.cognitive.intent_shim import intent_to_tasks
from app.dream_agent.llm_manager import get_llm_client
from app.dream_agent.schemas.structured_query import StructuredQuery
from app.dream_agent.states.agent_state import AgentState

logger = get_logger(__name__)

# 프롬프트 경로: app/dream_agent/cognitive/cognitive_stage.py → app/dream_agent/
PROMPTS_DIR = Path(__file__).parent.parent / "llm_manager" / "prompts"
COGNITIVE_PROMPT_PATH = PROMPTS_DIR / "cognitive.yaml"
CLIENTS_PROMPT_DIR = PROMPTS_DIR / "clients"

_cog_prompt_cache: dict | None = None
_client_profile_cache: dict[str, dict | None] = {}


def _load_cognitive_prompt() -> dict:
    global _cog_prompt_cache
    if _cog_prompt_cache is None:
        with open(COGNITIVE_PROMPT_PATH, "r", encoding="utf-8") as f:
            _cog_prompt_cache = yaml.safe_load(f)
    return _cog_prompt_cache


def _load_client_profile(client_id: str | None) -> dict | None:
    """clients/{client_id}.yaml 로드 (회사별 cognitive 지식). 없으면 None → 공용만 사용.

    Status: complete — A3 (2026-06-04): "회사마다 다른 시스템" 배선.
    회사 추가 = clients/{client}.yaml 한 장 (코드 무변경).
    """
    if not client_id:
        return None
    if client_id not in _client_profile_cache:
        path = CLIENTS_PROMPT_DIR / f"{client_id}.yaml"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _client_profile_cache[client_id] = yaml.safe_load(f)
        else:
            # 결정(fail-fast vs generic)은 caller(cognitive_stage)가 함 — 여기선 사실만 기록
            _client_profile_cache[client_id] = None
            logger.debug("client profile 파일 없음", client_id=client_id, path=str(path))
    return _client_profile_cache[client_id]


def _build_client_block(profile: dict) -> str:
    """클라이언트 프로필 → system_prompt 주입 텍스트 (brand·sources·KPI·은어·프로모션)."""
    out: list[str] = ["\n\n═══════════════════════════════════════════",
                      "## CLIENT PROFILE — 이 회사 전용 지식 (주입)",
                      "═══════════════════════════════════════════"]
    if profile.get("brand_context"):
        out.append(f"\n### 브랜드\n{profile['brand_context'].rstrip()}")
    srcs = profile.get("available_sources") or []
    if srcs:
        out.append("\n### 보유 데이터 소스 (targets.source 는 이 id 중 하나, 또는 unknown/multi)")
        out += [f"  - {s.get('id')}: {s.get('desc', '')}" for s in srcs]
    glos = profile.get("metric_glossary") or []
    if glos:
        out.append("\n### KPI 어휘 (이 용어가 보이면 metric_calculation)")
        out += [f"  - {g.get('term')}: {g.get('def', '')}" for g in glos]
    promos = profile.get("promotions") or []
    if promos:
        out.append(f"\n### 프로모션 코드: {', '.join(promos)}")
    slang = profile.get("brand_slang_map") or []
    if slang:
        out.append("\n### 브랜드 특정 은어 정규화")
        out += [f"  - {s}" for s in slang]
    return "\n".join(out)


def prepare_cognitive_prompt(state: AgentState, user_template: str) -> str:
    """AgentState + user_template → 포맷팅된 user_prompt (Sprint 13 I8).

    - state.conversation_history + state.history_limit → build_context_summary 호출
    - user_template의 {context_summary}에 주입
    - {user_input}, {language}도 동일 format 인자로

    Pure function — state를 수정하지 않음.

    Args:
        state: AgentState (user_input, language, conversation_history, history_limit 읽음)
        user_template: cognitive.yaml의 user_template 문자열

    Returns:
        포맷팅된 prompt 문자열.
    """
    user_input = state.get("user_input", "")
    language = state.get("language", "ko")
    history = state.get("conversation_history", [])
    history_limit = state.get("history_limit")   # None이면 injector가 Settings fallback

    context_summary = build_context_summary(history, history_limit)

    return user_template.format(
        user_input=user_input,
        language=language,
        context_summary=context_summary,
    )


async def cognitive_stage(state: AgentState) -> Command[Any]:
    """자연어 → StructuredQuery 번역.

    Args:
        state: AgentState (user_input, language, session_id 읽음)

    Returns:
        Command(update={structured_query}, goto="planning") — 정상
        Command(update={error}, goto=END)                    — 실패
    """
    user_input = state.get("user_input", "")
    language = state.get("language", "ko")
    session_id = state.get("session_id", "")

    logger.info("cognitive start", session_id=session_id, input=user_input[:60])

    config = _load_cognitive_prompt()
    system_prompt = config.get("system_prompt", "")
    user_template = config.get("user_template", "")
    lang_instructions = config.get("language_instructions", {})
    if language in lang_instructions:
        system_prompt += f"\n\n{lang_instructions[language]}"

    # 클라이언트 프로필 주입 (회사별 지식)
    # provenance 원칙 (2026-06-04): silent fallback 금지 — 어떤 프로필로 돌았는지 항상 명시.
    #   - client_id 명시 + 프로필 없음 → fail-fast (조용한 generic 금지, 데이터레이어 ADR-022 helper-B 정합)
    #   - client_id 없음 → generic 모드를 *명시적으로* 경고 (provenance=none)
    client_id = state.get("client_id")
    profile = _load_client_profile(client_id)
    if client_id and profile is None:
        msg = (f"client '{client_id}' cognitive 프로필 없음 "
               f"(clients/{client_id}.yaml 필요). generic fallback 안 함 (fail-fast).")
        logger.error("cognitive client profile missing — fail-fast", client_id=client_id)
        return Command(update={"error": msg}, goto=END)
    profile_provenance = client_id if profile else "none"
    if profile:
        system_prompt += _build_client_block(profile)
    else:
        logger.warning(
            "cognitive GENERIC 모드 — client profile 없음 (provenance=none, 공용 프롬프트만)",
            client_id=client_id,
        )

    # few-shot embed — 프로필 few_shot 우선, 없으면 공용 examples fallback
    examples = (profile or {}).get("few_shot") or config.get("examples", [])
    if examples:
        block = "\n\n## Examples\n"
        for i, ex in enumerate(examples, 1):
            block += f"\n### Example {i}\nInput: {ex['input']}\n"
            block += f"Output:\n{json.dumps(ex['output'], ensure_ascii=False, indent=2)}\n"
        system_prompt += block

    user_prompt = prepare_cognitive_prompt(state, user_template)

    client = get_llm_client("cognitive")
    try:
        raw = await client.generate_json(prompt=user_prompt, system_prompt=system_prompt)
        sq = StructuredQuery.model_validate(raw)
    except (ValidationError, Exception) as e:
        logger.error("cognitive failed", error=str(e))
        return Command(update={"error": f"Cognitive failed: {e}"}, goto=END)

    # PMAL (W3): intent 가 canonical → tasks 를 intent 에서 파생(W2 shim). intent=진실, tasks=그림자.
    # 분석 의도(domain 있음) 또는 operation-driven(recommend/diagnose/forecast/attribute)일 때 파생.
    # measure(+factual_lookup=Q&A)·모호(domain 빈 measure)는 LLM tasks 유지 — measure 제외가 그 보호
    # (2026-06-10: domain 없는 "개선안 추천해줘" 류가 라우팅 못 되던 것 해소, stage1 C).
    _op = (sq.intent.operation or "").lower() if sq.intent else ""
    if sq.intent is not None and (sq.intent.domain or _op in {"recommend", "diagnose", "forecast", "attribute"}):
        sq.tasks = intent_to_tasks(sq.intent)

    logger.info(
        "cognitive done",
        profile=profile_provenance,   # provenance: 어떤 client 프로필로 돌았나 (none=generic)
        brand=sq.targets.brand,
        operation=(sq.intent.operation if sq.intent else None),
        domain=(sq.intent.domain if sq.intent else None),
        depth=sq.goal.depth.value,
        tasks=[t.id.value for t in sq.tasks],
        cleaned=sq.meta.cleaned,      # 에이전트가 이해한 의도 재진술 (관측·진단용)
    )
    return Command(
        update={"structured_query": sq.model_dump(mode="json")},
        goto="planning",
    )
