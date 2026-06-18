"""Sprint 14 A1 — 그룹 D: Settings Validator Unit (5건)

명세: docs/_claude/sprint14_a1_hitl_timeout_plan.md §R2 그룹 D
대상: backend/app/core/config.py
  - HITL_RESUME_TIMEOUT_SEC: int = Field(default=1800, ge=1)

고려사항 (F-12): settings singleton 은 import-time 로드. monkeypatch.setenv 후 Settings()
재 인스턴스화 필요.
"""

import pytest
from pydantic import ValidationError


def _new_settings(ignore_env_file: bool = False):
    """env 재로드 위한 새 Settings 인스턴스.

    ignore_env_file=True — .env 파일 무시 (테스트 호스트의 .env 가 값을 덮지 않도록).
    """
    from app.core.config import Settings
    if ignore_env_file:
        return Settings(_env_file=None)
    return Settings()


# ──────────────────────────────────────────────────────────────────
# HT-12 — 0 → ValidationError
# ──────────────────────────────────────────────────────────────────

def test_HT12_env_zero_raises_validation_error(monkeypatch):
    monkeypatch.setenv("HITL_RESUME_TIMEOUT_SEC", "0")
    with pytest.raises(ValidationError):
        _new_settings()


# ──────────────────────────────────────────────────────────────────
# HT-12b — 음수 → ValidationError
# ──────────────────────────────────────────────────────────────────

def test_HT12b_env_negative_raises_validation_error(monkeypatch):
    monkeypatch.setenv("HITL_RESUME_TIMEOUT_SEC", "-5")
    with pytest.raises(ValidationError):
        _new_settings()


# ──────────────────────────────────────────────────────────────────
# HT-12c — 경계값 1 → 정상
# ──────────────────────────────────────────────────────────────────

def test_HT12c_env_boundary_one_accepted(monkeypatch):
    monkeypatch.setenv("HITL_RESUME_TIMEOUT_SEC", "1")
    s = _new_settings()
    assert s.HITL_RESUME_TIMEOUT_SEC == 1


# ──────────────────────────────────────────────────────────────────
# HT-12d — env 없음 → 기본값 1800
# ──────────────────────────────────────────────────────────────────

def test_HT12d_env_absent_uses_default(monkeypatch):
    """env + .env 둘 다 없는 상태 → 기본값 1800."""
    monkeypatch.delenv("HITL_RESUME_TIMEOUT_SEC", raising=False)
    s = _new_settings(ignore_env_file=True)
    assert s.HITL_RESUME_TIMEOUT_SEC == 1800


# ──────────────────────────────────────────────────────────────────
# HT-12e — 비숫자 → ValidationError
# ──────────────────────────────────────────────────────────────────

def test_HT12e_env_non_numeric_raises_validation_error(monkeypatch):
    monkeypatch.setenv("HITL_RESUME_TIMEOUT_SEC", "abc")
    with pytest.raises(ValidationError):
        _new_settings()
