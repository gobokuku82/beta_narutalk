"""Pipeline Run Store — in-memory 실행 기록 + 비동기 실행 + 중복 방지 Lock.

63 §2.3.3.7 동시성: 같은 (pipeline_name, frozenset(variables)) 진행 중이면 중복 거부.
POC = in-memory. MVP+ = Redis / DB row lock.

흐름:
    start()  → RunResult(pending) 생성 + inflight lock + asyncio.create_task(_run)
    _run()   → PipelineRunner.run(result=rec) — rec in-place 갱신 (라이브 polling)
    get()    → run_id 조회 (polling)

Status: complete — Phase 1 M1b (2026-05-28).
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.logging import get_logger
from app.pipelines.models import PipelineDef, RunResult
from app.pipelines.runner import PipelineRunner

logger = get_logger(__name__)

_ACTIVE = ("pending", "running", "validating")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunStore:
    """실행 기록 보관 + 중복 실행 방지."""

    def __init__(self, max_history: int = 200):
        self._runs: dict[str, RunResult] = {}
        self._inflight: dict[tuple, str] = {}
        self._order: list[str] = []
        self._max = max_history
        self._lock = asyncio.Lock()

    @staticmethod
    def _key(name: str, variables: dict) -> tuple:
        return (name, frozenset((k, str(v)) for k, v in variables.items()))

    async def start(
        self,
        pipeline: PipelineDef,
        variables: dict,
        trigger: str = "manual",
    ) -> tuple[RunResult, bool]:
        """실행 시작. 반환 = (record, is_duplicate). 중복이면 진행 중 record 반환."""
        key = self._key(pipeline.name, variables)
        async with self._lock:
            existing_id = self._inflight.get(key)
            if existing_id:
                rec = self._runs.get(existing_id)
                if rec and rec.status in _ACTIVE:
                    logger.info("pipeline duplicate run", pipeline=pipeline.name,
                                run_id=existing_id)
                    return rec, True
            run_id = uuid.uuid4().hex
            rec = RunResult(
                run_id=run_id,
                pipeline=pipeline.name,
                status="pending",
                variables=variables,
                trigger=trigger,
                total_steps=len(pipeline.steps),
                started_at=_now_iso(),
            )
            self._runs[run_id] = rec
            self._order.append(run_id)
            self._inflight[key] = run_id
            self._evict()

        asyncio.create_task(self._run(pipeline, variables, rec, key))
        return rec, False

    async def _run(self, pipeline: PipelineDef, variables: dict,
                   rec: RunResult, key: tuple) -> None:
        runner = PipelineRunner()
        try:
            await runner.run(pipeline, variables, result=rec)
        except Exception as e:  # noqa: BLE001 — 방어 (runner 내부서 대부분 처리)
            rec.status = "failed"
            rec.error = str(e)
            rec.error_layer = "runner"
            rec.finished_at = _now_iso()
            logger.error("pipeline run crashed", pipeline=pipeline.name, error=str(e))
        finally:
            async with self._lock:
                if self._inflight.get(key) == rec.run_id:
                    del self._inflight[key]

    def get(self, run_id: str) -> Optional[RunResult]:
        return self._runs.get(run_id)

    def recent(self, limit: int = 20) -> list[RunResult]:
        ids = self._order[-limit:] if limit else self._order
        return [self._runs[i] for i in reversed(ids) if i in self._runs]

    def _evict(self) -> None:
        while len(self._order) > self._max:
            old = self._order.pop(0)
            self._runs.pop(old, None)


_store: Optional[RunStore] = None


def get_run_store() -> RunStore:
    global _store
    if _store is None:
        _store = RunStore()
    return _store


def reset_run_store() -> None:
    """테스트용."""
    global _store
    _store = None


__all__ = ["RunStore", "get_run_store", "reset_run_store"]
