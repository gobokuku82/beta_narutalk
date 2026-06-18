# Dream Agent V2 - Specification Index

**Version**: 2.0 | **Date**: 2026-02-06 | **Status**: Draft

---

## Document Overview

Dream Agent V2 시스템의 기술 명세서 모음입니다.

---

## Core Documents

| Document | Description | Priority | Status |
|----------|-------------|----------|--------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 전체 시스템 아키텍처 | **Critical** | ✅ Draft |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Phase별 구현 계획서 | **Critical** | ✅ Active |
| [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) | WebSocket 통신 프로토콜 상세 | **Critical** | ✅ Draft |
| [API_SPEC.md](API_SPEC.md) | REST API 명세 | **High** | ✅ Draft |
| [HITL_SPEC.md](HITL_SPEC.md) | Human-in-the-Loop 시스템 | **High** | ✅ Draft |
| [SESSION_SPEC.md](SESSION_SPEC.md) | 세션 관리 시스템 | **High** | ✅ Draft |
| [DATA_MODELS.md](DATA_MODELS.md) | Pydantic 데이터 모델 | **High** | ✅ Draft |
| [DB_SCHEMA.md](DB_SCHEMA.md) | 데이터베이스 스키마 | **High** | ✅ Draft |
| [ERROR_CODES.md](ERROR_CODES.md) | 에러 코드 체계 | **Medium** | ✅ Draft |

---

## V2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend (Next.js)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐   │
│  │   Chat UI   │  │ Plan Viewer │  │ Todo List   │  │ HITL Controls │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───────┬───────┘   │
│         └────────────────┴────────────────┴─────────────────┘           │
│                                    │                                     │
│                          WebSocket + REST API                            │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼─────────────────────────────────────┐
│                         Backend (FastAPI)                                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    api/ (Interface Layer)                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │  routes/ │  │websocket/│  │ schemas/ │  │  Middleware      │  │   │
│  │  └────┬─────┘  └────┬─────┘  └──────────┘  └──────────────────┘  │   │
│  └───────┼─────────────┼────────────────────────────────────────────┘   │
│          │             │                                                 │
│  ┌───────┴─────────────┴────────────────────────────────────────────┐   │
│  │                 app/dream_agent/ (Application Layer)              │   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │                  orchestrator/ (LangGraph)                   │ │   │
│  │  │                                                              │ │   │
│  │  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐  │ │   │
│  │  │  │Cognitive │───►│ Planning │───►│Execution │───►│Response│ │ │   │
│  │  │  │  Node    │    │   Node   │    │  Node    │    │ Node  │  │ │   │
│  │  │  └──────────┘    └────┬─────┘    └────┬─────┘    └───────┘  │ │   │
│  │  │                       │               │                      │ │   │
│  │  │                  interrupt()     Send API                    │ │   │
│  │  │                  (Plan 승인)     (병렬 실행)                  │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                   │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │   │
│  │  │ workflow_       │  │ llm_manager/    │  │ tools/           │  │   │
│  │  │ managers/       │  │                 │  │                  │  │   │
│  │  │ • hitl_manager  │  │ • prompts/      │  │ • registry.py    │  │   │
│  │  │ • todo_manager  │  │ • client.py     │  │ • definitions/   │  │   │
│  │  │ • callback_mgr  │  │                 │  │                  │  │   │
│  │  └─────────────────┘  └─────────────────┘  └──────────────────┘  │   │
│  └───────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼─────────────────────────────────────┐
│                          Data Layer                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │
│  │    PostgreSQL    │  │      Redis       │  │    File Storage      │   │
│  │  • checkpoints   │  │  • session cache │  │  • reports/          │   │
│  │  • sessions      │  │  • rate limit    │  │  • exports/          │   │
│  │  • plans/todos   │  │  • exec cache    │  │  • uploads/          │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Communication Patterns

### 1. REST API (Synchronous)

```
Client ──[POST /agent/run]──► Server ──► Response (blocking)
```

- 짧은 작업에 적합
- 타임아웃: 300초

### 2. WebSocket + REST (Asynchronous)

```
1. Client ──[POST /agent/run-async]──► Server
   └── Response: { session_id, websocket_url }

2. Client ══[WS /ws/{session_id}]══► Server
   ├── Server ──[layer_start]──► Client
   ├── Server ──[todo_update]──► Client
   ├── Server ──[hitl_request]──► Client
   │   └── Client ──[hitl_response]──► Server
   └── Server ──[complete]──► Client
```

### 3. HITL Interrupt Flow

```
Execution ──► interrupt() ──► WebSocket ──► Frontend
                                               │
Frontend: 사용자 결정 (approve/modify/reject)
                                               │
Frontend ──► WebSocket/REST ──► Command(resume) ──► Execution 재개
```

---

## Key Design Decisions

### 1. Two-Level Orchestration

| Level | Component | Role |
|-------|-----------|------|
| Level 1 | `orchestrator/` | LangGraph StateGraph, 4-Layer 조율 |
| Level 2 | `execution/` | Todo 실행 스케줄링, 전략 결정 |

### 2. LangGraph Primitives

| Primitive | Usage |
|-----------|-------|
| **Command** | 레이어 간 hand-off (`goto="planning"`) |
| **Send** | Execution 내 병렬 Todo 실행 |
| **interrupt()** | HITL 중단점 (Plan 승인, 질문) |

### 3. State Strategy

| Purpose | Type | Reason |
|---------|------|--------|
| AgentState | TypedDict | 성능, Reducer 호환 |
| Layer I/O | Pydantic | 검증, 직렬화 |
| Domain Models | Pydantic | 불변성, 검증 |
| API Schema | Pydantic | FastAPI 자동 문서화 |

---

## Implementation Phases

### Phase 1: Foundation (Current)
- [x] Directory structure
- [x] YAML tool/prompt definitions
- [ ] AgentState + Models + Schemas
- [ ] Mock 4-Layer nodes
- [ ] Basic API + WebSocket

### Phase 2: Layer Implementation
- [ ] Cognitive (LLM intent classification)
- [ ] Planning (Todo generation)
- [ ] Execution (Send API parallel)
- [ ] Response (Multi-format output)

### Phase 3: HITL Completion
- [ ] interrupt_before planning
- [ ] Pause/Resume
- [ ] Natural language Plan editing
- [ ] LLM verification

### Phase 4: Production Ready
- [ ] Error handling
- [ ] Session persistence
- [ ] Monitoring + Health check
- [ ] Frontend integration

---

## Reference Documents

### V1 Legacy (Read-only)
- `docs/old/specs/` - V1 specs
- `docs/old/cham/specs/` - Detailed V1 specs
- `backend/_old/` - V1 code

### V2 Architecture
- `.claude/CLAUDE.md` - Project context
- Plan file - Architecture design document

---

*Last Updated: 2026-02-06*
