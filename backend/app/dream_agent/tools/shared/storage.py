"""storage.py — 호환 shim (Step 3b 이후, 2026-05-27).

원본 구현은 `backend/app/workspace/` 로 이동.
기존 import 들이 점진 전환될 때까지 본 모듈이 re-export.

이전:
    from app.dream_agent.tools.shared.storage import StorageBackend, FileStorage, get_storage, ...

전환 후 (Step 4 진행 중):
    from app.workspace import WorkspaceBackend, FileWorkspace, get_default_workspace, ...

위치 변경 사유: dream_agent 폴더 안에 두면 agent 종속처럼 보임. workspace 는
agent + direct API 둘 다 공유하는 자원 → app/ 직속 (dream_agent 형제).

본 shim 의 폐기 시점: Step 8 (전체 import 정리) 또는 그 이후.
"""
from __future__ import annotations

from app.workspace import (
    FileWorkspace as _FileWorkspace,
    Layer,
    WorkspaceBackend as _WorkspaceBackend,
    get_default_workspace,
    reset_workspace,
    set_workspace,
)


# ── 옛 이름 alias (호환) ──
StorageBackend = _WorkspaceBackend
FileStorage = _FileWorkspace


# 옛 함수명 alias
def get_storage() -> _WorkspaceBackend:
    """[deprecated] use app.workspace.get_default_workspace()."""
    return get_default_workspace()


def set_storage(backend: _WorkspaceBackend) -> None:
    """[deprecated] use app.workspace.set_workspace()."""
    set_workspace(backend)


def reset_storage() -> None:
    """[deprecated] use app.workspace.reset_workspace()."""
    reset_workspace()


# PostgresStorage 골격 (옛 stub, MVP+ workspace/db.py 로 이전 예정)
class PostgresStorage(_WorkspaceBackend):
    """[planned] MVP+ — app/workspace/db.py 에서 본격 구현 예정."""

    def save(self, layer, key, data, meta=None):
        raise NotImplementedError("PostgresStorage 미구현 — POC 는 FileWorkspace 사용")

    def load(self, layer, key):
        raise NotImplementedError

    def exists(self, layer, key):
        raise NotImplementedError

    def list_keys(self, layer, prefix=None):
        raise NotImplementedError


__all__ = [
    "Layer",
    "StorageBackend", "FileStorage", "PostgresStorage",
    "get_storage", "set_storage", "reset_storage",
]
