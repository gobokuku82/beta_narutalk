"""Shared Enums — 활성 카탈로그

2026-05-15 정리 (models/ cleanup A5):
  - 제거: IntentDomain, IntentCategory, Layer, ExecutionStrategy,
          TodoStatus, PlanStatus, SessionStatus
    (관련 deprecated 클래스 — intent.py / plan.py / todo.py / approval.py — 와 함께 사라짐)
  - 유지: ToolCategory, ToolParameterType (활성 사용처 있음)

2026-06-11 추가 정리: HITLRequestType 제거 — Sprint 12 event 트랙
  (models/hitl.py HITLRequest/HITLResponse + hitl_manager 장부 메서드) 폐기와 동반.
  신경로(run_turn + signal_resume)는 dict 기반. 복원 필요 시 git 히스토리 참조.

활성 TodoStatus 는 `app.dream_agent.schemas.execution_result.TodoStatus` (5값) 를 사용.

Reference: docs/_claude/models_cleanup_plan_2026-05-15.md
"""

from enum import Enum


class ToolCategory(str, Enum):
    """도구 카테고리 (기능 단계 축).

    Status: complete — 데이터 단계축 8 + rendering(2026-06-09) + qa·decision(2026-06-10 비단계축) = 11.
    rendering = 렌더/출력 단계(pdf/excel/ppt 파일 생성). report 가 텍스트생성 단계인 것과 같은 층위.
    포맷별 분리는 team_catalog agent 축(pdf_agent/ppt_agent — excel_agent 는 2026-06-12 폐기). chart_generator 등
    공유 렌더 tool 포함 → 포맷별이 아닌 단일 rendering 카테고리.
    (폴더명 'output' 은 .gitignore 충돌 → 'rendering' 사용.)
    """
    COLLECTION = "collection"
    NORMALIZATION = "normalization"
    CLEANING = "cleaning"
    PREPROCESSING = "preprocessing"
    METRICS = "metrics"
    COMPARISON = "comparison"
    ANALYSIS = "analysis"
    REPORT = "report"
    RENDERING = "rendering"
    QA = "qa"             # 질의응답 — 데이터 파이프 아닌 지식·메타·대화 답변(2026-06-10). 위 9는 데이터 단계축,
                          # qa 는 결이 다른 카테고리(질의응답_설계서_260610.md §1). 단일 qa_responder.
    DECISION = "decision"  # 의사결정 — 데이터/분석 → 행동 제안(옵션→시뮬→추천→승인). 현: 단일 recommender
                           # (ml_model.generate_recommendation 재사용, 의사결정_설계서_260610.md). (2026-06-10)


class ToolParameterType(str, Enum):
    """도구 파라미터 타입. `ToolParameter.type` 의 타입."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
