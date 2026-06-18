"""Pipeline 에러 코드 — 63 §2.3.3.6 (6 신규 코드).

frontend errorMessages.ts 와 1:1. DC-FE-1 검증 대상.
layer = runner | tool | validator | data_source (63 PipelineRunStatus.error.layer).
"""
from __future__ import annotations

# 63 §2.3.3.6 — Pipeline 6 에러 코드
PIPELINE_NOT_FOUND = "PIPELINE_NOT_FOUND"  # runner — name YAML 부재
PIPELINE_RUN_NOT_FOUND = "PIPELINE_RUN_NOT_FOUND"  # runner — run_id 무효
PIPELINE_STEP_FAILED = "PIPELINE_STEP_FAILED"  # tool — step.execute 예외
PIPELINE_VALIDATOR_FAILED = "PIPELINE_VALIDATOR_FAILED"  # validator — 검산 불일치
PIPELINE_DUPLICATE_RUN = "PIPELINE_DUPLICATE_RUN"  # runner — 동일 (name, vars) 진행 중
PIPELINE_DATA_SOURCE_MISSING = "PIPELINE_DATA_SOURCE_MISSING"  # data_source — raw 부재

# 부가 (graph 검증 — spec 6 외 내부용)
PIPELINE_GRAPH_INVALID = "PIPELINE_GRAPH_INVALID"  # runner — depends_on 사이클·미존재

ALL_CODES = [
    PIPELINE_NOT_FOUND,
    PIPELINE_RUN_NOT_FOUND,
    PIPELINE_STEP_FAILED,
    PIPELINE_VALIDATOR_FAILED,
    PIPELINE_DUPLICATE_RUN,
    PIPELINE_DATA_SOURCE_MISSING,
    PIPELINE_GRAPH_INVALID,
]

__all__ = ["ALL_CODES", *ALL_CODES]
