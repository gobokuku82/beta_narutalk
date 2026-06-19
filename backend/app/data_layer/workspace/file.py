"""FileWorkspace — POC. data/{client}/{layer}/{key} 파일 기반.

이전 (Step 3b, 2026-05-27): dream_agent/tools/shared/storage.py::FileStorage 이동.
client 별 격리: data/{client}/computed/... 등 회사명 무관.

단계 2 (2026-05-29): client-aware 전환. save/load/exists/list_keys 가 client 인자를
받아 data/{client}/{layer} 로 분기 (ADR-022 §미해결 "MVP dynamic client 분리" 실행).
단계 5 (2026-05-30): default 제거 — client 필수. 진입점(runner·API)이 항상 전달.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

from .base import Layer, WorkspaceBackend

logger = get_logger(__name__)


class FileWorkspace(WorkspaceBackend):
    """POC — data/{client}/{layer}/{key} 파일 기반 (client-aware).

    경로 = data/{client}/{LAYER_DIR[layer]}/{key}. client 필수(default 없음).
    MVP+ PostgresWorkspace 전환 시 client = schema/tenant.
    """

    LAYER_DIR = {
        "raw": "raw",
        "normalized": "normalized",   # 피봇 P1 (2026-06-17): cleaned→normalized rename
        "computed": "computed",
        "blended": "blended",   # ADR-032 D2: 교차소스 집계 레이어
    }

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)

    # ── 내부 유틸 ──
    def _dir(self, layer: Layer, client: str) -> Path:
        d = self.repo_root / "data" / client / self.LAYER_DIR[layer]
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _path(self, layer: Layer, key: str, client: str) -> Path:
        return self._dir(layer, client) / key

    # ── WorkspaceBackend 구현 ──
    def save(
        self,
        layer: Layer,
        key: str,
        data: Any,
        meta: dict | None = None,
        *,
        client: str,
    ) -> str:
        path = self._path(layer, key, client)

        if key.endswith(".json"):
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        elif key.endswith(".parquet"):
            import pandas as pd
            df = data if hasattr(data, "to_parquet") else pd.DataFrame(data)
            df.to_parquet(path, index=False)
        elif key.endswith(".jsonl"):
            lines = [json.dumps(x, ensure_ascii=False) for x in data]
            path.write_text("\n".join(lines), encoding="utf-8")
        else:
            raise ValueError(f"Unsupported extension: {key}")

        if meta:
            schema_dir = self._dir(layer, client) / "_schema"
            schema_dir.mkdir(exist_ok=True)
            schema_path = schema_dir / f"{path.stem}.json"
            schema_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        rel = str(path.relative_to(self.repo_root)).replace("\\", "/")
        logger.info("workspace.save", layer=layer, key=key, location=rel)
        return rel

    def load(self, layer: Layer, key: str, *, client: str) -> Any:
        path = self._path(layer, key, client)
        if not path.exists():
            raise FileNotFoundError(f"Not found: {path}")

        if key.endswith(".json"):
            return json.loads(path.read_text(encoding="utf-8"))
        if key.endswith(".parquet"):
            import pandas as pd
            return pd.read_parquet(path)
        if key.endswith(".jsonl"):
            return [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        raise ValueError(f"Unsupported extension: {key}")

    def exists(self, layer: Layer, key: str, *, client: str) -> bool:
        return self._path(layer, key, client).exists()

    def list_keys(
        self, layer: Layer, prefix: str | None = None, *, client: str
    ) -> list[str]:
        d = self.repo_root / "data" / client / self.LAYER_DIR[layer]
        if not d.exists():
            return []
        return sorted(
            p.name for p in d.iterdir()
            if p.is_file() and (not prefix or p.name.startswith(prefix))
        )


__all__ = ["FileWorkspace"]
