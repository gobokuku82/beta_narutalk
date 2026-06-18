"""Foundation 순수성 가드 — app.core 는 상위 레이어(app.dream_agent)를 import 하면 안 된다.

spec 16 §4 V1: core/decorators.py 의 trace_log 가 workflow_managers.learning_manager 를
(lazy) import 해 core↔workflow_managers 논리 순환(최하위↔최상위). trace_log 를 learning_manager
로 이전해 해소. 이 테스트가 재발 방지(아키텍처 불변식 I-core: foundation↛orchestration).
"""
from __future__ import annotations

import re
from pathlib import Path

_CORE = Path(__file__).resolve().parents[1] / "app" / "core"
_BACKEND = _CORE.parent.parent
_IMPORT_DREAM = re.compile(r"^\s*(from|import)\s+app\.dream_agent")


def test_core_does_not_import_dream_agent():
    offenders: list[str] = []
    for py in _CORE.rglob("*.py"):
        for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if _IMPORT_DREAM.match(line):
                offenders.append(f"{py.relative_to(_BACKEND)}:{i}: {line.strip()}")
    assert offenders == [], (
        "foundation(app.core) 가 상위 레이어 app.dream_agent 를 import (V1 순환):\n"
        + "\n".join(offenders)
    )
