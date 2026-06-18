"""Pipeline 영역 — Tool 조합 오케스트레이션 (ADR-023·027).

구성:
    models.py    — PipelineDef (YAML 계약) + RunResult
    loader.py    — flows/*.yaml → PipelineDef
    runner.py    — PipelineRunner (cache read-through + topo 실행 + 검증)
    validator.py — 산출 검증 (ADR-024 V4 정답 보존)
    flows/       — pipeline 정의 YAML (Maker 산출물)

진입점:
    from app.pipelines import PipelineRunner, load_pipeline, list_pipelines
"""
from __future__ import annotations

from app.pipelines.loader import FLOWS_DIR, list_pipelines, load_pipeline
from app.pipelines.models import PipelineDef, RunResult, StepResult
from app.pipelines.runner import PipelineRunner

__all__ = [
    "PipelineRunner",
    "load_pipeline",
    "list_pipelines",
    "FLOWS_DIR",
    "PipelineDef",
    "RunResult",
    "StepResult",
]
