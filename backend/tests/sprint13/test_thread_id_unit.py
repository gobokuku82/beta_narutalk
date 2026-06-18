"""T3 — thread_id 조합/분해 Unit 테스트

명세서: docs/_claude/checkpointer/sprint13_test_t3_thread_id_spec.md
대상: backend/api_v2/thread_id.py (신규)

5 케이스.
"""

import uuid
import pytest


# ──────────────────────────────────────────────────────────────────
# TH-01
# ──────────────────────────────────────────────────────────────────

def test_TH01_make_thread_id_basic():
    from api_v2.thread_id import make_thread_id

    conv = "550e8400-e29b-41d4-a716-446655440000"
    turn = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

    result = make_thread_id(conv, turn)

    expected = "550e8400-e29b-41d4-a716-446655440000_6ba7b810-9dad-11d1-80b4-00c04fd430c8"
    assert result == expected


# ──────────────────────────────────────────────────────────────────
# TH-02
# ──────────────────────────────────────────────────────────────────

def test_TH02_make_thread_id_with_real_uuid():
    from api_v2.thread_id import make_thread_id

    conv = str(uuid.uuid4())
    turn = str(uuid.uuid4())

    result = make_thread_id(conv, turn)

    # UUID는 `-`만 포함 → `_` 구분자는 정확히 1개
    assert result.count("_") == 1
    assert result == f"{conv}_{turn}"


# ──────────────────────────────────────────────────────────────────
# TH-03
# ──────────────────────────────────────────────────────────────────

def test_TH03_parse_thread_id_roundtrip():
    from api_v2.thread_id import make_thread_id, parse_thread_id

    conv_in = str(uuid.uuid4())
    turn_in = str(uuid.uuid4())

    thread_id = make_thread_id(conv_in, turn_in)
    conv_out, turn_out = parse_thread_id(thread_id)

    assert conv_out == conv_in
    assert turn_out == turn_in


# ──────────────────────────────────────────────────────────────────
# TH-04
# ──────────────────────────────────────────────────────────────────

def test_TH04_parse_thread_id_malformed():
    from api_v2.thread_id import parse_thread_id

    # 구분자 `_` 없음 → ValueError
    with pytest.raises(ValueError):
        parse_thread_id("noseparator")

    # 빈 문자열 → ValueError
    with pytest.raises(ValueError):
        parse_thread_id("")


# ──────────────────────────────────────────────────────────────────
# TH-05
# ──────────────────────────────────────────────────────────────────

def test_TH05_thread_id_uniqueness():
    from api_v2.thread_id import make_thread_id

    conv = str(uuid.uuid4())
    turn1 = str(uuid.uuid4())
    turn2 = str(uuid.uuid4())

    tid1 = make_thread_id(conv, turn1)
    tid2 = make_thread_id(conv, turn2)

    assert tid1 != tid2  # 같은 conv, 다른 turn → 다른 thread_id
    # 두 thread_id는 같은 conv prefix 공유 (그룹핑 가능)
    assert tid1.startswith(conv + "_")
    assert tid2.startswith(conv + "_")
