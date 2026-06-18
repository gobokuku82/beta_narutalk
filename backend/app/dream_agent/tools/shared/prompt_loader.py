"""Tool LLM 프롬프트 로더 — tool 로직(.py)과 프롬프트(콘텐츠)를 분리.

LLM 호출 tool 의 프롬프트를 `tools/prompts/<name>.yaml` 에서 로드한다. agent 레이어가
`llm_manager/prompts/*.yaml` 로 프롬프트를 분리한 것과 같은 콘텐츠/로직 분리 패턴
(spec 16 §1 = 콘텐츠는 코드 밖, spec 40 OS층/콘텐츠층). 프롬프트는 *자주 바뀌는 콘텐츠*라
코드 밖에 둬야 — 비전공자가 .py 안 건드리고 튜닝 + client 별 overlay(추후) 가능.

프롬프트가 *tool 레이어*(tools/prompts/)에 사는 이유: 프롬프트는 그 tool 의 콘텐츠라 tool 이
소유. agent-stage 프롬프트는 orchestration 자산이라 llm_manager/ 에 사는 것과 대칭.

Status: complete — system_prompt/user_template 로드 + 캐시. client overlay 는 MVP+ 확장점.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


@lru_cache(maxsize=None)
def load_tool_prompt(name: str) -> dict:
    """tools/prompts/<name>.yaml 로드(캐시). 보통 system_prompt + user_template."""
    path = _PROMPTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"tool prompt not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
