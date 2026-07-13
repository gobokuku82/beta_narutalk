"""표시 메타 리졸버 (2026-07-02) — tool 산출을 '어떻게 보여줄지' 조회.

tool 레이어에 둔 이유: executor(실행)·responder(응답) 양쪽이 tool 의 표시 메타를 조회하는데,
표시 메타는 tool 자체의 속성(ToolSpec.display, tools/catalog/*.yaml)이므로 tool 레이어가 자연스러운
진실 소스다. execution/response → tool 은 하향 의존 → 의존 불변식(spec 16) 위반 없음.
(리졸버를 response/ 에 두면 execution→response 역의존이 생기므로 여기 둔다.)

미선언/미주입 tool = 항상 `_EMPTY`(전 필드 기본, infra=False) → 환각 없이 조용히 비활성(inert).
"""
from __future__ import annotations

from app.dream_agent.models.tool import DisplaySpec
from app.dream_agent.tools.registry import get_registry

_EMPTY = DisplaySpec()


def resolve(tool: str | None) -> DisplaySpec:
    """tool 이름 → DisplaySpec. 미선언/미등록 tool = _EMPTY(inert)."""
    if not tool:
        return _EMPTY
    spec = get_registry().get(tool)
    display = spec.display if spec is not None else None
    return display if display is not None else _EMPTY


def is_infra(tool: str | None) -> bool:
    """인프라 tool 여부(구 'collector' 이름 규약 대체). 미선언 = False."""
    return resolve(tool).infra


__all__ = ["resolve", "is_infra", "DisplaySpec"]
