# WebSocket Protocol Specification — ADALLPIN POC

**Version**: 1.1 | **Date**: 2026-04-10 | **Status**: Active — POC

> **이 문서의 모든 타입/Enum은 [DATA_MODELS_poc.md](DATA_MODELS_poc.md)를 참조합니다.**
> 기준 문서: [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) (v3.2)

---

## 목차

1. [Overview — 멀티플렉싱 아키텍처](#1-overview--멀티플렉싱-아키텍처)
2. [채널 1: 스트리밍 채널 (`ws/stream`)](#2-채널-1-스트리밍-채널-wsstream)
3. [채널 2: HITL 제어 채널 (`ws/hitl`)](#3-채널-2-hitl-제어-채널-wshitl)
4. [공통 메시지 포맷](#4-공통-메시지-포맷)
5. [스트리밍 채널 이벤트 상세](#5-스트리밍-채널-이벤트-상세)
6. [HITL 채널 이벤트 상세](#6-hitl-채널-이벤트-상세)
7. [연결 관리 및 재연결](#7-연결-관리-및-재연결)
8. [시나리오](#8-시나리오)
9. [백엔드 구현](#9-백엔드-구현)
10. [프론트엔드 통합](#10-프론트엔드-통합)
11. [보안](#11-보안)

---

## 1. Overview — 멀티플렉싱 아키텍처

### 1.1 기존 vs POC 구조

```
기존 (v3.2): 세션당 2개 WebSocket
  ws/stream/{session_id}  ← 채팅 N개 = WebSocket 2N개
  ws/hitl/{session_id}    ← 브라우저 한도(6) 초과 위험

POC: AE당 2개 고정 (멀티플렉싱)
  ws/stream?user_id={uuid}  ← AE당 1개, 모든 세션 이벤트 수신
  ws/hitl?user_id={uuid}    ← AE당 1개, 모든 세션 HITL 수신
  → 채팅 100개여도 WebSocket 2개
```

> **구독 전략: 전략 B (전체 구독)**
>
> 멀티플렉싱 구조상 AE가 WS에 연결하면 자동으로 **해당 AE의 모든 채팅방 이벤트**를 수신한다.
> 명시적 subscribe/unsubscribe 프로토콜 없음 — user_id 기반으로 서버가 자동 라우팅한다.
>
> - **장점**: 방 전환 시 메시지 유실 없음, 별도 구독 관리 로직 불필요
> - **단점**: 방이 많으면 서버 부하 증가 (POC에서는 채팅방 수가 적어 무시 가능)
> - **대안 (미채택)**: 전략 A(현재 방만 구독)는 방 전환 시 이전 방의 이벤트를 놓칠 수 있어 REST 보충 로직이 필요함 → POC에서 제외

### 1.2 멀티플렉싱 원리

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (AE)                            │
│                                                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                  │
│  │  채팅방 A   │ │  채팅방 B   │ │  채팅방 C   │                  │
│  │ session_001│ │ session_002│ │ session_003│                  │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘                  │
│        └──────────────┼──────────────┘                          │
│                       │                                         │
│         ┌─────────────▼──────────────┐                          │
│         │   메시지 라우터 (FE)        │                          │
│         │   msg.session_id로 분배     │                          │
│         └─────────────┬──────────────┘                          │
│                       │                                         │
│     ws/stream (1개)   │   ws/hitl (1개)                         │
└───────────────────────┼─────────────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────────────┐
│                       │              Backend                     │
│         ┌─────────────▼──────────────┐                          │
│         │   ConnectionManager         │                          │
│         │   user_connections:         │                          │
│         │     Dict[user_id, WS]      │                          │
│         └─────────────┬──────────────┘                          │
│                       │                                         │
│    ┌──────────────────┼──────────────────┐                      │
│    │                  │                  │                      │
│    ▼                  ▼                  ▼                      │
│  LangGraph          LangGraph          LangGraph               │
│  session_001        session_002        session_003              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 엔드포인트

| 채널 | 엔드포인트 | 방향 |
|------|-----------|------|
| 스트리밍 | `ws://host/ws/stream?user_id={uuid}` | Server → Client (주) |
| HITL | `ws://host/ws/hitl?user_id={uuid}` | 양방향 |

> URL에 `session_id` 없음 — 메시지 내부 `session_id`로 라우팅.

---

## 2. 채널 1: 스트리밍 채널 (`ws/stream`)

### 2.1 연결

```
ws://host/ws/stream?user_id=550e8400-e29b-41d4-a716-446655440000
```

연결 후 auth 메시지 전송 (§11 참조).

### 2.2 Heartbeat

```json
// Server → Client (30초 간격)
{ "type": "ping", "timestamp": "2026-04-06T10:00:30Z" }

// Client → Server
{ "type": "pong", "timestamp": "2026-04-06T10:00:30Z" }
```

> 멀티플렉싱이므로 session_id 불필요 — 연결 자체가 AE 단위.

### 2.3 제어 명령 (Client → Server)

```json
// 일시정지 (사용자가 pause 버튼 클릭)
{ "type": "control_pause", "session_id": "session_001", "data": { "reason": "중간 결과 확인" } }

// 재개
{ "type": "control_resume", "session_id": "session_001", "data": {} }

// 취소
{ "type": "control_cancel", "session_id": "session_001", "data": { "reason": "사용자 취소" } }

// Todo 건너뜀
{ "type": "control_skip", "session_id": "session_001", "data": { "todo_id": "todo_003", "reason": "불필요" } }
```

> POC 제외: `control_retry` (재시도 미지원)

**제어 명령 서버 사이드 검증:**

| 명령 | 허용 조건 | 에러 |
|------|-----------|------|
| `control_pause` | 세션 status = `running` | `SESSION_INVALID_STATE` |
| `control_resume` | 세션 status = `paused` | `SESSION_INVALID_STATE` |
| `control_cancel` | 세션 status ∈ {created, running, paused} | `SESSION_INVALID_STATE` |
| `control_skip` | todo.status ∈ {pending, blocked, needs_approval} | `EXECUTION_INVALID_STATE` |

**pause 시 동작:**
1. 현재 실행 중인 Todo가 완료될 때까지 대기 (즉시 중단 아님)
2. 완료 후 다음 Todo 실행을 보류
3. SessionStatus → `paused`, PlanStatus → `paused`
4. 사용자에게 현재까지의 step_preview + 중간 결과 표시
5. `control_resume` 수신 시 다음 Todo부터 이어서 실행

### 2.4 화면 컨텍스트 전달 (Client → Server)

> 화면의 버튼 클릭이 채팅을 열고 컨텍스트를 자동 전달하는 구조.
> 일반 채팅 메시지(`send_message`)와 별도 타입으로 분리 — cognitive_node에서 별도 핸들러로 처리.

```json
{
  "type": "screen_context",
  "session_id": "session_001",
  "data": {
    "from_screen": "소재분석",
    "action": "소재_교체_요청",
    "target": "M-04",
    "context_data": {
      "campaign_id": "camp_001",
      "creative_id": "cr_042",
      "current_ctr": 1.2,
      "period": "2026-03-01~2026-03-31"
    },
    "client": "블루밤글로우",
    "user": "김대한"
  }
}
```

**필드 설명:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `from_screen` | string | O | 트리거한 화면 ("소재분석", "대시보드", "트렌드분석", "비용최적화", "리포트") |
| `action` | string | O | 수행 요청 ("소재_교체_요청", "리포트_생성", "AI_소재_생성_시작" 등) |
| `target` | string | X | 대상 ID (소재 ID, 캠페인 ID 등) |
| `context_data` | object | O | 화면별 맥락 정보 (캠페인/소재/기간 등) |
| `client` | string | O | 광고주명 |
| `user` | string | O | AE 이름 |

**처리 흐름:**
1. FE: 화면 버튼 클릭 → 채팅 패널 열림 + `screen_context` 메시지 전송
2. BE: cognitive_node가 `user_input` + `screen_context`를 함께 받아 의도 해석
3. BE: `screen_context.action`과 `context_data`를 기반으로 적합한 에이전트/시나리오 선택

---

## 3. 채널 2: HITL 제어 채널 (`ws/hitl`)

### 3.1 연결

```
ws://host/ws/hitl?user_id=550e8400-e29b-41d4-a716-446655440000
```

### 3.2 HITL 멀티세션 큐잉

```
AE가 채팅 3개를 동시에 실행 중일 때,
여러 세션에서 HITL 요청이 동시에 발생할 수 있다.

서버는 priority 순으로 큐잉하여 하나씩 FE에 전달:
  1. urgent (0) → 즉시 전달
  2. high (1)
  3. medium (2)
  4. low (3)

같은 priority면 requested_at 순 (먼저 요청된 것 우선).
FE는 현재 표시 중인 HITL이 있으면 다음 요청을 큐에 보관.
```

---

## 4. 공통 메시지 포맷

```typescript
interface BaseMessage {
  type:        string;       // 이벤트 타입
  session_id:  string;       // ★ 어떤 채팅방의 이벤트인지 (멀티플렉싱 핵심)
  message_id?: string;       // 스트리밍 채널만 — 재연결 resume에 활용
  timestamp:   string;       // ISO 8601
  data?:       any;
}
```

> 모든 메시지에 `session_id` 필수 — FE 메시지 라우터가 이 값으로 해당 채팅방에 분배.

---

## 5. 스트리밍 채널 이벤트 상세

### 5.1 Pipeline 이벤트

#### workflow_started

```json
{
  "type": "workflow_started",
  "session_id": "session_001",
  "message_id": "sess001_1",
  "timestamp": "2026-04-06T10:00:00Z",
  "data": {
    "user_input": "네이버 트렌드 분석해줘",
    "client_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### layer_start / layer_complete

```json
{
  "type": "layer_start",
  "session_id": "session_001",
  "message_id": "sess001_2",
  "timestamp": "2026-04-06T10:00:01Z",
  "data": {
    "layer": "cognitive",
    "description": "의도 분석 시작"
  }
}
```

```json
{
  "type": "layer_complete",
  "session_id": "session_001",
  "message_id": "sess001_3",
  "timestamp": "2026-04-06T10:00:02Z",
  "data": {
    "layer": "cognitive",
    "result": { "agent": "collection_agent", "confidence": 0.92 },
    "duration_ms": 1200,
    "next_layer": "planning"
  }
}
```

#### plan_generated / plan_approved

```json
{
  "type": "plan_generated",
  "session_id": "session_001",
  "message_id": "sess001_4",
  "timestamp": "2026-04-06T10:00:03Z",
  "data": {
    "plan_id": "plan_uuid_001",
    "version": 1,
    "status": "pending_approval",
    "strategy": "sequential",
    "todos": [
      { "id": "todo_001", "task": "네이버 데이터 수집", "tool": "naver_collector", "status": "pending", "priority": 1, "depends_on": [] },
      { "id": "todo_002", "task": "텍스트 전처리", "tool": "text_preprocessor", "status": "pending", "priority": 2, "depends_on": ["todo_001"] },
      { "id": "todo_003", "task": "키워드 추출", "tool": "keyword_extractor", "status": "pending", "priority": 3, "depends_on": ["todo_002"] },
      { "id": "todo_004", "task": "트렌드 분석", "tool": "trend_detector", "status": "pending", "priority": 4, "depends_on": ["todo_003"] },
      { "id": "todo_005", "task": "인사이트 도출", "tool": "insight_extractor", "status": "pending", "priority": 5, "depends_on": ["todo_004"] }
    ],
    "dependency_graph": {
      "todo_001": [], "todo_002": ["todo_001"], "todo_003": ["todo_002"],
      "todo_004": ["todo_003"], "todo_005": ["todo_004"]
    },
    "estimated_duration_sec": 120
  }
}
```

#### plan_approved

```json
{
  "type": "plan_approved",
  "session_id": "session_001",
  "message_id": "sess001_5",
  "timestamp": "2026-04-06T10:00:05Z",
  "data": {
    "plan_id": "plan_uuid_001",
    "approved_by": "user"
  }
}
```

### 5.2 Execution 이벤트

#### todo_started / todo_completed / todo_failed

```json
{
  "type": "todo_started",
  "session_id": "session_001",
  "message_id": "sess001_6",
  "timestamp": "2026-04-06T10:00:10Z",
  "data": {
    "todo_id": "todo_001",
    "task": "네이버 데이터 수집",
    "tool": "naver_collector",
    "status": "in_progress",
    "estimated_duration_sec": 30
  }
}
```

```json
{
  "type": "todo_completed",
  "session_id": "session_001",
  "message_id": "sess001_7",
  "timestamp": "2026-04-06T10:00:40Z",
  "data": {
    "todo_id": "todo_001",
    "task": "네이버 데이터 수집",
    "status": "completed",
    "result_summary": { "collected_count": 142, "period": "30d" },
    "duration_ms": 30000,
    "next_todos": ["todo_002"]
  }
}
```

```json
{
  "type": "todo_failed",
  "session_id": "session_001",
  "message_id": "sess001_err",
  "timestamp": "2026-04-06T10:00:45Z",
  "data": {
    "todo_id": "todo_001",
    "task": "네이버 데이터 수집",
    "status": "failed",
    "error": {
      "code": "TOOL_TIMEOUT",
      "message": "네이버 API 응답 시간 초과"
    }
  }
}
```

> POC: `retry_count`/`max_retries` 없음 — failed는 즉시 final.

### 5.3 Step Preview 이벤트 ★ POC 신규

```json
{
  "type": "step_preview",
  "session_id": "session_001",
  "message_id": "sess001_8",
  "timestamp": "2026-04-06T10:00:41Z",
  "data": {
    "todo_id": "todo_001",
    "tool": "naver_collector",
    "group": "수집",
    "step_index": 0,
    "total_steps": 5,
    "preview_type": "data_sample",
    "title": "네이버 데이터 수집 완료",
    "summary": "142건 수집, 최근 30일",
    "data": {
      "count": 142,
      "sample": [
        { "title": "여름 쿨링 제품 트렌드", "url": "https://...", "date": "2026-04-05" },
        { "title": "반려동물 쿨링매트 인기", "url": "https://...", "date": "2026-04-04" },
        { "title": "쿨링펫 신제품 출시 반응", "url": "https://...", "date": "2026-04-03" }
      ],
      "period": "30d"
    }
  }
}
```

> `step_preview`는 `todo_completed` 직후에 전송된다.
> FE는 이 이벤트를 받으면 해당 채팅방에 미리보기 카드를 렌더링한다.

**Tool별 step_preview 예시:**

```json
// keyword_extractor 완료 후
{
  "type": "step_preview",
  "session_id": "session_001",
  "data": {
    "tool": "keyword_extractor",
    "group": "ML",
    "step_index": 2,
    "total_steps": 5,
    "preview_type": "text",
    "title": "키워드 추출 완료",
    "summary": "상위 키워드 10개 추출",
    "data": {
      "keywords": ["쿨링매트", "반려동물", "여름", "CPC", "전환율",
                    "네이버쇼핑", "쿨링젤", "펫케어", "할인", "신제품"],
      "count": 10
    }
  }
}
```

```json
// ad_image_generator 완료 후
{
  "type": "step_preview",
  "session_id": "session_002",
  "data": {
    "tool": "ad_image_generator",
    "group": "이미지",
    "step_index": 1,
    "total_steps": 2,
    "preview_type": "image",
    "title": "광고 이미지 생성 완료",
    "summary": "2장 생성",
    "data": {
      "images": [
        { "url": "/api/v1/files/session_002/img_001.png", "width": 1080, "height": 1080 },
        { "url": "/api/v1/files/session_002/img_002.png", "width": 1200, "height": 628 }
      ],
      "count": 2
    }
  }
}
```

### 5.4 LLM Token 스트리밍

```json
{
  "type": "token_stream",
  "session_id": "session_001",
  "message_id": "sess001_20",
  "timestamp": "2026-04-06T10:01:30Z",
  "data": {
    "token": "네이버",
    "accumulated_text": "네이버",
    "layer": "response"
  }
}
```

### 5.5 완료/실패

#### complete

```json
{
  "type": "complete",
  "session_id": "session_001",
  "message_id": "sess001_final",
  "timestamp": "2026-04-06T10:02:00Z",
  "data": {
    "status": "success",
    "response": {
      "format": "mixed",
      "text": "네이버 트렌드 분석 결과입니다...",
      "summary": "쿨링매트 키워드 급상승, 전월 대비 142% 증가",
      "attachments": [],
      "step_previews": ["preview_001", "preview_002", "preview_003", "preview_004", "preview_005"]
    },
    "statistics": {
      "total_todos": 5,
      "completed": 5,
      "failed": 0,
      "execution_time_ms": 120000
    }
  }
}
```

> `step_previews`에 미리보기 ID 목록 포함 — FE가 스크롤 시 참조 가능.

#### failed

```json
{
  "type": "failed",
  "session_id": "session_001",
  "message_id": "sess001_fail",
  "timestamp": "2026-04-06T10:01:00Z",
  "data": {
    "status": "failed",
    "error": {
      "code": "TOOL_TIMEOUT",
      "message": "naver_collector 실행 시간 초과"
    },
    "partial_results": null
  }
}
```

### 5.6 Error (비치명적)

```json
{
  "type": "error",
  "session_id": "session_001",
  "message_id": "sess001_warn",
  "timestamp": "2026-04-06T10:00:50Z",
  "data": {
    "code": "LLM_SERVICE_ERROR",
    "message": "LLM 응답 지연 — 재시도 없이 진행"
  }
}
```

### 5.7 Session Paused / Resumed

```json
{
  "type": "session_paused",
  "session_id": "session_001",
  "message_id": "sess001_pause",
  "timestamp": "2026-04-06T10:01:00Z",
  "data": {
    "reason": "중간 결과 확인",
    "current_todo_id": "todo_003",
    "completed_todos": ["todo_001", "todo_002"],
    "step_previews_so_far": 2
  }
}
```

```json
{
  "type": "session_resumed",
  "session_id": "session_001",
  "message_id": "sess001_resume",
  "timestamp": "2026-04-06T10:03:00Z",
  "data": {
    "next_todo_id": "todo_003"
  }
}
```

> pause 시 현재 실행 중인 Todo는 완료까지 진행한 후 정지.
> resume 시 다음 대기 중인 Todo부터 실행 재개.

### 5.8 Session Deleted ★ POC

```json
{
  "type": "session_deleted",
  "session_id": "session_001",
  "message_id": "sess001_del",
  "timestamp": "2026-04-06T10:05:00Z",
  "data": {
    "reason": "user_deleted"
  }
}
```

> 채팅방이 삭제되면 실행 중인 작업을 자동 취소하고 이 이벤트를 전송한다.
> FE는 해당 session_id의 Redux store를 정리하고 채팅방 목록에서 제거한다.

### 5.8 Control ACK

```json
{
  "type": "control_ack",
  "session_id": "session_001",
  "message_id": "sess001_ack",
  "timestamp": "2026-04-06T10:00:05Z",
  "data": {
    "command": "control_skip",
    "success": true,
    "todo_id": "todo_003",
    "error": null
  }
}
```

### 5.9 메모리 압축 완료 이벤트 ★ POC 신규

```json
{
  "type": "memory_compressed",
  "session_id": "session_001",
  "message_id": "sess001_mem",
  "timestamp": "2026-04-06T10:02:05Z",
  "data": {
    "long_term_memory_id": "ltm_uuid_001",
    "summary": "쿨링펫 네이버 트렌드 분석 — 쿨링매트 키워드 급상승, 전월 대비 142% 증가",
    "key_insights": [
      "쿨링매트 키워드가 전월 대비 142% 급상승",
      "주요 채널: 네이버 블로그, 네이버 쇼핑",
      "경쟁 키워드: 쿨링젤, 펫케어"
    ]
  }
}
```

> 세션 완료 후 장기 기억 압축이 끝나면 전송. FE에서 "기억 저장됨" 토스트 표시.

---

## 6. HITL 채널 이벤트 상세

### 6.1 Server → Client: HITL 요청

#### hitl_plan_review

```json
{
  "type": "hitl_plan_review",
  "session_id": "session_001",
  "timestamp": "2026-04-06T10:00:04Z",
  "data": {
    "request_id": "hitl_uuid_001",
    "type": "plan_review",
    "title": "실행 계획을 검토해주세요.",
    "description": "네이버 트렌드 분석을 위한 5단계 실행 계획입니다.",
    "priority": "medium",
    "plan": {
      "plan_id": "plan_uuid_001",
      "todos": [
        { "id": "todo_001", "task": "네이버 데이터 수집", "tool": "naver_collector" },
        { "id": "todo_002", "task": "텍스트 전처리", "tool": "text_preprocessor" },
        { "id": "todo_003", "task": "키워드 추출", "tool": "keyword_extractor" },
        { "id": "todo_004", "task": "트렌드 분석", "tool": "trend_detector" },
        { "id": "todo_005", "task": "인사이트 도출", "tool": "insight_extractor" }
      ],
      "estimated_duration_sec": 120
    },
    "options": ["approve", "modify", "reject"],
    "wait_minutes": 5
  }
}
```

#### hitl_approval_request

```json
{
  "type": "hitl_approval_request",
  "session_id": "session_002",
  "timestamp": "2026-04-06T10:00:10Z",
  "data": {
    "request_id": "hitl_uuid_002",
    "type": "approval",
    "title": "이미지 생성 승인",
    "description": "광고 이미지 2장을 생성합니다.",
    "priority": "low",
    "todo": {
      "id": "todo_010",
      "task": "광고 이미지 생성",
      "tool": "ad_image_generator"
    },
    "options": ["approve", "skip", "reject"],
    "wait_minutes": 5
  }
}
```

#### hitl_clarification_request

```json
{
  "type": "hitl_clarification_request",
  "session_id": "session_003",
  "timestamp": "2026-04-06T10:00:03Z",
  "data": {
    "request_id": "hitl_uuid_003",
    "type": "clarification",
    "title": "분석 대상을 선택해주세요",
    "description": "의도가 불명확하여 분석 대상을 확인합니다.",
    "priority": "medium",
    "input_type": "choice",
    "options": ["네이버 트렌드", "유튜브 트렌드", "광고 성과", "이미지 생성"],
    "original_input": "분석해줘",
    "ambiguity": "분석 대상이 명시되지 않았습니다.",
    "wait_minutes": 5
  }
}
```

> ※ `original_input`, `ambiguity`는 HITLRequest.data에서 flat하게 펼쳐짐 (data.data 중첩 방지)

#### hitl_input_request

```json
{
  "type": "hitl_input_request",
  "session_id": "session_001",
  "timestamp": "2026-04-06T10:00:15Z",
  "data": {
    "request_id": "hitl_uuid_005",
    "type": "input",
    "title": "분석 기간을 선택해주세요",
    "description": "분석할 기간을 선택하면 해당 기간의 데이터로 실행합니다.",
    "priority": "low",
    "input_type": "choice",
    "options": ["7d", "30d", "90d"],
    "field": "date_range",
    "default_value": "30d",
    "labels": { "7d": "최근 7일", "30d": "최근 30일", "90d": "최근 3개월" },
    "wait_minutes": 5
  }
}
```

### 6.2 Client → Server: HITL 응답

```json
// Plan 승인
{
  "type": "hitl_plan_response",
  "session_id": "session_001",
  "data": {
    "request_id": "hitl_uuid_001",
    "action": "approve",
    "comment": "계획 승인"
  }
}
```

```json
// 명확화 응답
{
  "type": "hitl_clarification_response",
  "session_id": "session_003",
  "data": {
    "request_id": "hitl_uuid_003",
    "action": "approve",
    "value": "네이버 트렌드"
  }
}
```

```json
// 사용자 입력 응답
{
  "type": "hitl_input_response",
  "session_id": "session_001",
  "data": {
    "request_id": "hitl_uuid_005",
    "action": "approve",
    "value": "30d"
  }
}
```

> clarification/input 응답의 `action: "approve"`는 "사용자가 요청된 정보를 제공함"을 의미한다.

### 6.3 HITL 응답 ACK

```json
{
  "type": "hitl_response_ack",
  "session_id": "session_001",
  "timestamp": "2026-04-06T10:01:00Z",
  "data": {
    "request_id": "hitl_uuid_001",
    "action": "approve",
    "success": true
  }
}
```

### 6.4 HITL 타임아웃

```json
{
  "type": "hitl_timeout",
  "session_id": "session_001",
  "timestamp": "2026-04-06T10:05:00Z",
  "data": {
    "request_id": "hitl_uuid_001",
    "default_action": "approve",
    "wait_minutes": 5
  }
}
```

---

## 7. 연결 관리 및 재연결

### 7.1 재연결 — 멀티세션 resume

```
기존: resume_from=msg_042 (단일 세션)

POC (멀티플렉싱): 세션별 last_message_id를 복수 전달
```

```
ws://host/ws/stream?user_id={uuid}
  → auth 메시지 전송
  → resume 메시지 전송:

{
  "type": "resume",
  "data": {
    "sessions": {
      "session_001": "sess001_7",     // 이 세션은 msg_7까지 받음
      "session_002": "sess002_3",     // 이 세션은 msg_3까지 받음
      "session_003": null             // 이 세션은 아직 이벤트 못 받음
    }
  }
}
```

> 서버는 각 세션별로 누락된 메시지를 재전송.
> `null`이면 해당 세션의 모든 버퍼 메시지 전송.

### 7.2 Heartbeat 미응답

```
pong 미수신 2회 연속 → 서버가 close(4408, "ping timeout")
클라이언트 자동 재연결 (exponential backoff: 1s → 2s → 4s → 8s → max 30s)
```

### 7.3 Close Codes

| Code | 의미 | FE 대응 |
|------|------|---------|
| 1000 | 정상 종료 | — |
| 4401 | Unauthorized (auth 5초 초과) | 로그인 페이지 이동 |
| 4403 | Forbidden (JWT 무효) | 토큰 갱신 후 재연결 |
| 4408 | Ping timeout | 자동 재연결 |
| 4500 | Server error | 재연결 + 에러 표시 |

---

## 8. 시나리오

### 8.1 시나리오 A: 데이터 분석 (채팅 A에서)

```
ws/stream (AE 공유):

  workflow_started      { session_id: "session_001", ... }
  layer_start           { session_id: "session_001", layer: "cognitive" }
  layer_complete        { session_id: "session_001", layer: "cognitive", next: "planning" }
  plan_generated        { session_id: "session_001", todos: [5개] }

ws/hitl (AE 공유):

  hitl_plan_review      { session_id: "session_001", priority: "medium" }
  ← hitl_plan_response  { session_id: "session_001", action: "approve" }
  → hitl_response_ack   { session_id: "session_001", success: true }

ws/stream:

  plan_approved         { session_id: "session_001" }
  layer_start           { session_id: "session_001", layer: "execution" }
  todo_started          { session_id: "session_001", tool: "naver_collector" }
  todo_completed        { session_id: "session_001", tool: "naver_collector" }
  step_preview          { session_id: "session_001", tool: "naver_collector", preview_type: "data_sample" }
  todo_started          { session_id: "session_001", tool: "text_preprocessor" }
  todo_completed        { session_id: "session_001" }
  step_preview          { session_id: "session_001", tool: "text_preprocessor", preview_type: "statistics" }
  ... (keyword_extractor, trend_detector, insight_extractor 동일 패턴)
  layer_complete        { session_id: "session_001", layer: "execution" }
  layer_start           { session_id: "session_001", layer: "response" }
  token_stream × N      { session_id: "session_001" }
  complete              { session_id: "session_001", step_previews: [5개] }
  memory_compressed     { session_id: "session_001", summary: "..." }
```

### 8.2 시나리오 B: 채팅 2개 동시 실행 (HITL 큐잉)

```
AE가 채팅 A(데이터 분석)와 채팅 B(이미지 생성)를 동시 실행

ws/stream:
  workflow_started  { session_id: "session_001" }  // 채팅 A
  workflow_started  { session_id: "session_002" }  // 채팅 B
  ... (두 세션의 이벤트가 섞여서 도착 — FE가 session_id로 분배)

ws/hitl:
  // 두 세션에서 동시에 HITL 발생
  hitl_plan_review       { session_id: "session_001", priority: "medium" }
  hitl_approval_request  { session_id: "session_002", priority: "urgent" }

  // FE: priority 기준으로 session_002(urgent)를 먼저 표시
  // AE가 session_002 승인 → session_001 검토 순서로 처리
```

---

## 9. 백엔드 구현

### 9.1 ConnectionManager — User 기반

```python
from fastapi import WebSocket
from typing import Dict, Optional
import redis.asyncio as aioredis

class ConnectionManager:
    """멀티플렉싱 ConnectionManager — user_id 기반

    기존: session_id → Set[WebSocket]
    POC: user_id → WebSocket (AE당 1개씩)
    """
    def __init__(self, redis_url: str = None):
        self.stream_connections: Dict[str, WebSocket] = {}   # user_id → WS
        self.hitl_connections: Dict[str, WebSocket] = {}     # user_id → WS
        self.redis = aioredis.from_url(redis_url) if redis_url else None

    async def connect_stream(self, user_id: str, websocket: WebSocket):
        # 기존 연결이 있으면 교체 (탭 전환 등)
        old = self.stream_connections.get(user_id)
        if old:
            try:
                await old.close(code=1000, reason="replaced")
            except Exception:
                pass
        self.stream_connections[user_id] = websocket

    async def connect_hitl(self, user_id: str, websocket: WebSocket):
        old = self.hitl_connections.get(user_id)
        if old:
            try:
                await old.close(code=1000, reason="replaced")
            except Exception:
                pass
        self.hitl_connections[user_id] = websocket

    async def send_to_user_stream(self, user_id: str, message: dict):
        """특정 AE의 stream 채널로 메시지 전송"""
        ws = self.stream_connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                del self.stream_connections[user_id]

    async def send_to_user_hitl(self, user_id: str, message: dict):
        """특정 AE의 hitl 채널로 메시지 전송"""
        ws = self.hitl_connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                del self.hitl_connections[user_id]
```

### 9.2 WebSocket 엔드포인트

```python
from fastapi import WebSocket, WebSocketDisconnect, Query

@router.websocket("/ws/stream")
async def stream_endpoint(
    websocket: WebSocket,
    user_id: str = Query(...),
):
    await websocket.accept()

    # 인증 (5초 내 auth 메시지 필수)
    auth_result = await authenticate_ws(websocket, timeout=5)
    if not auth_result:
        await websocket.close(code=4401, reason="auth timeout")
        return

    await manager.connect_stream(user_id, websocket)

    # resume 처리 (멀티세션)
    try:
        first_msg = await asyncio.wait_for(websocket.receive_json(), timeout=3)
        if first_msg.get("type") == "resume":
            await handle_resume(user_id, first_msg["data"]["sessions"], websocket)
    except asyncio.TimeoutError:
        pass  # resume 없으면 그냥 진행

    try:
        while True:
            data = await websocket.receive_json()
            await handle_stream_message(user_id, data, manager)
    except WebSocketDisconnect:
        del manager.stream_connections[user_id]


@router.websocket("/ws/hitl")
async def hitl_endpoint(
    websocket: WebSocket,
    user_id: str = Query(...),
):
    await websocket.accept()

    auth_result = await authenticate_ws(websocket, timeout=5)
    if not auth_result:
        await websocket.close(code=4401, reason="auth timeout")
        return

    await manager.connect_hitl(user_id, websocket)

    # 대기 중인 HITL 요청 전송 (priority 순)
    await send_pending_hitl_requests(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await handle_hitl_message(user_id, data, manager)
    except WebSocketDisconnect:
        del manager.hitl_connections[user_id]
```

### 9.3 CallbackHandler — POC

```python
class WebSocketCallbackHandler:
    """LangGraph 콜백 — 멀티플렉싱 환경

    user_id로 AE를 식별하고, session_id로 채팅방을 구분한다.
    모든 이벤트에 session_id를 포함하여 FE 라우터가 분배할 수 있도록 한다.
    """
    def __init__(self, session_id: str, user_id: str, client_id: str,
                 manager: ConnectionManager):
        self.session_id = session_id
        self.user_id = user_id
        self.client_id = client_id
        self.manager = manager
        self._msg_counter = 0

    def _next_msg_id(self) -> str:
        self._msg_counter += 1
        return f"{self.session_id[:8]}_{self._msg_counter}"

    def _now(self) -> str:
        # from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    async def _send_stream(self, event_type: str, data: dict):
        """stream 채널로 전송 — user_id 기반"""
        await self.manager.send_to_user_stream(self.user_id, {
            "type": event_type,
            "session_id": self.session_id,
            "message_id": self._next_msg_id(),
            "timestamp": self._now(),
            "data": data,
        })

    async def _send_hitl(self, event_type: str, data: dict):
        """hitl 채널로 전송 — user_id 기반"""
        await self.manager.send_to_user_hitl(self.user_id, {
            "type": event_type,
            "session_id": self.session_id,
            "timestamp": self._now(),
            "data": data,
        })

    # ─── Pipeline 이벤트 ───

    async def on_workflow_started(self, user_input: str):
        await self._send_stream("workflow_started", {
            "user_input": user_input,
            "client_id": self.client_id,
        })

    async def on_layer_start(self, layer: str):
        DESCRIPTIONS = {
            "cognitive": "의도 분석 시작",
            "planning": "실행 계획 수립",
            "execution": "Tool 실행",
            "response": "응답 생성",
        }
        await self._send_stream("layer_start", {
            "layer": layer,
            "description": DESCRIPTIONS.get(layer, ""),
        })

    async def on_layer_complete(self, layer: str, result: dict,
                                 next_layer: str = None, duration_ms: float = 0):
        data = {"layer": layer, "result": result, "duration_ms": duration_ms}
        if next_layer:
            data["next_layer"] = next_layer
        await self._send_stream("layer_complete", data)

    async def on_plan_generated(self, plan: "Plan"):
        plan_dict = plan.model_dump(by_alias=True)
        plan_dict["todos"] = [
            {"id": t["id"], "task": t["task"], "tool": t["tool"],
             "status": t["status"], "priority": t.get("priority", 5),
             "depends_on": t.get("depends_on", [])}
            for t in plan_dict.get("todos", [])
        ]
        await self._send_stream("plan_generated", plan_dict)

    async def on_plan_approved(self, plan_id: str, approved_by: str = "user"):
        await self._send_stream("plan_approved", {
            "plan_id": plan_id,
            "approved_by": approved_by,
        })

    # ─── Execution 이벤트 ───

    async def on_todo_started(self, todo_id: str, task: str, tool: str,
                               estimated_duration_sec: int = 300):
        await self._send_stream("todo_started", {
            "todo_id": todo_id, "task": task, "tool": tool,
            "status": "in_progress",
            "estimated_duration_sec": estimated_duration_sec,
        })

    async def on_todo_completed(self, todo_id: str, task: str,
                                 result_summary: dict, next_todos: list,
                                 duration_ms: float = 0):
        await self._send_stream("todo_completed", {
            "todo_id": todo_id, "task": task, "status": "completed",
            "result_summary": result_summary,
            "duration_ms": duration_ms,
            "next_todos": next_todos,
        })

    async def on_todo_failed(self, todo_id: str, task: str, error: dict):
        await self._send_stream("todo_failed", {
            "todo_id": todo_id, "task": task, "status": "failed",
            "error": error,
        })

    # ─── Step Preview ★ ───

    async def on_step_preview(self, preview: dict):
        """단계별 미리보기 → stream 채널. todo_completed 직후 호출."""
        await self._send_stream("step_preview", preview)

    # ─── HITL ───

    async def on_hitl_request(self, hitl_request: dict):
        hitl_type = hitl_request.get("type")
        event_map = {
            "plan_review":    "hitl_plan_review",
            "approval":       "hitl_approval_request",
            "clarification":  "hitl_clarification_request",
            "input":          "hitl_input_request",
        }
        event_type = event_map.get(hitl_type, "hitl_request")

        payload = {**hitl_request}
        if hitl_type in ("clarification", "input"):
            inner_data = payload.pop("data", {})
            payload.update(inner_data)

        await self._send_hitl(event_type, payload)

    # ─── Token / Complete / Failed ───

    async def on_token_stream(self, token: str, accumulated: str):
        await self._send_stream("token_stream", {
            "token": token,
            "accumulated_text": accumulated,
            "layer": "response",
        })

    async def on_complete(self, response: dict, statistics: dict):
        await self._send_stream("complete", {
            "status": "success",
            "response": response,
            "statistics": statistics,
        })

    async def on_failed(self, error: dict):
        await self._send_stream("failed", {
            "status": "failed",
            "error": error,
            "partial_results": None,
        })

    # ─── Memory ───

    async def on_memory_compressed(self, memory: dict):
        """장기 기억 압축 완료 → stream 채널"""
        await self._send_stream("memory_compressed", memory)

    # ─── Control ACK ───

    async def on_control_ack(self, command: str, success: bool,
                              todo_id: str = None, error: dict = None):
        await self._send_stream("control_ack", {
            "command": command,
            "success": success,
            "todo_id": todo_id,
            "error": error,
        })

    # ─── Pause / Resume ───

    async def on_session_paused(self, reason: str, current_todo_id: str,
                                 completed_todos: list, previews_count: int):
        """사용자 pause → stream 채널. 현재 Todo 완료 후 정지."""
        await self._send_stream("session_paused", {
            "reason": reason,
            "current_todo_id": current_todo_id,
            "completed_todos": completed_todos,
            "step_previews_so_far": previews_count,
        })

    async def on_session_resumed(self, next_todo_id: str):
        """사용자 resume → stream 채널. 다음 Todo부터 재개."""
        await self._send_stream("session_resumed", {
            "next_todo_id": next_todo_id,
        })
```

---

## 10. 프론트엔드 통합

### 10.1 메시지 라우터

```typescript
// FE: 멀티플렉싱 메시지 라우터
const streamSocket = new WebSocket(`ws://host/ws/stream?user_id=${userId}`);

streamSocket.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  // auth_success는 인라인 처리
  if (msg.type === "auth_success") return;
  if (msg.type === "ping") { streamSocket.send(JSON.stringify({ type: "pong" })); return; }

  const sessionId = msg.session_id;

  // 해당 채팅방 컴포넌트로 라우팅
  const handler = streamMessageHandlers[msg.type];
  if (handler) {
    handler(sessionId, msg.data);
  }

  // 현재 보고 있는 채팅방이 아니면 배지 업데이트
  if (sessionId !== currentActiveSession) {
    store.dispatch(incrementUnreadBadge(sessionId));
  }
};
```

### 10.2 Stream 핸들러 맵

```typescript
const streamMessageHandlers: Record<string, (sessionId: string, data: any) => void> = {
  workflow_started:   (sid, d) => store.dispatch(setWorkflowStarted({ sessionId: sid, ...d })),
  layer_start:        (sid, d) => store.dispatch(setLayerStart({ sessionId: sid, ...d })),
  layer_complete:     (sid, d) => store.dispatch(setLayerComplete({ sessionId: sid, ...d })),
  plan_generated:     (sid, d) => store.dispatch(setPlan({ sessionId: sid, ...d })),
  plan_approved:      (sid, d) => store.dispatch(setPlanApproved({ sessionId: sid, ...d })),
  todo_started:       (sid, d) => store.dispatch(updateTodo({ sessionId: sid, ...d })),
  todo_completed:     (sid, d) => store.dispatch(updateTodo({ sessionId: sid, ...d })),
  todo_failed:        (sid, d) => store.dispatch(updateTodo({ sessionId: sid, ...d })),
  step_preview:       (sid, d) => store.dispatch(addStepPreview({ sessionId: sid, ...d })),
  token_stream:       (sid, d) => store.dispatch(appendToken({ sessionId: sid, token: d.token })),
  complete:           (sid, d) => store.dispatch(setComplete({ sessionId: sid, ...d })),
  failed:             (sid, d) => store.dispatch(setFailed({ sessionId: sid, ...d })),
  error:              (sid, d) => store.dispatch(addError({ sessionId: sid, ...d })),
  control_ack:        (sid, d) => { if (!d.success) showToast(`명령 실패: ${d.error?.message}`); },
  session_paused:     (sid, d) => { store.dispatch(setSessionPaused({ sessionId: sid, ...d })); showToast("작업이 일시정지되었습니다"); },
  session_resumed:    (sid, d) => { store.dispatch(setSessionResumed({ sessionId: sid, ...d })); },
  memory_compressed:  (sid, d) => { store.dispatch(setMemoryCompressed({ sessionId: sid, ...d })); showToast("기억 저장됨"); },
  session_deleted:    (sid, d) => {
    const state = store.getState();
    const wasActive = state.activeSessionId === sid;
    store.dispatch(removeSession(sid));
    if (wasActive) {
      // 현재 보고 있던 방이 삭제되면 다른 방으로 자동 전환
      const remaining = Object.keys(state.sessions).filter(id => id !== sid);
      if (remaining.length > 0) {
        // last_active_at 기준 가장 최근 방으로 전환
        const next = remaining.sort((a, b) =>
          state.sessions[b].lastAccessedAt - state.sessions[a].lastAccessedAt
        )[0];
        store.dispatch(setActiveSession(next));
      } else {
        store.dispatch(setActiveSession(null));  // 빈 상태 + "새 채팅" 유도
      }
    }
    showToast("채팅방이 삭제되었습니다");
  },
};
```

### 10.3 HITL 핸들러 맵

```typescript
const hitlMessageHandlers: Record<string, (sessionId: string, data: any) => void> = {
  hitl_plan_review:          (sid, d) => { store.dispatch(addHitlRequest({ sessionId: sid, ...d })); showHitlModal(sid, d); },
  hitl_approval_request:     (sid, d) => { store.dispatch(addHitlRequest({ sessionId: sid, ...d })); showApprovalModal(sid, d); },
  hitl_clarification_request:(sid, d) => { store.dispatch(addHitlRequest({ sessionId: sid, ...d })); showClarificationModal(sid, d); },
  hitl_input_request:        (sid, d) => { store.dispatch(addHitlRequest({ sessionId: sid, ...d })); showInputModal(sid, d); },
  hitl_response_ack:         (sid, d) => { if (!d.success) showToast("HITL 응답 실패"); },
  hitl_timeout:              (sid, d) => { store.dispatch(clearHitlRequest(sid, d.request_id)); showToast(`시간 초과 — ${d.default_action} 실행됨`); },
};
```

> 모든 핸들러의 첫 번째 인자가 `sessionId` — 멀티플렉싱 핵심.

### 10.4 Redux Store 구조 (멀티세션)

```typescript
interface AppState {
  sessions: {
    [sessionId: string]: {
      status: string;
      currentLayer: string | null;
      plan: Plan | null;
      todos: TodoItem[];
      stepPreviews: StepPreview[];
      tokenBuffer: string;
      hitlPending: HITLRequest[];  // 배열 — 멀티세션이므로 복수 가능
      unreadCount: number;
    };
  };
  activeSessionId: string | null;
  longTermMemories: LongTermMemory[];
}
```

### 10.5 방 전환 시 로딩 전략

> AE가 방A → 방B로 전환할 때의 표준 패턴.
> **REST = 히스토리 조회**, **WS = 새 메시지 수신** 역할 분담.

```typescript
// Redux store에 loaded 플래그를 두어 캐싱
// (10.4 AppState.sessions[sessionId]에 loaded: boolean 추가)

async function switchRoom(sessionId: string) {
  const session = store.getState().sessions[sessionId];

  // 1. 캐싱 확인 — 이미 불러온 방이면 API 호출 없이 바로 표시
  if (!session?.loaded) {
    // 2. REST로 메시지 히스토리 조회
    const res = await fetch(
      `/api/v1/chat/sessions/${sessionId}/messages?limit=50&offset=0`
    );
    const data = await res.json();
    store.dispatch(setSessionHistory({
      sessionId,
      messages: data.messages,
      loaded: true,
    }));
  }

  // 3. 활성 세션 전환 (이후 step_preview, token_stream 등은 WS로 자동 수신)
  store.dispatch(setActiveSession(sessionId));

  // 4. 미읽음 카운트 초기화
  store.dispatch(clearUnreadBadge(sessionId));

  // ※ WS 구독은 전략 B(전체 구독)이므로 별도 subscribe 불필요
  //    이미 user_id 기반으로 모든 세션 이벤트가 stream/hitl 채널에 들어옴
}
```

**캐싱 정책:**
- `loaded: false` → REST 호출 후 캐싱
- `loaded: true` → 즉시 표시 (API 호출 없음)
- 새 메시지가 WS로 들어오면 캐싱된 messages에 append

**메모리 관리:**

```typescript
const MAX_CACHED_ROOMS = 10;        // 채팅방 제한(§14.1)과 동일
const MAX_MESSAGES_PER_ROOM = 100;  // 방당 최대 캐싱 메시지 수

// 방별 메시지 수 제한 — 새 메시지 append 시 오래된 것 evict
function appendMessage(sessionId: string, message: any) {
  const session = chatState[sessionId];
  session.messages.push(message);

  if (session.messages.length > MAX_MESSAGES_PER_ROOM) {
    // 오래된 메시지 제거 — 최신 100개만 유지
    session.messages = session.messages.slice(-MAX_MESSAGES_PER_ROOM);
    session.hasOlderMessages = true;  // "이전 메시지 보기" 버튼 활성화
  }
}

// 방 수 제한은 서버에서 이미 10개로 제한되므로 FE LRU evict 불필요
// 단, 캐싱 상태는 비활성 방일수록 오래된 순으로 정리 가능
function cleanupInactiveRooms() {
  const rooms = Object.entries(chatState)
    .sort((a, b) => a[1].lastAccessedAt - b[1].lastAccessedAt);

  // 10개 초과 시 가장 오래된 것부터 messages만 비우고 loaded=false로
  if (rooms.length > MAX_CACHED_ROOMS) {
    const toEvict = rooms.slice(0, rooms.length - MAX_CACHED_ROOMS);
    for (const [sid, _] of toEvict) {
      chatState[sid].messages = [];
      chatState[sid].loaded = false;  // 재방문 시 REST로 다시 로드
    }
  }
}
```

**이전 메시지 조회:**
- `hasOlderMessages === true`면 사용자가 "이전 메시지 보기" 클릭 시
  `GET /api/v1/chat/sessions/{id}/messages?limit=50&offset=100` 호출하여 추가 로드

---

## 11. 보안

### 11.1 인증

```typescript
// 연결 후 첫 메시지로 인증
interface WsAuthMessage {
  type: "auth";
  data: { token: string; };
}

// 성공 응답
interface WsAuthSuccessMessage {
  type: "auth_success";
  data: { user_id: string; expires_at: string; };
}
```

| 규칙 | 설명 |
|------|------|
| 연결 후 5초 내 `auth` 필수 | 초과 시 close(4401) |
| `auth` 전 다른 메시지는 무시 | |
| JWT 검증 실패 시 close(4403) | |

### 11.2 채널 권한 검증 (Authorization)

> **모든 수신 메시지에 대해 `session_id` 접근 권한을 서버에서 반드시 검증한다.**
> user_id 기반 멀티플렉싱이지만, 악의적 클라이언트가 `{ session_id: "남의방" }` 메시지를
> 보낼 수 있으므로 **session_id별 소유권 체크가 필수**.

```python
async def verify_session_access(user_id: str, session_id: str) -> bool:
    """해당 AE가 해당 채팅방에 접근 권한이 있는지 DB 체크.

    chat_sessions.user_id == user_id 인지 확인.
    """
    session = await get_chat_session(session_id)
    return session is not None and session.user_id == user_id


async def handle_stream_message(user_id: str, data: dict, manager):
    """stream 채널 수신 메시지 처리 — 권한 검증 포함"""
    msg_type = data.get("type")
    session_id = data.get("session_id")

    if not msg_type:
        logger.warning("ws_missing_type", user_id=user_id)
        return

    # 권한 검증 — session_id가 있는 메시지는 반드시 소유권 체크
    if session_id and not await verify_session_access(user_id, session_id):
        await manager.send_to_user_stream(user_id, {
            "type": "error",
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "data": {
                "code": "CHANNEL_ACCESS_DENIED",
                "message": "해당 채팅방에 접근 권한이 없습니다.",
            }
        })
        logger.warning("ws_unauthorized_session", user_id=user_id, session_id=session_id)
        return

    # 이후 정상 처리
    ...
```

| 규칙 | 설명 |
|------|------|
| 모든 수신 메시지 | `session_id` 필드가 있으면 `verify_session_access()` 필수 |
| 권한 없음 | `error` 이벤트 전송 (`CHANNEL_ACCESS_DENIED`) — 연결은 유지 |
| 송신 메시지 | 서버가 생성하므로 별도 검증 불필요 (이미 권한 있는 세션의 이벤트만 전송) |

### 11.3 메시지 입력 검증

> 클라이언트가 보내는 WS 메시지는 **절대 그대로 신뢰하지 않는다.**
> XSS 방지, 크기 제한, 형식 검증을 서버에서 수행한다.

```python
import html
import re

# 메시지 크기 제한
MAX_WS_MESSAGE_BYTES = 1_048_576  # 1MB
MAX_TEXT_FIELD_LENGTH = 10_000    # 텍스트 필드당 최대 길이

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def validate_ws_message(raw: bytes, data: dict) -> tuple[bool, str]:
    """WS 메시지 검증 — 통과하면 (True, ''), 실패하면 (False, 에러메시지)"""
    # 1. 크기 제한
    if len(raw) > MAX_WS_MESSAGE_BYTES:
        return False, "message exceeds 1MB limit"

    # 2. 필수 필드
    if "type" not in data:
        return False, "missing type field"

    # 3. session_id 형식 검증 (있는 경우)
    session_id = data.get("session_id")
    if session_id:
        if not UUID_PATTERN.match(session_id.lower()):
            return False, "invalid session_id format"

    # 4. 텍스트 필드 XSS 이스케이프 + 길이 제한
    payload = data.get("data", {})
    if isinstance(payload, dict):
        for key in ("comment", "value", "instruction", "reason"):
            if key in payload and isinstance(payload[key], str):
                if len(payload[key]) > MAX_TEXT_FIELD_LENGTH:
                    return False, f"{key} exceeds {MAX_TEXT_FIELD_LENGTH} chars"
                # XSS 방지 — HTML 이스케이프
                payload[key] = html.escape(payload[key])

    return True, ""
```

| 규칙 | 값 | 대응 |
|------|---|------|
| WS 단일 프레임 최대 크기 | 1MB | 초과 시 메시지 거부 + close(1009 `"message too big"`) |
| 텍스트 필드 최대 길이 | 10,000자 | 초과 시 error 이벤트 반환 |
| XSS 이스케이프 | `html.escape()` | 모든 문자열 사용자 입력에 적용 |
| session_id 형식 | UUID v4 | 불일치 시 error 이벤트 반환 |
| 알 수 없는 type | 무시 + 경고 로그 | 연결 유지 |

### 11.4 Origin 검증 (CSRF 방지)

> WebSocket은 CORS가 적용되지 않으므로, **서버 핸드셰이크 단계에서 Origin 헤더를 반드시 체크**한다.
> 이걸 안 하면 다른 도메인에서 사용자 세션을 탈취하는 CSRF 공격에 노출된다.

```python
from fastapi import WebSocket, WebSocketException

ALLOWED_ORIGINS = {
    "https://adallpin.com",           # 프로덕션
    "https://staging.adallpin.com",   # 스테이징
    "http://localhost:3000",          # 로컬 개발
    "http://localhost:5173",          # Vite 로컬 개발
}

@router.websocket("/ws/stream")
async def stream_endpoint(
    websocket: WebSocket,
    user_id: str = Query(...),
):
    # Origin 검증 — accept() 전에 수행
    origin = websocket.headers.get("origin")
    if origin not in ALLOWED_ORIGINS:
        logger.warning("ws_invalid_origin", origin=origin, user_id=user_id)
        await websocket.close(code=4403, reason="invalid origin")
        return

    await websocket.accept()

    # 이후 auth 처리 (§11.1)
    ...
```

| 규칙 | 설명 |
|------|------|
| Origin 헤더 필수 | 없거나 `ALLOWED_ORIGINS`에 없으면 close(4403) |
| 환경변수 관리 | `WS_ALLOWED_ORIGINS`로 배포 환경별 설정 주입 |
| 로컬 개발 | `http://localhost:*` 허용 (프로덕션에서는 제거) |

### 11.5 보안 체크리스트 (POC 필수)

| # | 항목 | POC 적용 | 구현 위치 |
|---|------|----------|-----------|
| 1 | JWT 토큰 인증 | ✅ | §11.1 |
| 2 | 채널 구독 권한 체크 | ✅ | §11.2 |
| 3 | 메시지 입력 검증 (XSS, 크기) | ✅ | §11.3 |
| 4 | Origin 검증 | ✅ | §11.4 |
| 5 | WSS (TLS) | POC 배포 시 | 인프라 레벨 |
| 5 | 채팅방 수 제한 (AE당 10개) | ✅ POC | DM_poc §14.1, IC_poc §2.1 |
| 6 | 토큰 만료 후 재검증 | Phase 2 | — |
| 7 | WS 연결 수 제한 | 멀티플렉싱으로 자동 (AE당 2개 고정) | §1.1 |
| 8 | Rate limiting | Phase 2 | — |

---

## Change Log

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2026-04-06 | POC 초판. 멀티플렉싱, step_preview, memory_compressed, HITL 큐잉, 멀티세션 resume |

---

*Related: [DATA_MODELS_poc.md](DATA_MODELS_poc.md) | [INTERFACE_CONTRACT_poc.md](INTERFACE_CONTRACT_poc.md)*
