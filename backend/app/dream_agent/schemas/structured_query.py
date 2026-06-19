"""StructuredQuery — Cognitive 레이어 산출물

4-Layer 아키텍처의 핵심 계약:
  user_input (자연어) → [Cognitive] → StructuredQuery → [Planning] → Todo[]

Reference: docs/_claude/4layer_system/system_architecture.md
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ────────────────────────────────────────────────────────────────
# Enums
# ────────────────────────────────────────────────────────────────

class TaskType(str, Enum):
    """프레임 기본 작업 어휘 (open-vocab 기본값).

    프레임 추출(2026-06-19): 마케팅 전용 작업 제거 → 도메인 무관 generic 세트.
    `Task.id` 는 이제 **자유 문자열(str)** — 도메인은 이 enum 밖의 어휘도 자유롭게 사용한다.
    이 상수들은 intent_shim/planner 의 프레임 기본 라우팅 + 호환을 위한 reference 일 뿐.
    """

    # 데이터
    DATA_COLLECTION    = "data_collection"
    DATA_PREPROCESSING = "data_preprocessing"

    # 처리 (generic)
    METRIC_CALCULATION = "metric_calculation"
    ANALYSIS           = "analysis"
    COMPARISON         = "comparison"

    # 산출물
    INSIGHT_GENERATION = "insight_generation"
    SUMMARY_GENERATION = "summary_generation"
    REPORT_GENERATION  = "report_generation"

    # 의사결정
    RECOMMENDATION     = "recommendation"

    # 조회형 (Tool 불필요 — Response 직답)
    FACTUAL_LOOKUP     = "factual_lookup"


class GoalType(str, Enum):
    """응답의 최종 형태"""
    ANSWER   = "answer"      # 짧은 답변 (brief)
    METRIC   = "metric"      # 숫자/비율 조회
    INSIGHT  = "insight"     # 통찰/권고
    REPORT   = "report"      # 상세 보고서
    CREATIVE = "creative"    # 이미지/영상/카피
    MIXED    = "mixed"       # 여러 형태 복합


class OutputFormat(str, Enum):
    """출력 매체"""
    TEXT  = "text"
    PDF   = "pdf"
    PPT   = "ppt"           # 2026-06-09: 슬라이드(pptx_generator). enum 누락이 'ppt→pdf' 오매핑 원인이었음.
    EXCEL = "excel"         # 표 — 렌더러 폐기(2026-06-12, excel_template_filler stub 제거). 언어로는 유지(인식→정직 미지원 응답). planning 프롬프트 정합.
    IMAGE = "image"
    CHART = "chart"
    VIDEO = "video"
    MIXED = "mixed"


class Depth(str, Enum):
    """요청 깊이 — Planning이 Tool 체인 길이 결정에 사용"""
    BRIEF    = "brief"       # 최소 Tool (예: "감성 어때?")
    STANDARD = "standard"    # 기본 체인
    DETAILED = "detailed"    # 풀 체인 + 보고서


# Source 는 open-vocab 자유 문자열(str) — 도메인별 소스 id 를 SOURCE_REGISTRY 가 정의.
# 특수값: "unknown"(불명) · "multi"(복수 종합). (프레임 추출 2026-06-19: 마케팅 Source enum 제거)


# ────────────────────────────────────────────────────────────────
# Sub-structures
# ────────────────────────────────────────────────────────────────

class Period(BaseModel):
    """시간 범위"""
    raw: str                          # 원문 ("지난 3개월", "7일")
    start: Optional[str] = None       # ISO date
    end: Optional[str] = None         # ISO date
    window: Optional[str] = None      # 정규화: "3months", "7days"
    resolved: Optional[str] = None    # PMAL: 절대화 "2026-04" (B1=필드만, 절대화 강제는 B2)


class Targets(BaseModel):
    """대상 — '무엇에 대해'"""
    brand: Optional[str] = None
    product: Optional[str] = None
    competitors: list[str] = Field(default_factory=list)
    source: str = "unknown"            # open-vocab 소스 id (SOURCE_REGISTRY) | "unknown" | "multi"
    period: Optional[Period] = None
    keywords: list[str] = Field(default_factory=list)
    extra_filters: dict = Field(default_factory=dict)


class Goal(BaseModel):
    """목적 — '왜 / 어떤 결과'"""
    type: GoalType
    output_format: OutputFormat
    depth: Depth = Depth.STANDARD
    audience: Optional[str] = None    # "마케팅 팀장" 등 (선택)


class Task(BaseModel):
    """sub-intent (작업 단위) — id 는 open-vocab 자유 문자열(TaskType 기본값 또는 도메인 어휘)"""
    id: str
    priority: int = 1                 # 1=최우선
    params_override: dict = Field(default_factory=dict)


class Ambiguity(BaseModel):
    """모호성 판정"""
    is_ambiguous: bool = False
    severity: str = "none"            # none | low | medium | high
    reasons: list[str] = Field(default_factory=list)
    clarification_question: Optional[str] = None


class QueryMeta(BaseModel):
    """검증/추적 메타데이터"""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    ambiguity: Ambiguity = Field(default_factory=Ambiguity)
    missing: list[str] = Field(default_factory=list)   # 비어있는 필수 필드
    raw_input: str = ""
    cleaned: str = ""                                  # 에이전트가 이해한 "사용자가 원하는 것"
                                                       # 평어 재진술 (3겹: raw_input=원본 / cleaned=정제·재평가 /
                                                       # intent=구조화 언어). 관측·진단·학습용 — intent 가 실행 canonical.
                                                       # (2026-06-06, cleaned 추가: H5 원문안전망 + 100쿼리 진단)
    language: str = "ko"
    original_domain: Optional[str] = None              # legacy 호환 (analysis/content/...)


class SubIntent(BaseModel):
    """복합쿼리의 개별 의도 한 줄 — 다의도 씨앗 (S1, append-only 2026-06-09).

    `operation` 스칼라 천장(한 쿼리=한 HOW)을 *구조적으로* 푸는 칸. 복합("4월 매출 진단하고
    채널별 ROAS 비교") 쿼리에서 cognitive 가 각 의도를 한 개씩 채운다. Intent 의 분석 4칸과 동형.

    Status: planned — cognitive emit=지금(씨앗 심기) / planning 소비=MVP. 현 planning 은 미소비라
      현 동작 무영향(append-only). 의존·직렬/병렬(steps DAG)은 다음 성장링(S2) — 여기 미포함.
    """
    operation: str = "measure"
    domain: list[str] = Field(default_factory=list)
    metric: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)


class Intent(BaseModel):
    """PMAL 의도 — 쪽지의 핵심: '무엇을(WHAT) 어떻게(HOW)'.

    cognitive 가 채우는 PMAL 1급 칸 (spec 37 §2 / criteria_map §2 ①).
    - operation:  HOW. authored(파생 X) — 미언급 시 measure. (measure/breakdown/rank/compare/trend/diagnose/forecast/attribute)
    - domain:     WHAT 영역. SET(스칼라 X — ROAS=revenue∩ad_performance 다중 대응). 주제(매출/리뷰)를 *결정적으로* 담는 칸 = F2 anchor.
    - metric:     WHAT 지표. OPEN vocab (닫힌 enum X — 카탈로그 결합 회피).
    - dimensions: 분해 축 (channel/creative/member_grade...). tool 선택을 가르는 진짜 disambiguator.
    - sub_intents: 다의도 씨앗(S1, 2026-06-09). 복합(의도 2개+)일 때만 각 의도를 나열. 단일이면 [].
        operation 은 *대표 1개* 유지(back-compat) → 현 planning/shim 무영향. MVP 에 planning 이 소비.

    Status: partial — W1(2026-06-04): 칸 정의만. cognitive emit=W3, planning 소비=W4. 유효성 강제(검증)=B2.
    """
    operation: str = "measure"
    domain: list[str] = Field(default_factory=list)
    metric: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    sub_intents: list[SubIntent] = Field(default_factory=list)


# 인과·예측·기여 operation — 매핑할 tool 부재 → degrade (tasks 비움 + 정직 응답).
# cognitive(intent_shim)·response(responder) 공유 상수라 중립 계약 위치(schemas)에 둠
# (2026-06-05, spec 16 §4 V5: stage↔stage 옆결합 해소 — 둘 다 여기서 import).
DEGRADE_OPS = {"diagnose", "forecast", "attribute"}

# 시간 스코프 param — 값은 반드시 쿼리(사용자 기간)에서 와야 한다 (헌법 19 D3·R2, 슬라이스 1).
# 상류 tool 산출 데이터로 주입 금지(executor._inject_prev_outputs) + 상류 artifact 로 충족
# 간주 금지(planner.detect_plan_gaps) + 경계 형식검사 YYYY-MM(executor) 가 모두 이 집합을 본다.
# planning·execution·response 공유 계약이라 중립 위치(schemas)에 둠 — D1 진실소스 코드 1곳.
SCOPE_PARAMS = frozenset({"period", "period_a", "period_b"})


# ────────────────────────────────────────────────────────────────
# Root
# ────────────────────────────────────────────────────────────────

class StructuredQuery(BaseModel):
    """Cognitive 레이어 산출물 — 시스템의 핵심 계약

    Planning은 이 객체만 받으면 Tool 매핑을 할 수 있어야 한다.
    """
    model_config = ConfigDict(frozen=False)  # 멀티턴 상속 시 복사·수정 위해 mutable

    targets: Targets
    goal: Goal
    tasks: list[Task] = Field(default_factory=list)
    meta: QueryMeta
    intent: Optional[Intent] = None   # PMAL 의도 (W1 신설). B1 = tasks 와 병존 (intent=canonical, tasks=shim 파생). B2 에 tasks 제거.
