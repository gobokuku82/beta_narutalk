"""게이트 대장(43) §4 그림 = §1 표의 파생물 박제 (43 §5-3, 2026-06-12).

표를 고치고 그림 재생성을 잊으면 RED — "그림은 파생" 전략의 기계 강제.
재생성: cd backend && python -m scripts.generate_gate_map
"""
from __future__ import annotations

import re

from scripts.generate_gate_map import LEDGER, render


def test_gate_map_diagram_in_sync_with_ledger_table():
    md = LEDGER.read_text(encoding="utf-8")
    assert render(md) == md, (
        "43_gate_ledger §4 그림이 §1 표와 불일치 — "
        "`cd backend && python -m scripts.generate_gate_map` 으로 재생성하세요."
    )


def test_ledger_gate_ids_unique_and_complete():
    md = LEDGER.read_text(encoding="utf-8")
    ids = re.findall(r"^\| (G\d{2}) \|", md, re.M)
    assert len(ids) == len(set(ids)), f"게이트 ID 중복: {ids}"
    assert len(ids) >= 27, f"게이트 등기 누락 의심 (현재 {len(ids)}건 — 폐기면 행 제거+짝 단위)"
