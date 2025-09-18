"""
Standardized Exception Handling for NaruTalk Backend
표준화된 에러 처리 시스템 (LangGraph 0.6.x 최적화)
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback
import logging

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """
    에러 코드 정의
    - 체계적인 에러 분류
    - 디버깅 용이성
    """

    # Database Errors (DB_xxx)
    DATABASE_CONNECTION = "DB_001"
    DATABASE_QUERY = "DB_002"
    DATABASE_TIMEOUT = "DB_003"
    DATABASE_INTEGRITY = "DB_004"
    DATABASE_PERMISSION = "DB_005"

    # Agent Errors (AG_xxx)
    AGENT_INITIALIZATION = "AG_001"
    AGENT_EXECUTION = "AG_002"
    AGENT_TIMEOUT = "AG_003"
    AGENT_COMMUNICATION = "AG_004"
    AGENT_STATE = "AG_005"

    # Validation Errors (VAL_xxx)
    VALIDATION_INPUT = "VAL_001"
    VALIDATION_OUTPUT = "VAL_002"
    VALIDATION_SCHEMA = "VAL_003"
    VALIDATION_CONSTRAINT = "VAL_004"
    VALIDATION_FORMAT = "VAL_005"

    # Cache Errors (CACHE_xxx)
    CACHE_CONNECTION = "CACHE_001"
    CACHE_MISS = "CACHE_002"
    CACHE_EXPIRED = "CACHE_003"
    CACHE_OVERFLOW = "CACHE_004"
    CACHE_CORRUPTION = "CACHE_005"

    # Network Errors (NET_xxx)
    NETWORK_TIMEOUT = "NET_001"
    NETWORK_CONNECTION = "NET_002"
    NETWORK_DNS = "NET_003"
    NETWORK_SSL = "NET_004"
    NETWORK_PROXY = "NET_005"

    # LangGraph Specific (LG_xxx)
    LANGGRAPH_STATE = "LG_001"
    LANGGRAPH_CHECKPOINT = "LG_002"
    LANGGRAPH_WORKFLOW = "LG_003"
    LANGGRAPH_TOOL = "LG_004"
    LANGGRAPH_MESSAGE = "LG_005"

    # Business Logic Errors (BIZ_xxx)
    BUSINESS_RULE = "BIZ_001"
    BUSINESS_PERMISSION = "BIZ_002"
    BUSINESS_WORKFLOW = "BIZ_003"
    BUSINESS_DATA = "BIZ_004"
    BUSINESS_CONSTRAINT = "BIZ_005"

    # System Errors (SYS_xxx)
    SYSTEM_MEMORY = "SYS_001"
    SYSTEM_DISK = "SYS_002"
    SYSTEM_CPU = "SYS_003"
    SYSTEM_CONFIGURATION = "SYS_004"
    SYSTEM_UNKNOWN = "SYS_999"


class ErrorSeverity(str, Enum):
    """에러 심각도"""
    CRITICAL = "critical"  # 시스템 중단 필요
    ERROR = "error"        # 작업 실패
    WARNING = "warning"    # 경고 (작업 계속 가능)
    INFO = "info"          # 정보성


class APIException(Exception):
    """
    표준 API 예외 클래스
    - 구조화된 에러 정보
    - 추적 가능한 컨텍스트
    """

    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        detail: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        retry_able: bool = False,
        retry_after: Optional[int] = None
    ):
        """
        Initialize APIException

        Args:
            status_code: HTTP 상태 코드
            error_code: 에러 코드 (ErrorCode enum)
            message: 사용자 친화적 메시지
            detail: 상세 기술적 설명
            context: 추가 컨텍스트 정보
            severity: 에러 심각도
            retry_able: 재시도 가능 여부
            retry_after: 재시도 대기 시간 (초)
        """
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.detail = detail or message
        self.context = context or {}
        self.severity = severity
        self.retry_able = retry_able
        self.retry_after = retry_after
        self.timestamp = datetime.now().isoformat()
        self.traceback = traceback.format_exc() if detail is None else None

        super().__init__(self.message)

        # 로깅
        self._log_error()

    def _log_error(self):
        """에러 로깅"""
        log_data = {
            "error_code": self.error_code,
            "message": self.message,
            "detail": self.detail,
            "context": self.context,
            "severity": self.severity,
            "timestamp": self.timestamp
        }

        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical Error: {log_data}")
        elif self.severity == ErrorSeverity.ERROR:
            logger.error(f"Error: {log_data}")
        elif self.severity == ErrorSeverity.WARNING:
            logger.warning(f"Warning: {log_data}")
        else:
            logger.info(f"Info: {log_data}")

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "detail": self.detail,
                "severity": self.severity,
                "timestamp": self.timestamp,
                "retry": {
                    "able": self.retry_able,
                    "after": self.retry_after
                } if self.retry_able else None,
                "context": self.context,
                "traceback": self.traceback if self.traceback and logger.level <= logging.DEBUG else None
            },
            "status_code": self.status_code
        }

    def to_response(self) -> Dict[str, Any]:
        """API 응답용 딕셔너리"""
        return {
            "status": "error",
            "error_code": self.error_code,
            "message": self.message,
            "detail": self.detail if logger.level <= logging.DEBUG else None,
            "timestamp": self.timestamp,
            "retry_after": self.retry_after
        }


class ValidationError(APIException):
    """입력 검증 에러"""

    def __init__(
        self,
        field: str,
        message: str,
        value: Any = None,
        constraints: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=400,
            error_code=ErrorCode.VALIDATION_INPUT,
            message=f"Validation failed for field '{field}': {message}",
            context={
                "field": field,
                "value": str(value)[:100] if value else None,
                "constraints": constraints
            },
            severity=ErrorSeverity.WARNING,
            retry_able=False
        )


class DatabaseError(APIException):
    """데이터베이스 에러"""

    def __init__(
        self,
        operation: str,
        message: str,
        query: Optional[str] = None,
        database: Optional[str] = None
    ):
        super().__init__(
            status_code=500,
            error_code=ErrorCode.DATABASE_QUERY,
            message=f"Database operation '{operation}' failed: {message}",
            context={
                "operation": operation,
                "database": database,
                "query": query[:500] if query else None
            },
            severity=ErrorSeverity.ERROR,
            retry_able=True,
            retry_after=5
        )


class AgentError(APIException):
    """에이전트 실행 에러"""

    def __init__(
        self,
        agent_name: str,
        message: str,
        phase: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=500,
            error_code=ErrorCode.AGENT_EXECUTION,
            message=f"Agent '{agent_name}' failed: {message}",
            context={
                "agent": agent_name,
                "phase": phase,
                "state": state
            },
            severity=ErrorSeverity.ERROR,
            retry_able=True,
            retry_after=10
        )


class LangGraphError(APIException):
    """LangGraph 관련 에러"""

    def __init__(
        self,
        component: str,
        message: str,
        thread_id: Optional[str] = None,
        checkpoint_id: Optional[str] = None
    ):
        super().__init__(
            status_code=500,
            error_code=ErrorCode.LANGGRAPH_WORKFLOW,
            message=f"LangGraph {component} error: {message}",
            context={
                "component": component,
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id
            },
            severity=ErrorSeverity.ERROR,
            retry_able=True,
            retry_after=5
        )


class TimeoutError(APIException):
    """타임아웃 에러"""

    def __init__(
        self,
        operation: str,
        timeout: int,
        message: Optional[str] = None
    ):
        super().__init__(
            status_code=408,
            error_code=ErrorCode.NETWORK_TIMEOUT,
            message=message or f"Operation '{operation}' timed out after {timeout} seconds",
            context={
                "operation": operation,
                "timeout": timeout
            },
            severity=ErrorSeverity.WARNING,
            retry_able=True,
            retry_after=min(timeout * 2, 60)
        )


class ErrorHandler:
    """
    전역 에러 핸들러
    - 에러 수집 및 분석
    - 재시도 로직
    - 에러 복구
    """

    def __init__(self):
        self.error_history: List[APIException] = []
        self.error_counts: Dict[str, int] = {}
        self.max_history = 1000

    def handle_error(self, error: Exception) -> APIException:
        """
        일반 예외를 APIException으로 변환

        Args:
            error: 원본 예외

        Returns:
            APIException 인스턴스
        """
        if isinstance(error, APIException):
            api_error = error
        else:
            # 일반 예외를 APIException으로 변환
            api_error = APIException(
                status_code=500,
                error_code=ErrorCode.SYSTEM_UNKNOWN,
                message="An unexpected error occurred",
                detail=str(error),
                severity=ErrorSeverity.ERROR,
                retry_able=False
            )

        # 에러 기록
        self.record_error(api_error)

        return api_error

    def record_error(self, error: APIException):
        """에러 기록"""
        # 히스토리에 추가
        self.error_history.append(error)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

        # 카운트 업데이트
        error_key = f"{error.error_code}_{error.status_code}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

    def get_error_stats(self) -> Dict[str, Any]:
        """에러 통계 반환"""
        recent_errors = self.error_history[-10:] if self.error_history else []

        return {
            "total_errors": len(self.error_history),
            "error_counts": self.error_counts,
            "recent_errors": [
                {
                    "code": e.error_code,
                    "message": e.message,
                    "timestamp": e.timestamp
                }
                for e in recent_errors
            ],
            "most_common": (
                max(self.error_counts.items(), key=lambda x: x[1])
                if self.error_counts else None
            )
        }

    async def with_retry(
        self,
        func,
        max_retries: int = 3,
        retry_delay: int = 1,
        exponential_backoff: bool = True
    ):
        """
        재시도 로직과 함께 함수 실행

        Args:
            func: 실행할 비동기 함수
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 지연 (초)
            exponential_backoff: 지수 백오프 사용 여부

        Returns:
            함수 실행 결과
        """
        import asyncio

        last_error = None
        delay = retry_delay

        for attempt in range(max_retries + 1):
            try:
                return await func()
            except Exception as e:
                last_error = self.handle_error(e)

                if not last_error.retry_able or attempt == max_retries:
                    raise last_error

                # 재시도 대기
                wait_time = last_error.retry_after or delay
                logger.info(f"Retrying after {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)

                # 백오프 적용
                if exponential_backoff:
                    delay *= 2

        raise last_error


# 전역 에러 핸들러 인스턴스
_error_handler = ErrorHandler()


# 편의 함수들
def handle_error(error: Exception) -> APIException:
    """에러 처리"""
    return _error_handler.handle_error(error)


def get_error_stats() -> Dict[str, Any]:
    """에러 통계 반환"""
    return _error_handler.get_error_stats()


async def with_retry(func, **kwargs):
    """재시도 로직과 함께 실행"""
    return await _error_handler.with_retry(func, **kwargs)