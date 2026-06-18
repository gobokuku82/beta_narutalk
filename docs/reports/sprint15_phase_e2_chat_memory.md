# Sprint 15 — Phase E2 세부 작업계획서 (채팅 메모리 통합)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 (초안) / 2026-04-28 (E2-5 Conversation list 추가) |
| Phase | E-2 — 채팅 메모리 통합 (5 항목 정책 #2/#3/#4 + #6 신규) |
| 마스터 | [`sprint15_implementation_plan.md`](./sprint15_implementation_plan.md) |
| 의존 | Phase E-1 ✅ (메모리 인프라) |
| 다음 | [`sprint15_phase_e3_clarification.md`](./sprint15_phase_e3_clarification.md) (Clarification HITL) |
| 예상 작업량 | ~7시간 (1.5~2세션) ← E2-5 추가로 +3h |
| Acceptance | 채팅창 로드 (#2) + Cognitive 직전 cascade (#3) + 토큰 cap (#4) + persist_turn + **Conversation list sidebar (#6)** |

---

## 0. 본 문서의 역할

Phase E-2 의 **채팅 ↔ 메모리 통합 작업 카탈로그**. Phase E-1 의 인프라 위에 정책 logic + UI 통합.

**5 항목 정책 #2/#3/#4 의 실현**:
- #2 채팅창 열 때 최근 20 turn + Load More
- #3 LLM 히스토리 = 마지막 5 turn + 1500 token cap
- #4 길어지면 잘라내기 (drop oldest)

---

## 1. Phase E-2 의 의도

### 1.1 왜 채팅 통합 부터?

E-1 인프라만으로는 사용자에게 가치 0. **채팅이 메모리를 먹기 시작해야** 학습 데이터 누적 (H2) 시작.

### 1.2 작업 원칙

- **Cognitive 직전 cascade 가 H0 자동 해결의 핵심** (다음 phase E-3 의 토대)
- **persist_turn 은 background** — 사용자 latency 영향 X
- **토큰 cap 정확** — 비용 SLO 준수

---

## 2. 작업 분해 — 5 sub-phase (E2-5 추가)

```
E2-1  persist_turn 구현 (Response 후 자동 저장 + conversation_meta)
        ↓
E2-2  대시보드 채팅창 로드 (#2 — turn 단위 메시지)
        ↓
E2-3  Cognitive 직전 cascade (#3)
        ↓
E2-4  토큰 cap 잘라내기 (#4)
        ↓
E2-5  Conversation list sidebar (#6 — 신규)
```

### 시간 추정

| Sub-phase | 시간 | 누적 |
|-----------|------|------|
| E2-1 persist_turn (+ conversation_meta) | 1.5h | 1.5h |
| E2-2 채팅창 로드 UI | 1h | 2.5h |
| E2-3 Cognitive cascade | 1h | 3.5h |
| E2-4 토큰 cap | 1h | 4.5h |
| **E2-5 Conversation list sidebar** | 2.5h | **7h** |

---

## 3. E2-1: persist_turn 구현 (~1시간)

### 3.1 목표

Response 단계 완료 시 turn 데이터를 **conversation type 메모리** 에 자동 저장 (implicit source).

### 3.2 작업 1.1 — MemoryManager.persist_turn (messages 배열, schema_version v1)

**원칙 적용** (35 spec §0.1):
- `schema_version: "v1"` 필드 명시 (진화 방어)
- `messages` 배열 = append-only (event sourcing 영감)
- `metadata` = JSONB 자유 영역
- 정확한 message type / summary 생성 = **의도적 미정** (쓰면서 결정)

**파일**: `backend/app/dream_agent/workflow_managers/memory_manager/manager.py` (수정)

**메서드 추가**:
```python
async def persist_turn(
    self, session_id: str, conversation_id: str, user_id: str,
    messages: list[dict],            # ← 사용자/AI 메시지 배열 (append-only)
    plan: dict,
    result_data: dict,
    summary: str | None = None,     # 1줄 요약 (sidebar)
) -> None:
    """Response 후 turn 데이터 기록 (implicit). v1 schema.
    
    저장 대상 (3 곳):
        1. type=conversation, key=f"turn_{ts}" — turn 핵심 (messages + metadata)
        2. type=conversation_meta, key=f"conv_{cid}" — sidebar 메타
        3. type=session, key="last_query" — 24h TTL
    
    schema_version="v1" — 35 spec §0.1 / §5.2.
    """
    from datetime import datetime
    timestamp = datetime.utcnow().isoformat()
    
    # 1. Turn 데이터 — v1 schema (messages 배열 중심)
    if summary is None:
        # 의도적 단순 — 첫 user message 50자 (LLM 호출 X). UX 결정 시 변경.
        first_query = next((m["content"] for m in messages if m.get("role") == "user"), "")
        summary = first_query[:50] + ("..." if len(first_query) > 50 else "")
    
    await self.set(
        key=f"turn_{timestamp}",
        content={
            "schema_version": "v1",          # ← 진화 방어
            "conversation_id": conversation_id,
            "session_id": session_id,
            "messages": messages,            # ← append-only 배열
            "summary": summary,
            "metadata": {                    # ← 자유 영역
                "plan": plan,
                "result_data": result_data,
                "completed_at": timestamp,
            },
        },
        scope_type="user", scope_id=user_id,
        type="conversation", source="implicit",
    )
    
    # 2. Conversation 메타 (E2-5 sidebar)
    existing_meta = await self.get(f"conv_{conversation_id}", "user", user_id)
    if existing_meta:
        existing_content = existing_meta.content
        new_meta_content = {
            **existing_content,
            "last_turn_at": timestamp,
            "turn_count": existing_content.get("turn_count", 0) + 1,
        }
    else:
        new_meta_content = {
            "schema_version": "v1",
            "conversation_id": conversation_id,
            "title": summary,                # 첫 turn 의 summary 사용
            "started_at": timestamp,
            "last_turn_at": timestamp,
            "turn_count": 1,
        }
    
    await self.set(
        key=f"conv_{conversation_id}",
        content=new_meta_content,
        scope_type="user", scope_id=user_id,
        type="conversation_meta", source="implicit",
    )
    
    # 3. Session 단기 (24h)
    last_user_msg = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        ""
    )
    await self.set(
        key="last_query",
        content={
            "schema_version": "v1",
            "query": last_user_msg,
            "timestamp": timestamp,
        },
        scope_type="session", scope_id=session_id,
        type="session", source="implicit",
        ttl=86400,
    )
```

**v1 message 형식 (의도적 단순)**:
```python
# user message
{"role": "user", "content": "리뷰 분석", "ts": "..."}

# AI 응답 (단일 message)
{"role": "assistant", "type": "result", "content": "...", "attachments": [...], "ts": "..."}

# Clarification 질의 (E-3 통합)
{"role": "assistant", "type": "clarification", "content": "어떤 브랜드?", "ts": "..."}

# Clarification 답변 (사용자)
{"role": "user", "content": "블루밍글로우", "ts": "..."}
```

→ message `type` 의 정확한 분류 / 새 type 추가 = **자유**. JSONB 안의 배열이라 schema 진화 0 비용.

### 3.3 작업 1.2 — Response stage 통합

**파일**: `backend/app/dream_agent/response/response_stage.py` (수정)

**변경**:
```python
async def response_node(state, config):
    # ... 기존 response 생성
    payload = ResponsePayload.model_validate(result)
    
    # 신규: persist_turn (background, 실패해도 turn 진행에 영향 X)
    try:
        from app.dream_agent.workflow_managers.memory_manager import get_memory_manager
        mm = get_memory_manager()
        await mm.persist_turn(
            session_id=state["session_id"],
            user_id=state.get("user_id", "demo"),
            query=state["query"],
            plan=state.get("plan", {}),
            result=payload.model_dump(),
        )
    except Exception as e:
        logger.warning("persist_turn failed (non-blocking)", error=str(e))
    
    return Command(update={"response": payload.model_dump(mode="json")}, goto=END)
```

**원칙**: 
- try/except 로 wrap — persist 실패해도 사용자 응답엔 영향 X
- await 사용 (async background) — 단 throughput 영향 측정 후 fire-and-forget 변환 검토

### 3.4 단위 테스트

**경로**: `backend/tests/sprint15/test_persist_turn_unit.py` (신규)

**TC**:
- TC-PT-01: persist_turn 호출 → conversation entry 생성
- TC-PT-02: persist_turn → session entry 갱신 (last_query)
- TC-PT-03: persist 실패 시 turn 진행 계속

### 3.5 Acceptance — E2-1

- [ ] MemoryManager.persist_turn 추가
- [ ] response_stage 통합
- [ ] try/except wrap (non-blocking)
- [ ] 3 TC 통과

---

## 4. E2-2: 대시보드 채팅창 로드 (#2, ~1시간)

### 4.1 목표

채팅창 열 때 **최근 20 turn 자동 로드 + "Load More" 버튼** 으로 추가 20씩.

### 4.2 작업 2.1 — API endpoint 추가

**파일**: `backend/api_v2/memory.py` (수정)

**Endpoint**:
```python
@router.get("/conversations")
async def list_conversations(
    user_id: str = Query(...),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
) -> dict:
    """5 항목 #2 — 사용자 대화 이력 (최신순).
    
    Returns:
        {
            "items": [...],   # 최신순 (last_query 가 첫 element)
            "total": int,     # 전체 turn 수
            "has_more": bool, # 추가 로드 가능?
        }
    """
    mm = get_memory_manager()
    all_entries = await mm.search(
        type="conversation",
        scope_type="user", scope_id=user_id,
    )
    # 최신순 정렬
    all_entries.sort(key=lambda e: e.created_at, reverse=True)
    
    paginated = all_entries[offset:offset + limit]
    return {
        "items": [e.model_dump(mode="json") for e in paginated],
        "total": len(all_entries),
        "has_more": offset + limit < len(all_entries),
    }
```

### 4.3 작업 2.2 — 대시보드 채팅창 UI 갱신

**파일**: `dashboard/index.html` (수정)

**기능**:
- 페이지 로드 시 `loadConversations()` 자동 호출 (offset=0, limit=20)
- 채팅창 상단에 표시 (오래된 것 위, 최근 것 아래 — 일반 채팅 UX)
- "Load More" 버튼 — 클릭 시 offset += 20
- 더 이상 없을 때 버튼 비활성화

**JavaScript 골격**:
```javascript
let _conversationOffset = 0;
const PAGE_SIZE = 20;

async function loadConversations(reset = false) {
    if (reset) _conversationOffset = 0;
    
    const res = await fetch(
        `/api/v2/memory/conversations?user_id=${USER_ID}&offset=${_conversationOffset}&limit=${PAGE_SIZE}`
    );
    const data = await res.json();
    
    // 채팅창 상단에 prepend (오래된 것 위로)
    const container = document.getElementById('chat-history');
    data.items.reverse();  // 시간순으로 다시
    data.items.forEach(item => {
        const turn = renderHistoryTurn(item);
        container.prepend(turn);
    });
    
    _conversationOffset += data.items.length;
    
    // Load More 버튼 상태
    const btn = document.getElementById('load-more-history');
    btn.style.display = data.has_more ? 'block' : 'none';
}

function renderHistoryTurn(turn) {
    const div = document.createElement('div');
    div.className = 'history-turn';
    div.innerHTML = `
        <div class="history-query">${turn.content.query}</div>
        <div class="history-response">${turn.content.result?.message || ''}</div>
        <div class="history-time">${formatTime(turn.created_at)}</div>
    `;
    return div;
}

// 페이지 로드 시
window.addEventListener('DOMContentLoaded', () => {
    loadConversations(true);
});
```

### 4.4 Acceptance — E2-2

- [ ] `/api/v2/memory/conversations` endpoint
- [ ] 대시보드 페이지 로드 시 자동 20개 로드
- [ ] Load More 버튼 정상 작동
- [ ] 더 없을 시 버튼 비활성화
- [ ] 사용자 브라우저 검증

---

## 5. E2-3: Cognitive 직전 cascade (#3, ~1시간)

### 5.1 목표

Cognitive 진입 시 메모리 cascade → 사용자 컨텍스트 augment. **마지막 5 turn + 토큰 cap 1500**.

이게 **H0 자동 해결의 핵심** — 같은 정보 반복 안 묻기.

### 5.2 작업 3.1 — Cognitive stage 수정

**파일**: `backend/app/dream_agent/cognitive/cognitive_stage.py` (수정)

**변경**:
```python
async def cognitive_node(state, config):
    session_id = state["session_id"]
    user_id = state.get("user_id", "demo")
    
    # 신규: 메모리 cascade (5 항목 #3)
    from app.dream_agent.workflow_managers.memory_manager import get_memory_manager
    mm = get_memory_manager()
    context = await mm.get_context(session_id, user_id)
    
    # 마지막 5 turn 추출 (conversation type 만)
    recent_turns = []
    for key, content in context.user_data.items():
        if key.startswith("conversation:"):
            recent_turns.append(content)
    recent_turns.sort(key=lambda c: c.get("completed_at", ""), reverse=True)
    recent_turns = recent_turns[:5]
    
    # 토큰 cap 적용 (5 항목 #4)
    from app.dream_agent.llm_manager.utils import trim_to_token_budget
    recent_turns = trim_to_token_budget(recent_turns, max_tokens=1500)
    
    # 사용자 선호 (preference type)
    preferences = {
        k.replace("preference:", ""): v
        for k, v in context.merged.items()
        if k.startswith("preference:")
    }
    
    # Augmented input
    augmented_query = state["query"]
    if preferences:
        augmented_query += f"\n\n## 사용자 선호 (참고)\n{format_preferences(preferences)}"
    if recent_turns:
        augmented_query += f"\n\n## 이전 대화 (최근 {len(recent_turns)} turn)\n{format_history(recent_turns)}"
    
    logger.info(
        "cognitive memory augmented",
        preferences_count=len(preferences),
        recent_turns_count=len(recent_turns),
    )
    
    # ... 기존 cognitive LLM 호출 (augmented_query 사용)
```

### 5.3 Helper 함수

**파일**: `backend/app/dream_agent/cognitive/memory_format.py` (신규, ~50 LoC)

```python
"""Memory context formatting for Cognitive input.

Status: complete — Sprint 15 P0.
"""

def format_preferences(prefs: dict) -> str:
    """선호 → 자연어 표시."""
    return "\n".join(f"- {k}: {v.get('value')}" for k, v in prefs.items())


def format_history(turns: list[dict]) -> str:
    """대화 이력 → 자연어 표시.
    
    각 turn 을 (사용자 쿼리 + AI 응답 요약) 형태로.
    """
    lines = []
    for i, t in enumerate(turns, 1):
        query = t.get("query", "")
        result_msg = (t.get("result") or {}).get("message") or ""
        # 길면 truncate
        if len(result_msg) > 200:
            result_msg = result_msg[:200] + "..."
        lines.append(f"[Turn {i}] User: {query}\n         AI: {result_msg}")
    return "\n\n".join(lines)
```

### 5.4 Acceptance — E2-3

- [ ] cognitive_node 수정
- [ ] 메모리 cascade + augment 작동
- [ ] format_preferences / format_history helper
- [ ] 통합 테스트: persist_turn → 다음 turn cognitive 가 history 받음

---

## 6. E2-4: 토큰 cap 잘라내기 (#4, ~1시간)

### 6.1 목표

토큰 budget 초과 시 **oldest drop**. POC 단계엔 단순 잘라내기 (요약 = Sprint 16+).

### 6.2 작업 4.1 — Helper 함수

**파일**: `backend/app/dream_agent/llm_manager/utils.py` (신규 또는 추가)

```python
"""LLM utility functions — Sprint 15 P0.

Status: complete — Sprint 15 P0.
"""

import re
from typing import Any


def estimate_tokens(text_or_dict: Any) -> int:
    """간단 토큰 추정 — 한국어 고려.
    
    Heuristic: 한국어 1 char ≈ 1 token, 영어 4 char ≈ 1 token.
    
    POC 단계엔 충분. MVP 시 tiktoken 도입.
    """
    if isinstance(text_or_dict, dict):
        text = str(text_or_dict)
    else:
        text = str(text_or_dict)
    
    # 한국어 character 수
    korean_chars = len(re.findall(r"[가-힣]", text))
    # 비한국어 character 수
    other_chars = len(text) - korean_chars
    
    return korean_chars + (other_chars // 4)


def trim_to_token_budget(
    turns: list[dict], max_tokens: int,
) -> list[dict]:
    """5 항목 #4 — 토큰 budget 초과 시 oldest drop.
    
    Args:
        turns: 시간순 (오래된 것 먼저)
        max_tokens: 토큰 cap (예: 1500)
    
    Returns:
        budget 안에 들어가는 turns (최신부터 유지, oldest drop)
    """
    total = 0
    result = []
    for turn in reversed(turns):  # 최신부터
        cost = estimate_tokens(turn)
        if total + cost > max_tokens:
            break
        result.insert(0, turn)
        total += cost
    return result
```

### 6.3 단위 테스트

**경로**: `backend/tests/sprint15/test_llm_utils_unit.py` (신규)

**TC**:
- TC-LU-01: estimate_tokens 한국어
- TC-LU-02: estimate_tokens 영어
- TC-LU-03: estimate_tokens 혼합
- TC-LU-04: trim_to_token_budget — budget 안 넘침 (전체 유지)
- TC-LU-05: trim_to_token_budget — oldest drop (budget 초과)
- TC-LU-06: trim_to_token_budget — 최신 1개도 budget 초과 (빈 list 반환)

### 6.4 Acceptance — E2-4

- [ ] `llm_manager/utils.py` 신규
- [ ] estimate_tokens + trim_to_token_budget
- [ ] 6 TC 통과

---

## 6.5 E2-5: Conversation List Sidebar (#6 신규, ~2.5시간)

### 6.5.1 목표

대시보드 좌측 sidebar 에 사용자 conversation 목록 표시. ChatGPT/Claude 패턴.

**5 항목 정책 #6 (신규)**:
- 위치: 좌측 sidebar
- 리스트 개수: **최근 5개 + Load More**
- 새 채팅 (conversation) 생성 버튼
- 클릭 시 해당 conversation 의 **최근 5 turn** 로드
- 삭제: conversation 의 turn 만 삭제. user preference 보존

### 6.5.2 작업 5.1 — API endpoints (3개)

**파일**: `backend/api_v2/memory.py` (수정)

```python
@router.get("/conversations/list")
async def list_conversations(
    user_id: str = Query(...),
    offset: int = Query(0, ge=0),
    limit: int = Query(5, le=50),
) -> dict:
    """5 항목 #6 — 사용자 conversation 목록 (최신순, 5 default).
    
    Returns:
        {items: [{conversation_id, title, last_turn_at, turn_count}], total, has_more}
    """
    mm = get_memory_manager()
    metas = await mm.search(
        type="conversation_meta",
        scope_type="user", scope_id=user_id,
    )
    metas.sort(key=lambda e: e.content.get("last_turn_at", ""), reverse=True)
    paginated = metas[offset:offset + limit]
    
    return {
        "items": [
            {
                "conversation_id": e.content.get("conversation_id"),
                "title": e.content.get("title"),
                "last_turn_at": e.content.get("last_turn_at"),
                "turn_count": e.content.get("turn_count"),
            }
            for e in paginated
        ],
        "total": len(metas),
        "has_more": offset + limit < len(metas),
    }


@router.get("/conversations/{conversation_id}/turns")
async def list_conversation_turns(
    conversation_id: str,
    user_id: str = Query(...),
    limit: int = Query(5, le=50),
) -> list[dict]:
    """특정 conversation 의 최근 N turn 로드 (사용자가 sidebar 클릭 시)."""
    mm = get_memory_manager()
    all_turns = await mm.search(
        type="conversation",
        scope_type="user", scope_id=user_id,
    )
    # conversation_id 로 filter
    filtered = [t for t in all_turns if t.content.get("conversation_id") == conversation_id]
    # 최신순 N개
    filtered.sort(key=lambda e: e.content.get("completed_at", ""), reverse=True)
    return [t.model_dump(mode="json") for t in filtered[:limit]]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str = Query(...),
) -> dict:
    """Conversation 삭제 — turn + meta 만. user preference 보존.
    
    삭제 대상:
        - type=conversation 의 모든 turn (content.conversation_id = id)
        - type=conversation_meta key=f"conv_{conversation_id}"
    
    보존:
        - type=preference (사용자 brand 등 — 다음 conversation 활용)
        - type=knowledge
        - 다른 conversation 의 turn
    """
    mm = get_memory_manager()
    
    # 1. turn 삭제
    all_turns = await mm.search(
        type="conversation", scope_type="user", scope_id=user_id,
    )
    deleted_count = 0
    for t in all_turns:
        if t.content.get("conversation_id") == conversation_id:
            await mm.delete(t.key, "user", user_id)
            deleted_count += 1
    
    # 2. meta 삭제
    await mm.delete(f"conv_{conversation_id}", "user", user_id)
    
    return {"deleted_turns": deleted_count, "conversation_id": conversation_id}
```

### 6.5.3 작업 5.2 — 대시보드 좌측 Sidebar UI

**파일**: `dashboard/index.html` (수정)

**HTML 구조 (좌측 sidebar 신규)**:
```html
<div id="app-layout" style="display:flex">
    <!-- 신규 좌측 sidebar -->
    <aside id="conversation-sidebar">
        <button id="new-chat-btn">+ 새 채팅</button>
        <div id="conversation-list"></div>
        <button id="load-more-conv" class="hidden">더 보기</button>
    </aside>
    
    <!-- 기존 메인 (chat + pipeline + result) -->
    <main id="main-content">
        <!-- 기존 컨텐츠 -->
    </main>
</div>
```

**CSS 골격**:
```css
#conversation-sidebar {
    width: 240px;
    background: #1a1a1a;
    border-right: 1px solid #333;
    padding: 12px;
    overflow-y: auto;
}
#new-chat-btn {
    width: 100%;
    padding: 10px;
    background: #2a2a2a;
    color: white;
    border: 1px solid #444;
    cursor: pointer;
}
.conversation-item {
    display: flex;
    align-items: center;
    padding: 8px;
    margin-top: 4px;
    background: #2a2a2a;
    border-radius: 4px;
    cursor: pointer;
}
.conversation-item:hover { background: #333; }
.conversation-item.active { background: #444; }
.conversation-title { flex: 1; overflow: hidden; text-overflow: ellipsis; }
.conversation-delete { color: #888; padding: 4px; cursor: pointer; }
```

**JavaScript**:
```javascript
let _convOffset = 0;
const CONV_PAGE_SIZE = 5;
let _activeConversationId = null;

async function loadConversations(reset = false) {
    if (reset) {
        _convOffset = 0;
        document.getElementById('conversation-list').innerHTML = '';
    }
    
    const res = await fetch(
        `/api/v2/memory/conversations/list?user_id=${USER_ID}&offset=${_convOffset}&limit=${CONV_PAGE_SIZE}`
    );
    const data = await res.json();
    
    const list = document.getElementById('conversation-list');
    data.items.forEach(conv => {
        const div = document.createElement('div');
        div.className = 'conversation-item';
        div.dataset.id = conv.conversation_id;
        div.innerHTML = `
            <div class="conversation-title">${escapeHtml(conv.title)}</div>
            <span class="conversation-delete" data-id="${conv.conversation_id}">🗑</span>
        `;
        div.querySelector('.conversation-title').addEventListener('click', () => 
            switchConversation(conv.conversation_id)
        );
        div.querySelector('.conversation-delete').addEventListener('click', e => {
            e.stopPropagation();
            deleteConversation(conv.conversation_id);
        });
        list.appendChild(div);
    });
    
    _convOffset += data.items.length;
    document.getElementById('load-more-conv').classList.toggle('hidden', !data.has_more);
}

async function switchConversation(conversation_id) {
    _activeConversationId = conversation_id;
    
    // active 표시
    document.querySelectorAll('.conversation-item').forEach(el => 
        el.classList.toggle('active', el.dataset.id === conversation_id)
    );
    
    // 최근 5 turn 로드
    const res = await fetch(
        `/api/v2/memory/conversations/${conversation_id}/turns?user_id=${USER_ID}&limit=5`
    );
    const turns = await res.json();
    
    // 채팅창에 표시 (E2-2 의 renderHistoryTurn 재사용)
    const container = document.getElementById('chat-history');
    container.innerHTML = '';
    turns.reverse().forEach(t => {
        container.appendChild(renderHistoryTurn(t));
    });
    
    // conversation_id 를 현재 turn 에 적용 (다음 query 시 사용)
    _currentConversationId = conversation_id;
}

async function deleteConversation(conversation_id) {
    if (!confirm('이 대화를 삭제할까요? (turn 만 삭제, 사용자 선호는 유지)')) return;
    
    await fetch(
        `/api/v2/memory/conversations/${conversation_id}?user_id=${USER_ID}`,
        { method: 'DELETE' }
    );
    
    // 활성 conversation 이었으면 새 채팅으로
    if (_activeConversationId === conversation_id) {
        startNewChat();
    }
    
    loadConversations(true);  // 목록 reload
}

function startNewChat() {
    _activeConversationId = null;
    _currentConversationId = `conv_${generateId()}`;  // 새 ID
    document.getElementById('chat-history').innerHTML = '';
    document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
}

// 이벤트 wire-up
document.getElementById('new-chat-btn').addEventListener('click', startNewChat);
document.getElementById('load-more-conv').addEventListener('click', () => loadConversations(false));

// 페이지 로드
window.addEventListener('DOMContentLoaded', () => {
    loadConversations(true);
});
```

### 6.5.4 작업 5.3 — 통합 테스트

**경로**: `backend/tests/sprint15/test_conversation_list_integration.py` (신규)

**TC**:
- TC-CL-01: persist_turn → conversation_meta 생성 (첫 turn)
- TC-CL-02: persist_turn 두 번 → meta turn_count 증가
- TC-CL-03: GET /conversations/list — 최신순 5개
- TC-CL-04: GET /conversations/{id}/turns — 5 turn
- TC-CL-05: DELETE /conversations/{id} — turn + meta 삭제, preference 보존
- TC-CL-06: 빈 conversation list (사용자 첫 사용)

### 6.5.5 Acceptance — E2-5

- [ ] 3 endpoint (list / turns / delete)
- [ ] 좌측 sidebar UI
- [ ] 새 채팅 / 클릭 로드 / 삭제 작동
- [ ] 6 TC 통과
- [ ] 사용자 브라우저 검증

### 6.5.6 결정 lock (2026-04-28)

- 위치: **좌측** (사용자 권고대로)
- 리스트 개수: **최근 5개 + Load More** (사용자 권고대로)
- 삭제 정책: **conversation turn 만 삭제, user preference 보존** (권고대로)

---

## 7. 검증 / 테스트 strategy

### 7.1 자동 테스트

```bash
# Phase E-2 단위
pytest backend/tests/sprint15/test_persist_turn_unit.py -v
pytest backend/tests/sprint15/test_llm_utils_unit.py -v

# 전체 회귀
pytest backend/tests/ -v
```

**기대**: 254 (E-1) + 9 (E-2) = **263+ passed**.

### 7.2 통합 시나리오

**E2E 시나리오 — 메모리 통합 작동 확인**:

1. 사용자 첫 turn: `"블루밍글로우 네이버 리뷰 분석"` → 정상 진행 → response 후 persist_turn
2. 사용자 두 번째 turn: `"감성 분석 결과 다시 보여줘"` → cognitive 직전 cascade → 이전 turn 의 brand=블루밍글로우 컨텍스트 자동 첨부
3. 채팅창 reload → 이전 2 turn 자동 표시

### 7.3 메모리 검증 (DB)

```sql
-- 대화 이력 확인
SELECT key, content->'query' as query, source, created_at
FROM memory_entries
WHERE type = 'conversation' AND scope_type = 'user' AND scope_id = 'demo'
ORDER BY created_at DESC
LIMIT 10;

-- 토큰 cap 동작 확인 (긴 대화 후)
-- log 에서 trim_to_token_budget 호출 횟수 / 결과 count 확인
```

---

## 8. Risk + 완화

| Risk | 완화 |
|------|------|
| persist_turn 실패 → turn 진행 막힘 | try/except wrap (non-blocking) |
| 메모리 cascade DB 호출 latency | turn 단위 in-memory cache (Phase E-3 통합 시 추가) |
| 토큰 cap heuristic 부정확 | tiktoken 도입 (Sprint 16+) — POC 단순 |
| Load More 무한 스크롤 시 페이지네이션 충돌 | offset 기반 + has_more flag |
| persist_turn 중복 (재시도 시) | upsert 의 unique key (timestamp 포함) — 충돌 가능성 낮음 |
| 채팅 history UX 부담 (오래된 것 위에) | "Load More" 버튼 명시 — 무한 스크롤 X |

---

## 9. 완료 체크리스트

### E2-1 persist_turn
- [ ] MemoryManager.persist_turn 추가
- [ ] response_stage 통합
- [ ] try/except wrap
- [ ] 3 TC 통과

### E2-2 채팅창 로드
- [ ] `/api/v2/memory/conversations` endpoint
- [ ] 대시보드 자동 로드 + Load More
- [ ] 사용자 브라우저 검증

### E2-3 Cognitive cascade
- [ ] cognitive_node 수정
- [ ] format helpers
- [ ] persist_turn → cascade 통합 시나리오 작동

### E2-4 토큰 cap
- [ ] `llm_manager/utils.py` 신규
- [ ] estimate_tokens + trim_to_token_budget
- [ ] 6 TC 통과

### E2-5 Conversation list sidebar (#6, 신규)
- [ ] 3 endpoint (list / turns / delete)
- [ ] 좌측 sidebar UI (HTML / CSS / JS)
- [ ] 새 채팅 + 클릭 로드 + 삭제
- [ ] 6 TC 통과

### Phase E-2 종합
- [ ] 자동 테스트 269+ passed (263 + E2-5 6)
- [ ] E2E 시나리오 작동 (사용자 1차 turn → 2차 turn 컨텍스트 자동)
- [ ] sidebar conversation 관리 작동
- [ ] 커밋 (`feat(sprint15): Phase E-2 채팅 메모리 통합 — persist_turn + 채팅창 + cascade + 토큰 cap + Conversation sidebar`)
- [ ] 다음 [`sprint15_phase_e3_clarification.md`](./sprint15_phase_e3_clarification.md)

---

## 10. 다음 Phase 연결

Phase E-2 완료 후 → **Phase E-3**: Clarification HITL (5 항목 #5)

특히 **Cognitive cascade (E2-3)** 가 Phase E-3 의 **메모리 자동 답 활용** 의 입력.

[`sprint15_phase_e3_clarification.md`](./sprint15_phase_e3_clarification.md) 참조.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-28 | 초안 — Phase E-2 4 sub-phase. persist_turn + 채팅창 + cascade + 토큰 cap. ~4h 추정. 9 TC + E2E 시나리오 |
| 2026-04-28 | **E2-5 Conversation list sidebar (#6) 추가** — 사용자 요구로 신규. 좌측 sidebar + 최근 5개 + Load More + 새 채팅 + 삭제 (turn 만, preference 보존). +2.5h, persist_turn 에 conversation_meta 저장 추가. 5 항목 정책 → 6 항목 |
| 2026-04-29 | **persist_turn schema 갱신** — 35 spec §0.1 설계 원칙 적용. content 안에 `schema_version: "v1"` + `messages` 배열 (append-only) + `metadata` (자유 영역). 의도적 단순 (message type 정확한 분류 / summary 생성 방법 = 쓰면서 결정). Clarification messages 통합 정책 (별도 row X) |
