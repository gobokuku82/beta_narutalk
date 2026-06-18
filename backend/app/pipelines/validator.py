"""Pipeline 산출 Validator — ADR-024 V4 (정답 보존) 의 코드 측 구현.

검증 3종:
    1. schema   — Pydantic Output 모델 model_validate 통과 (ValidatorDef.output_schema)
    2. expected — value_min / rows_min 등 경계 검사
    3. reference — 정답 fixture 파일과 subset deep-compare (clumi 정답 17 보존)

fail_policy:
    block  — 실패 시 RunStatus=failed
    alert  — 실패 기록 + RunStatus=completed (로그·UI 경고)
    ignore — 검증 스킵

Status: complete — Phase 1 M1 (2026-05-28).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel

from app.core.logging import get_logger
from app.pipelines.models import PipelineDef
from app.schemas import outputs as standard_outputs

logger = get_logger(__name__)

# schema 이름 해석 — 표준 outputs 패키지(__init__ 가 dashboard1 + 전 batch 재노출).
# (구 clumi_outputs 는 schemas/outputs/dashboard1 로 통합됨 — 2026-05-28)
_SCHEMA_MODULES = [standard_outputs]


def _resolve_schema(name: str) -> Optional[type[BaseModel]]:
    """schema 이름 → 등록 모듈에서 Pydantic 모델 탐색."""
    for module in _SCHEMA_MODULES:
        model = getattr(module, name, None)
        if isinstance(model, type) and issubclass(model, BaseModel):
            return model
    return None


def _first_numeric(output: dict[str, Any]) -> Optional[float]:
    """output 의 첫 숫자 값 (value_min 비교용 — KPI 단일 값 패턴)."""
    for k, v in output.items():
        if k.startswith("_"):
            continue
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            return float(v)
    return None


def _deep_subset_match(expected: Any, actual: Any, path: str = "") -> list[str]:
    """expected 의 모든 키·값이 actual 에 존재·일치하는지 (subset). 불일치 경로 목록 반환."""
    mismatches: list[str] = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path or '<root>'}: type dict != {type(actual).__name__}"]
        for k, v in expected.items():
            if k not in actual:
                mismatches.append(f"{path}.{k}: missing")
            else:
                mismatches.extend(_deep_subset_match(v, actual[k], f"{path}.{k}"))
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) < len(expected):
            mismatches.append(f"{path}: list mismatch")
        else:
            for i, v in enumerate(expected):
                mismatches.extend(_deep_subset_match(v, actual[i], f"{path}[{i}]"))
    else:
        if expected != actual:
            mismatches.append(f"{path}: {expected!r} != {actual!r}")
    return mismatches


def validate_output(
    pipeline: PipelineDef,
    output: dict[str, Any],
    *,
    base_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """산출 검증 → {ok, checks[], fail_policy}.

    base_dir: reference.file 상대 경로 해석 기준 (기본 = repo backend/).
    """
    v = pipeline.validator
    if v is None or v.fail_policy == "ignore":
        return {"ok": True, "checks": [], "fail_policy": v.fail_policy if v else "ignore"}

    checks: list[dict[str, Any]] = []
    ok = True

    # 1. schema
    if v.output_schema:
        model = _resolve_schema(v.output_schema)
        if model is None:
            checks.append({"check": "schema", "schema": v.output_schema, "ok": True,
                           "note": "schema 모델 미발견 — skip"})
        else:
            try:
                model.model_validate(output)
                checks.append({"check": "schema", "schema": v.output_schema, "ok": True})
            except Exception as e:  # noqa: BLE001
                ok = False
                checks.append({"check": "schema", "schema": v.output_schema, "ok": False,
                               "error": str(e)})

    # 2. expected (value_min / rows_min)
    if "value_min" in v.expected:
        val = _first_numeric(output)
        passed = val is not None and val >= v.expected["value_min"]
        ok = ok and passed
        checks.append({"check": "value_min", "min": v.expected["value_min"],
                       "actual": val, "ok": passed})
    if "rows_min" in v.expected:
        rows = output.get("rows") or output.get("table") or output.get("items")
        n = len(rows) if hasattr(rows, "__len__") else 0
        passed = n >= v.expected["rows_min"]
        ok = ok and passed
        checks.append({"check": "rows_min", "min": v.expected["rows_min"],
                       "actual": n, "ok": passed})

    # 3. reference (정답 보존 — subset deep-compare)
    if v.reference and v.reference.get("file"):
        ref_path = Path(v.reference["file"])
        if not ref_path.is_absolute():
            base = base_dir or Path(__file__).resolve().parents[2]  # backend/
            ref_path = (base / ref_path).resolve()
        if ref_path.exists():
            expected = json.loads(ref_path.read_text(encoding="utf-8"))
            mismatches = _deep_subset_match(expected, output)
            passed = not mismatches
            ok = ok and passed
            checks.append({"check": "reference", "file": str(ref_path), "ok": passed,
                           "mismatches": mismatches[:10]})
        else:
            checks.append({"check": "reference", "file": str(ref_path), "ok": True,
                           "note": "reference 파일 없음 — skip"})

    return {"ok": ok, "checks": checks, "fail_policy": v.fail_policy}


__all__ = ["validate_output"]
