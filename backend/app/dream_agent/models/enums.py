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
"""

from enum import Enum


class ToolCategory(str, Enum):
    """도구 카테고리 — ⚠ **폐쇄 집합 아님 (open-vocab, 2026-07-02)**.

    `ToolSpec.category` 는 검증된 자유 문자열이며 이 Enum 값 밖의 도메인 고유 어휘도 유효하다
    (registry 가 미지 카테고리를 raise 하지 않고 수용). 이 Enum 은 이제 (1) 하위호환 상수
    (ToolCategory.COLLECTION == "collection"), (2) 조직화/요약용 **문서화된 권장 관례**로만 남는다.
    관례 집합은 아래 `KNOWN_TOOL_CATEGORIES`.

    구 마케팅 파이프의 단계축 어휘 11값(권장 관례):
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
                          # qa 는 결이 다른 카테고리. 단일 qa_responder.
    DECISION = "decision"  # 의사결정 — 데이터/분석 → 행동 제안(옵션→시뮬→추천→승인). 현: 단일 recommender.
                           # (2026-06-10)


# open-vocab 관례 집합 (advisory) — registry/요약이 참조하나 폐쇄 검증엔 쓰지 않는다.
# 도메인은 이 밖의 자유 문자열 카테고리도 등록 가능(관례 밖 = registry debug 로그만).
KNOWN_TOOL_CATEGORIES: frozenset[str] = frozenset(c.value for c in ToolCategory)


class ToolParameterType(str, Enum):
    """도구 파라미터 타입. `ToolParameter.type` 의 타입."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
