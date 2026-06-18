"""Pipeline YAML 로더 — flows/ 트리에서 PipelineDef 파싱.

Maker (ADR-027) 가 생성한 YAML 정의를 읽어 PipelineDef 로 변환.
registry.py 의 catalog 로더와 같은 패턴 (YAML → Pydantic).

Status: complete — Phase 1 M1 (2026-05-28).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml

from app.core.logging import get_logger
from app.pipelines.models import PipelineDef

logger = get_logger(__name__)

FLOWS_DIR = Path(__file__).parent / "flows"
_VAR_RE = re.compile(r"\$\{(\w+)\}")


def declared_variables(pipeline: PipelineDef) -> list[str]:
    """pipeline 이 요구하는 ${var} 목록 (top-level 선언 + step inputs + cache key)."""
    found: set[str] = set()

    def scan(v: Any) -> None:
        if isinstance(v, str):
            found.update(_VAR_RE.findall(v))
        elif isinstance(v, dict):
            for x in v.values():
                scan(x)
        elif isinstance(v, list):
            for x in v:
                scan(x)

    scan(pipeline.model_extra or {})  # client/period 등 top-level ${var} 선언
    for step in pipeline.steps:
        scan(step.inputs)
    if pipeline.cache and pipeline.cache.key_template:
        scan(pipeline.cache.key_template)
    return sorted(found)


def _flows_dir(flows_dir: Optional[Path]) -> Path:
    return flows_dir or FLOWS_DIR


def load_pipeline(name: str, flows_dir: Optional[Path] = None) -> PipelineDef:
    """이름으로 pipeline YAML 1개 로드.

    Args:
        name: pipeline name (= YAML `name:` = 파일 stem)
        flows_dir: override (test용)

    Raises:
        FileNotFoundError: 해당 pipeline 없음
    """
    base = _flows_dir(flows_dir)
    # 파일명 == name.yaml 우선, 없으면 트리 스캔 (name 필드 매치)
    direct = base / f"{name}.yaml"
    if direct.exists():
        return _parse(direct)

    for yaml_file in base.rglob("*.yaml"):
        if yaml_file.name.startswith("_"):
            continue
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
        if data.get("name") == name:
            return PipelineDef.model_validate(data)

    raise FileNotFoundError(f"Pipeline '{name}' not found under {base}")


def list_pipelines(flows_dir: Optional[Path] = None) -> list[PipelineDef]:
    """flows/ 의 모든 pipeline 정의 로드 (catalog 용)."""
    base = _flows_dir(flows_dir)
    out: list[PipelineDef] = []
    if not base.exists():
        return out
    for yaml_file in sorted(base.rglob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue
        try:
            out.append(_parse(yaml_file))
        except Exception as e:  # noqa: BLE001 — 1개 실패가 전체 막지 않음
            logger.error("pipeline load failed", file=str(yaml_file), error=str(e))
    return out


def _parse(path: Path) -> PipelineDef:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return PipelineDef.model_validate(data)


__all__ = ["load_pipeline", "list_pipelines", "declared_variables", "FLOWS_DIR"]
