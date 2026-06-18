# Error Codes Specification

**Version**: 2.0 | **Date**: 2026-02-06 | **Status**: Draft

---

## 1. Overview

Dream Agent V2의 에러 코드 체계입니다. 일관된 에러 형식과 코드를 사용하여 클라이언트가 에러를 적절히 처리할 수 있도록 합니다.

### 1.1 Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "세션을 찾을 수 없습니다.",
    "details": {
      "session_id": "sess_abc123"
    },
    "recoverable": false,
    "suggested_action": "create_new_session"
  },
  "meta": {
    "request_id": "req_xyz789",
    "timestamp": "2026-02-06T10:00:00Z"
  }
}
```

### 1.2 Error Code Structure

```
{CATEGORY}_{SUBCATEGORY}_{SPECIFIC}

예시:
- SESSION_NOT_FOUND
- EXECUTION_TODO_FAILED
- HITL_TIMEOUT
```

---

## 2. Error Categories

### 2.1 Category Overview

| Category | Code Range | HTTP Status | Description |
|----------|------------|-------------|-------------|
| `VALIDATION` | 1000-1999 | 400 | 입력 검증 오류 |
| `AUTH` | 2000-2999 | 401, 403 | 인증/권한 오류 |
| `SESSION` | 3000-3999 | 404, 409 | 세션 관련 오류 |
| `PLAN` | 4000-4999 | 404, 409 | 플랜 관련 오류 |
| `EXECUTION` | 5000-5999 | 500 | 실행 오류 |
| `HITL` | 6000-6999 | 400, 408 | HITL 오류 |
| `TOOL` | 7000-7999 | 500, 502 | 도구 실행 오류 |
| `LLM` | 8000-8999 | 502, 503 | LLM 서비스 오류 |
| `SYSTEM` | 9000-9999 | 500, 503 | 시스템 오류 |

---

## 3. Validation Errors (1000-1999)

| Code | Name | HTTP | Description | Suggested Action |
|------|------|------|-------------|------------------|
| 1001 | `VALIDATION_INVALID_INPUT` | 400 | 잘못된 입력 형식 | 입력 형식 확인 |
| 1002 | `VALIDATION_MISSING_FIELD` | 400 | 필수 필드 누락 | 필수 필드 제공 |
| 1003 | `VALIDATION_INVALID_TYPE` | 400 | 잘못된 데이터 타입 | 데이터 타입 확인 |
| 1004 | `VALIDATION_OUT_OF_RANGE` | 400 | 값이 허용 범위 초과 | 허용 범위 내 값 사용 |
| 1005 | `VALIDATION_INVALID_FORMAT` | 400 | 잘못된 형식 (이메일, URL 등) | 올바른 형식 사용 |
| 1006 | `VALIDATION_TOO_LONG` | 400 | 입력이 너무 김 | 길이 제한 준수 |
| 1007 | `VALIDATION_EMPTY_INPUT` | 400 | 빈 입력 | 값 제공 |
| 1008 | `VALIDATION_INVALID_LANGUAGE` | 400 | 지원하지 않는 언어 | 지원 언어 사용 |

**Example:**
```json
{
  "error": {
    "code": "VALIDATION_MISSING_FIELD",
    "message": "필수 필드가 누락되었습니다: message",
    "details": {
      "field": "message",
      "required": true
    },
    "recoverable": true,
    "suggested_action": "provide_required_field"
  }
}
```

---

## 4. Authentication Errors (2000-2999)

| Code | Name | HTTP | Description | Suggested Action |
|------|------|------|-------------|------------------|
| 2001 | `AUTH_REQUIRED` | 401 | 인증 필요 | 로그인/토큰 제공 |
| 2002 | `AUTH_INVALID_TOKEN` | 401 | 잘못된 토큰 | 토큰 갱신 |
| 2003 | `AUTH_TOKEN_EXPIRED` | 401 | 토큰 만료 | 토큰 갱신 |
| 2004 | `AUTH_INVALID_API_KEY` | 401 | 잘못된 API 키 | API 키 확인 |
| 2005 | `AUTH_FORBIDDEN` | 403 | 권한 없음 | 권한 요청 |
| 2006 | `AUTH_RATE_LIMIT_EXCEEDED` | 429 | 요청 한도 초과 | 잠시 후 재시도 |
| 2007 | `AUTH_SESSION_OWNER_MISMATCH` | 403 | 세션 소유자 불일치 | 본인 세션 접근 |

**Example:**
```json
{
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "인증 토큰이 만료되었습니다.",
    "details": {
      "expired_at": "2026-02-06T09:00:00Z"
    },
    "recoverable": true,
    "suggested_action": "refresh_token"
  }
}
```

---

## 5. Session Errors (3000-3999)

| Code | Name | HTTP | Description | Suggested Action |
|------|------|------|-------------|------------------|
| 3001 | `SESSION_NOT_FOUND` | 404 | 세션을 찾을 수 없음 | 새 세션 생성 |
| 3002 | `SESSION_EXPIRED` | 410 | 세션 만료 | 새 세션 생성 |
| 3003 | `SESSION_ALREADY_RUNNING` | 409 | 이미 실행 중인 세션 | 기존 세션 사용 |
| 3004 | `SESSION_NOT_RESUMABLE` | 409 | 재개할 수 없는 상태 | 상태 확인 |
| 3005 | `SESSION_ALREADY_COMPLETED` | 409 | 이미 완료된 세션 | 새 세션 생성 |
| 3006 | `SESSION_LIMIT_EXCEEDED` | 429 | 동시 세션 한도 초과 | 기존 세션 종료 |
| 3007 | `SESSION_CANCELLED` | 410 | 취소된 세션 | 새 세션 생성 |

**Example:**
```json
{
  "error": {
    "code": "SESSION_NOT_RESUMABLE",
    "message": "세션을 재개할 수 없습니다.",
    "details": {
      "session_id": "sess_abc123",
      "current_status": "completed",
      "resumable_statuses": ["paused", "hitl_waiting", "failed"]
    },
    "recoverable": false,
    "suggested_action": "create_new_session"
  }
}
```

---

## 6. Plan Errors (4000-4999)

| Code | Name | HTTP | Description | Suggested Action |
|------|------|------|-------------|------------------|
| 4001 | `PLAN_NOT_FOUND` | 404 | 플랜을 찾을 수 없음 | 세션 확인 |
| 4002 | `PLAN_ALREADY_APPROVED` | 409 | 이미 승인된 플랜 | 수정 후 재승인 |
| 4003 | `PLAN_REJECTED` | 410 | 거부된 플랜 | 새 플랜 생성 |
| 4004 | `PLAN_MODIFICATION_FAILED` | 500 | 플랜 수정 실패 | 재시도 |
| 4005 | `PLAN_INVALID_EDIT` | 400 | 잘못된 수정 요청 | 수정 내용 확인 |
| 4006 | `PLAN_DEPENDENCY_CYCLE` | 400 | 의존성 순환 발생 | 의존성 수정 |
| 4007 | `PLAN_TODO_NOT_FOUND` | 404 | Todo를 찾을 수 없음 | Todo ID 확인 |

**Example:**
```json
{
  "error": {
    "code": "PLAN_DEPENDENCY_CYCLE",
    "message": "Todo 의존성에 순환이 발생했습니다.",
    "details": {
      "cycle": ["todo_001", "todo_003", "todo_001"],
      "problematic_todo": "todo_003"
    },
    "recoverable": true,
    "suggested_action": "fix_dependency"
  }
}
```

---

## 7. Execution Errors (5000-5999)

| Code | Name | HTTP | Description | Suggested Action |
|------|------|------|-------------|------------------|
| 5001 | `EXECUTION_FAILED` | 500 | 실행 실패 | 재시도 |
| 5002 | `EXECUTION_TODO_FAILED` | 500 | Todo 실행 실패 | 해당 Todo 재시도 |
| 5003 | `EXECUTION_TODO_BLOCKED` | 409 | Todo가 차단됨 (의존성) | 선행 작업 완료 |
| 5004 | `EXECUTION_TODO_SKIPPED` | 200 | Todo 건너뜀 | - |
| 5005 | `EXECUTION_NO_READY_TODOS` | 409 | 실행 가능한 Todo 없음 | 상태 확인 |
| 5006 | `EXECUTION_MAX_RETRIES` | 500 | 최대 재시도 횟수 초과 | 수동 개입 |
| 5007 | `EXECUTION_CANCELLED` | 410 | 실행 취소됨 | 새 세션 생성 |
| 5008 | `EXECUTION_PARTIAL` | 500 | 부분 실행 완료 | 결과 확인 후 재시도 |

**Example:**
```json
{
  "error": {
    "code": "EXECUTION_TODO_FAILED",
    "message": "Todo 실행 중 오류가 발생했습니다.",
    "details": {
      "todo_id": "todo_003",
      "todo_task": "감성 분석",
      "tool": "sentiment_analyzer",
      "original_error": "Model API timeout"
    },
    "recoverable": true,
    "suggested_action": "retry_todo"
  }
}
```

---

## 8. HITL Errors (6000-6999)

| Code | Name | HTTP | Description | Suggested Action |
|------|------|------|-------------|------------------|
| 6001 | `HITL_TIMEOUT` | 408 | HITL 응답 타임아웃 | 기본 동작 실행됨 |
| 6002 | `HITL_INVALID_RESPONSE` | 400 | 잘못된 HITL 응답 | 올바른 형식 제공 |
| 6003 | `HITL_REQUEST_EXPIRED` | 410 | HITL 요청 만료 | - |
| 6004 | `HITL_REQUEST_NOT_FOUND` | 404 | HITL 요청을 찾을 수 없음 | 요청 ID 확인 |
| 6005 | `HITL_SESSION_NOT_PAUSED` | 409 | 세션이 일시정지 상태 아님 | 상태 확인 |
| 6006 | `HITL_ALREADY_RESPONDED` | 409 | 이미 응답됨 | - |
| 6007 | `HITL_INVALID_ACTION` | 400 | 잘못된 액션 | 허용된 액션 사용 |

**Example:**
```json
{
  "error": {
    "code": "HITL_TIMEOUT",
    "message": "HITL 응답 대기 시간이 초과되었습니다.",
    "details": {
      "request_id": "hitl_001",
      "request_type": "plan_review",
      "timeout_sec": 300,
      "default_action_taken": "approve"
    },
    "recoverable": false,
    "suggested_action": null
  }
}
```

---

## 9. Tool Errors (7000-7999)

| Code | Name | HTTP | Description | Suggested Action |
|------|------|------|-------------|------------------|
| 7001 | `TOOL_NOT_FOUND` | 404 | 도구를 찾을 수 없음 | 도구 이름 확인 |
| 7002 | `TOOL_EXECUTION_FAILED` | 500 | 도구 실행 실패 | 재시도 |
| 7003 | `TOOL_TIMEOUT` | 504 | 도구 실행 타임아웃 | 재시도 또는 건너뛰기 |
| 7004 | `TOOL_INVALID_PARAMS` | 400 | 잘못된 도구 파라미터 | 파라미터 확인 |
| 7005 | `TOOL_UNAVAILABLE` | 503 | 도구 일시 사용 불가 | 잠시 후 재시도 |
| 7006 | `TOOL_RATE_LIMITED` | 429 | 외부 API 요청 한도 | 잠시 후 재시도 |
| 7007 | `TOOL_AUTH_FAILED` | 502 | 외부 API 인증 실패 | API 키 확인 |
| 7008 | `TOOL_DEPENDENCY_MISSING` | 500 | 필요한 선행 데이터 없음 | 의존성 확인 |

**Example:**
```json
{
  "error": {
    "code": "TOOL_RATE_LIMITED",
    "message": "외부 API 요청 한도를 초과했습니다.",
    "details": {
      "tool": "google_trends",
      "api": "Google Trends API",
      "retry_after_sec": 60
    },
    "recoverable": true,
    "suggested_action": "retry_after_delay"
  }
}
```

---

## 10. LLM Errors (8000-8999)

| Code | Name | HTTP | Description | Suggested Action |
|------|------|------|-------------|------------------|
| 8001 | `LLM_SERVICE_ERROR` | 502 | LLM 서비스 오류 | 재시도 |
| 8002 | `LLM_TIMEOUT` | 504 | LLM 응답 타임아웃 | 재시도 |
| 8003 | `LLM_RATE_LIMITED` | 429 | LLM API 한도 초과 | 잠시 후 재시도 |
| 8004 | `LLM_CONTEXT_TOO_LONG` | 400 | 컨텍스트 길이 초과 | 입력 축소 |
| 8005 | `LLM_INVALID_RESPONSE` | 502 | LLM 응답 파싱 실패 | 재시도 |
| 8006 | `LLM_CONTENT_FILTERED` | 400 | 콘텐츠 필터링됨 | 입력 수정 |
| 8007 | `LLM_MODEL_UNAVAILABLE` | 503 | 모델 일시 사용 불가 | 대체 모델 사용 |

**Example:**
```json
{
  "error": {
    "code": "LLM_CONTEXT_TOO_LONG",
    "message": "입력이 모델의 최대 컨텍스트 길이를 초과했습니다.",
    "details": {
      "input_tokens": 150000,
      "max_tokens": 128000,
      "model": "gpt-4"
    },
    "recoverable": true,
    "suggested_action": "reduce_input"
  }
}
```

---

## 11. System Errors (9000-9999)

| Code | Name | HTTP | Description | Suggested Action |
|------|------|------|-------------|------------------|
| 9001 | `SYSTEM_INTERNAL_ERROR` | 500 | 내부 서버 오류 | 지원팀 문의 |
| 9002 | `SYSTEM_DATABASE_ERROR` | 500 | 데이터베이스 오류 | 재시도 |
| 9003 | `SYSTEM_CACHE_ERROR` | 500 | 캐시 오류 | 재시도 |
| 9004 | `SYSTEM_MAINTENANCE` | 503 | 시스템 점검 중 | 잠시 후 재시도 |
| 9005 | `SYSTEM_OVERLOADED` | 503 | 시스템 과부하 | 잠시 후 재시도 |
| 9006 | `SYSTEM_RESOURCE_EXHAUSTED` | 503 | 리소스 부족 | 잠시 후 재시도 |
| 9007 | `SYSTEM_CONFIG_ERROR` | 500 | 설정 오류 | 지원팀 문의 |

**Example:**
```json
{
  "error": {
    "code": "SYSTEM_MAINTENANCE",
    "message": "시스템 점검 중입니다.",
    "details": {
      "maintenance_end": "2026-02-06T12:00:00Z",
      "reason": "Scheduled database maintenance"
    },
    "recoverable": true,
    "suggested_action": "retry_after_maintenance"
  }
}
```

---

## 12. WebSocket Error Codes

WebSocket 연결 관련 에러는 별도 코드 체계를 사용합니다.

| Code | Name | Description |
|------|------|-------------|
| 1001 | `WS_CLOSE_GOING_AWAY` | 서버 종료 |
| 1002 | `WS_CLOSE_PROTOCOL_ERROR` | 프로토콜 오류 |
| 1003 | `WS_CLOSE_UNSUPPORTED` | 지원하지 않는 데이터 |
| 1006 | `WS_CLOSE_ABNORMAL` | 비정상 종료 |
| 1008 | `WS_CLOSE_POLICY_VIOLATION` | 정책 위반 |
| 1011 | `WS_CLOSE_UNEXPECTED` | 예상치 못한 오류 |
| 4000 | `WS_SESSION_NOT_FOUND` | 세션을 찾을 수 없음 |
| 4001 | `WS_AUTH_REQUIRED` | 인증 필요 |
| 4002 | `WS_AUTH_FAILED` | 인증 실패 |
| 4003 | `WS_SESSION_EXPIRED` | 세션 만료 |

---

## 13. Error Handling Guidelines

### 13.1 Client-side Handling

```typescript
// error-handler.ts

interface ErrorHandler {
  handle(error: ApiError): void;
}

const errorHandlers: Record<string, ErrorHandler> = {
  // 인증 오류: 토큰 갱신 또는 로그인 페이지로
  AUTH_TOKEN_EXPIRED: {
    handle: async (error) => {
      const refreshed = await refreshToken();
      if (!refreshed) {
        redirectToLogin();
      }
    }
  },

  // 세션 오류: 새 세션 생성 안내
  SESSION_NOT_FOUND: {
    handle: (error) => {
      showNotification("세션이 만료되었습니다. 새로 시작해주세요.");
      redirectToHome();
    }
  },

  // HITL 타임아웃: 결과 표시
  HITL_TIMEOUT: {
    handle: (error) => {
      showNotification(`기본 동작이 실행되었습니다: ${error.details.default_action_taken}`);
    }
  },

  // 실행 오류: 재시도 옵션 제공
  EXECUTION_TODO_FAILED: {
    handle: (error) => {
      showRetryDialog(error.details.todo_id);
    }
  },

  // 기본 핸들러
  default: {
    handle: (error) => {
      showErrorNotification(error.message);
      if (error.recoverable) {
        showRetryButton();
      }
    }
  }
};

function handleApiError(error: ApiError) {
  const handler = errorHandlers[error.code] || errorHandlers.default;
  handler.handle(error);
}
```

### 13.2 Server-side Error Creation

```python
# core/errors.py

from enum import Enum
from typing import Optional, Dict, Any

class ErrorCode(str, Enum):
    VALIDATION_INVALID_INPUT = "VALIDATION_INVALID_INPUT"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    EXECUTION_TODO_FAILED = "EXECUTION_TODO_FAILED"
    # ...

class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        suggested_action: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        self.suggested_action = suggested_action

    def to_dict(self) -> dict:
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "suggested_action": self.suggested_action
        }

# 사용 예:
raise AppError(
    code=ErrorCode.SESSION_NOT_FOUND,
    message="세션을 찾을 수 없습니다.",
    details={"session_id": session_id},
    recoverable=False,
    suggested_action="create_new_session"
)
```

### 13.3 FastAPI Exception Handler

```python
# api/middleware/error_handler.py

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=get_http_status(exc.code),
        content={
            "success": False,
            "error": exc.to_dict(),
            "meta": {
                "request_id": request.state.request_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

def get_http_status(code: ErrorCode) -> int:
    status_map = {
        "VALIDATION_": 400,
        "AUTH_": 401,
        "SESSION_NOT_FOUND": 404,
        "SESSION_": 409,
        "PLAN_NOT_FOUND": 404,
        "PLAN_": 409,
        "EXECUTION_": 500,
        "HITL_TIMEOUT": 408,
        "HITL_": 400,
        "TOOL_NOT_FOUND": 404,
        "TOOL_": 500,
        "LLM_": 502,
        "SYSTEM_": 500
    }

    for prefix, status in status_map.items():
        if code.value.startswith(prefix):
            return status
    return 500
```

---

## 14. Logging & Monitoring

### 14.1 Error Logging Format

```python
# 에러 발생 시 로그 형식
{
    "timestamp": "2026-02-06T10:00:00Z",
    "level": "ERROR",
    "request_id": "req_xyz789",
    "session_id": "sess_abc123",
    "error": {
        "code": "EXECUTION_TODO_FAILED",
        "message": "Todo 실행 실패",
        "details": {...}
    },
    "stack_trace": "...",
    "context": {
        "todo_id": "todo_003",
        "tool": "sentiment_analyzer",
        "user_id": "user_123"
    }
}
```

### 14.2 Error Metrics

```python
# Prometheus metrics
from prometheus_client import Counter

error_counter = Counter(
    'dream_agent_errors_total',
    'Total error count',
    ['error_code', 'category', 'recoverable']
)

# 에러 발생 시
error_counter.labels(
    error_code="EXECUTION_TODO_FAILED",
    category="EXECUTION",
    recoverable="true"
).inc()
```

---

## Related Documents

- [API_SPEC.md](API_SPEC.md) - REST API 명세
- [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) - WebSocket 프로토콜
- [HITL_SPEC.md](HITL_SPEC.md) - HITL 시스템
- [SESSION_SPEC.md](SESSION_SPEC.md) - 세션 관리

---

*Last Updated: 2026-02-06*
