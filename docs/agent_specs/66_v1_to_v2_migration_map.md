# 66. v1 → v2 Migration Map

| 항목 | 내용 |
|------|------|
| 버전 | v1.0 |
| 작성일 | 2026-05-13 |
| 상태 | Accepted |
| 영역 | 60대 — Frontend v1 (frontend_old) → v2 마이그레이션 가이드 |
| 의존 | [60](60_frontend_overview_v1.0.md) / [61](61_frontend_architecture_v1.0.md) / [62](62_workflow_canvas_design_v1.2.md) / [63](63_frontend_backend_contract_v1.0.md) |
| 분석 출처 | [`docs/reports/frontend_v1_analysis_for_v2_layout.md`](../reports/frontend_v1_analysis_for_v2_layout.md) |

---

## 0. 본 문서의 역할

v1 (`docs/old/frontend_old/`) 의 11 페이지 / 컴포넌트 / 상태를 v2 로 어떻게 이동하는지 1:1 매핑 가이드.

**핵심 결정** (사용자 통찰 "동료 화면 + 채팅 지시" 반영):
- v1 의 **Layout 패턴 그대로** 채택 (TopBar + Sidebar + Outlet + SideChatPanel)
- v1 의 **11 페이지 유지** + v2 신규 3 추가 = 14 라우트
- **도구만 마이그레이션** (Redux → Zustand, Radix → shadcn, react-router v6 → TanStack Router)
- **데이터 source** = `data/mock/` 12 CSV → 백엔드 mock API (Sprint 1+)

---

## 1. 페이지 매핑 (11 v1 + 3 신규) — 2026-06-01 v2 완료 박제

### 1.1 v1 페이지 → v2 라우트 (현 상태)

| v1 페이지 | v2 라우트 | v2 파일 (실 위치) | 데이터 source | 현 상태 |
|----------|----------|------------------|--------------|---------|
| `CampaignHome` | `/dashboard` | [features/dashboard_v1/DashboardV1Page.tsx](../../frontend/src/features/dashboard_v1/DashboardV1Page.tsx) | `/api/admin/pipelines/category/dashboard_v1` (6 pipeline) | ✅ Active |
| `ChannelAnalysis` (v1, cross-client) | (`/analysis` 폐기 2026-06-01) | — | (cross-client 개념 = MVP+ 재진입) | 🗑️ 폐기 |
| ChannelPage (v2, client) | `/channel` | [features/channel/ChannelPage.tsx](../../frontend/src/features/channel/ChannelPage.tsx) | `/api/admin/pipelines/category/channel` (3 pipeline) | ✅ Active |
| `TrendAnalysis` | `/trend` | [features/trend/TrendPage.tsx](../../frontend/src/features/trend/TrendPage.tsx) | `/api/admin/pipelines/category/trend` (7 pipeline) | ✅ Active |
| `CreativeAnalysis` | `/creatives` | [features/creative/CreativePage.tsx](../../frontend/src/features/creative/CreativePage.tsx) | `/api/admin/pipelines/category/creative` (8 pipeline) | ✅ Active |
| `CostOptimization` | `/cost` | [features/cost/CostPage.tsx](../../frontend/src/features/cost/CostPage.tsx) | `/api/admin/pipelines/category/cost` (7 pipeline) | ✅ Active |
| `HitlCenter` | `/hitl` | [features/hitl/HitlCenterPage.tsx](../../frontend/src/features/hitl/HitlCenterPage.tsx) | HITL pause/resume | ✅ Active |
| `PortfolioView` | `/portfolio` | [features/portfolio/PortfolioPage.tsx](../../frontend/src/features/portfolio/PortfolioPage.tsx) | placeholder (MVP+ 다중 client) | ✅ stub |
| `AgentChat` | `/agent` | [features/agent/AgentChatPage.tsx](../../frontend/src/features/agent/AgentChatPage.tsx) | ws_agent (Cognitive→Planning→Execution) | ✅ Active |
| `Report` | `/report` | [features/report/ReportPage.tsx](../../frontend/src/features/report/ReportPage.tsx) | placeholder | ✅ stub |
| `Settings` | `/settings` | [features/settings/SettingsPage.tsx](../../frontend/src/features/settings/SettingsPage.tsx) | (설정) | ✅ stub |
| `ColorTest` | — | — | — | 🗑️ 폐기 (디자인 테스트용) |
| (Sprint 16 신규) Dashboard1 | `/dashboard1` | [features/dashboard1/Dashboard1Page.tsx](../../frontend/src/features/dashboard1/Dashboard1Page.tsx) | `/api/dashboard1/*` (20 endpoint, 별 path) | ✅ Active |

> ✅ **2026-06-01 v2 마이그레이션 완료 박제**:
> - 5 v2 페이지 (DashboardV1Page/ChannelPage/TrendPage/CreativePage/CostPage) = `useCategoryResults` hook → `/api/admin/pipelines/category/{cat}` → PipelineRunner → tool → `data/{client}/raw/` → cleaned/computed.
> - 구 v1 파일 (DashboardPage/ChannelAnalysisPage/TrendAnalysisPage/CreativeAnalysisPage/CostOptimizationPage) = 모두 삭제됨.
> - 구 mock layer (`/api/mock/*` + `useMockData` + `data/mock/`) = 폐기 (2026-05-28).
> - `/analysis` 라우트 + `ChannelAnalysisPage.tsx` (v1 cross-client) = 2026-06-01 폐기 (commit `fba80fd`). MVP+ 재진입 후보.

### 1.2 v2 신규 페이지 (Sprint 15+)

| 라우트 | 화면 | features 폴더 | mock 데이터 | 출처 |
|--------|------|-------------|----------|------|
| `/workflow` | Workflow Canvas (React Flow) | `features/workflow/*` | (Plan/Todo) | spec 62 |
| `/memory` | Memory View + Template Library | `features/memory/*` | (memory_entries) | spec 35 / 62 W3 |
| `/conversations` | 대화 이력 / 검색 | `features/conversations/*` | (memory_entries.type=conversation) | E2-5 |

### 1.3 Sidebar 메뉴 매핑 (컨텍스트별)

#### 포트폴리오 컨텍스트 (4탭, v1 유지)

```
📊 포트폴리오   /portfolio
📈 채널분석    /analysis
👥 사용자개입  /hitl
📄 리포트     /report
```

#### 클라이언트 컨텍스트 (8 v1 + 3 신규 = 11탭)

```
v1 (8):
  🏠 대시보드   /dashboard
  📈 채널분석   /analysis
  📊 트렌드     /trend
  🎨 소재       /creatives
  💰 비용       /cost
  👥 사용자개입 /hitl
  💬 에이전트   /agent
  📄 리포트     /report

신규 v2 (3):
  🔗 워크플로우 /workflow
  🧠 메모리     /memory
  📋 대화이력   /conversations
```

**그룹화 권장** (메뉴 11개 압박 완화):
```
[ 📊 분석 ]
  - 대시보드 / 채널 / 트렌드 / 소재 / 비용
[ 🤖 AI ]
  - 에이전트 / 워크플로우 / 메모리 / 대화이력
[ 👥 리뷰 ]
  - 사용자개입 / 리포트
```

---

## 2. 컴포넌트 매핑

### 2.1 Layout 컴포넌트

| v1 | v2 | 변경점 |
|----|----|--------|
| `components/layout/GlobalLayout.tsx` | `components/layout/GlobalLayout.tsx` | Provider 제거 (Zustand 자동), Resizer 동일 |
| `components/layout/TopBar.tsx` | `components/layout/TopBar.tsx` | useSelector → useStore hooks, shadcn DropdownMenu / Avatar |
| `components/layout/Sidebar.tsx` | `components/layout/Sidebar.tsx` | navigationSlice → useNavigation store (Zustand) |
| `components/chat/SideChatPanel.tsx` | `features/agent/SideChatPanel.tsx` | 기존 + 대화 dropdown / Plan review 인라인 / 컨텍스트 칩 |
| `components/chat/ChatCore.tsx` | `features/agent/ChatCore.tsx` | WS 통합 + Zustand agent store |

### 2.2 도메인 컴포넌트

| v1 | v2 |
|----|----|
| `components/agentChat/*` | `features/agent/*` |
| `components/campaign/*` | `features/campaign/*` |
| `components/channel/*` | `features/channel/*` |
| `components/chat/*` | `features/agent/*` (chat 도 agent 아래) |
| `components/cost/*` | `features/cost/*` |
| `components/creative/*` | `features/creative/*` |
| `components/performance/*` | `features/dashboard/*` (CampaignHome 의 일부) |
| `components/report/*` | `features/report/*` |
| `components/settings/*` | `features/settings/*` |
| `components/common/*` | `components/ui/*` (shadcn) + `lib/*` (헬퍼) |

### 2.3 Redux Slice → Zustand Store 매핑

| v1 (Redux slice) | v2 (Zustand store 위치) | 비고 |
|-----------------|----------------------|------|
| `features/agentChat/agentChatSlice.ts` | `features/agent/store.ts` | useAgent |
| `features/auth/authSlice.ts` | `features/auth/store.ts` | useAuth (Sprint 6+) |
| `features/campaign/*` | `features/campaign/store.ts` | useCampaign |
| `features/channel/*` | `features/channel/store.ts` | useChannel |
| `features/chatPanel/chatPanelSlice.ts` | `features/agent/chatPanelStore.ts` | useChatPanel (sub-store of agent) |
| `features/client/*` | `features/session/store.ts` | useSession (클라이언트 선택 = session 일부) |
| `features/cost/*` | `features/cost/store.ts` | useCost |
| `features/creative/*` | `features/creative/store.ts` | useCreative |
| `features/hitl/hitlSlice.ts` | `features/hitl/store.ts` | useHitl |
| `features/navigation/navigationSlice.ts` | `features/navigation/store.ts` | useNavigation (컨텍스트 + 탭) |
| `features/portfolio/*` | `features/portfolio/store.ts` | usePortfolio |
| `features/report/*` | `features/report/store.ts` | useReport |
| `features/settings/*` | `features/settings/store.ts` | useSettings |
| `features/trend/*` | `features/trend/store.ts` | useTrend |
| `app/store.ts` (combineReducers) | (제거 — Zustand 는 store 분산) | — |

→ **15 slice → 15 store**. 단지 도구 변경. 책임 / API 동일.

---

## 3. 마이그레이션 우선순위 (Sprint 별)

### Sprint 0 (인프라 + Layout 포팅) — ~1주

| # | 작업 | 산출물 |
|---|------|--------|
| 1 | frontend/ 디렉터리 셋업 | ✅ 완료 (commit 7f0d1e1) |
| 2 | shadcn/ui primitives 설치 | `components/ui/*.tsx` 15+ |
| 3 | **GlobalLayout** 포팅 (v1 → Zustand) | `components/layout/GlobalLayout.tsx` |
| 4 | **TopBar** 포팅 | `components/layout/TopBar.tsx` |
| 5 | **Sidebar** 포팅 + navigation store | `components/layout/Sidebar.tsx` + `features/navigation/store.ts` |
| 6 | **SideChatPanel** 포팅 (껍데기만) + chatPanel store | `features/agent/SideChatPanel.tsx` + `features/agent/chatPanelStore.ts` |
| 7 | App.tsx → GlobalLayout 적용 | — |

### Sprint 1 (라우트 + Mock API 연동) — ~1주

| # | 작업 | 산출물 |
|---|------|--------|
| 1 | TanStack Router 셋업 (또는 react-router v7) | `routes/*.tsx` 14개 (placeholder) |
| 2 | **백엔드 `mock_data.py`** (12 endpoint, Sprint 1 핵심) | `backend/api_v2/mock_data.py` |
| 3 | TanStack Query hooks (mock 12개) | `src/api/hooks/useMock*.ts` |
| 4 | zod schema (mock 12 row types) | `src/api/schemas.ts` 확장 |
| 5 | WebSocket 통합 + agent store | `features/agent/store.ts` + WS 라우팅 |
| 6 | session store (client / context) | `features/session/store.ts` |

### Sprint 2 (대시보드 페이지 첫 채움) — ~2주

| # | 페이지 | mock CSV | 작업량 |
|---|-------|---------|--------|
| 1 | PortfolioView | company_info + 통합 KPI | ~1d |
| 2 | CampaignHome | campaigns + daily + funnel | ~2d |
| 3 | ChannelAnalysis | channel_performance + daily | ~2d |
| 4 | **WorkflowCanvas (W1)** | (Plan/Todo) | ~2d |
| 5 | AgentChat (전체화면) | — | ~1d |

### Sprint 3 (분석 페이지) — ~2주

| 페이지 | CSV |
|--------|-----|
| TrendAnalysis | daily + review_trends |
| CreativeAnalysis | creatives + ab_tests (+ AI 5축 radar) |
| CostOptimization | budget + daily + keywords |
| HitlCenter | (시스템) |
| **WorkflowCanvas (W2)** | — |

### Sprint 4~5 (대화 / 메모리 / 리포트)
- Conversation sidebar (E2-5)
- Memory View
- Template Library (W3)
- Report

### Sprint 6+ (운영 / 인증)

---

## 4. 변환 패턴 — Redux Slice → Zustand Store

### 4.1 chatPanelSlice 예시

**v1 (Redux Toolkit)**:
```typescript
// features/chatPanel/chatPanelSlice.ts
const chatPanelSlice = createSlice({
  name: 'chatPanel',
  initialState: { isOpen: false, width: 400 },
  reducers: {
    toggleChatPanel: (state) => { state.isOpen = !state.isOpen; },
    openChatPanel: (state) => { state.isOpen = true; },
    closeChatPanel: (state) => { state.isOpen = false; },
    setChatPanelWidth: (state, action) => {
      state.width = Math.min(600, Math.max(300, action.payload));
    },
  },
});
export const { toggleChatPanel, openChatPanel, closeChatPanel, setChatPanelWidth }
  = chatPanelSlice.actions;
```

**v2 (Zustand + persist)**:
```typescript
// features/agent/chatPanelStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ChatPanelState {
  isOpen: boolean;
  width: number;
  toggle: () => void;
  open: () => void;
  close: () => void;
  setWidth: (w: number) => void;
}

export const useChatPanel = create<ChatPanelState>()(
  persist(
    (set) => ({
      isOpen: false,
      width: 400,
      toggle: () => set((s) => ({ isOpen: !s.isOpen })),
      open: () => set({ isOpen: true }),
      close: () => set({ isOpen: false }),
      setWidth: (w) => set({ width: Math.min(600, Math.max(300, w)) }),
    }),
    { name: 'chat-panel' },
  ),
);
```

→ **코드량 비슷, Provider 제거, useSelector 제거**. 컴포넌트에서 `const { isOpen, toggle } = useChatPanel()` 한 줄.

### 4.2 navigationSlice 예시 (more complex)

v1 의 컨텍스트 자동 전환 (포트폴리오 ↔ 클라이언트) 로직 유지:

```typescript
// features/navigation/store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const PORTFOLIO_TABS = [
  { id: 'portfolio', label: '포트폴리오', path: '/portfolio' },
  { id: 'analysis', label: '채널분석', path: '/analysis' },
  { id: 'hitl', label: '사용자개입', path: '/hitl' },
  { id: 'report', label: '리포트', path: '/report' },
];

const CLIENT_TABS = [
  { id: 'dashboard', label: '대시보드', path: '/dashboard' },
  // ... v1 그대로 + 신규 3
  { id: 'workflow', label: '워크플로우', path: '/workflow' },
  { id: 'memory', label: '메모리', path: '/memory' },
  { id: 'conversations', label: '대화이력', path: '/conversations' },
];

interface NavigationState {
  context: 'portfolio' | 'client';
  selectedClientId: string | null;
  currentTab: string;
  availableTabs: typeof PORTFOLIO_TABS;
  setContext: (ctx: 'portfolio' | 'client') => void;
  setClient: (id: string | null, name: string | null) => void;
  setCurrentTab: (id: string) => void;
}

export const useNavigation = create<NavigationState>()(
  persist(
    (set) => ({
      context: 'portfolio',
      selectedClientId: null,
      currentTab: 'portfolio',
      availableTabs: PORTFOLIO_TABS,
      setContext: (ctx) => set({
        context: ctx,
        availableTabs: ctx === 'portfolio' ? PORTFOLIO_TABS : CLIENT_TABS,
      }),
      setClient: (id, _name) => set({
        selectedClientId: id,
        context: id ? 'client' : 'portfolio',
        availableTabs: id ? CLIENT_TABS : PORTFOLIO_TABS,
      }),
      setCurrentTab: (id) => set({ currentTab: id }),
    }),
    { name: 'navigation' },
  ),
);
```

---

## 5. Drift 방지 — 마이그레이션 체크리스트

각 페이지 포팅 시:

- [ ] v1 페이지 파일 읽기 → 핵심 로직 / 데이터 흐름 파악
- [ ] v2 features/{domain}/ 폴더 생성
- [ ] store.ts (Zustand) 작성 (v1 slice 변환)
- [ ] UI 컴포넌트 분해 → shadcn/ui primitives + cn() 패턴
- [ ] Recharts / TanStack Table 등 라이브러리 그대로 사용 (v1 호환)
- [ ] mock API hook 사용 (`useMock*`)
- [ ] zod schema 검증 (TanStack Query queryFn 안에서)
- [ ] 라우트 등록 (`routes/{domain}.tsx`)
- [ ] Sidebar 메뉴 항목 추가 (navigation store)
- [ ] 테스트 (Vitest + RTL)
- [ ] Storybook (선택, MVP+)

---

## 6. Risk + 완화

| Risk | 완화 |
|------|------|
| v1 코드 직접 import (혼동) | `docs/old/frontend_old/` 격리. **읽기만, import 금지** (사용자 통찰 "v1/v2 섞임 금지") |
| Redux Provider 의존하는 v1 컴포넌트 | Zustand 는 Provider 없음 — 그대로 hook 호출. 단순 |
| navigation 컨텍스트 자동 전환 복잡도 | v1 navigationSlice 그대로 Zustand 화 (위 §4.2) |
| 11+3 사이드바 메뉴 압박 | 그룹화 (위 §1.3) / 아이콘 + tooltip |
| 백엔드 mock API 가 LangGraph 와 별개 | `/api/mock/*` 만 신규. LangGraph 영향 0 |
| 시점 불일치 (캠페인 2025-03~04 vs daily 2024-10~2025-03) | 데이터 표시 시 시점 명시 / 필터 |

---

## 7. 관련 문서

### 7.1 60대 (Frontend)
- [60_frontend_overview_v1.0.md](60_frontend_overview_v1.0.md) — 진입점
- [61_frontend_architecture_v1.0.md](61_frontend_architecture_v1.0.md) — State / Routing / Component / Design
- [62_workflow_canvas_design_v1.2.md](62_workflow_canvas_design_v1.2.md) — Workflow Canvas
- [63_frontend_backend_contract_v1.0.md](63_frontend_backend_contract_v1.0.md) — REST + WS + zod (Mock API 추가됨)
- **66_v1_to_v2_migration_map.md** ← 본 문서

### 7.2 백엔드
- [21_WEBSOCKET_PROTOCOL_v1.5.md](21_WEBSOCKET_PROTOCOL_v1.5.md)
- [20_INTERFACE_CONTRACT_v1.1.md](20_INTERFACE_CONTRACT_v1.1.md)
- [22_error_codes_v1.1.md](22_error_codes_v1.1.md)

### 7.3 데이터
- [`data/description/mock/INDEX.md`](../../data/description/mock/INDEX.md) — 6 분할 문서 (INDEX/SCHEMA/RELATIONSHIPS/API_MAPPING/UI_MAPPING/ROADMAP)

### 7.4 분석 / 보고
- [`docs/reports/frontend_v1_analysis_for_v2_layout.md`](../reports/frontend_v1_analysis_for_v2_layout.md) — v1 분석 + 3 축 검증

### 7.5 v1 코드 (참조 only)
- [`docs/old/frontend_old/`](../old/frontend_old/) — 11 페이지 / 15 slice / GlobalLayout / SideChatPanel

---

## 8. 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-05-13 | 초안 — v1 11 페이지 → v2 14 라우트 매핑 / 컴포넌트 + 15 slice 매핑 / Sprint 별 우선순위 / Redux→Zustand 변환 패턴 / 마이그레이션 체크리스트 / Risk. 본 문서 = 60대 마이그레이션의 진실 소스 |
