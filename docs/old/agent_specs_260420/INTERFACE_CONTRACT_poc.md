# Interface Contract — ADALLPIN POC

**Version**: 1.1 | **Date**: 2026-04-10 | **Status**: Active — POC

> **이 문서의 모든 타입/Enum은 [DATA_MODELS_poc.md](DATA_MODELS_poc.md)를 참조합니다.**
> 기준 문서: [INTERFACE_CONTRACT.md](INTERFACE_CONTRACT.md) (v3.2)

---

## 목차

1. [개요](#1-개요)
2. [REST API — 채팅 세션](#2-rest-api--채팅-세션)
3. [REST API — Agent 실행](#3-rest-api--agent-실행)
4. [REST API — HITL](#4-rest-api--hitl)
5. [REST API — 메모리](#5-rest-api--메모리)
6. [REST API — 미리보기](#6-rest-api--미리보기)
7. [WebSocket 채널 개요](#7-websocket-채널-개요)
8. [Layer Contract](#8-layer-contract)
9. [AgentState Contract](#9-agentstate-contract)
10. [Error Contract](#10-error-contract)
11. [Validation Rules](#11-validation-rules)
12. [화면-에이전트 연결 매트릭스](#12-화면-에이전트-연결-매트릭스)

---

## 1. 개요

ADALLPIN POC의 **FE ↔ BE 인터페이스 계약**을 정의합니다.

### 1.1 POC 제외 항목

| 제외 항목 | 사유 |
|-----------|------|
| fallback | POC 불필요 |
| fail 재시도 | failed 즉시 final |
| 실시간 모니터링 | anomaly_detector 미포함 |
| 예산 재배치 API | budget_review 미포함 |
| Plan 롤백 | POC 불필요 |
| Rate Limiting | POC 불필요 |

### 1.2 POC 추가 항목

| 추가 항목 | 설명 |
|-----------|------|
| 멀티 채팅 세션 | AE당 N개 채팅방 |
| 메모리 API | 장기 기억 조회 |
| 중간 미리보기 | 단계별 결과 조회 |
| WebSocket 멀티플렉싱 | AE당 2개 고정 |
| pause/resume | 사용자가 언제든 작업 중단/재개 가능 |
| 병렬 실행 | depends_on 기반 Orchestrator 자동 판단 |

---

## 2. REST API — 채팅 세션

### 2.1 채팅방 생성 — `POST /api/v1/chat/sessions`

```typescript
interface CreateChatSessionRequest {
  client_id: string;       // UUID — 광고주 ID
  title?:    string;       // 채팅방 제목 (생략 시 자동 생성)
}

// 응답 201
interface CreateChatSessionResponse {
  success: true;
  data: {
    session_id: string;    // 생성된 채팅방 UUID
    title:      string;
    status:     "created";
    created_at: string;    // ISO 8601
  };
  meta: {
    request_id: string;
    timestamp:  string;
  };
}

// 응답 400 — 채팅방 개수 제한 초과 (AE당 최대 10개)
interface CreateChatSessionLimitErrorResponse {
  success: false;
  error: {
    code:    "CHAT_SESSION_LIMIT_EXCEEDED";
    message: "활성 채팅방이 10개를 초과했습니다. 기존 채팅방을 삭제 후 다시 시도해주세요.";
    details: {
      current: number;     // 현재 채팅방 수 (= 10)
      max:     number;     // 제한 (10)
    };
  };
  meta: {
    request_id: string;
    timestamp:  string;
  };
}
```

> **카운트 정책 (DM_poc §14.1 참조):**
> 해당 user_id의 `chat_sessions` 테이블 행 중 **삭제되지 않은 모든 행**을 카운트한다.
> status 무관 — created/running/paused/completed/failed/cancelled 모두 포함.
> 새 채팅방을 만들려면 기존 채팅방을 명시적으로 `DELETE`로 삭제해야 한다.

### 2.2 채팅방 목록 — `GET /api/v1/chat/sessions`

```typescript
// GET /api/v1/chat/sessions?client_id={uuid}&status=running&limit=20
interface ChatSessionListResponse {
  sessions: Array<{
    session_id:     string;
    client_id:      string;
    title:          string;
    status:         string;     // → SessionStatus (DATA_MODELS_poc §2.9)
    created_at:     string;
    last_active_at: string;
    message_count:  number;     // 해당 세션의 메시지 수
  }>;
  total_count: number;
}
```

### 2.3 채팅방 삭제 — `DELETE /api/v1/chat/sessions/{session_id}`

```typescript
// → 204 No Content
// 진행 중인 실행이 있으면 자동 취소 후 삭제
```

### 2.4 채팅방 히스토리 — `GET /api/v1/chat/sessions/{session_id}/messages`

```typescript
// GET /api/v1/chat/sessions/{session_id}/messages?limit=50&offset=0
interface ChatMessageListResponse {
  messages: Array<{
    id:         string;
    role:       "user" | "assistant" | "system";
    content:    string;
    metadata:   object;     // step_preview 참조 등
    created_at: string;
  }>;
  total_count: number;
}
```

---

## 3. REST API — Agent 실행

### 3.1 동기 실행 — `POST /api/v1/agent/run`

```typescript
interface AgentRunRequest {
  message:         string;       // 필수: 사용자 메시지 (1~10000자)
  session_id: string;       // 필수: 채팅방 UUID
  language?:       string;       // "ko" | "en" | "ja" (기본: "ko")
  config?: {
    auto_approve_plan?: boolean; // Plan 자동 승인
    skip_hitl?:         boolean; // HITL 전체 생략
  };
}

// 응답 200
interface AgentRunResponse {
  success: true;
  data: {
    session_id: string;
    response: {
      format:       string;     // "text" | "image" | "pdf" | "mixed"
      text:         string;
      summary:      string;
      attachments:  Attachment[];
      step_previews: string[];  // StepPreview ID 목록
    };
  };
  meta: {
    request_id: string;
    timestamp:  string;
  };
}
```

### 3.2 비동기 실행 — `POST /api/v1/agent/run-async`

```typescript
interface AgentRunAsyncRequest {
  message:         string;
  session_id: string;
  language?:       string;
  config?:         object;
}

// 응답 202 Accepted
interface AgentRunAsyncResponse {
  session_id:  string;
  stream_url:  string;  // ws://host/ws/stream?user_id={uuid}  ← 멀티플렉싱
  hitl_url:    string;  // ws://host/ws/hitl?user_id={uuid}    ← 멀티플렉싱
  status:      "started";
}
```

> WebSocket URL에 `session_id`가 없음 — 멀티플렉싱 구조.
> 메시지 내부의 `session_id`로 어떤 채팅방의 이벤트인지 구분.

---

## 4. REST API — HITL

### 4.1 HITL 대기 목록 — `GET /api/v1/hitl/pending`

```typescript
// GET /api/v1/hitl/pending?user_id={uuid}&limit=20&sort=priority
// 멀티세션 — AE의 모든 채팅방에서 발생한 HITL 요청을 priority 순으로
interface HITLPendingListResponse {
  items: Array<{
    request_id:      string;     // HITLRequest.id (by_alias)
    session_id: string;     // 어떤 채팅방에서 발생
    client_id:       string;
    type:            string;     // → HITLRequestType (DATA_MODELS_poc §2.10)
    priority:        string;     // → HITLPriority (DATA_MODELS_poc §2.11)
    status:          string;
    title:           string;
    description:     string;
    options:         string[];
    requested_at:    string;
    wait_minutes:    number;
  }>;
  total_count: number;
}
```

### 4.2 Plan 승인/수정/거절 — `POST /api/v1/hitl/{session_id}/plan`

```typescript
interface HITLPlanRequest {
  request_id: string;       // HITLRequest.id (by_alias)
  action:     "approve" | "modify" | "reject";
  instruction?: string;     // action = "modify" 시 자연어 수정 지시
  comment?:   string;
}
```

### 4.3 Todo 승인 — `POST /api/v1/hitl/{session_id}/approve`

```typescript
interface HITLApproveRequest {
  request_id: string;
  action:     "approve" | "skip" | "reject";
  comment?:   string;
}
```

### 4.4 명확화 응답 — `POST /api/v1/hitl/{session_id}/clarification`

```typescript
interface HITLClarificationRequest {
  request_id: string;
  value:      string;
  comment?:   string;
}
```

### 4.5 사용자 입력 — `POST /api/v1/hitl/{session_id}/input`

```typescript
interface HITLInputRequest {
  request_id: string;
  value:      string | number;
  comment?:   string;
}
```

---

## 5. REST API — 메모리

### 5.1 장기 기억 목록 — `GET /api/v1/memory/long-term`

```typescript
// GET /api/v1/memory/long-term?client_id={uuid}&limit=10
interface LongTermMemoryListResponse {
  memories: Array<{
    id:                string;
    client_id:         string;
    source_session_id: string;    // 원본 채팅방 ID
    summary:           string;    // LLM 생성 요약
    key_insights:      string[];  // 핵심 인사이트
    tools_used:        string[];  // 사용된 Tool 목록
    created_at:        string;
  }>;
  total_count: number;
}
```

### 5.2 장기 기억 상세 — `GET /api/v1/memory/long-term/{memory_id}`

```typescript
interface LongTermMemoryDetailResponse {
  id:                string;
  client_id:         string;
  source_session_id: string;
  summary:           string;
  key_insights:      string[];
  tools_used:        string[];
  metadata:          object;
  created_at:        string;
}
```

---

## 6. REST API — 미리보기

### 6.1 세션 미리보기 목록 — `GET /api/v1/chat/sessions/{session_id}/previews`

```typescript
// 해당 채팅방의 모든 StepPreview 조회
interface StepPreviewListResponse {
  previews: Array<{
    todo_id:       string;
    tool:          string;      // PocTool 값
    group:         string;      // "수집" | "전처리" | "ML" 등
    step_index:    number;
    total_steps:   number;
    preview_type:  string;      // "data_sample" | "statistics" | "image" | "text" | "chart"
    title:         string;
    summary:       string;
    data:          object;
    created_at:    string;
  }>;
}
```

---

## 7. WebSocket 채널 개요

> 상세 명세 → [WEBSOCKET_PROTOCOL_poc.md](WEBSOCKET_PROTOCOL_poc.md)

### 7.1 멀티플렉싱 구조

```
기존 (v3.2): 세션당 2개
  ws/stream/{session_id}  ← 세션마다 연결
  ws/hitl/{session_id}    ← 세션마다 연결
  → 채팅 4개 = WebSocket 8개 → 브라우저 한도(6) 초과

POC: AE당 2개 고정
  ws/stream?user_id={uuid}  ← AE당 1개, 모든 세션 이벤트 수신
  ws/hitl?user_id={uuid}    ← AE당 1개, 모든 세션 HITL 수신
  → 채팅 N개여도 WebSocket 2개
```

### 7.2 메시지 라우팅

```json
{
  "type": "step_preview",
  "session_id": "chat_session_uuid_001",  // ← 어떤 채팅방인지
  "data": { ... }
}
```

> FE는 `session_id`로 메시지를 해당 채팅방 컴포넌트에 라우팅.
> 현재 보고 있는 채팅방이 아닌 메시지는 배지/알림으로 표시.

---

## 8. Layer Contract

### 8.1 Layer 데이터 흐름

```
                    ExecutionContext (client_id, user_id, memory)
                           │ (모든 레이어에 외부 주입)
                           │
┌──────────────┐  CognitiveOutput   ┌──────────────┐
│   Cognitive  │ ─────────────────► │   Planning   │
│    Layer     │  Intent + Tools    │    Layer     │
└──────────────┘                    └──────────────┘
       │                                   │
  장기 기억 조회                       Plan + TodoItems
  (LongTermMemory)                         │
                                           ▼
┌──────────────┐  ExecutionOutput   ┌──────────────┐
│   Response   │ ◄───────────────── │  Execution   │
│    Layer     │  Results+Previews │    Layer     │
└──────────────┘                    └──────────────┘
                                      │
                                 StepPreview 전송
                                 (각 Tool 완료 시)
```

### 8.2 Cognitive Layer I/O

```python
# 입력
class CognitiveInput:
    user_input: str
    language: str = "ko"
    long_term_memories: List[dict] = []  # 관련 장기 기억

# 출력 → AgentState.cognitive_result
# 타입: CognitiveOutput — DATA_MODELS_poc §5.2
```

### 8.3 Planning Layer I/O

```python
# 입력
class PlanningInput:
    intent: Intent
    suggested_tools: List[str] = []

# 출력 → AgentState.plan + AgentState.todos
```

### 8.4 Execution Layer I/O

```python
# 입력 — TodoItem 단위
class ExecutionInput:
    todo: TodoItem
    previous_results: dict
    context: ExecutionContext     # client_id, session_memory 포함

# 출력 → AgentState.execution_results 업데이트
# + StepPreview WS 이벤트 전송
```

### 8.5 Response Layer I/O

```python
# 입력
class ResponseInput:
    user_input: str
    intent: Intent
    execution_results: dict
    step_previews: List[dict]    # 단계별 미리보기 참조
    language: str = "ko"

# 출력 → AgentState.response_result
```

---

## 9. AgentState Contract

### 9.1 초기 상태

```python
initial_state = AgentState(
    session_id        = session_id,      # 채팅방 UUID
    user_input        = request.message,
    language          = request.language or "ko",

    cognitive_result  = {},
    planning_result   = {},
    execution_results = {},
    response_result   = {},

    plan              = {},
    todos             = [],

    error             = None,
    hitl_pending      = None,
    trace             = [],

    memory_context    = session_memory_dict,   # SessionMemory에서 주입
)
```

### 9.2 세션 완료 시 메모리 압축

```
AgentState 완료 (response_result 채워짐)
  → SessionMemory에 대화 + 결과 저장
  → LLM으로 압축 → LongTermMemory 생성
  → 다음 세션에서 Cognitive Layer가 참조
```

---

## 10. Error Contract

### 10.1 에러 코드 (POC 축소)

| Category | Code Range | 대표 에러 |
|----------|------------|-----------|
| VALIDATION | 1000-1999 | `VALIDATION_INVALID_INPUT` |
| AUTH | 2000-2999 | `AUTH_TOKEN_EXPIRED` |
| SESSION | 3000-3999 | `SESSION_NOT_FOUND`, `SESSION_INVALID_STATE`, `CHAT_SESSION_LIMIT_EXCEEDED` |
| PLAN | 4000-4999 | `PLAN_NOT_FOUND` |
| EXECUTION | 5000-5999 | `EXECUTION_TODO_FAILED` |
| HITL | 6000-6999 | `HITL_TIMEOUT`, `HITL_ALREADY_RESPONDED` |
| TOOL | 7000-7999 | `TOOL_NOT_FOUND`, `TOOL_TIMEOUT` |
| LLM | 8000-8999 | `LLM_SERVICE_ERROR` |
| SYSTEM | 9000-9999 | `SYSTEM_INTERNAL_ERROR` |

> POC 제외: `AD_API_RATE_LIMIT`, `REPORT_GENERATION_FAILED`, `CLIENT_ACCESS_DENIED` 등

### 10.2 공통 에러 응답

```typescript
interface ErrorResponse {
  success: false;
  error: {
    code:     string;
    message:  string;
    details?: object;
  };
  meta: {
    request_id: string;
    timestamp:  string;
  };
}
```

> POC: `recoverable`, `suggested_action` 필드 제거 — 재시도/fallback 없으므로.

---

## 11. Validation Rules

| 필드 | 규칙 | 에러 코드 |
|------|------|-----------|
| `message` | 1~10000자, strip 후 빈 문자열 불가 | `VALIDATION_INVALID_INPUT` |
| `session_id` | UUID v4 형식 (소문자 정규화) | `VALIDATION_INVALID_FORMAT` |
| `language` | `"ko"`, `"en"`, 또는 `"ja"` | `VALIDATION_INVALID_LANGUAGE` |

---

## 12. 화면-에이전트 연결 매트릭스

> FE 화면의 버튼/트리거가 어떤 에이전트를 호출하는지 정의합니다.
> 채팅 시작 시 `screen_context` 메시지(WS §2.4)로 컨텍스트가 전달되며,
> cognitive_node가 아래 매핑을 기반으로 적합한 에이전트/시나리오를 선택합니다.

| 화면 | 버튼/트리거 | 호출 에이전트 | 핵심 시나리오 |
|------|------------|--------------|--------------|
| 대시보드 | 매일 자동 업데이트 | collection + preprocessing + analysis | 전체 파이프라인 정기 실행 |
| 대시보드 | "상세 분석 보기" | analysis_agent | POC-01, POC-06 |
| ROAS분석 | "상세 분석 시작" | analysis_agent | POC-01 |
| 소재분석 | "AI 소재 생성 시작" | analysis + image_creation | POC-02, POC-05 + 이미지 생성 |
| 소재분석 | "A/B 테스트 시작" | analysis_agent | POC-03 |
| 소재분석 | "영상 스토리보드" | analysis + video_creation | POC-02 + 스토리보드 |
| 트렌드분석 | "소재 기획 시작" | analysis + image_creation | POC-07, POC-08 + 이미지 생성 |
| 비용최적화 | "AI 예산 재배분 승인" | analysis_agent | POC-01, POC-04 |
| 비용최적화 | "무의미 키워드 중지" | analysis_agent | POC-04 |
| 리포트 | "생성" 버튼 | report + pdf | POC-09 + PDF 렌더링 |
| 채팅 | 자유 대화 | 전체 (Planning이 결정) | — |

> **참고**: 전체 화면-에이전트 매핑은 ADALLPIN_에이전트_기능명세서.md §9 참조.
> 위 매트릭스는 POC 범위의 핵심 트리거만 요약한 것입니다.

---

## Change Log

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2026-04-06 | POC 초판. 멀티채팅세션, 메모리, 미리보기, 멀티플렉싱 WS |
| 1.1 | 2026-04-10 | §12 화면-에이전트 연결 매트릭스 추가 |

---

*Related: [DATA_MODELS_poc.md](DATA_MODELS_poc.md) | [WEBSOCKET_PROTOCOL_poc.md](WEBSOCKET_PROTOCOL_poc.md)*
