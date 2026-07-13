"""Workspace — tool 산출물 *공유 저장* layer ("수십개 tool 끼리 데이터 전달").

DataSource (input 관절) 와 짝이 되는 OUTPUT 공유 공간:
    DataSource = 외부 → 시스템 (raw 데이터 가져옴)
    Workspace  = 시스템 내부 산출 (tool 들 사이 공유 + 캐시)

agent · direct API 둘 다 같은 Workspace 사용 → 정답값 캐시 공유 (ms 응답).

위치: backend/app/data_layer/workspace/ (dream_agent 형제 — agent + API 공유).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Literal

Layer = Literal["raw", "normalized", "computed", "blended"]


class WorkspaceBackend(ABC):
    """저장 추상 — POC FileWorkspace, MVP+ PostgresWorkspace 공통 인터페이스.

    구현체:
        - FileWorkspace: data/{client}/{layer}/{key} 파일 기반 (POC)
        - PostgresWorkspace: {client}.{stem}_{layer} (schema=client, 접미사 네이밍 — MVP+)
    """

    @abstractmethod
    def save(
        self,
        layer: Layer,
        key: str,
        data: Any,
        meta: dict | None = None,
        *,
        client: str,
    ) -> str:
        """저장 후 location (경로 or DB row id) 반환.

        client = 회사/테넌트 키 (필수). 진입점(runner·API)이 전달.
        MVP+ PostgresWorkspace 에선 client = DB schema/tenant.
        """

    @abstractmethod
    def load(self, layer: Layer, key: str, *, client: str) -> Any:
        """load — 없으면 FileNotFoundError."""

    @abstractmethod
    def exists(self, layer: Layer, key: str, *, client: str) -> bool:
        """키 존재 여부."""

    @abstractmethod
    def list_keys(
        self, layer: Layer, prefix: str | None = None, *, client: str
    ) -> list[str]:
        """레이어의 키 목록."""


__all__ = ["WorkspaceBackend", "Layer"]
