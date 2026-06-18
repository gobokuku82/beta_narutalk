"""Pipeline API — `/api/admin/pipelines/*` (63 §2.3.3, ADR-023 Trigger=button).

§2.3.1 Direct API (/api/dashboard1/*) 와 분리:
    Direct API = 읽기 (cache hit 우선, 단일 tool).
    Pipeline API = 쓰기 트리거 (Runner 가 YAML 해석·실행·검증 → Workspace 갱신).

Endpoint 4 (POC v1):
    GET  /api/admin/pipelines            — PipelineCatalog (flows/ scan)
    POST /api/admin/pipelines/run/{name} — PipelineRunCreated (비동기 run_id 즉시)
    GET  /api/admin/pipelines/runs/{id}  — PipelineRunStatus (polling 2s)
    GET  /api/admin/pipelines/runs       — PipelineRunList (최근 N)

진행 표시 = Polling 2s (§2.3.3.5). 동시성 = (name, variables) Lock (§2.3.3.7).

Status: complete — Phase 1 M1b (2026-05-28).
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.pipelines.errors import (
    PIPELINE_DUPLICATE_RUN,
    PIPELINE_NOT_FOUND,
    PIPELINE_RUN_NOT_FOUND,
)
from app.pipelines import PipelineRunner
from app.pipelines.loader import declared_variables, list_pipelines, load_pipeline
from app.pipelines.models import RunResult
from app.pipelines.store import get_run_store

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin/pipelines", tags=["Admin", "Pipelines"])


# ─────────────────────────────────────────────────────────────────
# 요청 / 응답 모델 (63 §2.3.3.4)
# ─────────────────────────────────────────────────────────────────


class PipelineRunRequest(BaseModel):
    variables: dict[str, str] = Field(default_factory=dict)
    trigger: Literal["manual"] = "manual"


class PipelineRunCreated(BaseModel):
    run_id: str
    pipeline_name: str
    status: Literal["pending"] = "pending"
    trigger: str
    variables: dict[str, str]
    created_at: str
    poll_url: str


# ─────────────────────────────────────────────────────────────────
# RunResult → PipelineRunStatus (63 §2.3.3.4) 매핑
# ─────────────────────────────────────────────────────────────────


def _to_status_dict(r: RunResult) -> dict[str, Any]:
    completed = sum(1 for s in r.steps if s.status == "completed")
    total = r.total_steps if r.total_steps is not None else len(r.steps)
    if r.status == "completed":
        percent = 100.0
    elif total:
        percent = round(completed / total * 100, 1)
    else:
        percent = 0.0

    steps = [
        {
            "id": s.id,
            "status": s.status,
            "started_at": s.started_at,
            "completed_at": s.finished_at,
            "output_key": None,
            "error": ({"code": "PIPELINE_STEP_FAILED", "message": s.error}
                      if s.error else None),
        }
        for s in r.steps
    ]

    validator = None
    if r.validation is not None:
        issues = []
        for c in r.validation.get("checks", []):
            if not c.get("ok", True):
                sev = "error" if r.validation.get("fail_policy") == "block" else "warning"
                issues.append({"severity": sev,
                               "message": c.get("error") or f"{c.get('check')} 검증 실패"})
        validator = {"passed": r.validation.get("ok"), "issues": issues}

    error = None
    if r.status == "failed":
        error = {
            "code": r.error_code or "PIPELINE_STEP_FAILED",
            "layer": r.error_layer or "runner",
            "message": r.error or "unknown error",
            "failed_step": r.failed_step,
        }

    result_keys = [r.cache_key] if (r.cache_key and r.status == "completed") else []

    return {
        "run_id": r.run_id,
        "pipeline_name": r.pipeline,
        "status": r.status,
        "variables": {k: str(v) for k, v in r.variables.items()},
        "steps": steps,
        "progress": {"total_steps": total, "completed_steps": completed, "percent": percent},
        "validator": validator,
        "result_keys": result_keys,
        "error": error,
        "created_at": r.started_at,
        "updated_at": r.finished_at or r.started_at,
        "completed_at": (r.finished_at
                         if r.status in ("completed", "failed", "cancelled") else None),
    }


# ─────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────


@router.get("", summary="등록된 pipeline 카탈로그 (flows/ scan)")
async def get_pipeline_catalog() -> dict[str, Any]:
    pipelines = list_pipelines()
    entries = []
    by_category: dict[str, int] = {}
    for p in pipelines:
        cat = p.category or "uncategorized"
        by_category[cat] = by_category.get(cat, 0) + 1
        entries.append({
            "name": p.name,
            "visualization_id": p.visualization_id or "",
            "category": cat,
            "description": p.description,
            "owner": p.owner or "developer",
            "required_variables": declared_variables(p),
            "estimated_seconds": None,
        })
    entries.sort(key=lambda e: (e["category"], e["name"]))
    return {"total": len(entries), "by_category": by_category, "pipelines": entries}


@router.get("/category/{category}", summary="카테고리 전체 pipeline 산출 (페이지 표시용)")
async def get_category_results(
    category: str,
    client: str = Query(..., description="회사 식별자 (필수)"),
    period: str = Query("2026-04"),
) -> dict[str, Any]:
    """카테고리 pipeline 을 모두 실행(cache hit)해 visualization_id 별 산출 반환.

    페이지가 1회 호출 → 모든 시각화 데이터 수신. 5 v1 페이지 데이터 source.
    각 pipeline 의 required_variables 만 pool(client·period)에서 선택.
    """
    pool = {"client": client, "period": period}
    pipelines = [p for p in list_pipelines() if p.category == category]
    runner = PipelineRunner()

    results: dict[str, Any] = {}
    for p in pipelines:
        variables = {k: pool[k] for k in declared_variables(p) if k in pool}
        rec = await runner.run(p, variables)
        viz = p.visualization_id or p.name
        results[viz] = {
            "name": p.name,
            "status": rec.status,
            "output": rec.output,
            "error": rec.error,
        }

    return {"category": category, "client": client, "period": period, "results": results}


@router.post("/run/{name}", summary="pipeline 실행 트리거 (Trigger=button)")
async def run_pipeline(name: str, req: PipelineRunRequest) -> PipelineRunCreated:
    try:
        pipeline = load_pipeline(name)
    except FileNotFoundError:
        raise HTTPException(
            404, {"code": PIPELINE_NOT_FOUND, "message": f"pipeline '{name}' 부재"}
        )

    rec, is_duplicate = await get_run_store().start(pipeline, req.variables, req.trigger)
    if is_duplicate:
        raise HTTPException(409, {
            "code": PIPELINE_DUPLICATE_RUN,
            "message": f"'{name}' 동일 변수 실행 진행 중",
            "run_id": rec.run_id,
        })

    return PipelineRunCreated(
        run_id=rec.run_id,
        pipeline_name=name,
        status="pending",
        trigger=req.trigger,
        variables=req.variables,
        created_at=rec.started_at or "",
        poll_url=f"/api/admin/pipelines/runs/{rec.run_id}",
    )


@router.get("/runs", summary="최근 실행 이력")
async def list_runs(limit: int = Query(20, ge=1, le=200)) -> dict[str, Any]:
    runs = get_run_store().recent(limit)
    return {"total": len(runs), "runs": [_to_status_dict(r) for r in runs]}


@router.get("/runs/{run_id}", summary="실행 상태 조회 (polling)")
async def get_run(run_id: str) -> dict[str, Any]:
    rec = get_run_store().get(run_id)
    if rec is None:
        raise HTTPException(
            404, {"code": PIPELINE_RUN_NOT_FOUND, "message": f"run '{run_id}' 부재"}
        )
    return _to_status_dict(rec)
