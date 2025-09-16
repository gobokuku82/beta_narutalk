"""
Pydantic schemas for agent tool inputs and outputs
에이전트 도구의 입출력 검증을 위한 스키마 정의
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============= Base Schemas =============
class BaseTaskInput(BaseModel):
    """모든 에이전트 태스크의 기본 입력 스키마"""
    task_id: str = Field(description="고유 태스크 ID")
    task_description: str = Field(description="수행할 작업에 대한 상세 설명")
    context: Dict[str, Any] = Field(default_factory=dict, description="실행 컨텍스트 정보")
    priority: int = Field(default=1, description="작업 우선순위 (1-10)")
    timeout: Optional[int] = Field(default=60, description="타임아웃 설정 (초)")


class BaseTaskOutput(BaseModel):
    """모든 에이전트 태스크의 기본 출력 스키마"""
    task_id: str = Field(description="태스크 ID")
    status: Literal["success", "failed", "partial"] = Field(description="실행 상태")
    confidence_score: float = Field(description="결과 신뢰도 (0.0-1.0)")
    execution_time: float = Field(description="실행 소요 시간 (초)")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    error_message: Optional[str] = Field(default=None, description="에러 메시지")


# ============= Data Analysis Schemas =============
class DataAnalysisInput(BaseTaskInput):
    """데이터 분석 에이전트 입력 스키마"""
    query: str = Field(description="분석할 쿼리 또는 질문")
    data_source: Optional[str] = Field(default="main_db", description="데이터 소스 지정")
    analysis_type: Literal["sql", "statistical", "aggregation", "trend"] = Field(
        default="sql", description="분석 유형"
    )
    filters: Optional[Dict[str, Any]] = Field(default=None, description="필터 조건")
    limit: Optional[int] = Field(default=100, description="결과 제한")


class DataAnalysisOutput(BaseTaskOutput):
    """데이터 분석 에이전트 출력 스키마"""
    sql_query: Optional[str] = Field(default=None, description="생성된 SQL 쿼리")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="분석 결과")
    row_count: int = Field(default=0, description="결과 행 수")
    summary: Optional[str] = Field(default=None, description="결과 요약")
    visualizations: Optional[List[Dict]] = Field(default=None, description="시각화 데이터")


# ============= Information Retrieval Schemas =============
class InfoRetrievalInput(BaseTaskInput):
    """정보 검색 에이전트 입력 스키마"""
    search_query: str = Field(description="검색할 쿼리")
    search_type: Literal["vector", "keyword", "hybrid"] = Field(
        default="hybrid", description="검색 방식"
    )
    collections: Optional[List[str]] = Field(
        default=["hr_rules", "policies"], description="검색할 컬렉션"
    )
    top_k: int = Field(default=5, description="반환할 상위 결과 수")
    similarity_threshold: float = Field(default=0.7, description="유사도 임계값")
    metadata_filter: Optional[Dict] = Field(default=None, description="메타데이터 필터")


class InfoRetrievalOutput(BaseTaskOutput):
    """정보 검색 에이전트 출력 스키마"""
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="검색된 문서")
    total_found: int = Field(default=0, description="전체 검색 결과 수")
    relevance_scores: List[float] = Field(default_factory=list, description="관련성 점수")
    sources: List[str] = Field(default_factory=list, description="출처 정보")
    summary: Optional[str] = Field(default=None, description="검색 결과 요약")


# ============= Document Generation Schemas =============
class DocumentGenerationInput(BaseTaskInput):
    """문서 생성 에이전트 입력 스키마"""
    document_type: Literal["report", "summary", "email", "memo", "presentation"] = Field(
        description="생성할 문서 유형"
    )
    content_data: Dict[str, Any] = Field(description="문서에 포함할 데이터")
    template: Optional[str] = Field(default=None, description="사용할 템플릿")
    format: Literal["text", "markdown", "html", "pdf"] = Field(
        default="markdown", description="출력 형식"
    )
    language: str = Field(default="ko", description="문서 언어")
    style: Optional[str] = Field(default="professional", description="문서 스타일")


class DocumentGenerationOutput(BaseTaskOutput):
    """문서 생성 에이전트 출력 스키마"""
    document_content: str = Field(description="생성된 문서 내용")
    document_format: str = Field(description="문서 형식")
    word_count: int = Field(default=0, description="단어 수")
    sections: List[str] = Field(default_factory=list, description="문서 섹션 목록")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="문서 메타데이터")


# ============= Compliance Validation Schemas =============
class ComplianceInput(BaseTaskInput):
    """규정 검증 에이전트 입력 스키마"""
    validation_type: Literal["hr_policy", "legal", "regulatory", "internal"] = Field(
        description="검증 유형"
    )
    content_to_validate: str = Field(description="검증할 내용")
    rules_to_check: Optional[List[str]] = Field(default=None, description="확인할 규정 목록")
    strict_mode: bool = Field(default=True, description="엄격 모드 사용 여부")
    compliance_level: Literal["must", "should", "may"] = Field(
        default="must", description="준수 수준"
    )


class ComplianceOutput(BaseTaskOutput):
    """규정 검증 에이전트 출력 스키마"""
    is_compliant: bool = Field(description="규정 준수 여부")
    violations: List[Dict[str, Any]] = Field(default_factory=list, description="위반 사항")
    warnings: List[str] = Field(default_factory=list, description="경고 사항")
    recommendations: List[str] = Field(default_factory=list, description="권고 사항")
    compliance_score: float = Field(default=1.0, description="준수 점수 (0.0-1.0)")
    checked_rules: List[str] = Field(default_factory=list, description="확인된 규정 목록")


# ============= Storage Decision Schemas =============
class StorageInput(BaseTaskInput):
    """저장 결정 에이전트 입력 스키마"""
    data_to_store: Dict[str, Any] = Field(description="저장할 데이터")
    data_type: str = Field(description="데이터 유형")
    storage_requirements: Optional[Dict[str, Any]] = Field(
        default=None, description="저장 요구사항"
    )
    retention_period: Optional[int] = Field(default=365, description="보관 기간 (일)")
    encryption_required: bool = Field(default=False, description="암호화 필요 여부")
    backup_strategy: Literal["none", "daily", "weekly", "realtime"] = Field(
        default="daily", description="백업 전략"
    )


class StorageOutput(BaseTaskOutput):
    """저장 결정 에이전트 출력 스키마"""
    storage_location: str = Field(description="저장 위치")
    storage_method: str = Field(description="저장 방법")
    storage_id: Optional[str] = Field(default=None, description="저장된 데이터 ID")
    metadata_stored: Dict[str, Any] = Field(default_factory=dict, description="저장된 메타데이터")
    compression_used: bool = Field(default=False, description="압축 사용 여부")
    encryption_applied: bool = Field(default=False, description="암호화 적용 여부")


# ============= Aggregated Results Schema =============
class AggregatedResults(BaseModel):
    """여러 에이전트 실행 결과를 집계한 스키마"""
    session_id: str = Field(description="세션 ID")
    total_tasks: int = Field(description="전체 태스크 수")
    completed_tasks: int = Field(description="완료된 태스크 수")
    failed_tasks: int = Field(description="실패한 태스크 수")
    total_execution_time: float = Field(description="전체 실행 시간")
    average_confidence: float = Field(description="평균 신뢰도")
    results_by_agent: Dict[str, Any] = Field(description="에이전트별 결과")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())