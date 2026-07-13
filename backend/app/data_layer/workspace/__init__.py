"""Workspace layer — tool 산출물 공유 저장 ("수십개 tool 끼리 데이터 전달").

DataSource (input 관절) 와 짝:
    app/data_layer/data_sources/ — 외부 → 시스템 INPUT
    app/data_layer/workspace/    — 시스템 내부 OUTPUT 공유 (본 패키지)

위치: backend/app/data_layer/workspace/ (dream_agent 형제 — agent + API 공유)
"""
from __future__ import annotations
from pathlib import Path

from .base import Layer, WorkspaceBackend
from .file import FileWorkspace

# ── 싱글톤 ──
_default: WorkspaceBackend | None = None


def get_default_workspace() -> WorkspaceBackend:
    """전역 default workspace (POC: FileWorkspace)."""
    global _default
    if _default is None:
        # backend/app/data_layer/workspace/__init__.py → parents: workspace(0) data_layer(1) app(2) backend(3)
        repo_root = Path(__file__).resolve().parents[3]
        _default = FileWorkspace(repo_root)
    return _default


def set_workspace(ws: WorkspaceBackend) -> None:
    """테스트용 — DI override."""
    global _default
    _default = ws


def reset_workspace() -> None:
    """테스트용 — 싱글톤 초기화."""
    global _default
    _default = None


__all__ = [
    "Layer",
    "WorkspaceBackend",
    "FileWorkspace",
    "get_default_workspace",
    "set_workspace",
    "reset_workspace",
]
