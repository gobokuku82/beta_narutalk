# 61. Frontend Architecture — State / Routing / Component / Design System

| 항목 | 내용 |
|------|------|
| 버전 | v1.0 |
| 작성일 | 2026-05-13 |
| 상태 | Accepted |
| 의존 | [60_frontend_overview_v1.0.md](60_frontend_overview_v1.0.md) (진입점) |
| 관련 | [62 Workflow Canvas](62_workflow_canvas_design_v1.2.md) / [63 Backend Contract (예정)](.) |

---

## 0. 본 문서의 역할

60 Overview 에서 결정된 Tech Stack 의 **architecture 4 영역** 통합:

1. **State** — Zustand store 구성 (UI 상태) + TanStack Query (서버 상태)
2. **Routing** — 라우트 15개 + Global / Workspace 레이아웃 (2026-06-01 정합 갱신)
3. **Component Inventory** — shadcn/ui primitives + features 폴더 구조
4. **Design System** — 색상 토큰 / 타이포 / 다크 모드 / 컴포넌트 스타일

> 본 문서는 [`docs/_claude/new_frontend/04/05/06/08/09`](../_claude/new_frontend/) 5 문서를 옵션 A (Zustand + TanStack Query) 기준으로 재정리한 정식 spec.

---

## 1. State Architecture

### 1.1 두 종류의 상태 — 분리 원칙

| 종류 | 도구 | 특징 |
|------|------|------|
| **UI 상태 (Client State)** | **Zustand** | 인메모리, persist 옵션, WebSocket 수신 처리 |
| **서버 상태 (Server State)** | **TanStack Query** | 캐시 / 무효화 / 백그라운드 refetch / Suspense |

**원칙**: 서버에서 오는 데이터는 절대 Zustand 에 복사 X. TanStack Query 의 cache 가 진실. Zustand 는 **클라이언트 only 상태** (모달 open / 선택된 노드 id / 입력값 등).

### 1.2 Zustand Store 구성 — 7 store

```
src/stores/
├─ auth.ts           # 인증 / 세션 토큰 (Sprint 6+)
├─ session.ts        # 현재 conversation_id / turn_id / active state
├─ agent.ts          # 채팅 메시지 / 노드 이벤트 (WS 수신, 메모리만)
├─ hitl.ts           # plan_review modal / pause 상태 / pending edit
├─ workflow.ts       # 노드 / 엣지 / position / selected_node_id (62)
├─ attachments.ts    # 업로드 진행 / 미리보기 (Sprint 4+)
└─ settings.ts       # 테마 / 사용자 preference
```

#### auth store (Sprint 6+)

```typescript
// stores/auth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  userId: string | null;
  email: string | null;
  setUser: (user: { id: string; email: string }) => void;
  logout: () => void;
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      userId: null,
      email: null,
      setUser: ({ id, email }) => set({ userId: id, email }),
      logout: () => set({ userId: null, email: null }),
    }),
    { name: 'auth-storage' }
  )
);
```

#### session store

| 필드 | 타입 | 역할 |
|------|------|------|
| `conversationId` | `string \| null` | 현재 대화 |
| `turnId` | `string \| null` | 현재 진행 turn |
| `connectionStatus` | `'connected' \| 'reconnecting' \| 'closed'` | WebSocket 상태 |
| `setConversation(id)` | function | 대화 전환 |
| `setTurn(id)` | function | turn 시작 |
| `resetTurn()` | function | turn 종료 (cleanup) |

#### agent store (가장 무거움)

| 필드 | 타입 | 역할 |
|------|------|------|
| `messages` | `ChatMessage[]` | 누적 채팅 메시지 (in-memory only — 영속화 X, 서버 refetch) |
| `nodeEvents` | `NodeEvent[]` | cognitive/planning/execution/response 이벤트 (`node_event` 수신) |
| `appendUserMessage(content)` | function | 사용자 query 송신 시 |
| `appendNodeEvent(msg)` | function | `node_event` WS 수신 시 |
| `finalizeFromComplete(data)` | function | `complete` 수신 — `data.response.text` 를 assistant 메시지로 |
| `clearTurn()` | function | turn 종료 시 |

> ⚠️ **검증 정정 (2026-05-15, 사이클 3)**: 백엔드는 토큰 스트리밍(`agent_message`)을 발행하지 않으므로 `streamingMessage`/`streamingBuffer`/`appendStreamingChunk` 류 필드는 **데드코드** — 제거 대상. 최종 응답은 `complete.data.response` 1회 수신. 메시지는 백엔드 DB (memory_entries) 가 진실, Zustand 는 **현재 보이는 turn 만** 캐시.

#### hitl store

| 필드 | 타입 | 역할 |
|------|------|------|
| `modalOpen` | `boolean` | plan_review modal 표시 |
| `pendingRequest` | `HitlRequest \| null` | 현재 응답 대기 요청 |
| `editMode` | `'structured' \| 'nl' \| null` | 편집 UI 모드 |
| `nlInput` | `string` | NL textarea 입력값 (전송 전 보존) |
| `cascadeResult` | `{invalidated, preserved, restart_from} \| null` | 마지막 ack 결과 (UI tint) |
| `setPending(r)` / `clearPending()` / `setEditMode(m)` | functions | — |

#### workflow store (62 연동)

| 필드 | 타입 | 역할 |
|------|------|------|
| `nodes` | `Node[]` (React Flow) | 캔버스 노드 (position 포함) |
| `edges` | `Edge[]` | depends_on 매핑 |
| `selectedNodeId` | `string \| null` | 속성 패널에 표시할 노드 |
| `mode` | `'list' \| 'graph'` | toggle 상태 |
| `layoutDirection` | `'TB' \| 'LR'` | dagre 방향 (Top-Bottom / Left-Right) |
| `setPlan(plan)` | function | 백엔드 plan → 노드/엣지 변환 + dagre 자동 배치 |
| `updateNodePosition(id, pos)` | function | 드래그 시 |
| `selectNode(id)` | function | 더블클릭 시 |

#### attachments / settings store (Sprint 4+ / Sprint 0)

생략 — slim 한 구조 (각 ~30 LoC).

### 1.3 영속화 정책

| Store | persist? | 이유 |
|-------|---------|------|
| auth | ✅ | localStorage. 재방문 시 자동 로그인 |
| settings | ✅ | 테마 / 언어 preference |
| session | ❌ | 매 페이지 로드 시 백엔드 refetch |
| agent | ❌ | 메시지는 백엔드 DB 가 진실 |
| hitl | ❌ | turn 종료 시 자동 reset |
| workflow | ⚠️ 부분 | mode / layoutDirection 만 persist. 노드/엣지는 plan 에서 재계산 |
| attachments | ❌ | 업로드 진행은 ephemeral |

**원칙**: 영속화는 사용자 preference 와 인증만. 서버에서 다시 가져올 수 있는 것은 절대 persist 안 함.

### 1.4 Server State — TanStack Query

#### Query keys 규약

```typescript
// src/api/queryKeys.ts
export const queryKeys = {
  conversations: {
    all: ['conversations'] as const,
    list: () => [...queryKeys.conversations.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.conversations.all, 'detail', id] as const,
  },
  turns: {
    all: ['turns'] as const,
    list: (conversationId: string) => [...queryKeys.turns.all, 'list', conversationId] as const,
    detail: (id: string) => [...queryKeys.turns.all, 'detail', id] as const,
  },
  memory: {
    all: ['memory'] as const,
    byScope: (userId: string, scope: string) => [...queryKeys.memory.all, userId, scope] as const,
    workflowTemplates: (userId: string) => [...queryKeys.memory.all, userId, 'workflow_template'] as const,
  },
  attachments: {
    list: (turnId: string) => ['attachments', turnId] as const,
  },
};
```

#### Hook 패턴

```typescript
// src/api/hooks/useConversations.ts
import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../queryKeys';
import { rest } from '../rest';
import { ConversationListSchema } from '../schemas';

export function useConversations(limit = 20) {
  return useQuery({
    queryKey: queryKeys.conversations.list(),
    queryFn: async () => {
      const data = await rest.get(`/api/conversations?limit=${limit}`);
      return ConversationListSchema.parse(data);  // zod 검증
    },
    staleTime: 30 * 1000,
  });
}
```

#### 카테고리

| Hook | 백엔드 endpoint | 캐시 정책 |
|------|----------------|----------|
| `useConversations()` | `GET /api/conversations` | 30s stale |
| `useConversation(id)` | `GET /api/conversations/:id` | 1min stale |
| `useTurns(convId)` | `GET /api/conversations/:id/turns` | 10s stale |
| `useMemory(userId, scope)` | `GET /api/memory?...` | 1min stale (Sprint 15+) |
| `useWorkflowTemplates(userId)` | `GET /api/memory?type=workflow_template` | 5min stale (Sprint 15 P1) |
| `useSaveTemplate()` (mutation) | `POST /api/memory` | invalidate list |
| `useApplyTemplate()` (mutation) | `POST /api/memory/:id/apply` | — |

### 1.5 WebSocket 통합 — Zustand store update

> ⚠️ **검증 정정 (2026-05-15, 사이클 3)**: 이전 예시는 단일 `setupWebSocket(url)` 에 `agent_message` 케이스를 두고 `hitl_request` 를 같은 핸들러에서 받았으나 — (1) `agent_message` 는 백엔드 미발행, (2) 채널이 `/ws/agent` 와 `/ws/hitl` 둘로 나뉘고 메시지 종류가 채널별로 다름. 채널별 핸들러로 분리하고 spec 21 §2.2 / §3.2 의 실제 이벤트만 라우팅. 진실 소스 = [21](21_WEBSOCKET_PROTOCOL_v1.5.md) + [63 §4](63_frontend_backend_contract_v1.0.md).

```typescript
// src/api/ws.ts (간략) — 채널별 핸들러 분리
import { useAgent } from '@/features/agent/store';
import { useHitl } from '@/features/hitl/store';
import { useSession } from '@/features/session/store';

// /ws/agent 수신 — node_event / hitl_request / paused / resumed / complete / error / callback 4종
function handleAgentMessage(msg: WSMessage) {
  switch (msg.type) {
    case 'connected':   useSession.getState().setConnectionStatus('connected'); break;
    case 'node_event':  useAgent.getState().appendNodeEvent(msg); break;
    case 'hitl_request': useHitl.getState().setPending(msg.data); break;
    case 'paused':      useHitl.getState().setPaused(msg.data); break;
    case 'resumed':     useHitl.getState().clearPending(); break;
    case 'complete':    useAgent.getState().finalizeFromComplete(msg.data);
                        useSession.getState().resetTurn(); break;
    case 'error':       useSession.getState().setError(msg); break;
    // layer_start / todo_start / todo_complete / progress — 진행 표시
  }
}

// /ws/hitl 수신 — connected / hitl_ack / error / pong
function handleHitlMessage(msg: WSMessage) {
  switch (msg.type) {
    case 'hitl_ack': useHitl.getState().setCascadeResult(msg.data); break;
    case 'error':    useSession.getState().setError(msg); break;
  }
}
```

**원칙**:
- WS 메시지 = zod 검증(`WSMessageSchema`, [63 §4.3](63_frontend_backend_contract_v1.0.md)) 후 store update. **스키마가 백엔드와 정합해야 함** — 어긋나면 `safeParse` 가 전량 폐기 (이번 검증의 핵심 발견).
- 검증 실패 = console.error + 무시 (silent fail X — 디버깅)
- `node_event` 의 `data` 는 노드 State update dict — store 에서 `node` 키로 분기해 `structured_query`/`plan`/`execution_result`/`response` 추출
- store 의 setter 는 항상 immutable

### 1.6 v1 (Redux) → v2 (Zustand) 매핑

| v1 (Redux) | v2 (Zustand) | 변경점 |
|-----------|--------------|--------|
| `authSlice` | `useAuth` store | Provider 제거 / useSelector 제거 |
| `sessionSlice` | `useSession` store | 동일 |
| `agentSlice` | `useAgent` store | extraReducers 제거 (선택 X) |
| `hitlSlice` | `useHitl` store | 동일 |
| `attachmentsSlice` | `useAttachments` store | 동일 |
| `settingsSlice` | `useSettings` store | persist middleware 동일 |
| RTK Query (api) | TanStack Query hooks | endpoints → 개별 hook 파일 |
| `wsMiddleware` | `setupWebSocket()` 모듈 | store 라우팅 더 명시적 |
| `redux-persist` | `zustand persist` middleware | 1줄로 감 |

**코드량 절감**: ~40% (Provider / Selector / dispatch / action creators 모두 제거)

---

## 2. Routing — 15 라우트 (2026-06-01 v2 정합 갱신)

> **Layout 결정 변경** (2026-05-13 v1.1): 사용자 통찰 "동료 화면 + 채팅 지시" 반영하여 **v1 GlobalLayout 패턴** 채택. Conversation-first → Dashboard + Side Chat 으로 전환.
>
> **2026-06-01 정합 갱신**: cross-client 분석 라우트 폐기 (commit `fba80fd`). 포트폴리오 4 → 3 라우트.

### 2.1 라우트 매트릭스 (포트폴리오 / 클라이언트 컨텍스트별)

#### 포트폴리오 컨텍스트 (3 라우트, 2026-06-01 정합)

| 경로 | 화면 | 데이터 source |
|------|------|--------------|
| `/portfolio` | PortfolioPage (placeholder, MVP+ 다중 client) | — |
| `/hitl` | HitlCenterPage | HITL pause/resume |
| `/report` | ReportPage (placeholder) | — |

#### 클라이언트 컨텍스트 (도메인 dashboard 라우트 — 예시)

> ⚠️ 아래 dashboard 라우트의 데이터 source (`/api/dashboard1/*`, `/api/admin/pipelines/*`) 는 **deleted** — 도메인별 dashboard 페이지는 재정의 대상. 라우팅 패턴(클라이언트 컨텍스트 + GlobalLayout)만 framework.

| 경로 | 화면 | 데이터 source |
|------|------|--------------|
| `/dashboard` (예시) | 도메인 dashboard 페이지 | (도메인 데이터 source — 재정의) |
| `/agent` | AgentChatPage (전체화면 채팅) | ws_agent |
| `/workflow` | WorkflowPage (React Flow) | (Plan/Todo) |
| `/memory` + `/conversations` | (Sprint 15+ 예정) | (memory_entries) |
| `/report` | ReportPage | 통합 |

#### 신규 (Sprint 15+) — v2 vision

| 경로 | 화면 | Sprint | 출처 spec |
|------|------|--------|---------|
| `/workflow` | Workflow Canvas (React Flow) | 2 (W1) | 62 |
| `/memory` | Memory View + Template Library | 5 | 35 / 62 W3 |
| `/conversations` | 대화 이력 / 검색 | 4 | E2-5 |

#### 공통

| 경로 | 화면 |
|------|------|
| `/settings/*` | 설정 (theme / account / advanced) |

### 2.2 라우터 선택 — TanStack Router 또는 React Router v7

**Sprint 0 결정 권장** (1 day PoC):
- **TanStack Router**: 100% 타입 안전 / file-based + code-based / TanStack Query 자연 통합
- **React Router v7**: Data API (loader/action) / Remix 흡수 / 더 익숙 (v6 경험자)

→ **POC 후 결정**. 둘 다 v6 보다 우수. (60 §2.1 표 참조)

### 2.3 GlobalLayout (v1 패턴 채택, 모든 라우트 공통)

> **변경 (2026-05-13 v1.1)**: 사용자 통찰 "동료 화면 + 채팅 지시" 반영. v1 frontend 의 `GlobalLayout` 구조 그대로 채택.

```
┌────────────────────────────────────────────────────────────────────┐
│ TopBar (h-16)                                                       │
│   로고 / 클라이언트 선택 / 날짜 / 알림 / 💬 채팅 토글 / 사용자       │
├──────┬──────────────────────────────────────┬──────────────────────┤
│ Side │                                       │ ◀ Resizer            │
│ bar  │  Outlet (선택된 페이지 = 대쉬보드)     │   (300~600px)        │
│      │                                       │ ┌──────────────────┐ │
│ w-20 │  - 도메인 dashboard 페이지 (예시) / │ │ SideChatPanel    │ │
│ 다크 │    HitlCenter /                      │ │ - Connected 표시 │ │
│      │    PortfolioView / Report /          │ │ - ChatCore       │ │
│ icon │    AgentChat (전체화면)              │ │   compact 모드   │ │
│ +    │  - WorkflowCanvas / Memory /         │ │ - 전체화면 버튼   │ │
│ 라벨 │    Templates / Conversations         │ │ - 닫기 버튼      │ │
│      │                                       │ │                  │ │
│      │                                       │ │ 슬라이드 인/아웃  │ │
│      │                                       │ │ (translate-x)    │ │
│      │                                       │ └──────────────────┘ │
└──────┴──────────────────────────────────────┴──────────────────────┘
```

**핵심 패턴**:
- TopBar = 컨텍스트 표시 + 채팅 토글 (💬 버튼)
- Sidebar = 컨텍스트별 메뉴 자동 전환 (포트폴리오 ↔ 클라이언트)
- Outlet = 메인 작업 영역 (대쉬보드 또는 신규 영역)
- SideChatPanel = 우측 호출형 (toggle / 리사이즈 / 영속화)

**컨텍스트별 Sidebar 메뉴**:
- 포트폴리오: 포트폴리오 / 사용자개입 / 리포트
- 클라이언트:
  - 도메인 dashboard 페이지 (예시) / 사용자개입 / 에이전트 / 리포트
  - 신규 (Sprint 15+): 워크플로우 / 메모리 / 대화이력 (3탭)
  - (그룹화 권장: "분석" / "AI")

### 2.4 SideChatPanel — 호출형 채팅 (v1 패턴 + v2 확장)

```
┌──────────────────────────────────┐
│ 헤더: 대화 선택 ▾ + Connected     │
│        + 전체화면 / 닫기          │
├──────────────────────────────────┤
│ 메시지 누적 (스크롤)              │
│  - chat message                  │
│  - node event indicator          │
│  - Plan review (인라인)          │
│  - Clarification HITL            │
├──────────────────────────────────┤
│ 컨텍스트 칩 (현재 보는 대쉬보드)   │
│ "📊 도메인 dashboard · ENT-001"  │
├──────────────────────────────────┤
│ 자연어 입력창                     │
│ [⚡ 적용]                         │
└──────────────────────────────────┘
```

**메커니즘**:
- `chatPanelStore.isOpen` boolean — TopBar 💬 또는 어디서든 `openChatPanel()`
- 너비 300~600px 사용자 드래그 + 영속화 (zustand persist)
- 전체화면 = `navigate('/agent')` + `closeChatPanel()`
- ESC / X = `closeChatPanel()`

**v1 대비 확장**:
- 대화 선택 dropdown (E2-5 sidebar 와 연동)
- Plan review modal → SideChatPanel 안 인라인
- Clarification HITL 통합
- 컨텍스트 자동 첨부 (대쉬보드 차트 클릭 시 채팅에 전달)

### 2.5 라우트 가드 (Sprint 6+ 인증 후)

```typescript
// src/routes/_protected.tsx (Sprint 6+)
import { useAuth } from '@/stores/auth';
import { Navigate } from '@tanstack/react-router';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { userId } = useAuth();
  if (!userId) return <Navigate to="/login" />;
  return <>{children}</>;
}
```

---

## 3. Component Inventory

### 3.1 폴더 구조

```
src/components/
├─ ui/                    # shadcn/ui primitives (CLI 설치)
│  ├─ button.tsx
│  ├─ dialog.tsx
│  ├─ dropdown-menu.tsx
│  ├─ input.tsx
│  ├─ select.tsx
│  ├─ tabs.tsx
│  ├─ toast.tsx (Sonner 통합)
│  ├─ tooltip.tsx
│  ├─ resizable.tsx
│  ├─ sheet.tsx
│  ├─ form.tsx (react-hook-form 통합)
│  └─ ... (15+ 확장)
├─ layout/
│  ├─ GlobalLayout.tsx
│  ├─ TopBar.tsx
│  ├─ Sidebar.tsx
│  └─ Workspace.tsx
├─ markdown/
│  └─ MarkdownRenderer.tsx  # react-markdown + remark-gfm
├─ features/
│  ├─ agent/
│  │  ├─ ChatPanel.tsx
│  │  ├─ MessageCard.tsx
│  │  ├─ NodeEventList.tsx
│  │  └─ StreamingMessage.tsx
│  ├─ conversations/
│  │  ├─ ConversationList.tsx
│  │  ├─ ConversationItem.tsx
│  │  └─ NewConversationButton.tsx
│  ├─ hitl/
│  │  ├─ PlanReviewModal.tsx
│  │  ├─ ClarificationModal.tsx (Sprint 15 P1)
│  │  └─ CascadeIndicator.tsx
│  ├─ workflow/                  # 62 ⭐
│  │  ├─ WorkflowCanvas.tsx
│  │  ├─ NodeComponent.tsx
│  │  ├─ EdgeComponent.tsx
│  │  ├─ PropertyPanel.tsx
│  │  ├─ NodeLibrary.tsx (W4)
│  │  └─ TemplateLibrary.tsx (W3)
│  ├─ attachments/ (Sprint 4+)
│  │  ├─ AttachmentGallery.tsx
│  │  └─ AttachmentCard.tsx
│  ├─ memory/ (Sprint 5+)
│  │  ├─ MemoryView.tsx
│  │  └─ MemoryEntry.tsx
│  └─ auth/ (Sprint 6+)
│     ├─ LoginForm.tsx
│     └─ UserMenu.tsx
└─ index.ts
```

### 3.2 shadcn/ui primitives (Sprint 0 설치)

| 컴포넌트 | 용도 | 의존 |
|---------|------|------|
| `button` | 모든 액션 | — |
| `dialog` | Plan review modal / Save modal | Radix Dialog |
| `dropdown-menu` | TopBar 사용자 메뉴 / 노드 우클릭 | Radix DropdownMenu |
| `input` / `textarea` | 폼 입력 | — |
| `select` | 노드 속성 (tool / agent 선택) | Radix Select |
| `tabs` | Workspace 토글 / 설정 | Radix Tabs |
| `tooltip` | 노드 hover / 아이콘 힌트 | Radix Tooltip |
| `toast` | Sonner | sonner |
| `resizable` | 3-패널 분할 | react-resizable-panels |
| `sheet` | 우측 속성 패널 (62) | Radix Dialog |
| `form` | react-hook-form 통합 | react-hook-form |
| `card` | 메시지 카드 / 템플릿 카드 | — |
| `badge` | 상태 표시 (running / completed / failed) | — |
| `separator` | 시각적 구분 | Radix Separator |
| `scroll-area` | 긴 list 스크롤 | Radix ScrollArea |

**설치 명령** (Sprint 0):
```bash
npx shadcn@latest init
npx shadcn@latest add button dialog dropdown-menu input select tabs tooltip toast resizable sheet form card badge separator scroll-area
```

### 3.3 외부 라이브러리 채택 매트릭스

| 영역 | 채택 | 사유 |
|------|------|------|
| Dialog / Dropdown / Select / Tabs / Tooltip | Radix UI (shadcn/ui 가 wrap) | 접근성 표준 |
| Toast | Sonner | 모던 디자인 / 가벼움 |
| 3-패널 | react-resizable-panels (shadcn Resizable) | 표준 |
| 아이콘 | lucide-react | 트리쉐이킹 / 일관성 |
| 마크다운 | react-markdown + remark-gfm | XSS 방어 (자체 구현 금지) |
| 그래프 캔버스 | **@xyflow/react (React Flow)** ⭐ | 62 결정 |
| 자동 레이아웃 | **dagre** | 62 결정 |
| 폼 | react-hook-form + zod | 성능 + 검증 |
| 테이블 | TanStack Table | 표준 |
| 차트 | Recharts | v1 사용 경험 |

### 3.4 Component props 일관성 규칙

#### 명명
- `onXxx` (e.g., `onSave`, `onDelete`) — 핸들러
- `xxxOpen` (e.g., `modalOpen`) — boolean state
- `defaultXxx` — uncontrolled 초기값
- `xxx` (state) + `onXxxChange` — controlled

#### children vs render props
- 기본 children pattern (React 컨벤션)
- render props 는 list / tree 같은 동적 렌더링만

#### Optional vs required
- prop 의 95% 이상이 사용되는 경우 → required
- 나머지 → optional + default

### 3.5 v1 → v2 컴포넌트 매핑

| v1 컴포넌트 | v2 위치 | 변경 |
|------------|---------|------|
| `pages/Dashboard.tsx` (vanilla) | `routes/conversations.$id.tsx` | React 19 + Router |
| `components/Chat.tsx` | `features/agent/ChatPanel.tsx` | shadcn/ui 통합 |
| `components/TodoList.tsx` | `features/workflow/{WorkflowCanvas|TodoList}.tsx` | toggle UI |
| `components/HitlModal.tsx` | `features/hitl/PlanReviewModal.tsx` | shadcn Dialog |
| `components/CascadeView.tsx` | `features/hitl/CascadeIndicator.tsx` | 분리 |

---

## 4. Design System

> **단일 진실 = [spec 64 Design System](64_design_system_v1.0.md)** (high-level 결정·이유·자취·메타룰) + `frontend/src/styles/*.md` (카테고리별 토큰 표).
> 본 §4 = 60번대 spec 시스템 안 link 표. 디자인 결정/룰 변경 시 spec 64 + styles/*.md 갱신.

### 4.0 카테고리별 단일 진실 link

| 카테고리 | 단일 진실 | 박제 상태 |
|---|---|---|
| Color | [`styles/PALETTE.md`](../../frontend/src/styles/PALETTE.md) | ✅ v1 (2026-06-08) |
| Typography | [`styles/TYPOGRAPHY.md`](../../frontend/src/styles/TYPOGRAPHY.md) | ✅ v1 (2026-06-08) |
| Spacing | [`styles/SPACING.md`](../../frontend/src/styles/SPACING.md) | ✅ v1 (2026-06-08, Phase 2) |
| Radius | [`styles/RADIUS.md`](../../frontend/src/styles/RADIUS.md) | ✅ v1 (2026-06-08, Phase 3) |
| Motion | [`styles/MOTION.md`](../../frontend/src/styles/MOTION.md) | ✅ v1 (2026-06-08, Phase 5) |
| Elevation | [`styles/ELEVATION.md`](../../frontend/src/styles/ELEVATION.md) | ✅ v1 (2026-06-08, Phase 6) |
| Layout | [`styles/LAYOUT.md`](../../frontend/src/styles/LAYOUT.md) | ✅ v1 (2026-06-08, Phase 4) |

→ 메타룰 (MR1 임의값 금지 등) + 8 카테고리 통합 view = **spec 64**.

### 4.1 색상 토큰 (CSS Variables) — PALETTE.md 참조

> **단일 진실 = [`PALETTE.md`](../../frontend/src/styles/PALETTE.md)** + [`globals.css`](../../frontend/src/styles/globals.css).
> 본 절은 진화 자취만 유지. 토큰 값/룰 변경 시 PALETTE.md 갱신.

shadcn/ui 패턴 — `:root` 에 HSL 정의 + Tailwind `hsl(var(--name))` 매핑.

**현 비주얼 = "2026 Warm Neutral + Warm Dusty"** (2026-06-08):
 - 베이스 : 따뜻한 모래/스톤 뉴트럴 (`--background` 39° 38% 96%)
 - 액센트 : 옥스블러드/마호가니 1개 (`--primary` 350° 55% 38%)
 - 절제 : 그라데이션·glow 0, hairline 보더
 - 5 룰 : 채도 ≤60% / 명도 38~56% / hue 자유 / 역할별 segmentation / WCAG AA
 - 다크 모드 : 라이트 invert (L+12, S+2, hue 동일)

#### 진화 자취

| 시점 | 변경 | 자취 |
|---|---|---|
| Sprint 0 | shadcn 기본값 (회색/blue) | 초기 placeholder |
| 2026-05-13 | "2026 Warm Neutral" — 따뜻한 베이지 + 옥스블러드 | memory `feedback_no_ai_looking_ui` |
| 2026-05-22 | A2 — `--chart-1~5` 비채널 다계열 / `--channel-*` 채널 분해 분리 | 통합계획서 §5.4 |
| 2026-06-08 (1) | Warm Dusty — status/chart 채도 격차 해소 | commit `9625cea` |
| 2026-06-08 (2) | **palette 5 룰 박제** ([PALETTE.md](../../frontend/src/styles/PALETTE.md) v1) | 본 문서 §4.1 단순화 |

상세 토큰 표 / 새 색 추가 절차 / 다크 변환 룰 = **PALETTE.md** 참조.

#### 의미적 토큰 (workflow 전용)

```css
:root {
  --node-task: 220 8% 90%;          /* 회색 */
  --node-branch: 45 100% 70%;       /* 노랑 */
  --node-start: 142 76% 36%;        /* 녹색 */
  --node-end: 217 91% 60%;          /* 청색 */
  --node-running: 0 84% 60%;        /* 빨강 (펄스) */
  --node-completed: 142 76% 30%;    /* 진녹색 */
  --node-failed: 0 84% 40%;         /* 진빨강 */
  --node-invalidated: 0 100% 90%;   /* 🔴 tint */

  --edge-default: 240 5% 65%;
  --edge-invalidated: 0 84% 60%;
}
```

### 4.2 Tailwind config 통합

```typescript
// tailwind.config.ts
export default {
  content: ['./src/**/*.{ts,tsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        // ... 모든 토큰 매핑
        node: {
          task: 'hsl(var(--node-task))',
          branch: 'hsl(var(--node-branch))',
          // ...
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans: ['Pretendard', 'system-ui', 'sans-serif'],
      },
    },
  },
};
```

### 4.3 타이포그래피 — TYPOGRAPHY.md 참조

> **단일 진실 = [`TYPOGRAPHY.md`](../../frontend/src/styles/TYPOGRAPHY.md)** + [`tailwind.config.ts`](../../frontend/tailwind.config.ts).
> font-family · scale · weight · 사용 룰 · 임의값 폐기 룰 = 본 문서 참조.

**현 결정 요약** (2026-06-08 v1):
- 폰트 = Pretendard sans + tabular-nums (숫자)
- Scale 8 단계 = `text-2xs` (10px, 신설) ~ `text-3xl` (30px)
- Weight 4 단계 = `font-normal` / `font-medium` (default) / `font-semibold` (강조) / `font-bold` (Hero)
- **임의값 금지** (T1) — `text-[Npx]` 사용 X. 이전 57건 임의값 (text-[9/10/11px]) → `text-2xs` 통일

### 4.4 간격 / 반경 / 그림자

| 토큰 | 값 |
|------|-----|
| `--radius` | 0.5rem (8px) — 카드 / 노드 |
| `--radius-sm` | 0.25rem (4px) — 버튼 / input |
| `--shadow-sm` | shadow-sm Tailwind 기본 |
| `--shadow-md` | shadow-md — 모달 / Sheet |

### 4.5 다크 모드 전환

```typescript
// src/stores/settings.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useSettings = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'light' as 'light' | 'dark' | 'system',
      setTheme: (theme) => {
        set({ theme });
        applyTheme(theme);
      },
    }),
    { name: 'settings' }
  )
);

function applyTheme(theme: 'light' | 'dark' | 'system') {
  const resolved = theme === 'system'
    ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : theme;
  document.documentElement.setAttribute('data-theme', resolved);
}
```

### 4.6 컴포넌트 스타일 패턴 — cn() 헬퍼

```typescript
// src/lib/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// 사용 예
<button className={cn(
  'px-4 py-2 rounded',
  variant === 'primary' && 'bg-primary text-primary-foreground',
  variant === 'secondary' && 'bg-secondary text-secondary-foreground',
  disabled && 'opacity-50 cursor-not-allowed',
  className,  // 호출자 override
)} />
```

### 4.7 cva (class-variance-authority) — variant 패턴

shadcn/ui 가 사용. 컴포넌트 props 로 variant / size 받기.

```typescript
import { cva } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground',
        destructive: 'bg-destructive text-destructive-foreground',
        outline: 'border border-input',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 px-3',
        lg: 'h-11 px-8',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  }
);
```

---

## 5. Storybook 가이드 (선택, MVP+)

### 우선순위 대상
- Button / Card / Badge / Input (primitives)
- WorkflowCanvas 의 노드 타입 (W1 후)
- MessageCard
- ClarificationModal (Sprint 15 P1)

### 폴더
```
src/components/ui/button.tsx
src/components/ui/button.stories.tsx
```

→ Sprint 0 에 setup 만. story 작성은 MVP 진입 시.

---

## 6. 테스트 전략

### 6.1 단위 (Vitest + Testing Library)

- Zustand store 로직
- 컴포넌트 렌더링 (props → UI)
- 헬퍼 함수 (cn, dagre 레이아웃)

### 6.2 통합 (Vitest + MSW)

- TanStack Query hooks + 모의 backend
- WebSocket 수신 → store update

### 6.3 E2E (Playwright)

- 자연어 입력 → Plan 시각화 → 편집 → 결과
- Multi-tab / 새로고침 복원

### 6.4 Visual (Storybook + Chromatic, 선택)

- 컴포넌트 시각 회귀

---

## 7. v1 → v2 마이그레이션 우선순위

| Phase | 작업 | Sprint |
|-------|------|--------|
| Phase 1 | Sprint 0 셋업 (디렉터리 / 도구) | 0 |
| Phase 2 | shadcn/ui primitives + GlobalLayout | 0 |
| Phase 3 | Zustand stores 7개 + persist | 1 |
| Phase 4 | TanStack Query hooks + zod 스키마 | 1 |
| Phase 5 | WebSocket 통합 + 기본 채팅 | 1 |
| Phase 6 | ChatPanel + PlanReview modal + WorkflowCanvas W1 | 2 |
| Phase 7 | 시각적 편집 (W2) + Cascade | 3 |
| Phase 8 | 대화 관리 / Attachment | 4 |
| Phase 9 | Memory View + Template Library (W3) | 5 |

---

## 8. Risk / Mitigations

| Risk | 완화 |
|------|------|
| Zustand store 가 비대화 (단일 store 의 over-stuffing) | 7 store 분리 + 각 100~200 LoC 이내 |
| TanStack Query cache invalidation 누락 | mutation 시 invalidateQueries 명시 / DevTools 확인 |
| WS 메시지 zod 검증 실패 시 silent fail | console.error + Sentry (Sprint 6+) |
| 다크 모드 색상 미스 | Storybook 에서 visual 확인 (Sprint 0 후) |
| shadcn/ui copy-paste 디자인 drift | tailwind config 디자인 토큰만 수정 (컴포넌트 직접 변경 X) |
| React 19 안정성 | Sprint 0 시점 stable 확인 / React 18 fallback 가능 |

---

## 9. 관련 문서

### 9.1 60대
- [60_frontend_overview_v1.0.md](60_frontend_overview_v1.0.md) — 진입점
- [62_workflow_canvas_design_v1.2.md](62_workflow_canvas_design_v1.2.md) — Workflow Canvas
- *63 (예정)* — Frontend Backend Contract

### 9.2 백엔드
- [21_WEBSOCKET_PROTOCOL_v1.5.md](21_WEBSOCKET_PROTOCOL_v1.5.md) — WS 메시지 계약 (zod 검증 기준)
- [22_error_codes_v1.1.md](22_error_codes_v1.1.md) — 에러 카탈로그
- [35_DB_SCHEMA_v1.0.md](35_DB_SCHEMA_v1.0.md) — memory_entries (Memory View 의존)

### 9.3 탐색 자취
- [docs/_claude/new_frontend/04](../_claude/new_frontend/04_state_architecture_v2.md) — State (Redux 기반, 본 문서가 Zustand 로 변환)
- [docs/_claude/new_frontend/05](../_claude/new_frontend/05_routing_layout_v2.md) — Routing
- [docs/_claude/new_frontend/06](../_claude/new_frontend/06_component_inventory.md) — Components
- [docs/_claude/new_frontend/08](../_claude/new_frontend/08_design_system.md) — Design System
- [docs/_claude/new_frontend/09](../_claude/new_frontend/09_message_card_system.md) — Message Card

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
