# ERD — 시각화 모음 (Database / Hierarchy / Flow)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-29 |
| 위치 | `docs/agent_specs/erd_database.md` (시각화 전용) |
| 정식 spec | [`35_DB_SCHEMA_v1.0.md`](./35_DB_SCHEMA_v1.0.md) (테이블 정의 source of truth) |
| 짝 | [`30_DATA_MODELS_v1.1.md`](./30_DATA_MODELS_v1.1.md) (Pydantic 모델) |
| 형식 | Mermaid (markdown native — IDE / GitHub 자동 렌더링) |

---

## 0. 본 문서의 역할

**시각화 전용** — 5 view 다이어그램으로 시스템 데이터 구조 한눈 파악.

- ERD (관계형 DB)
- 의미적 hierarchy (User → Conversation → Turn)
- 데이터 흐름 (4Layer ↔ Memory)
- Memory type 분류
- Sprint 진화

다이어그램 외 정의 / 컬럼 / query 패턴 = `35_DB_SCHEMA_v1.0.md` 참조.

---

## 1. View 1: Database ERD (Sprint 15 P0)

```mermaid
erDiagram
    checkpoints ||--o{ checkpoint_writes : "1:N"

    checkpoints {
        VARCHAR thread_id PK "= turn_id"
        VARCHAR checkpoint_ns PK
        VARCHAR checkpoint_id PK
        VARCHAR parent_checkpoint_id
        VARCHAR type
        BYTEA checkpoint "serialized state"
        JSONB metadata
    }

    checkpoint_writes {
        VARCHAR thread_id PK
        VARCHAR checkpoint_ns PK
        VARCHAR checkpoint_id PK
        VARCHAR task_id PK
        INTEGER idx PK
        VARCHAR channel
        VARCHAR type
        BYTEA value
        VARCHAR task_path
    }

    memory_entries {
        UUID id PK
        VARCHAR type "8 enum"
        VARCHAR scope_type "4 enum"
        VARCHAR scope_id "user/session/conv ID"
        VARCHAR key
        JSONB content "type 별 schema"
        VARCHAR source "explicit/implicit/extracted"
        FLOAT confidence "0.0~1.0"
        TIMESTAMP created_at
        TIMESTAMP updated_at
        TIMESTAMP expires_at "NULL = 무한"
    }
```

### 1.1 관계 요약

| From | To | 종류 | 비고 |
|------|----|----|------|
| `checkpoints` | `checkpoint_writes` | 1:N (FK) | LangGraph native |
| `memory_entries` | (독립) | — | scope_id soft FK 만 |
| `checkpoints` | `memory_entries` | (분리) | 같은 DB, 다른 책임 |

→ POC 단계 = **memory_entries 단일 테이블 + JSONB 유연성**. Sprint 16+ 정규화 가능.

---

## 2. View 2: 의미적 Hierarchy (User → Conversation → Turn)

```mermaid
graph TB
    User["👤 User<br/>user_id"]

    User --> Conv1["💬 Conversation 1<br/>conv_xxx"]
    User --> Conv2["💬 Conversation 2<br/>conv_yyy"]
    User --> ConvN["💬 ... N개"]

    Conv1 --> Turn1A["🔄 Turn<br/>turn_aaa"]
    Conv1 --> Turn1B["🔄 Turn<br/>turn_bbb"]
    Conv2 --> Turn2A["🔄 Turn<br/>turn_ccc"]

    Turn1A --> CP1[("📌 LangGraph<br/>checkpoints")]
    Turn1B --> CP2[("📌 LangGraph<br/>checkpoints")]
    Turn2A --> CP3[("📌 LangGraph<br/>checkpoints")]

    User -. preference .-> MemPref[("🧠 Memory:<br/>preference")]
    Conv1 -. conversation_meta .-> MemMeta1[("🧠 Memory:<br/>conversation_meta")]
    Conv2 -. conversation_meta .-> MemMeta2[("🧠 Memory:<br/>conversation_meta")]
    Turn1A -. turn 데이터 .-> MemTurn1[("🧠 Memory:<br/>conversation type")]
    Turn1B -. turn 데이터 .-> MemTurn2[("🧠 Memory:<br/>conversation type")]
    Turn2A -. turn 데이터 .-> MemTurn3[("🧠 Memory:<br/>conversation type")]

    Turn1A -. session 24h .-> MemSess[("🧠 Memory:<br/>session, TTL 24h")]

    style User fill:#4a90e2,color:#fff
    style Conv1 fill:#7ec8e3
    style Conv2 fill:#7ec8e3
    style ConvN fill:#7ec8e3
    style MemPref fill:#90ee90
    style MemMeta1 fill:#90ee90
    style MemMeta2 fill:#90ee90
    style MemTurn1 fill:#fff4a3
    style MemTurn2 fill:#fff4a3
    style MemTurn3 fill:#fff4a3
    style MemSess fill:#ffb6c1
```

### 2.1 ID 의 hierarchy

| Level | ID | 예시 | 비고 |
|-------|----|----|------|
| 1 | `user_id` | `demo` | POC = 단일 사용자 |
| 2 | `conversation_id` | `conv_fa81d02` | 사용자가 "+ 새 채팅" 시 발급 |
| 3 | `turn_id` (= `session_id`) | `turn_d36ffd35ad77` | 쿼리 1회당 발급 |

**Sprint 15 P0 단순화**: `session_id` ↔ `turn_id` 통합 (1 turn = 1 session).

### 2.2 scope_type 별 ID 연결

| scope_type | scope_id 의미 | type 예 | TTL |
|----------|-----------|------|-----|
| `user` | user_id | preference / conversation / conversation_meta | 무한 |
| `session` | turn_id | session 단기 변수 | 24h |
| `org` | org_id | (Sprint 16+) | 무한 |
| `global` | "" | system default | 무한 |

→ **conversation 은 별도 scope 아님** — soft FK (`content.conversation_id`) 로 grouping.

---

## 3. View 3: 데이터 흐름 (4Layer ↔ Memory)

### 3.1 Read 흐름 (Cognitive 직전 cascade)

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant W as ws_agent
    participant C as Cognitive
    participant M as MemoryManager
    participant DB as memory_entries
    participant P as Planning

    U->>W: 쿼리 ("데이터 분석")
    W->>C: cognitive_node(state)

    Note over C,M: Sprint 15 P0 — E2-3 Cognitive 직전 cascade
    C->>M: get_context(session_id, user_id)
    M->>DB: SELECT scope=session
    M->>DB: SELECT scope=user
    M->>DB: SELECT scope=org
    M->>DB: SELECT scope=global
    DB-->>M: rows
    M-->>C: MemoryContext (cascade merged)

    Note over C: query + context → augmented input

    C->>C: LLM 호출 (cognitive)
    C-->>P: StructuredQuery (clarifications_needed?)

    Note over P: Phase E-3: clarification 처리 시 추가 cascade
```

### 3.2 Write 흐름 (Response 후 persist_turn)

```mermaid
sequenceDiagram
    participant R as Response
    participant M as MemoryManager
    participant DB as memory_entries

    Note over R,M: E2-1 persist_turn (non-blocking)
    R->>M: persist_turn(session_id, conv_id, user_id, query, plan, result)

    Note over M,DB: 3 곳 저장
    M->>DB: UPSERT type=conversation (turn 데이터)
    M->>DB: UPSERT type=conversation_meta (대화 메타)
    M->>DB: UPSERT type=session (24h TTL)
    DB-->>M: OK
    M-->>R: persist 완료
```

### 3.3 Clarification 흐름 (E-3 H0 자동 해결 ⭐)

```mermaid
sequenceDiagram
    participant C as Cognitive
    participant V as Validator
    participant M as MemoryManager
    participant DB as memory_entries
    participant U as User
    participant W as Dashboard

    C->>C: LLM (StructuredQuery)
    C->>V: validate (required field backup)
    V-->>C: clarifications_needed (있을 시)

    loop 각 clarification 항목
        C->>M: find_clarification_answer(field)
        M->>DB: SELECT scope=session > user > org > global
        alt 답 있음 (메모리 hit)
            DB-->>M: value
            M-->>C: value
            C->>C: augment + skip (자동 해결 ⭐)
        else 답 없음 (메모리 miss)
            M-->>C: None
            C->>W: interrupt(type=clarification)
            W->>U: 모달 표시
            U->>W: 답변
            W->>C: clarification_response
            C->>M: store_clarification(field, value)
            M->>DB: UPSERT type=preference, scope=user
            Note over M,DB: 다음 turn 부터 자동 활용
        end
    end
```

---

## 4. View 4: Memory Type 분류 (8 가지)

```mermaid
graph TB
    Memory["🧠 Memory<br/>(memory_entries 테이블)"]

    Memory --> ShortTerm["⏱ 단기<br/>(TTL 짧음)"]
    Memory --> LongTerm["♾ 장기<br/>(TTL 무한)"]
    Memory --> Cache["💾 Cache<br/>(TTL 1-7일)"]

    ShortTerm --> Session["session<br/>(24h)<br/>scope=session"]

    LongTerm --> Pref["preference<br/>(사용자 선호)<br/>scope=user"]
    LongTerm --> Conv["conversation<br/>(개별 turn)<br/>scope=user"]
    LongTerm --> ConvMeta["conversation_meta<br/>(sidebar)<br/>scope=user"]
    LongTerm --> Plan["plan<br/>(plan 이력)<br/>scope=user"]
    LongTerm --> Pattern["pattern<br/>(추출 패턴)<br/>scope=user/org"]
    LongTerm --> Knowledge["knowledge<br/>(도메인 지식)<br/>scope=user/org"]

    Cache --> ToolCache["tool_cache<br/>(tool 결과)<br/>scope=global/user"]

    style ShortTerm fill:#ffb6c1
    style LongTerm fill:#90ee90
    style Cache fill:#fff4a3
    style Session fill:#ffe0e6
    style Pref fill:#d0f0d0
    style Conv fill:#d0f0d0
    style ConvMeta fill:#d0f0d0
    style Plan fill:#d0f0d0
    style Pattern fill:#d0f0d0,stroke-dasharray: 5 5
    style Knowledge fill:#d0f0d0,stroke-dasharray: 5 5
    style ToolCache fill:#fffcc0,stroke-dasharray: 5 5
```

### 4.1 도입 시점

| 도입 | type |
|------|------|
| **Sprint 15 P0** | preference / conversation / conversation_meta / plan / session |
| Sprint 16+ | knowledge / tool_cache |
| Sprint 17+ | pattern (자동 추출) |

---

## 5. View 5: Sprint 별 진화

```mermaid
timeline
    title DB Schema 진화 timeline

    Sprint 12 : LangGraph Checkpointer 도입
              : checkpoints + checkpoint_writes
              : (interrupt/resume 지원)

    Sprint 14 A3 : Schema 변경 없음
                 : 코드만 — Plan adapter (어댑터 layer, throwaway)

    Sprint 15 P0 : memory_entries 신규 테이블
                 : 5 type 활성 (preference/conversation/conversation_meta/plan/session)
                 : Hybrid schema (정규화 + JSONB)
                 : ADR-010 D 단일화 (planner.Plan 통일)

    Sprint 16+ : knowledge type 추가
               : tool_cache type 추가
               : Org / Global scope 활성

    Sprint 17+ : pattern 추출 background job
               : (별도 patterns 테이블 가능성)

    Sprint 18+ : 맞춤형 에이전트 (H4)
               : pgvector 도입 검토 (semantic search)
```

---

## 6. View 6: E2-5 Conversation Sidebar 데이터 흐름

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant D as Dashboard
    participant API as memory API
    participant M as MemoryManager
    participant DB as memory_entries

    Note over U,DB: 페이지 로드 시 자동
    D->>API: GET /api/v2/memory/conversations/list?limit=5
    API->>M: search(type=conversation_meta, scope=user)
    M->>DB: SELECT WHERE type='conversation_meta'
    DB-->>M: rows
    M-->>API: list (sorted by last_turn_at desc)
    API-->>D: 5개 conversation
    D->>U: 좌측 sidebar 표시

    Note over U,DB: 사용자가 conversation 클릭
    U->>D: click conv_xxx
    D->>API: GET /api/v2/memory/conversations/conv_xxx/turns?limit=5
    API->>M: search(type=conversation, content_filter)
    M->>DB: SELECT WHERE content->>'conversation_id'=conv_xxx
    DB-->>M: 5 turn
    M-->>API: turns
    API-->>D: 최근 5 turn
    D->>U: 채팅창에 메시지 표시

    Note over U,DB: 사용자가 🗑 삭제 클릭
    U->>D: delete conv_xxx
    D->>API: DELETE /api/v2/memory/conversations/conv_xxx
    API->>M: delete all turns + meta (preference 보존)
    M->>DB: DELETE type=conversation WHERE conv_id=xxx
    M->>DB: DELETE type=conversation_meta WHERE key=conv_xxx
    Note over DB: type=preference 보존
    DB-->>M: deleted count
    M-->>API: OK
    API-->>D: 200
    D->>U: sidebar 갱신
```

---

## 7. View 7: 사용자 ↔ AI 자유 대화 (Vision H0~H4)

```mermaid
graph LR
    Q1["1차 turn<br/>'데이터 찾아줘'"] --> Clar1{"clarification?"}
    Clar1 -->|memory miss| Ask1["💬 모달:<br/>'어떤 대상?'"]
    Ans1["사용자:<br/>'&lt;entity&gt;'"]
    Ask1 --> Ans1
    Ans1 --> Mem1[("Memory.set<br/>preference.entity")]
    Mem1 --> Plan1[Planning]
    Plan1 --> Exec1[Execution]
    Exec1 --> Resp1[Response]
    Resp1 --> PT1[("persist_turn<br/>conversation +<br/>conversation_meta")]

    PT1 -.학습 누적.-> Q2

    Q2["2차 turn<br/>'데이터 찾아줘'<br/>(entity 또 누락)"] --> Clar2{"clarification?"}
    Clar2 -->|memory hit ⭐| AutoResolve["✅ 자동 해결:<br/>entity=&lt;entity&gt;<br/>(질문 안 함)"]
    AutoResolve --> Plan2[Planning]
    Plan2 --> Exec2[Execution]
    Exec2 --> Resp2[Response]

    style Q1 fill:#4a90e2,color:#fff
    style Q2 fill:#4a90e2,color:#fff
    style Mem1 fill:#90ee90
    style PT1 fill:#90ee90
    style AutoResolve fill:#ffd700,stroke:#ff6b35,stroke-width:3px
    style Ask1 fill:#ffb6c1
```

→ **H0 자동 해결 메커니즘** = 메모리 cascade 가 clarification 직전에 답을 자동 augment.

---

## 8. View 8: Schema 진화 — 확장/변경 용이성 ⭐

**원칙** (35 spec §0.1): JSONB content + schema_version + append-only.

```mermaid
graph TB
    V1["📦 v1 (Sprint 15 P0)<br/>messages 배열 + metadata"]

    V1 -->|0 비용| V1A["+ 새 message type<br/>(clarification / progress / system)"]
    V1 -->|0 비용| V1B["+ metadata 새 필드<br/>(plan / context / tags)"]
    V1 -->|0 비용| V1C["+ message attachments 위치 변경"]

    V1 -->|🟡 1 마이그레이션| V1D["+ 새 memory type<br/>(feedback / audit)"]
    V1D --> V1D1["CHECK constraint 갱신"]

    V1 -->|🔴 v2 진입| V2["📦 v2 (Sprint 16+ 가능)<br/>구조 변경 (예: messages 분리)"]
    V2 --> V2A["v1 reader 그대로 유지<br/>(schema_version 분기)"]
    V2 --> V2B["v2 writer 신규"]
    V2 --> V2C["기존 v1 row 절대 mutate X"]

    style V1 fill:#90ee90
    style V1A fill:#d0f0d0
    style V1B fill:#d0f0d0
    style V1C fill:#d0f0d0
    style V1D fill:#fff4a3
    style V2 fill:#ffb6c1
```

### 8.1 진화 시 reader 분기 패턴

```python
def parse_conversation_content(content: dict) -> Conversation:
    schema_version = content.get("schema_version", "v1")
    if schema_version == "v1":
        return _parse_v1(content)
    elif schema_version == "v2":
        return _parse_v2(content)
    else:
        raise ValueError(f"Unknown schema_version: {schema_version}")
```

→ 새 v 추가 시 신규 분기만 추가. 기존 분기 손대지 않음.

### 8.2 변경 결정 규칙

| 변경 | 어떻게 |
|------|------|
| messages / metadata 안 변경 | v1 그대로 (schema_version 유지) |
| 구조 자체 변경 (key 명명 / 트리 구조) | v2 신규. 기존 v1 row 보존 |
| 새 type 추가 | CHECK constraint 갱신 + reader 분기 |

---

## 9. 다이어그램 렌더링

### 9.1 IDE / 에디터

- **VS Code**: Mermaid Markdown Preview 확장 자동 렌더링
- **PyCharm**: Mermaid 플러그인
- **GitHub**: 자동 렌더링 (markdown 안의 ```mermaid 블록)

### 9.2 본 문서의 한계

Mermaid = 스타일/레이아웃 제한적. 본격 도식 (drawio / Figma) 필요 시 별도 자료.

---

## 10. 관련 문서

- **정식 spec**: [`35_DB_SCHEMA_v1.0.md`](./35_DB_SCHEMA_v1.0.md) — 컬럼 / 제약 / query 패턴
- **Pydantic models**: [`30_DATA_MODELS_v1.1.md`](./30_DATA_MODELS_v1.1.md)
- **north star**: [`00_vision_and_intent.md`](./00_vision_and_intent.md)
- **ADR**: ADR-010 (Plan/Todo schema 통합), ADR-015 (메모리 + Clarification) — 결정 박제

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
