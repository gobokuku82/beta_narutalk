"""Domain Models — 활성 공개 API 큐레이션

OctorAD 의 **내부 도메인 모델 + Tool I/O 공유 타입** 만 노출.
레이어 경계 DTO (Schema) 는 `app.dream_agent.schemas/` 참조.
레이어 산출물 모델 (Plan/PlannedTodo) 은 `app.dream_agent.planning.planner` 참조.

## 무엇이 어디 있나

| 영역 | 위치 |
|------|------|
| **레이어 산출물 DTO** (Schema) | `app.dream_agent.schemas/` — StructuredQuery / ExecutionResult / ResponsePayload |
| **Plan / PlannedTodo** | `app.dream_agent.planning.planner` (Planning 레이어가 소유) |
| **AgentState** (LangGraph 전역) | `app.dream_agent.states.agent_state` |
| **Tool 입력 컨텍스트** | `models/execution.py::ExecutionContext` (본 패키지) |
| **Tool 메타** | `models/tool.py` (`ToolSpec`/`ToolParameter`) |

## 정리 이력 (2026-05-15)

models/ cleanup A1~A6 으로 다음 deprecated 항목 제거:
  - `intent.py` (Intent, Entity) — Sprint 9 이전 의도 분류, StructuredQuery 로 통합됨
  - `plan.py` (Plan, PlanChange, PlanVersion) — ADR-010 으로 `planner.Plan` 단일화
  - `todo.py` (TodoItem, validate_transition) — `planner.PlannedTodo` 단일화
  - `enums.py` 의 IntentDomain/IntentCategory/Layer/ExecutionStrategy/TodoStatus(8값)/PlanStatus/SessionStatus
  - `execution.py::ExecutionResult` (단일 Tool wrapper) — `schemas/execution_result.py` 와 별 책임의 동명이인 해소

## 정리 이력 (2026-06-11~12, 정리 전환 Sprint)

  - `hitl.py` (HITLRequest/HITLResponse) + `HITLRequestType` — Sprint 12 event 트랙 잔재 (hitl_ack 거짓 신호 버그의 원인)
  - `domain.py` 11종 (Review/NormalizedReview/CleanedText/Sentiment*/Keyword*/Insight/ChannelPerformance/Creative/Importance)
    — 폐기된 blooming 체인(naver_collector→...)의 계약 대상. 소비처 0 재검증 후 삭제.
    현행 tool I/O 는 `app/schemas/outputs` 의 *Output 모델 사용 (동명이인 주의). 복원은 git 히스토리.

상세: `docs/_claude/models_cleanup_plan_2026-05-15.md` + `docs/agent_specs/30_DATA_MODELS_v1.1.md`
"""

from app.dream_agent.models.enums import (
    ToolCategory,
    ToolParameterType,
)
from app.dream_agent.models.execution import ExecutionContext
# (2026-06-11) hitl.py(HITLRequest/HITLResponse) + HITLRequestType 폐기 — Sprint 12
# event 트랙 잔재. 신경로 HITL 은 dict 기반(signal_resume). 복원은 git 히스토리.
from app.dream_agent.models.tool import StoragePolicy, ToolParameter, ToolSpec
from app.schemas.outputs.dashboard1 import (  # 이름 정리 2026-05-28: clumi_outputs → schemas/outputs (하위호환 재노출)
    # KPI 9
    RevenueOutput,
    AdCostOutput,
    RoasOutput,
    CacOutput,
    PromoRevenueOutput,
    PromoRoasOutput,
    NewMembersOutput,
    AovOutput,
    SignupConversionOutput,
    # MoM 4
    MomRevenueOutput,
    RepurchaseMomOutput,
    AovMomOutput,
    NewMembersMomOutput,
    # Segment 7
    GradeRevenueOutput,
    GradeTimeseriesOutput,
    AgeSegmentOutput,
    CategoryDistOutput,
    ChannelDistOutput,
    MemberGuestOutput,
    UnknownShareOutput,
)

__all__ = [
    # ── Enums ──
    "ToolCategory",
    "ToolParameterType",
    # ── Execution (Tool 컨텍스트) ──
    "ExecutionContext",
    # ── Tool 메타 ──
    "ToolSpec",
    "ToolParameter",
    "StoragePolicy",
    # ── C:LUMI Outputs — frontend typed contract (2026-05-26 신설) ──
    # KPI 9
    "RevenueOutput",
    "AdCostOutput",
    "RoasOutput",
    "CacOutput",
    "PromoRevenueOutput",
    "PromoRoasOutput",
    "NewMembersOutput",
    "AovOutput",
    "SignupConversionOutput",
    # MoM 4
    "MomRevenueOutput",
    "RepurchaseMomOutput",
    "AovMomOutput",
    "NewMembersMomOutput",
    # Segment 7
    "GradeRevenueOutput",
    "GradeTimeseriesOutput",
    "AgeSegmentOutput",
    "CategoryDistOutput",
    "ChannelDistOutput",
    "MemberGuestOutput",
    "UnknownShareOutput",
]
