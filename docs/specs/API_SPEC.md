# REST API Specification

**Version**: 2.0 | **Date**: 2026-02-06 | **Status**: Draft

---

## 1. Overview

Dream Agent V2의 REST API 명세입니다.

### 1.1 Base URL

```
Development: http://localhost:8000/api
Production:  https://api.dream-agent.com/v2
```

### 1.2 Authentication

```http
Authorization: Bearer <jwt_token>
X-API-Key: <api_key>
```

### 1.3 Common Headers

```http
Content-Type: application/json
Accept: application/json
Accept-Language: ko-KR
```

### 1.4 Response Format

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-02-06T10:00:00Z"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { ... }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-02-06T10:00:00Z"
  }
}
```

---

## 2. Agent Endpoints

### 2.1 Run Agent (Synchronous)

동기 방식으로 에이전트를 실행하고 완료까지 대기합니다.

```http
POST /api/agent/run
```

**Request:**
```json
{
  "message": "라네즈 리뷰 분석해서 인사이트 뽑아줘",
  "language": "ko",
  "session_id": "optional_session_id",
  "config": {
    "auto_approve_plan": false,
    "skip_hitl": false,
    "max_execution_time_sec": 300
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "status": "completed",
    "response": {
      "format": "mixed",
      "text": "라네즈 리뷰 분석 결과입니다...",
      "summary": "전반적으로 긍정적 반응 (78%)",
      "attachments": [
        {
          "type": "chart",
          "title": "감성 분석 차트",
          "url": "/files/sess_abc123/sentiment.png"
        }
      ]
    },
    "plan_id": "plan_xyz789",
    "statistics": {
      "total_todos": 5,
      "completed_todos": 5,
      "execution_time_ms": 45000,
      "tokens_used": 15000
    }
  }
}
```

### 2.2 Run Agent (Asynchronous)

비동기 방식으로 실행하고 즉시 반환합니다. 진행상황은 WebSocket으로 수신합니다.

```http
POST /api/agent/run-async
```

**Request:**
```json
{
  "message": "라네즈 리뷰 분석해서 인사이트 뽑아줘",
  "language": "ko",
  "config": {
    "auto_approve_plan": false
  }
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "status": "running",
    "websocket_url": "ws://localhost:8000/ws/sess_abc123",
    "message": "Agent started. Connect to WebSocket for updates."
  }
}
```

### 2.3 Stream Agent (SSE)

Server-Sent Events로 스트리밍 실행합니다.

```http
POST /api/agent/stream
```

**Request:**
```json
{
  "message": "라네즈 리뷰 분석해서 인사이트 뽑아줘",
  "language": "ko"
}
```

**Response (200 OK, Content-Type: text/event-stream):**
```
event: session_start
data: {"session_id": "sess_abc123"}

event: layer_start
data: {"layer": "cognitive"}

event: layer_complete
data: {"layer": "cognitive", "result": {...}}

event: todo_update
data: {"todo_id": "todo_001", "status": "in_progress", "progress": 50}

event: complete
data: {"response": {...}}
```

### 2.4 Get Agent Status

에이전트 실행 상태를 조회합니다.

```http
GET /api/agent/status/{session_id}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "status": "executing",
    "current_layer": "execution",
    "progress": {
      "total_todos": 5,
      "completed_todos": 2,
      "current_todo": {
        "id": "todo_003",
        "task": "키워드 분석",
        "progress_percentage": 45
      }
    },
    "hitl_pending": null,
    "started_at": "2026-02-06T10:00:00Z",
    "estimated_completion": "2026-02-06T10:05:00Z"
  }
}
```

### 2.5 Stop Agent

실행 중인 에이전트를 중지합니다.

```http
POST /api/agent/stop/{session_id}
```

**Request:**
```json
{
  "reason": "User requested cancellation"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Agent stopped",
    "session_id": "sess_abc123",
    "stopped_at": "2026-02-06T10:05:30Z",
    "completed_todos": ["todo_001", "todo_002"],
    "cancelled_todos": ["todo_003", "todo_004", "todo_005"]
  }
}
```

---

## 3. Session Endpoints

### 3.1 List Sessions

```http
GET /api/sessions
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (active, completed, failed) |
| `limit` | int | Max items (default: 20, max: 100) |
| `offset` | int | Pagination offset |
| `sort` | string | Sort field (created_at, updated_at) |
| `order` | string | Sort order (asc, desc) |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": "sess_abc123",
        "status": "completed",
        "message": "라네즈 리뷰 분석...",
        "created_at": "2026-02-06T10:00:00Z",
        "completed_at": "2026-02-06T10:05:00Z"
      }
    ],
    "pagination": {
      "total": 45,
      "limit": 20,
      "offset": 0,
      "has_next": true
    }
  }
}
```

### 3.2 Get Session

```http
GET /api/sessions/{session_id}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "sess_abc123",
    "status": "completed",
    "language": "ko",
    "message": "라네즈 리뷰 분석해서 인사이트 뽑아줘",
    "cognitive_result": {
      "intent": {...},
      "entities": [...]
    },
    "plan": {
      "id": "plan_xyz789",
      "status": "completed",
      "todos": [...]
    },
    "response": {...},
    "created_at": "2026-02-06T10:00:00Z",
    "completed_at": "2026-02-06T10:05:00Z",
    "statistics": {...}
  }
}
```

### 3.3 Delete Session

```http
DELETE /api/sessions/{session_id}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Session deleted",
    "session_id": "sess_abc123"
  }
}
```

### 3.4 Resume Session

중단된 세션을 재개합니다.

```http
POST /api/sessions/{session_id}/resume
```

**Request:**
```json
{
  "modifications": []
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "status": "running",
    "websocket_url": "ws://localhost:8000/ws/sess_abc123"
  }
}
```

---

## 4. Plan Endpoints

### 4.1 Get Plan

```http
GET /api/plans/{plan_id}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "plan_xyz789",
    "session_id": "sess_abc123",
    "status": "executing",
    "version": 2,
    "todos": [
      {
        "id": "todo_001",
        "task": "데이터 수집",
        "tool": "collector",
        "status": "completed",
        "priority": 10,
        "depends_on": []
      },
      {
        "id": "todo_002",
        "task": "감성 분석",
        "tool": "sentiment_analyzer",
        "status": "in_progress",
        "priority": 8,
        "depends_on": ["todo_001"]
      }
    ],
    "dependency_graph": {
      "todo_001": [],
      "todo_002": ["todo_001"]
    },
    "estimated_duration_sec": 120,
    "mermaid_diagram": "graph LR...",
    "created_at": "2026-02-06T10:00:00Z"
  }
}
```

### 4.2 Approve Plan

```http
POST /api/plans/{plan_id}/approve
```

**Request:**
```json
{
  "comment": "Looks good, proceed."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Plan approved",
    "plan_id": "plan_xyz789",
    "new_status": "approved",
    "execution_starting": true
  }
}
```

### 4.3 Modify Plan

구조화된 방식으로 플랜을 수정합니다.

```http
PATCH /api/plans/{plan_id}
```

**Request:**
```json
{
  "edits": [
    {
      "action": "add_todo",
      "params": {
        "task": "경쟁사 분석",
        "tool": "competitor_analyzer",
        "insert_after": "todo_002"
      }
    },
    {
      "action": "remove_todo",
      "todo_id": "todo_005"
    },
    {
      "action": "update_todo",
      "todo_id": "todo_003",
      "params": {
        "priority": 9
      }
    }
  ],
  "reason": "Added competitor analysis, removed unnecessary step"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Plan updated",
    "plan_id": "plan_xyz789",
    "new_version": 3,
    "changes_applied": [
      "Added todo: 경쟁사 분석",
      "Removed todo: todo_005",
      "Updated todo_003 priority to 9"
    ],
    "updated_todos": [...]
  }
}
```

### 4.4 Modify Plan (Natural Language)

자연어로 플랜을 수정합니다.

```http
POST /api/plans/{plan_id}/nl-edit
```

**Request:**
```json
{
  "instruction": "리뷰 수집 다음에 경쟁사 분석도 추가해주고, 영상 생성은 빼줘"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Plan updated via natural language",
    "plan_id": "plan_xyz789",
    "new_version": 3,
    "interpreted_edits": [
      {
        "action": "add_todo",
        "description": "경쟁사 분석 Todo를 '리뷰 수집' 다음에 추가"
      },
      {
        "action": "remove_todo",
        "description": "영상 생성 Todo 제거"
      }
    ],
    "updated_todos": [...]
  }
}
```

### 4.5 Reject Plan

```http
POST /api/plans/{plan_id}/reject
```

**Request:**
```json
{
  "reason": "분석 범위가 너무 좁습니다."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Plan rejected",
    "plan_id": "plan_xyz789",
    "session_status": "cancelled"
  }
}
```

### 4.6 Get Plan History

```http
GET /api/plans/{plan_id}/history
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "plan_id": "plan_xyz789",
    "versions": [
      {
        "version": 1,
        "change_type": "create",
        "changed_by": "system",
        "created_at": "2026-02-06T10:00:00Z",
        "todo_count": 5
      },
      {
        "version": 2,
        "change_type": "user_edit",
        "changed_by": "user_123",
        "created_at": "2026-02-06T10:02:00Z",
        "change_reason": "Added competitor analysis",
        "todo_count": 6
      }
    ]
  }
}
```

---

## 5. Todo Endpoints

### 5.1 Get Todo

```http
GET /api/todos/{todo_id}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "todo_001",
    "plan_id": "plan_xyz789",
    "task": "데이터 수집",
    "description": "올리브영에서 라네즈 리뷰 수집",
    "status": "completed",
    "priority": 10,
    "tool": "collector",
    "tool_params": {
      "brand": "라네즈",
      "platform": "oliveyoung",
      "limit": 1000
    },
    "depends_on": [],
    "result": {
      "collected_count": 987,
      "date_range": "2025-11-06 ~ 2026-02-05"
    },
    "started_at": "2026-02-06T10:01:00Z",
    "completed_at": "2026-02-06T10:03:00Z"
  }
}
```

### 5.2 Approve Todo

```http
POST /api/todos/{todo_id}/approve
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Todo approved",
    "todo_id": "todo_004",
    "new_status": "pending"
  }
}
```

### 5.3 Skip Todo

```http
POST /api/todos/{todo_id}/skip
```

**Request:**
```json
{
  "reason": "이번에는 불필요"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Todo skipped",
    "todo_id": "todo_004",
    "new_status": "skipped"
  }
}
```

### 5.4 Retry Todo

```http
POST /api/todos/{todo_id}/retry
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Todo queued for retry",
    "todo_id": "todo_003",
    "new_status": "pending",
    "retry_count": 2
  }
}
```

---

## 6. HITL Endpoints

### 6.1 Pause Execution

```http
POST /api/hitl/{session_id}/pause
```

**Request:**
```json
{
  "reason": "Need to review intermediate results"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Execution paused",
    "session_id": "sess_abc123",
    "status": "paused",
    "current_todo": "todo_003"
  }
}
```

### 6.2 Resume Execution

```http
POST /api/hitl/{session_id}/resume
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Execution resumed",
    "session_id": "sess_abc123",
    "status": "running"
  }
}
```

### 6.3 Submit Input

```http
POST /api/hitl/{session_id}/input
```

**Request:**
```json
{
  "request_id": "hitl_003",
  "field": "date_range",
  "value": "3m"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Input received",
    "session_id": "sess_abc123",
    "status": "running"
  }
}
```

### 6.4 Get Pending Actions

```http
GET /api/hitl/{session_id}/pending
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "pending_actions": [
      {
        "request_id": "hitl_002",
        "type": "approval_request",
        "todo_id": "todo_005",
        "message": "영상 생성을 시작하려면 승인이 필요합니다.",
        "created_at": "2026-02-06T10:08:00Z",
        "timeout_at": "2026-02-06T11:08:00Z"
      }
    ]
  }
}
```

### 6.5 Verify Current State (LLM)

```http
POST /api/hitl/{session_id}/verify
```

**Request:**
```json
{
  "verify_type": "intermediate_results",
  "question": "지금까지 수집된 데이터가 충분한가요?"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "verification_result": {
      "summary": "현재까지 987개의 리뷰를 수집했습니다...",
      "quality_score": 0.85,
      "recommendations": [
        "데이터 양은 충분합니다.",
        "기간을 늘리면 트렌드 파악이 더 정확해질 수 있습니다."
      ]
    }
  }
}
```

---

## 7. Tools Endpoints

### 7.1 List Tools

```http
GET /api/tools
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category (collection, normalization, cleaning, preprocessing, metrics, comparison, analysis, report) |
| `active` | boolean | Filter by active status |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "tools": [
      {
        "name": "collector",
        "display_name": "데이터 수집기",
        "category": "data",
        "description": "다양한 플랫폼에서 리뷰 데이터를 수집합니다.",
        "parameters": [
          {
            "name": "brand",
            "type": "string",
            "required": true,
            "description": "수집할 브랜드명"
          }
        ],
        "requires_approval": false
      },
      {
        "name": "video_generator",
        "display_name": "영상 생성기",
        "category": "content",
        "description": "분석 결과를 영상으로 생성합니다.",
        "requires_approval": true
      }
    ],
    "total": 15
  }
}
```

### 7.2 Get Tool

```http
GET /api/tools/{tool_name}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "name": "sentiment_analyzer",
    "display_name": "감성 분석기",
    "category": "analysis",
    "description": "ABSA 기반 속성별 감성 분석",
    "parameters": [
      {
        "name": "text_data",
        "type": "array",
        "required": true,
        "description": "분석할 텍스트 리스트"
      },
      {
        "name": "aspects",
        "type": "array",
        "required": false,
        "default": ["texture", "scent", "moisturizing", "packaging", "price"],
        "description": "분석할 속성 리스트"
      }
    ],
    "produces": ["sentiment_result"],
    "requires_approval": false,
    "estimated_duration_sec": 30
  }
}
```

---

## 8. Health Endpoints

### 8.1 Health Check

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 86400,
  "services": {
    "database": "connected",
    "redis": "connected",
    "llm_provider": "connected"
  }
}
```

### 8.2 Ready Check

```http
GET /ready
```

**Response (200 OK):**
```json
{
  "status": "ready",
  "checks": {
    "database": true,
    "migrations": true,
    "cache": true
  }
}
```

---

## 9. Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/agent/run` | 10 req | 1 min |
| `/api/agent/run-async` | 20 req | 1 min |
| `/api/agent/stream` | 10 req | 1 min |
| `/api/plans/*` | 60 req | 1 min |
| `/api/todos/*` | 60 req | 1 min |
| `/api/hitl/*` | 120 req | 1 min |
| `/api/sessions/*` | 60 req | 1 min |
| `/api/tools` | 100 req | 1 min |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1707213600
```

---

## 10. Error Codes

See [ERROR_CODES.md](ERROR_CODES.md) for complete error code reference.

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_INPUT` | 400 | 잘못된 입력 |
| `UNAUTHORIZED` | 401 | 인증 필요 |
| `FORBIDDEN` | 403 | 권한 없음 |
| `NOT_FOUND` | 404 | 리소스 없음 |
| `RATE_LIMIT_EXCEEDED` | 429 | 요청 한도 초과 |
| `INTERNAL_ERROR` | 500 | 내부 서버 오류 |
| `LLM_ERROR` | 502 | LLM 서비스 오류 |
| `TIMEOUT` | 504 | 타임아웃 |

---

## Related Documents

- [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) - WebSocket 프로토콜
- [HITL_SPEC.md](HITL_SPEC.md) - HITL 시스템 상세
- [SESSION_SPEC.md](SESSION_SPEC.md) - 세션 관리
- [ERROR_CODES.md](ERROR_CODES.md) - 에러 코드 체계

---

*Last Updated: 2026-02-06*
