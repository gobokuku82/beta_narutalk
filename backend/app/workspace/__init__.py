"""Workspace layer — tool 산출물 공유 저장 (사용자 표현: "수십개 tool 끼리 데이터 전달").

DataSource (input 관절) 와 짝:
    app/data_sources/ — 외부 → 시스템 INPUT
    app/workspace/    — 시스템 내부 OUTPUT 공유 (본 패키지)

위치: backend/app/workspace/ (dream_agent 형제 — agent + API 공유)
이전 (Step 3b): dream_agent/tools/shared/storage.py → 본 패키지

spec: docs/_claude/architecture/backend_data_agent_2026-05-26.md §4.0
memory: project_tool_data_agent_separation
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
        # backend/app/workspace/__init__.py → parents: workspace(0) app(1) backend(2) repo(3)
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
