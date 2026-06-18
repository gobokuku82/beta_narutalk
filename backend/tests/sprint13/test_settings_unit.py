"""T5 — Settings / .env 확장 Unit 테스트

명세서: docs/_claude/checkpointer/sprint13_test_t5_settings_spec.md
대상: backend/app/core/config.py Settings + .env.example

6 케이스.
"""

from pathlib import Path

import pytest


NEW_FIELD_NAMES = [
    "DEFAULT_USER_ID",
    "MAX_CONCURRENT_TURNS_PER_USER",
    "MAX_WS_CONNECTIONS_PER_USER",
    "DEFAULT_HISTORY_LIMIT",
    "MAX_HISTORY_LIMIT",
    "TITLE_SOURCE",
    "TITLE_MAX_LENGTH",
]


# ──────────────────────────────────────────────────────────────────
# SE-01
# ──────────────────────────────────────────────────────────────────

def test_SE01_new_fields_exist():
    from app.core.config import Settings

    s = Settings(_env_file=None)

    for name in NEW_FIELD_NAMES:
        assert hasattr(s, name), f"누락 필드: {name}"


# ──────────────────────────────────────────────────────────────────
# SE-02
# ──────────────────────────────────────────────────────────────────

def test_SE02_default_values():
    from app.core.config import Settings

    s = Settings(_env_file=None)

    assert s.DEFAULT_USER_ID == "demo"
    assert s.MAX_CONCURRENT_TURNS_PER_USER == 3
    assert s.MAX_WS_CONNECTIONS_PER_USER == 5
    assert s.DEFAULT_HISTORY_LIMIT == 3
    assert s.MAX_HISTORY_LIMIT == 10
    assert s.TITLE_SOURCE == "first_query"
    assert s.TITLE_MAX_LENGTH == 15


# ──────────────────────────────────────────────────────────────────
# SE-03
# ──────────────────────────────────────────────────────────────────

def test_SE03_field_types():
    from app.core.config import Settings

    s = Settings(_env_file=None)

    assert isinstance(s.DEFAULT_USER_ID, str)
    assert isinstance(s.MAX_CONCURRENT_TURNS_PER_USER, int)
    assert isinstance(s.MAX_WS_CONNECTIONS_PER_USER, int)
    assert isinstance(s.DEFAULT_HISTORY_LIMIT, int)
    assert isinstance(s.MAX_HISTORY_LIMIT, int)
    assert isinstance(s.TITLE_SOURCE, str)
    assert isinstance(s.TITLE_MAX_LENGTH, int)


# ──────────────────────────────────────────────────────────────────
# SE-04 — env override
# ──────────────────────────────────────────────────────────────────

def test_SE04_env_override(monkeypatch):
    monkeypatch.setenv("MAX_CONCURRENT_TURNS_PER_USER", "10")
    monkeypatch.setenv("DEFAULT_USER_ID", "test_user")
    monkeypatch.setenv("TITLE_MAX_LENGTH", "20")

    from app.core.config import Settings
    s = Settings(_env_file=None)

    assert s.MAX_CONCURRENT_TURNS_PER_USER == 10
    assert s.DEFAULT_USER_ID == "test_user"
    assert s.TITLE_MAX_LENGTH == 20


# ──────────────────────────────────────────────────────────────────
# SE-05 — 잘못된 타입은 ValidationError
# ──────────────────────────────────────────────────────────────────

def test_SE05_invalid_type_rejected(monkeypatch):
    monkeypatch.setenv("MAX_CONCURRENT_TURNS_PER_USER", "not_a_number")

    from app.core.config import Settings
    with pytest.raises(Exception) as exc_info:
        Settings(_env_file=None)

    # pydantic ValidationError 메시지에 필드명 포함
    assert "MAX_CONCURRENT_TURNS_PER_USER" in str(exc_info.value) or "int" in str(exc_info.value).lower()


# ──────────────────────────────────────────────────────────────────
# SE-06 — .env.example에 신규 필드 명시
# ──────────────────────────────────────────────────────────────────

def test_SE06_env_example_has_new_fields():
    # pyproject.toml의 testpaths=backend/tests 기준. 프로젝트 루트는 상위.
    # cwd가 어디든 확실하게 찾기 위해 이 테스트 파일 위치 기준으로 탐색.
    here = Path(__file__).resolve()
    # backend/tests/sprint13/test_settings_unit.py → 3단계 상위 = 프로젝트 루트
    project_root = here.parents[3]
    env_example = project_root / ".env.example"

    assert env_example.exists(), f".env.example 없음: {env_example}"
    text = env_example.read_text(encoding="utf-8")

    for key in NEW_FIELD_NAMES:
        assert key in text, f".env.example에 누락: {key}"
