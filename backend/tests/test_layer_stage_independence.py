"""Stage 독립성 가드 — response stage 는 cognitive stage 내부를 import 하면 안 된다.

spec 16 §4 V5: responder 가 `cognitive.intent_shim.DEGRADE_OPS` 를 import (마지막 stage가
첫 stage 내부를 파고드는 옆결합). 공유 상수 DEGRADE_OPS 를 schemas(공유 계약, 둘 다 하향
의존)로 이전해 해소. 이 테스트가 재발 방지.
"""
from __future__ import annotations

import re
from pathlib import Path

_RESPONSE = Path(__file__).resolve().parents[1] / "app" / "dream_agent" / "response"
_IMPORT_COGNITIVE = re.compile(r"^\s*(from|import)\s+app\.dream_agent\.cognitive")


def test_response_does_not_import_cognitive():
    offenders: list[str] = []
    for py in _RESPONSE.rglob("*.py"):
        for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if _IMPORT_COGNITIVE.match(line):
                offenders.append(f"response/{py.name}:{i}: {line.strip()}")
    assert offenders == [], (
        "response stage 가 cognitive 내부를 import (V5 stage↔stage 옆결합). "
        "공유 상수는 schemas 로:\n" + "\n".join(offenders)
    )
