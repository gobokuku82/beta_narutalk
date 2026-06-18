# Sprint 14 A3 — Q3 사전 조사: 메모리 시스템 architecture 설계 (초안)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 |
| 작성자 | Claude (Hybrid 방식 — 9 영역 옵션 + 추천 + vision 매핑) |
| 자매 문서 | [`agent_specs/00_vision_and_intent.md`](../agent_specs/00_vision_and_intent.md) (north star) / [`agent_specs/35_DB_SCHEMA_v1.0.md`](../agent_specs/35_DB_SCHEMA_v1.0.md) (정식 DB schema spec — ERD 포함) / [`sprint14_a3_poc1_settlement.md`](./sprint14_a3_poc1_settlement.md) / [`sprint14_a3_poc1_deliverables.md`](./sprint14_a3_poc1_deliverables.md) Q3 |
| 목적 | ADR-015 (메모리 + clarification + 자유 대화 architecture) 결정 입력 자료 |
| 본 문서 위치 | `docs/reports/sprint14_a3_research_q3_memory.md` |
| 작업 방식 | Hybrid — Claude 가 9 영역 초안 → 사용자 영역별 ✅ lock / 🟡 토론 / ❌ 변경 |

---

## 0. 본 문서의 역할

**메모리 시스템 첫 설계 문서**. 분석이 아니라 design from scratch.

사용자 사전 조건:
- ✅ PostgreSQL DB 에 저장
- ✅ `backend/app/dream_agent/workflow_managers/memory_manager/` 폴더 (placeholder)
- 🟡 Schema 미정 — 본 문서가 결정 entry-point
- 🟡 Manager API 미정

본 문서가 다루지 않는 것:
- 코드 구현 (ADR-015 결정 후 Phase E)
- 패턴 추출 알고리즘 본격 (Sprint 17+)
- Privacy / Security 본격 (MVP 진입 시)

---

## 1. Vision 매핑 — 메모리는 어느 가설을 구현?

| Vision 요소 | 메모리 역할 |
|---------|---------|
| **H0 의도 모호성** | 이전 답변 저장 → 동일 모호도 반복 시 자동 답 활용 |
| **H1 발견** | 사용자 ↔ AI 대화 누적 → 발견의 흔적 보존 |
| **H2 학습 데이터** | 메모리 = 학습 데이터의 저장소 (가설 자체) |
| **H3 패턴화** | 메모리 누적 → 패턴 추출 (Sprint 17+) |
| **H4 맞춤화** | 메모리 + 패턴 → 기업/사용자별 맞춤 응답 (Sprint 18+) |

→ 메모리는 **H2 의 인프라이자 H0/H1 의 자동화 도구이자 H3/H4 의 데이터 소스**.

---

## 2. 9 영역 설계 매트릭스

### 영역 1: 저장 대상 (Scope) — 무엇을 메모리에?

| 카테고리 | 내용 | Vision 매핑 | 우선순위 |
|--------|------|---------|------|
| **사용자 선호** | brand / channel / 분석 종류 default | H0 / H1 / H4 | ⭐ Sprint 15 P0 |
| **대화 이력** | 쿼리 / clarification 답변 / 편집 | H1 / H2 | ⭐ Sprint 15 P0 |
| **Plan 이력** | 승인 / 거부 / 수정 이력 | H1 / H2 | Sprint 15 P1 |
| **Tool cache** | 같은 입력 → 같은 결과 cache | 성능 + H4 일관성 | Sprint 16+ |
| **패턴 (학습된)** | 추출된 사용자/기업 패턴 | H3 산출물 | Sprint 17+ |
| **도메인 지식** | 명시적 가르침 ("이 brand 는 항상 ~") | H4 입력 | Sprint 16+ |
| **세션 컨텍스트** | 대화 흐름 / 임시 변수 (단기) | H1 | ⭐ Sprint 15 P0 |

**Claude 추천 — 3 layer 분리**:
- **단기 (Session)**: 세션 컨텍스트, 진행 중 clarification, 임시 변수 — TTL 짧음 (24h)
- **장기 (User/Org)**: 사용자 선호, 대화 이력, plan 이력, 패턴, 도메인 지식 — TTL 무한
- **Cache**: tool 결과 — 별도 layer (TTL 1~7일)

**Sprint 15 P0 범위**: 단기 + 장기 (Cache 후순위).

✅ lock / 🟡 토론 / ❌ 변경: `____`

---

### 영역 2: Schema 형태

| Option | 내용 | 장점 | 단점 |
|--------|------|------|------|
| A. Key-Value | `(key, value)` 단순 저장 | 간단, 빠름 | 구조 표현 한계, 검색 어려움 |
| B. JSONB Document | Postgres JSONB column | 유연, 가변 schema, GIN index 검색 | 정규화 부족 |
| C. Relational tables | 메모리 type 별 정규화 테이블 | 명확, 무결성 | type 추가 시 마이그레이션, 다양성 처리 어려움 |
| **D. Hybrid** | 핵심 metadata 정규화 + content JSONB | 균형 — 검색 가능 + 유연 | 복잡도 ↑ (관리 가능 수준) |

**Claude 추천 — D Hybrid** (가장 합리적):

```sql
CREATE TABLE memory_entries (
    id UUID PRIMARY KEY,
    type VARCHAR(32) NOT NULL,           -- preference / conversation / plan / pattern / knowledge / session
    scope_type VARCHAR(16) NOT NULL,     -- global / org / user / session
    scope_id VARCHAR(255) NOT NULL,      -- user_id / org_id / session_id
    key VARCHAR(255) NOT NULL,           -- "brand", "channel_default" 등
    content JSONB NOT NULL,              -- 유연한 본문
    source VARCHAR(16) NOT NULL,         -- explicit / implicit / extracted
    confidence FLOAT DEFAULT 1.0,        -- 패턴 추출 시 0.0~1.0
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP                 -- nullable (장기 = NULL)
);
CREATE INDEX idx_memory_scope ON memory_entries(scope_type, scope_id, type);
CREATE INDEX idx_memory_content ON memory_entries USING GIN (content);
CREATE INDEX idx_memory_expires ON memory_entries(expires_at) WHERE expires_at IS NOT NULL;
```

**근거**:
- POC ~ MVP 단계 schema 변경 빈번 → JSONB 가 마이그레이션 비용 절감
- 핵심 검색 (scope, type, key) 은 정규화 컬럼 → 빠름
- content 검색 (예: brand="블루밍글로우" 인 모든 user) → GIN index

✅ lock / 🟡 토론 / ❌ 변경: `____`

---

### 영역 3: 저장 단위 (Granularity)

| Tier | 내용 | POC 의미 | MVP 의미 |
|------|------|--------|--------|
| **Global** | 시스템 전체 default | 작음 (POC = 단일 시스템) | 작음 |
| **Org** | 기업별 암묵지 | 작음 (POC = 단일 기업) | ⭐ 큼 (vision §1 의 "기업별 맞춤") |
| **User** | 개인 선호 | ⭐ 큼 (POC 사용자 1인) | ⭐ 큼 |
| **Session** | 대화 세션 컨텍스트 | ⭐ 큼 (자유 대화 단위) | ⭐ 큼 |
| **Turn** | 한 쿼리 임시 | 매우 짧음 (in-memory) | 매우 짧음 |

**Claude 추천 — 5 tier 모두 지원** (Turn 만 in-memory):

조회 시 cascade — Session → User → Org → Global (가까운 것 우선):
```python
def get_context(session_id, user_id, org_id="default"):
    return merge(
        get(scope_session, session_id),  # 가장 가까운
        get(scope_user, user_id),
        get(scope_org, org_id),
        get(scope_global, ""),            # fallback
    )
```

저장 시 사용자 / 시스템이 명시 — "이 정보는 user 레벨" 처럼.

**Sprint 15 P0 범위**: Session + User. Org / Global 은 Sprint 16+.

✅ lock / 🟡 토론 / ❌ 변경: `____`

---

### 영역 4: 조회 시점 (Read)

4Layer 어디서 메모리 조회?

| 시점 | 조회 내용 | Vision 매핑 |
|------|--------|---------|
| **Cognitive 직전** | 사용자 컨텍스트 (선호, 최근 대화) | H0 (모호도 자동 해결) / H1 |
| **Cognitive 출력 시점** | clarification 판단 — 메모리에 답이 있는지? | **H0 핵심** — 같은 모호도 반복 시 답이 메모리에 있으면 묻지 X |
| **Planning 직전** | default tool_params (brand 등) | H0 / H1 / H4 |
| **Execution 중** | 사용자 선호 (출력 format, period 등) | H4 (맞춤형) |
| **Response 생성** | 사용자 톤 / 표시 형식 선호 | H4 |

**Claude 추천 — Cognitive 직전 + Clarification 시점이 핵심**:

```
사용자 query
   ↓
[Cognitive 직전] context = memory.get_context(session, user)
   query + context → augmented input
   ↓
Cognitive 분석 (StructuredQuery 출력)
   ↓
[Clarification 판단]
   if missing field 발견:
       memory_value = memory.get(field, scope=user)
       if memory_value:
           augment StructuredQuery (질문 skip)
       else:
           trigger clarification HITL
   ↓
Planning, Execution, Response (각 시점 필요 시 추가 조회)
```

**핵심 통찰**: H0 의도 모호성 가설의 "자동 해결" 메커니즘 = **Clarification 트리거 직전 메모리 조회**.

✅ lock / 🟡 토론 / ❌ 변경: `____`

---

### 영역 5: 저장 시점 (Write)

| 시점 | 저장 내용 | Source 라벨 |
|------|--------|---------|
| **Clarification 답변 직후** | "brand=블루밍글로우" 같은 명시 사실 | `explicit` |
| **사용자 명시 action** | "이거 기억해" 버튼 / 대화 명령 | `explicit` |
| **Response 성공 후** | 승인된 plan, 사용자 편집 이력, 결과 | `implicit` |
| **자동 패턴 추출** | background job — 누적 데이터 → 패턴 | `extracted` (Sprint 17+) |
| **에러 / 거부 시** | 거부된 plan, 사용자 negative feedback | `implicit` |

**Claude 추천 — 다중 시점 + source 라벨 분리**:

```python
class MemorySource(Literal):
    EXPLICIT = "explicit"      # 사용자 명시 / clarification 답변
    IMPLICIT = "implicit"      # 시스템 추론 (성공 turn 후)
    EXTRACTED = "extracted"    # 패턴 추출 (background)
```

**Sprint 15 P0 범위**:
- ✅ Clarification 답변 직후 (explicit) — H0 자동 해결의 시드
- ✅ Response 성공 후 (implicit) — H1/H2 누적
- 🟡 사용자 명시 action — Sprint 16 UX 결정 후
- ❌ 자동 패턴 추출 — Sprint 17+

**저장 정책**: explicit > implicit > extracted (충돌 시 우선순위).

✅ lock / 🟡 토론 / ❌ 변경: `____`

---

### 영역 6: Lifecycle

메모리 type 별 다른 정책:

| Type | TTL | 갱신 | 삭제 trigger |
|------|------|------|---------|
| **사용자 선호** (preference) | 무한 | 새 명시 시 update | 사용자 명시 / 충돌 시 explicit 우선 |
| **대화 이력** (conversation) | 90일 (기본, 사용자 옵션) | append-only | TTL 만료 / 사용자 요청 |
| **Plan 이력** (plan) | 무한 | append-only | 사용자 요청 |
| **Tool cache** | 1~7일 (tool 별) | LRU | TTL / cache size limit |
| **패턴** (pattern) | 무한 | 재계산 시 update | 사용자 검증 실패 시 confidence ↓ |
| **도메인 지식** (knowledge) | 무한 | 사용자 명시 update | 사용자 명시 |
| **세션 컨텍스트** (session) | 24h | 세션 종료 후 일부만 user 로 promote | TTL |

**Claude 추천 — 위 정책. 단 POC 단계엔**:
- TTL 무한 (장기 메모리만 구현)
- 90일 / LRU 등 = MVP 시
- 단기 (session) 만 24h TTL

**삭제 권한** (개인정보 / GDPR 대비):
- 사용자가 자기 메모리 삭제 가능 — Manager API 의 `delete_user_memory(user_id)` 필요
- POC 단계엔 미구현 (사용자 1인)

✅ lock / 🟡 토론 / ❌ 변경: `____`

---

### 영역 7: Manager API (memory_manager interface)

```python
class MemoryManager:
    """메모리 시스템 통합 manager.
    
    Status: planned — Sprint 15 P0 구현.
    """

    # ── 핵심 CRUD ──
    async def get(
        self, key: str, scope_type: str, scope_id: str,
    ) -> Optional[MemoryEntry]:
        """단일 entry 조회."""

    async def set(
        self, key: str, content: dict, *, 
        scope_type: str, scope_id: str,
        type: str, source: str = "explicit",
        ttl: Optional[int] = None,
    ) -> MemoryEntry:
        """entry 저장 / 갱신 (upsert)."""

    async def delete(
        self, key: str, scope_type: str, scope_id: str,
    ) -> bool:
        """단일 entry 삭제."""

    # ── 다층 조회 (cascade) ──
    async def get_context(
        self, session_id: str, user_id: str, org_id: str = "default",
    ) -> MemoryContext:
        """Session → User → Org → Global cascade.
        
        Returns:
            MemoryContext with merged dict (가까운 scope 우선)
        """

    # ── Search (JSONB GIN) ──
    async def search(
        self, type: str, scope_type: str, scope_id: str,
        content_filter: Optional[dict] = None,
    ) -> list[MemoryEntry]:
        """type / scope / content 조건 조회."""

    # ── Clarification 통합 ──
    async def store_clarification(
        self, session_id: str, user_id: str,
        field: str, value: Any,
    ) -> MemoryEntry:
        """Clarification 답변 저장. user scope 에 자동 promote."""

    async def find_clarification_answer(
        self, session_id: str, user_id: str, field: str,
    ) -> Optional[Any]:
        """Cognitive 가 clarification 직전 조회. 다층 cascade."""

    # ── Turn 기록 ──
    async def persist_turn(
        self, session_id: str, user_id: str,
        query: str, plan: dict, result: dict,
    ) -> None:
        """Response 후 turn 데이터 기록 (implicit)."""

    # ── 패턴 추출 (Sprint 17+) ──
    async def extract_patterns(self, user_id: str) -> list[Pattern]:
        """background job. POC 미구현."""
```

**Claude 추천**: 위 interface — Sprint 15 P0 에서 첫 5 메서드 + clarification 2개 + persist_turn. extract_patterns 는 Sprint 17.

✅ lock / 🟡 토론 / ❌ 변경: `____`

---

### 영역 8: Checkpointer 와의 관계

**LangGraph Checkpointer (PostgreSQL)** = thread 단위 graph state 저장 (interrupt/resume 의 핵심).
**Memory** = thread 초월 knowledge / preference / pattern.

| 차원 | Checkpointer | Memory |
|------|------------|--------|
| 단위 | thread / turn | session / user / org |
| Schema | AgentState (LangGraph 정의) | MemoryEntry (본 시스템 정의) |
| 저장 | LangGraph 자동 (각 node 후) | manager 가 명시 호출 |
| 조회 | LangGraph 자동 (resume 시) | manager 가 명시 호출 (Cognitive / Clarification) |
| 수명 | turn 종료 후 보존 (debugging) | TTL 정책 별도 |

**Claude 추천 — 분리 (다른 테이블, 같은 DB)**:

| 테이블 | 용도 |
|------|------|
| `checkpoints` (LangGraph native) | thread state |
| `checkpoint_writes` (LangGraph native) | step writes |
| `memory_entries` (신규) | 메모리 시스템 |

**연결점** (Sprint 17+):
- Pattern 추출 시 `checkpoints` 의 turn 이력 → `memory_entries` 의 pattern 으로 변환
- Memory 가 Checkpointer 의 "long-term layer" 역할

**LangGraph Memory 라이브러리 (참고)**:
- LangGraph 0.2.x 부터 `Store` interface 제공 (cross-thread memory)
- 우리 시스템에 적용 시: `MemoryManager` 가 `BaseStore` 구현체 가능
- 단, POC 단계엔 단순 직접 구현 (LangGraph Store 의존성 추가 회피)

✅ lock / 🟡 토론 / ❌ 변경: `____`

---

### 영역 9: Data Model (Pydantic schema)

```python
# backend/app/dream_agent/models/memory.py (신규)
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    """단일 메모리 entry — DB 의 memory_entries 테이블에 매핑."""
    
    id: UUID = Field(default_factory=uuid4)
    type: Literal[
        "preference",     # 사용자 선호 (brand 등)
        "conversation",   # 대화 이력
        "plan",           # plan 이력
        "pattern",        # 추출된 패턴 (Sprint 17+)
        "knowledge",      # 도메인 지식
        "session",        # 세션 컨텍스트 (단기)
        "tool_cache",     # tool 결과 cache
    ]
    scope_type: Literal["global", "org", "user", "session"]
    scope_id: str
    key: str
    content: dict[str, Any]
    source: Literal["explicit", "implicit", "extracted"]
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class MemoryContext(BaseModel):
    """다층 cascade 결과 — Cognitive / Planning 입력."""
    
    session_data: dict[str, Any]   # session scope
    user_data: dict[str, Any]      # user scope
    org_data: dict[str, Any]       # org scope
    global_data: dict[str, Any]    # global scope
    merged: dict[str, Any]         # cascade 결과 (가까운 우선)


class Pattern(BaseModel):
    """추출된 패턴 (Sprint 17+)."""
    
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    pattern_type: str            # "default_value" / "preference_correlation" 등
    pattern_data: dict[str, Any]
    confidence: float
    sample_size: int             # 패턴 추출에 사용된 데이터 수
    extracted_at: datetime
```

**Claude 추천 — 위 schema. 단순 / 명시적 / Sprint 별 진입 가능**.

✅ lock / 🟡 토론 / ❌ 변경: `____`

---

## 3. 통합 Architecture — 9 결정의 종합

```
┌──────────────────────────────────────────────────────┐
│ 사용자 query                                            │
└────────────┬─────────────────────────────────────────┘
             ↓
   ┌───────────────────┐
   │  Cognitive 직전    │ ◀─── memory.get_context(session, user)
   └────────┬──────────┘     → MemoryContext (cascade)
            ↓
       Cognitive
            ↓ StructuredQuery
   ┌───────────────────┐
   │ Clarification 판단 │
   │   missing fields?  │
   │     ↓ Yes          │ ──→ memory.find_clarification_answer(field)
   │   answer in mem?   │
   │     ↓ No           │ ──→ trigger clarification HITL
   │     ↓ user 답변     │
   │     ↓              │ ──→ memory.store_clarification(field, value)
   │   (augment SQ)     │
   └────────┬──────────┘
            ↓
       Planning ◀────────── memory.get(default_params, scope=user)
            ↓
       Execution ◀────────── memory.get(preferences, scope=user)
            ↓
       Response
            ↓
   ┌───────────────────┐
   │  Turn 종료 후       │ ──→ memory.persist_turn(session, plan, result)
   └───────────────────┘     (background)

   ┌───────────────────┐
   │  Sprint 17+        │ ──→ memory.extract_patterns(user_id)
   │  Pattern 추출      │     (background job)
   └───────────────────┘
```

### 3.1 Sprint 별 구현 단계

| Sprint | 메모리 기능 |
|--------|---------|
| **15 P0** | Hybrid schema + 5 tier scope (Session+User 만) + 7 type 중 4 (preference/conversation/plan/session) + Manager API 핵심 7 메서드 + Cognitive 직전 cascade + Clarification 통합 |
| **15 P1** | persist_turn 본격 + 사용자 명시 action UI |
| **16** | Org / Global scope + tool_cache type + 외부 명시 action 본격 |
| **17** | Pattern 추출 background job + extracted source 활성화 |
| **18+** | 맞춤형 응답 본격 (H4) |

---

## 4. 외부 참고 (간단)

POC 단계 = 직접 구현 채택. 단 다른 시스템에서 인사이트:

| 시스템 | 핵심 컨셉 | 본 시스템 적용 가능성 |
|------|---------|----------------|
| **LangGraph Memory** (Store) | thread 초월 store interface | Sprint 16+ MemoryManager 가 BaseStore 호환 가능. 지금은 직접 구현 |
| **OpenAI Memory** (ChatGPT) | user-level 명시 + 자동 추출 + 사용자 끄기 | 사용자 명시 / 자동 추출 분리 컨셉 채택 (source 라벨) |
| **Mem0** | semantic memory + similarity search | Sprint 17+ pattern 추출 시 참고 |
| **Letta (MemGPT)** | hierarchical (core / archival / recall) | 본 시스템 3 layer (단기/장기/cache) 와 유사 컨셉 |

---

## 5. 검증 / 테스트 전략 (Sprint 15 진입 시)

### 5.1 단위 테스트
- `MemoryManager` 각 메서드 단위 (모의 DB)
- `MemoryEntry` schema validation
- Cascade 로직 (Session → User → Org → Global)

### 5.2 통합 테스트
- Cognitive 직전 cascade → 메모리 hit/miss 시나리오
- Clarification 답변 저장 → 다음 turn 자동 활용
- Turn 종료 후 persist → 다음 session 활용

### 5.3 E2E 시나리오
- "블루밍글로우 리뷰 분석" 1차 → clarification 으로 brand 답 → 메모리 저장
- "리뷰 분석" 2차 (brand 미명시) → 메모리에서 자동 brand 채움 → clarification skip
- = **H0 자동 해결의 회귀 테스트**

---

## 6. Risk + 완화

| Risk | 완화 |
|------|------|
| 메모리 일관성 (cascade 충돌) | source 라벨 우선순위 (explicit > implicit > extracted) + 명확한 cascade 순서 |
| DB 부하 (모든 turn 마다 cascade 조회) | Cognitive 입력 1회만 cascade, 이후 in-memory cache (turn 단위) |
| Schema 진화 (JSONB 변경 시 마이그레이션) | content 필드별 명시 schema (별도 Pydantic) — content 변경 시 version 필드 |
| 사용자 의도 ↔ 메모리 충돌 (예: 사용자가 "다른 brand" 명시) | explicit > implicit. 사용자 명시 시 즉시 저장 (override) |
| 패턴 추출 의도 어긋남 (Sprint 17) | confidence 가중치 + 사용자 검증 step (안 하면 confidence ↓) |
| Privacy (메모리에 민감 정보) | POC 단계 = N/A. MVP 시 user-level 메모리 끄기 옵션 + 삭제 API |

---

## 7. ADR-015 의 메모리 부분 골격

ADR-015 본문 작성 시 본 자료에서 가져갈 핵심:

### Decision (메모리 부분):
1. **Schema**: Hybrid (정규화 + JSONB)
2. **Granularity**: 5 tier (Global / Org / User / Session / Turn) — POC 단계 Session + User
3. **Read 시점**: Cognitive 직전 cascade + Clarification 판단 시
4. **Write 시점**: Clarification 답변 / Response 후 / 사용자 명시
5. **Lifecycle**: Type 별 정책 (선호 무한 / 대화 90일 / cache 1~7일)
6. **API**: MemoryManager 11 메서드 (Sprint 15 P0 = 7개)
7. **Checkpointer 분리**: 다른 테이블, 같은 DB
8. **Data model**: MemoryEntry / MemoryContext / Pattern Pydantic

### Consequences:
- ✅ H0 자동 해결 메커니즘 확보
- ✅ H2 학습 데이터 인프라
- ✅ Sprint 17 패턴 추출 entry-point
- ⚠ DB 부하 — turn 마다 cascade, 완화 = in-memory cache
- ⚠ Schema 진화 비용 — content 필드 version 으로 완화

---

## 8. 검토 결과 — 9 영역 lock (2026-04-28)

| 영역 | 추천 | 사용자 답 |
|------|------|---------|
| 1 저장 대상 | 3 layer (단기 + 장기 + cache), Sprint 15 P0 = 단기 + 장기 4 type | ✅ **권고대로** |
| 2 Schema | D Hybrid (정규화 + JSONB) | ✅ **권고대로** |
| 3 Granularity | 5 tier, Sprint 15 P0 = Session + User | ✅ **권고대로** |
| 4 Read 시점 | Cognitive 직전 + Clarification 판단 | ✅ **권고대로** |
| 5 Write 시점 | Clarification / Response / explicit | ✅ **권고대로** |
| 6 Lifecycle | Type 별 정책. POC = 단기 24h 만 | ✅ **권고대로** |
| 7 Manager API | 11 메서드 (P0 = 7) | ✅ **권고대로** |
| 8 Checkpointer 관계 | 분리 (다른 테이블, 같은 DB) | ✅ **권고대로** |
| 9 Data model | MemoryEntry / MemoryContext / Pattern | ✅ **권고대로** |

**메모리 설계 v1.0 lock — Sprint 15 P0 구현 입력**.

추가 결정 (2026-04-28):
- **Q4 (Clarification UX) 자료 SKIP** — UX 세부는 Sprint 15 구현 중 결정. 큰 그림 (Cognitive 직전 cascade + Clarification 판단 메커니즘) 은 본 영역 4 에서 lock.
- ADR-015 본문의 메모리 부분 = 본 자료 §3, §7 그대로. UX 부분 = 구현 진행하며 점진 작성.

---

## 9. 다음 단계

1. **사용자 본 자료 검토** + 9 영역 답 lock
2. 보류 영역만 토론 (Option B 방식)
3. **Q4 (Clarification UX) 자료 진입** — Q3 메모리 결정 받고 (특히 영역 4 Cognitive 직전 cascade 가 Q4 의 입력)
4. Q3 + Q4 자료 → ADR-015 본문 작성 (Phase D Step 4)

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-28 | 초안 — Vision 매핑 + 9 영역 매트릭스 (저장 대상 / schema / granularity / read / write / lifecycle / API / checkpointer / data model) + 통합 architecture + Sprint 별 구현 단계 + 외부 참고 + 검증 전략 + Risk + ADR-015 골격 |
| 2026-04-28 | **v1.0 lock** — 사용자 9 영역 모두 권고대로 동의. Q4 (Clarification UX 자료) SKIP — UX 세부는 Sprint 15 구현 중 결정. ADR-015 본문 메모리 부분 = 본 자료 §3, §7 직접 사용 |
