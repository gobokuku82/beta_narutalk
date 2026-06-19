"""DataSource layer — tool ↔ data 사이의 '관절' (사용자 표현).

위치: backend/app/data_layer/data_sources/ (dream_agent 형제 — agent + API 공유)
표준 패턴: Repository (Fowler) + Adapter (Cockburn Hexagonal)
"""
from __future__ import annotations
from pathlib import Path

from .base import DataSource, DataSourceError, DataSourceNotFound
from .file import (
    DEFAULT_MAPPING,
    SOURCE_REGISTRY,
    FileDataSource,
    SourceSpec,
    source_kind,
    source_platform,
    sources_by_kind,
)

# ── 싱글톤 ──
_default: DataSource | None = None


def get_default_data_source() -> DataSource:
    """전역 default DataSource (POC: FileStorage 패턴 동일)."""
    global _default
    if _default is None:
        # backend/app/data_layer/data_sources/__init__.py → parents: data_sources(0) data_layer(1) app(2) backend(3)
        repo_root = Path(__file__).resolve().parents[3]
        _default = FileDataSource(repo_root)
    return _default


def set_data_source(ds: DataSource) -> None:
    """테스트용 — DI override."""
    global _default
    _default = ds


def reset_data_source() -> None:
    """테스트용 — 싱글톤 초기화."""
    global _default
    _default = None


__all__ = [
    "DataSource",
    "DataSourceError",
    "DataSourceNotFound",
    "FileDataSource",
    "DEFAULT_MAPPING",
    "SOURCE_REGISTRY",
    "SourceSpec",
    "source_kind",
    "source_platform",
    "sources_by_kind",
    "get_default_data_source",
    "set_data_source",
    "reset_data_source",
]
