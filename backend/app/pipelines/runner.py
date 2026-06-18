"""Pipeline Runner — YAML pipeline 정의를 해석·실행.

ADR-027 권한: Pipeline = Tool 조합 + step 순서 + cache_key (계산·fetch 금지).
Runner 는 Tool 을 *호출* 만 한다. 데이터 fetch 는 Tool→DataSource, 계산은 Tool 내부.

실행 흐름:
    1. cache read-through  — cache.key_template 해석 → workspace.exists 시 즉시 load
    2. step 실행           — depends_on topo 정렬 → Tool.execute (previous_results 주입)
    3. 산출 검증            — validator.validate_output (ADR-024 V4)

cache 쓰기: POC 기존 Tool 은 self-save (revenue_total 등) → Runner 는 read-through 만.
            self-save 안 하는 Tool 대비 fallback save (sanitized) 포함.

Status: complete — Phase 1 M1 (2026-05-28) walking skeleton (Batch 1).
"""
from __future__ import annotations

import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.registry import ToolRegistry, get_registry
from app.pipelines.models import (
    PipelineDef,
    RunResult,
    StepDef,
    StepResult,
)
from app.pipelines.validator import validate_output
from app.workspace import WorkspaceBackend, get_default_workspace

logger = get_logger(__name__)

_VAR_RE = re.compile(r"\$\{(\w+)\}")


# ─────────────────────────────────────────────────────────────────
# helpers — 변수 치환 / topo 정렬 / 직렬화 안전
# ─────────────────────────────────────────────────────────────────


def substitute(value: Any, variables: dict[str, Any]) -> Any:
    """`${var}` 치환. 단일 `${var}` 는 원본 타입 보존, 임베디드는 문자열 치환."""
    if isinstance(value, str):
        whole = _VAR_RE.fullmatch(value.strip())
        if whole:
            return variables.get(whole.group(1), value)
        return _VAR_RE.sub(
            lambda m: str(variables.get(m.group(1), m.group(0))), value
        )
    if isinstance(value, dict):
        return {k: substitute(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute(v, variables) for v in value]
    return value


def topo_order(steps: list[StepDef]) -> list[StepDef]:
    """depends_on 위상 정렬 (Kahn). 선언 순서 안정 유지. 사이클·미존재 의존 시 ValueError."""
    by_id = {s.id: s for s in steps}
    if len(by_id) != len(steps):
        raise ValueError("duplicate step id")
    indeg = {s.id: 0 for s in steps}
    adj: dict[str, list[str]] = {s.id: [] for s in steps}
    for s in steps:
        for dep in s.depends_on:
            if dep not in by_id:
                raise ValueError(f"step '{s.id}' depends_on unknown step '{dep}'")
            adj[dep].append(s.id)
            indeg[s.id] += 1
    queue = [s.id for s in steps if indeg[s.id] == 0]  # 선언 순서 보존
    out: list[StepDef] = []
    while queue:
        nid = queue.pop(0)
        out.append(by_id[nid])
        for m in adj[nid]:
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    if len(out) != len(steps):
        raise ValueError("cycle detected in steps.depends_on")
    return out


def json_safe(obj: Any) -> Any:
    """직렬화 안전 변환 — DataFrame 등 비직렬 값은 제거 (collector 산출 방어)."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    return None  # DataFrame·set 등 — output 에서 제외


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────


class PipelineRunner:
    """pipeline 정의 1개를 실행. registry / workspace DI (테스트 override)."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        workspace: Optional[WorkspaceBackend] = None,
    ):
        self.registry = registry or get_registry()
        self.workspace = workspace or get_default_workspace()

    async def run(
        self,
        pipeline: PipelineDef,
        variables: dict[str, Any],
        *,
        run_id: Optional[str] = None,
        force: bool = False,
        result: Optional[RunResult] = None,
    ) -> RunResult:
        """pipeline 실행. force=True 면 cache 무시 재계산.

        result: RunStore 가 만든 기존 record (in-place 갱신 → 라이브 polling).
                None 이면 새로 생성 (단독 호출·테스트).
        """
        t0 = time.perf_counter()
        if result is None:
            run_id = run_id or uuid.uuid4().hex
            result = RunResult(
                run_id=run_id,
                pipeline=pipeline.name,
                status="running",
                variables=variables,
                started_at=_now_iso(),
            )
        else:
            result.status = "running"
            result.started_at = result.started_at or _now_iso()
        result.total_steps = len(pipeline.steps)
        run_id = result.run_id
        client = variables.get("client")  # ①.6: client 필수 (진입점이 보장)
        if not client:
            raise ValueError("pipeline 실행에 client 필요 — variables['client'] 누락")

        # 1. cache read-through
        cache_key: Optional[str] = None
        layer = "computed"
        if pipeline.cache and pipeline.cache.key_template:
            cache_key = substitute(pipeline.cache.key_template, variables)
            layer = pipeline.cache.layer
            result.cache_key = cache_key
            result.cache_layer = layer
            if not force:
                try:
                    if self.workspace.exists(layer, cache_key, client=client):
                        loaded = self.workspace.load(layer, cache_key, client=client)
                        result.cache_hit = True
                        result.output = json_safe(loaded)
                        logger.info("pipeline cache hit", pipeline=pipeline.name,
                                    layer=layer, key=cache_key)
                        return self._finalize(result, pipeline, t0)
                except Exception as e:  # noqa: BLE001 — cache 손상 시 재계산
                    logger.warning("pipeline cache read failed → recompute",
                                   pipeline=pipeline.name, key=cache_key, error=str(e))

        # 2. step 실행
        try:
            ordered = topo_order(pipeline.steps)
        except ValueError as e:
            result.status = "failed"
            result.error = f"step graph invalid: {e}"
            result.error_code = "PIPELINE_GRAPH_INVALID"
            result.error_layer = "runner"
            return self._finalize(result, pipeline, t0)

        ctx = ExecutionContext(
            session_id=run_id,
            plan_id=pipeline.name,
            client_id=client,
        )
        step_outputs: dict[str, Any] = {}
        final_step_id: Optional[str] = ordered[-1].id if ordered else None

        for step in ordered:
            sr = StepResult(id=step.id, tool=step.tool, status="running",
                            started_at=_now_iso())
            s0 = time.perf_counter()
            try:
                tool_cls = self.registry.import_tool(step.tool)
                spec = self.registry.get(step.tool)
                tool = tool_cls(spec)
                resolved_inputs = substitute(step.inputs, variables)
                # ⑷ (2026-06-01) Param 사전 검증 — silent failure 차단 (Step 1 디버깅)
                valid, errs = tool.validate_params(resolved_inputs)
                if not valid:
                    raise ValueError(f"param validation failed: {'; '.join(errs)}")
                ctx.previous_results = step_outputs  # 이전 step 산출 주입
                out = await tool.execute(resolved_inputs, ctx)
                step_outputs[step.id] = out
                sr.status = "completed"
            except Exception as e:  # noqa: BLE001
                sr.status = "failed"
                sr.error = str(e)
                sr.finished_at = _now_iso()
                sr.duration_ms = (time.perf_counter() - s0) * 1000
                result.steps.append(sr)
                result.status = "failed"
                result.error = f"step '{step.id}' ({step.tool}) failed: {e}"
                result.failed_step = step.id
                # raw 부재 → data_source layer (63 §2.3.3.6 PIPELINE_DATA_SOURCE_MISSING)
                if isinstance(e, FileNotFoundError):
                    result.error_code = "PIPELINE_DATA_SOURCE_MISSING"
                    result.error_layer = "data_source"
                else:
                    result.error_code = "PIPELINE_STEP_FAILED"
                    result.error_layer = "tool"
                logger.error("pipeline step failed", pipeline=pipeline.name,
                             step=step.id, tool=step.tool, error=str(e))
                return self._finalize(result, pipeline, t0)
            sr.finished_at = _now_iso()
            sr.duration_ms = (time.perf_counter() - s0) * 1000
            result.steps.append(sr)

        # 3. 최종 산출 = topo 마지막 step (계산 step) 의 산출
        final_raw = step_outputs.get(final_step_id, {}) if final_step_id else {}
        result.output = json_safe(final_raw) or {}

        # fallback cache save — self-save 안 한 Tool 대비 (기존 Tool 은 이미 저장됨)
        if cache_key and not self.workspace.exists(layer, cache_key, client=client):
            try:
                clean = {k: v for k, v in result.output.items() if not k.startswith("_")}
                meta = result.output.get("_meta") or {"pipeline": pipeline.name, "run_id": run_id}
                self.workspace.save(layer, cache_key, clean, meta=meta, client=client)
            except Exception as e:  # noqa: BLE001
                logger.warning("pipeline fallback save failed", key=cache_key, error=str(e))

        # 4. 검증 (ADR-024 V4)
        result.status = "validating"
        result.validation = validate_output(pipeline, result.output)
        return self._finalize(result, pipeline, t0)

    def _finalize(self, result: RunResult, pipeline: PipelineDef, t0: float) -> RunResult:
        """status 확정 + 타이밍. validator fail_policy=block 시 failed."""
        if result.status not in ("failed", "cancelled"):
            v = result.validation
            if v and not v.get("ok", True) and v.get("fail_policy") == "block":
                result.status = "failed"
                result.error = "validation failed (fail_policy=block)"
                result.error_code = "PIPELINE_VALIDATOR_FAILED"
                result.error_layer = "validator"
            else:
                result.status = "completed"
        result.finished_at = _now_iso()
        result.duration_ms = (time.perf_counter() - t0) * 1000
        return result


__all__ = ["PipelineRunner", "substitute", "topo_order", "json_safe"]
