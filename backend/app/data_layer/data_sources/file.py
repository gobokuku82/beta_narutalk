"""FileDataSource — POC. data/{client}/raw/{file} 파일 기반.

확장자 분기:
    .csv   → pandas.DataFrame
    .json  → dict | list
    .jsonl → list[dict]
    .sql   → str

DEFAULT_MAPPING = source_id → 파일명 (확장자 포함, client 무관 공통).
신규 client 추가 시 데이터 파일만 동일 이름으로 두면 자동 작동.

향후 client 별로 다른 mapping 필요 시 __init__ 에 client_mappings: dict[str, dict] 추가.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.logging import get_logger

from .base import DataSource, DataSourceNotFound

logger = get_logger(__name__)


# ── 단일 진실 소스: source_id → SourceSpec (filename + kind + platform) ──
# kind     : external(API, 외부커넥터 수집) | internal(내 서버, 내부리더)
# platform : 외부 source 플랫폼명. 내부·미정 = None.
# external/internal 구분은 폴더 아닌 매핑표·tool 책임.


@dataclass(frozen=True)
class SourceSpec:
    """수집 소스 1개 메타 — 파일명 + 종류 + 플랫폼."""
    filename: str
    kind: str                 # "external" | "internal"
    platform: str | None = None


# 프레임 추출(2026-06-19): 마케팅 도메인 소스 매핑 제거. 빈 레지스트리.
# 새 도메인은 여기에 source_id → SourceSpec(filename, kind, platform) 을 등록한다.
# 미등록 source_id 조회 시 DataSourceNotFound — 빈-프레임 정상 동작.
SOURCE_REGISTRY: dict[str, SourceSpec] = {}


# 하위호환: source_id → 파일명 (기존 import·테스트 유지). SOURCE_REGISTRY 에서 파생.
DEFAULT_MAPPING: dict[str, str] = {sid: s.filename for sid, s in SOURCE_REGISTRY.items()}


def source_kind(source_id: str) -> str | None:
    """source_id → 'external' | 'internal' | None(미등록)."""
    s = SOURCE_REGISTRY.get(source_id)
    return s.kind if s else None


def source_platform(source_id: str) -> str | None:
    """source_id → 외부 source 플랫폼명 | None."""
    s = SOURCE_REGISTRY.get(source_id)
    return s.platform if s else None


def sources_by_kind(kind: str) -> list[str]:
    """kind('external'|'internal') 의 source_id 목록 (정렬)."""
    return sorted(sid for sid, s in SOURCE_REGISTRY.items() if s.kind == kind)


class FileDataSource(DataSource):
    """data/{client}/raw/{filename} 파일 기반 DataSource."""

    def __init__(
        self,
        repo_root: Path,
        mapping: dict[str, str] | None = None,
    ):
        """
        Args:
            repo_root: project repo root (data/ 의 부모)
            mapping: source_id → 파일명 (None 이면 DEFAULT_MAPPING)
        """
        self.repo_root = Path(repo_root)
        self.mapping = mapping or DEFAULT_MAPPING

    def _path(self, client: str, source_id: str) -> Path:
        if source_id not in self.mapping:
            raise DataSourceNotFound(
                f"source_id '{source_id}' not in mapping "
                f"(registered: {sorted(self.mapping.keys())})"
            )
        filename = self.mapping[source_id]
        return self.repo_root / "data" / client / "raw" / filename

    # ── DataSource 구현 ──
    def has(self, client: str, source_id: str) -> bool:
        try:
            return self._path(client, source_id).exists()
        except DataSourceNotFound:
            return False

    def get(self, client: str, source_id: str) -> Any:
        path = self._path(client, source_id)
        if not path.exists():
            raise DataSourceNotFound(
                f"file not found: client={client} source_id={source_id} path={path}"
            )

        suffix = path.suffix.lower()
        logger.info("data_source.get", client=client, source_id=source_id,
                    suffix=suffix, path=str(path))

        if suffix == ".csv":
            return pd.read_csv(path, encoding="utf-8-sig")
        if suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if suffix == ".jsonl":
            return [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        if suffix == ".sql":
            return path.read_text(encoding="utf-8")

        raise DataSourceNotFound(f"unsupported extension: {suffix}")

    def list_sources(self, client: str) -> list[str]:
        client_dir = self.repo_root / "data" / client / "raw"
        if not client_dir.exists():
            return []
        return sorted(
            sid for sid, fname in self.mapping.items()
            if (client_dir / fname).exists()
        )

    def stream_jsonl(self, client: str, source_id: str):
        """jsonl 파일을 record 단위 yield — 대용량 메모리 절약 (예: 대용량 event source).

        Note: FileDataSource 특화 메서드. abstract DataSource 인터페이스에는 포함하지 않음
              (다른 client/storage 가 jsonl stream 일반화 필요해진 시점에 옮김).
        """
        path = self._path(client, source_id)
        if not path.exists():
            raise DataSourceNotFound(
                f"file not found: client={client} source_id={source_id} path={path}"
            )
        if path.suffix.lower() != ".jsonl":
            raise DataSourceNotFound(
                f"stream_jsonl 는 jsonl 만 지원: source_id={source_id} suffix={path.suffix}"
            )
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


__all__ = [
    "FileDataSource",
    "DEFAULT_MAPPING",
    "SourceSpec",
    "SOURCE_REGISTRY",
    "source_kind",
    "source_platform",
    "sources_by_kind",
]
