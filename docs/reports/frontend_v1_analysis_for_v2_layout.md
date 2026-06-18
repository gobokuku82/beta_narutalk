# frontend_old (v1) 분석 — "대쉬보드 + 채팅창 호출" 패턴 가능성 검토

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-05-13 |
| 분석 대상 | [`docs/old/frontend_old/`](../old/frontend_old/) — Redux Toolkit + React Router v6 기반 v1 |
| 분석 목적 | 사용자 통찰 **"동료 화면 (대쉬보드) + 채팅창 호출"** UX 가 v1 패턴으로 가능한지 검증 |
| 결론 (요약) | ✅ **Layout 패턴은 v1 이 그대로 정답**. 도구만 마이그레이션 (Redux → Zustand, Radix → shadcn, react-router v6 → TanStack Router). v1 의 11 페이지 유지 + 신규 영역 (Workflow Canvas / Memory / Template) 추가 가능. **단 데이터 source 결정 필요** (마케팅 분석 API 운명) |
| 다음 단계 | Spec 60/61/62 갱신 + 사용자 결정 (대쉬보드 데이터 source) 후 Sprint 1 진입 |

---

## 0. 사용자 통찰 (재확인)

> "**다른 직원의 화면 (대쉬보드) 보면서 다른직원에게 명령/질문 (채팅창) 하는 UX 느낌**"

이걸 분석 기준점으로 함.

---

## 1. v1 의 Layout 구조 — **이미 사용자 의도 그대로**

### 1.1 GlobalLayout (좌측 사이드 + 메인 + 호출형 채팅)

```
┌────────────────────────────────────────────────────────────────────┐
│ TopBar (h-16)                                                       │
│   로고 / 클라이언트 선택 / 날짜 / 알림 / 💬 채팅 토글 / 사용자        │
├──────┬──────────────────────────────────────┬──────────────────────┤
│ Side │                                       │ ◀ Resizer            │
│ bar  │  Outlet (선택된 페이지)                │   (300~600px)        │
│      │                                       │ ┌──────────────────┐ │
│ w-20 │  - CampaignHome (대시보드)            │ │ SideChatPanel    │ │
│ 다크 │  - ChannelAnalysis                    │ │ - Connected 표시 │ │
│      │  - TrendAnalysis                      │ │ - ChatCore       │ │
│ icon │  - CreativeAnalysis                   │ │   compact 모드   │ │
│ +    │  - CostOptimization                   │ │ - 전체화면 버튼   │ │
│ 라벨 │  - HitlCenter                         │ │ - 닫기 버튼      │ │
│      │  - PortfolioView                      │ │                  │ │
│      │  - AgentChat (전체화면 채팅)          │ │ 슬라이드 인/아웃  │ │
│      │  - Report / Settings                  │ │ (translate-x)    │ │
│      │                                       │ └──────────────────┘ │
└──────┴───────────────────────────────────────┴──────────────────────┘
```

**파일**: [`docs/old/frontend_old/src/components/layout/GlobalLayout.tsx`](../old/frontend_old/src/components/layout/GlobalLayout.tsx) (전체 ~90 LoC)

### 1.2 핵심 메커니즘 — chatPanelSlice

```ts
// chatPanelSlice.ts
interface ChatPanelState {
  isOpen: boolean;
  width: number;  // 300~600px, 사용자 드래그로 조정
}

actions: toggleChatPanel / openChatPanel / closeChatPanel / setChatPanelWidth
```

**호출 트리거**:
- TopBar 우측 💬 버튼 클릭 → `toggleChatPanel()`
- 페이지 내부 어디서든 `dispatch(openChatPanel())` 가능
- ESC 키 / X 버튼 → `closeChatPanel()`

**리사이즈**: GlobalLayout 의 `handleMouseDown` 으로 width 조정 + Redux 에 persist.

### 1.3 메뉴 컨텍스트 자동 전환 — navigationSlice

| 컨텍스트 | 메뉴 (탭) |
|---------|----------|
| **포트폴리오** (다중 클라이언트 overview) | 포트폴리오 / 채널분석 / 사용자개입 / 리포트 (4탭) |
| **클라이언트** (특정 클라이언트 선택 후) | 대시보드 / 채널분석 / 트렌드분석 / 소재분석 / 사용자개입 / 에이전트 / 비용최적화 / 리포트 (8탭) |

→ 사이드바가 **클라이언트 선택 여부에 따라 자동 변경**. localStorage 영속화.

### 1.4 11 페이지 카탈로그

| 페이지 | 라우트 | 도메인 |
|--------|--------|--------|
| `CampaignHome` | `/dashboard` | 클라이언트 캠페인 종합 |
| `ChannelAnalysis` | `/analysis` | 채널별 성과 분석 |
| `TrendAnalysis` | `/trend` | 트렌드 분석 |
| `CreativeAnalysis` | `/creatives` | 소재 분석 |
| `CostOptimization` | `/cost` | 비용 최적화 |
| `HitlCenter` | `/hitl` | 사용자 개입 센터 (현재 HITL 시스템과 같은 영역) |
| `PortfolioView` | `/portfolio` | 다중 클라이언트 포트폴리오 |
| `AgentChat` | `/agent` | 에이전트 전체화면 채팅 (SideChat 의 확장 버전) |
| `Report` | `/report` | 리포트 |
| `Settings` | `/settings` | 설정 |
| `ColorTest` | (제거) | 디자인 테스트 |

→ 도메인 = **마케팅 분석 (광고 캠페인 / 채널 / 소재 / 트렌드 / 비용)**.

---

## 2. 사용자 의도 매핑 검증

| 사용자 의도 | v1 구현 | 정합도 |
|------------|---------|:------:|
| **"다른 직원 화면" 보기** | Outlet 에 대쉬보드 페이지 표시 | ✅ 100% |
| **"채팅으로 지시"** | SideChatPanel 토글 + 입력 | ✅ 100% |
| **두 영역 동시 visible** | 채팅 열린 상태 = 메인 + 사이드 공존 | ✅ 100% |
| **호출형** (필요할 때만) | toggle / 리사이즈 / 닫기 | ✅ 100% |
| **컨텍스트 인지** | 현재 페이지 / 클라이언트 선택 = Redux 에서 챗에 전달 | ⚠️ 부분 (구현 필요) |
| **전체화면 모드** | `/agent` 라우트로 이동 | ✅ 100% |

**결론**: v1 의 layout 패턴은 **사용자 의도와 완벽 정합**. 새로 디자인 X.

---

## 3. v2 (새 vision) 영역과의 통합

### 3.1 추가 필요 영역

| 영역 | 출처 spec | v1 에 존재? | 통합 방법 |
|------|----------|:----------:|----------|
| **Workflow Canvas (React Flow)** | 62 | ❌ | 신규 페이지 `/workflow` 또는 대쉬보드 내부 |
| **Memory View** | 35 / Sprint 15 | ❌ | 신규 페이지 `/memory` |
| **Workflow Template Library** | 62 W3 | ❌ | 신규 페이지 `/templates` |
| **Conversation Sidebar (E2-5)** | Sprint 15 | ❌ | SideChatPanel 헤더에 dropdown 또는 별도 panel |
| **Clarification HITL Modal** | ADR-015 | ❌ | SideChatPanel 내부 + modal |

### 3.2 라우트 통합안 (v1 11 + 신규 3~5)

```
포트폴리오 컨텍스트 (4탭):
  /portfolio    [v1] 포트폴리오 overview
  /analysis     [v1] 채널분석 (전체)
  /hitl         [v1] 사용자개입 센터
  /report       [v1] 리포트

클라이언트 컨텍스트 (8 + 3 = 11탭, 또는 그룹화):
  /dashboard    [v1] 캠페인 종합
  /analysis     [v1] 채널분석
  /trend        [v1] 트렌드분석
  /creatives    [v1] 소재분석
  /cost         [v1] 비용최적화
  /hitl         [v1] 사용자개입
  /report       [v1] 리포트
  /agent        [v1] 에이전트 전체화면
  /workflow     [⭐ 신규] Workflow Canvas (62)
  /memory       [⭐ 신규] Memory + Template Library (35 / 62 W3)
  /conversations [⭐ 신규] 대화 이력 (Sprint 15 E2-5)

설정:
  /settings     [v1]
```

→ 11탭이 메뉴 압박. **그룹화 옵션**:
- "분석" 그룹 (대시보드 / 채널 / 트렌드 / 소재 / 비용)
- "AI 작업" 그룹 (에이전트 / 워크플로우 / 메모리 / 대화)
- "리뷰" 그룹 (HITL / 리포트)

### 3.3 SideChatPanel 의 확장

v1 SideChatPanel 의 기존 구조:
```
헤더: "ADALLPIN Agent" + Connected + 전체화면 / 닫기
본문: ChatCore (compact)
```

v2 확장:
```
헤더: 대화 선택 dropdown ▾ + Connected + 전체화면 / 닫기
본문: 
  - 메시지 누적 (기존)
  - Plan review modal (인라인 또는 floating)
  - Clarification HITL 처리
  - 노드 이벤트 표시 (선택)
  - 컨텍스트 칩 (현재 보고 있는 대쉬보드/차트)
```

---

## 4. 도구 마이그레이션 (v1 → v2)

[`docs/agent_specs/60_frontend_overview_v1.0.md`](../agent_specs/60_frontend_overview_v1.0.md) §2.4 에 이미 정의:

| v1 (기존) | v2 (Sprint 15+) | 이유 |
|-----------|----------------|------|
| Redux Toolkit | Zustand | 12배 작음, 코드량 절반 |
| RTK Query | TanStack Query | Zustand 와 짝, 2026 표준 |
| Radix 직접 | shadcn/ui | 디자인 시스템 0 부담 |
| react-router v6 | TanStack Router 또는 v7 | 데이터 API |
| Tailwind v3 | Tailwind v3.4 또는 v4 | (사용자 결정 보류) |
| useState 폼 | react-hook-form + zod | 검증 |

→ **Layout 구조는 그대로 유지**. 도구만 교체.

---

## 5. ⚠️ 결정 필요 — 데이터 source

### 5.1 v1 의 대쉬보드 데이터 source

v1 페이지들 (CampaignHome / ChannelAnalysis / 등) 은 **외부 마케팅 분석 API** 에서 데이터를 받아 차트로 시각화하는 구조로 추정.

**현재 새 백엔드 (LangGraph) 의 미구현 영역**:
- ❌ 캠페인 데이터 저장 / 조회 API
- ❌ 채널 성과 데이터 API
- ❌ 소재 분석 결과 저장 API
- ❌ 비용 데이터 API
- ❌ 트렌드 데이터 API

→ 현재 새 백엔드는 **LangGraph 4-Layer 에이전트** + **memory_entries** 만. 마케팅 도메인 데이터 모델 없음.

### 5.2 4 옵션

| 옵션 | 설명 | 비용 | 적합도 |
|------|------|------|:------:|
| **A** | **v1 백엔드 + 새 백엔드 공존** — v1 의 마케팅 API 와 새 LangGraph API 두 곳 호출 | 낮음 (기존 유지) | ⭐⭐⭐ |
| **B** | **새 백엔드에 분석 API 추가** — Sprint 16+ 에서 캠페인/채널/... 데이터 모델 + API 신설 | 높음 (~수주) | ⭐⭐ (POC 단계 과함) |
| **C** | **AI 생성 결과 = 대쉬보드** — vision H4. 사용자가 AI 와 대화한 결과가 누적되어 대쉬보드 화면 자동 형성 | 중간 (LLM 의존 ↑) | ⭐⭐⭐⭐ (vision 정합) |
| **D** | **외부 BI 임베드** — Tableau / Looker / Metabase iframe | 낮음 | ⭐⭐ (UX 통합 약함) |

**권고**: **C → A 단계적**.
- POC (Sprint 0~5): C — AI 가 생성한 결과를 대쉬보드 페이지에 누적 (vision H4 의 manifestation)
- MVP (Sprint 6~10): A — 실제 광고 플랫폼 (구글/메타/네이버) API 연동
- Production (Sprint 11+): B — 백엔드에 정형 분석 API 추가

### 5.3 사용자 결정 필요

| 질문 | 후보 |
|------|------|
| 대쉬보드 데이터는 어디서? | C (AI 생성) / A (v1 백엔드) / B (새 API) / D (외부 BI) |
| v1 의 마케팅 페이지 (소재/채널/비용)를 어떻게 채울지? | 빈 페이지 + AI 결과 채우기 (C) / 외부 API (A) / 임시 mock (POC) |
| Sprint 15 에 대쉬보드 데이터 모델 도입? | Yes (B) / No (C+A) |

---

## 6. 통합 후 권고 Layout (spec 갱신 후보)

[`60_frontend_overview_v1.0.md`](../agent_specs/60_frontend_overview_v1.0.md) §3.1 의 ConversationWorkspace 가 너무 conversation-first 였음. **v1 layout 으로 정정**:

### 권고 — v2 Layout

```
GlobalLayout (= v1 동일, 도구만 변경):
├─ TopBar
│  ├─ 로고
│  ├─ 클라이언트 / 컨텍스트 선택
│  ├─ 검색 (Sprint 5+)
│  ├─ 알림 (HITL pending count)
│  ├─ 💬 채팅 토글
│  └─ 사용자 메뉴
│
├─ Sidebar (좌, w-20 또는 w-72, 다크)
│  └─ 컨텍스트별 메뉴 (포트폴리오 4 / 클라이언트 8~11)
│
├─ Main (Outlet)
│  └─ 선택된 페이지 (대쉬보드 / 워크플로우 / 메모리 / ...)
│
└─ SideChatPanel (우, 300~600px 리사이즈, 호출형)
   ├─ 헤더: 대화 선택 ▾ + Connected + 전체화면 / 닫기
   ├─ 메시지 누적
   ├─ Plan review (인라인)
   ├─ Clarification HITL
   └─ 입력창 + 자연어 명령
```

### Workflow Canvas (62) 의 위치

| 옵션 | 설명 |
|------|------|
| **A** | 별도 페이지 `/workflow` — Sidebar 메뉴 항목 |
| **B** | `/agent` 페이지 안에 toggle (리스트 ↔ 그래프) |
| **C** | 모든 대쉬보드에서 부분 영역으로 사용 (overview) |
| **D (권고)** | **A + B 통합** — 메인 페이지로 `/workflow`, 대화 내 미리보기 카드도 가능 |

### Conversation Sidebar (E2-5)

- 옵션 1: SideChatPanel 의 헤더에 dropdown ("최근 대화 ▾")
- 옵션 2: 별도 페이지 `/conversations`
- 옵션 3: 둘 다 (헤더 dropdown 빠른 전환, 페이지는 전체 검색)

**권고**: 옵션 3.

---

## 7. 작업 계획 (Spec / 코드 마이그레이션)

### Phase 1 — Spec 갱신 (이번 사이클)

- [ ] [`60_frontend_overview_v1.0.md`](../agent_specs/60_frontend_overview_v1.0.md) §3.1 Workspace 레이아웃 → v1 GlobalLayout 패턴으로 정정 (TopBar + Sidebar + Outlet + SideChatPanel)
- [ ] [`61_frontend_architecture_v1.0.md`](../agent_specs/61_frontend_architecture_v1.0.md) §2.4 Workspace 구조 → 동일 정정
- [ ] [`62_workflow_canvas_design_v1.0.md`](../agent_specs/62_workflow_canvas_design_v1.0.md) §2.3 3-Panel → "메인 영역 안의 캔버스 + 우측 채팅 패널" 로 정정
- [ ] 신규: `66_v1_to_v2_migration_map.md` — v1 11 페이지 → v2 페이지 매핑 + 폐기/유지/신규 결정

### Phase 2 — 데이터 source 결정 (사용자)

- [ ] §5.3 의 3 질문 답변
- [ ] 대쉬보드 mock data 전략 결정 (POC 동안)

### Phase 3 — frontend Sprint 0 코드 보강 (작은 변경)

- [ ] `src/components/layout/GlobalLayout.tsx` — v1 GlobalLayout 패턴 포팅 (Zustand 기반)
- [ ] `src/components/layout/TopBar.tsx` — v1 TopBar 포팅
- [ ] `src/components/layout/Sidebar.tsx` — v1 Sidebar 포팅 (lucide-react 아이콘 유지)
- [ ] `src/features/chatPanel/store.ts` — Zustand 버전 (v1 chatPanelSlice 변환)
- [ ] `src/features/navigation/store.ts` — Zustand 버전 (v1 navigationSlice 변환)
- [ ] `src/features/agent/SideChatPanel.tsx` — v1 SideChatPanel 포팅

### Phase 4 — Sprint 1 진행

- [ ] TanStack Router 셋업 (라우트 14개)
- [ ] 각 페이지 빈 placeholder (CampaignHome / ChannelAnalysis / ...)
- [ ] WebSocket 통합 (api/ws.ts)
- [ ] Plan review modal 통합

---

## 8. Risk + 완화

| Risk | 완화 |
|------|------|
| 11+3 = 14 메뉴 압박 (사이드바 좁음) | 그룹화 / 아이콘 only + tooltip / 컨텍스트별 표시 |
| 대쉬보드 데이터 source 미정 | §5.3 사용자 결정 (POC = C, MVP = A 권고) |
| v1 의 Redux 코드 마이그레이션 비용 | Layout 만 포팅, Page 내부는 Sprint 별로 점진 |
| 컨텍스트 (포트폴리오 ↔ 클라이언트) 자동 전환 복잡도 | v1 navigationSlice 그대로 Zustand 화 |
| SideChatPanel 안에 너무 많은 기능 | Plan review / Clarification = modal floating, sidebar 는 채팅만 |
| Workflow Canvas (62) vs 대쉬보드 페이지의 비중 | §6 옵션 D — 둘 다 가능 |

---

## 9. 결론

### 9.1 가능성 = ✅ 100%

> "**대쉬보드 + 채팅창 호출**" 은 가능할 뿐만 아니라, **v1 이 이미 그 구조**.

새 vision (60/62) 의 "Conversation-first" 가 약간 더 채팅 중심으로 정제되었는데, **v1 의 "Dashboard-first + Side Chat" 이 사용자 의도와 정확 일치**.

→ Spec 60/61/62 의 일부 갱신 + v1 GlobalLayout 패턴 채택 + 도구만 마이그레이션 (Redux → Zustand 등).

### 9.2 핵심 결정 — 데이터 source

대쉬보드 데이터를 어디서 받을지 (§5.3) 만 결정되면 진행 가능. **권고 = C (AI 생성) → A (외부 API) 단계적**.

### 9.3 작업 흐름

1. **사용자 결정** (§5.3 데이터 source / §6 Workflow Canvas 위치)
2. **Spec 60/61/62 갱신** + 신규 66 마이그레이션 맵
3. **frontend Sprint 0 코드 보강** — v1 GlobalLayout 패턴 포팅
4. **Sprint 1 진입** — 라우트 + WebSocket + 페이지 placeholder

---

## 10. 검증 사이클 (3 축)

### 10.1 검증 1 — 사용자 통찰 5개 정합성

| 통찰 | 본 제안 ("v1 layout 채택 + 도구 마이그레이션") | 정합? |
|------|------------------------------------------|:----:|
| **확장/변경 용이성** ([project_extension_ease_priority](../../C:/Users/gobok/.claude/projects/c--kdy-Projects-octormate-beta-v001/memory/project_extension_ease_priority.md)) | v1 layout = 이미 검증된 패턴. 변경 비용 낮음. 신규 영역 (Workflow / Memory / Template) 추가 자유 | ✅ |
| **v1/v2 섞임 금지** (feedback_no_mixed_codebases) | v1 코드 → `docs/old/frontend_old/` 격리 (이미 됨). 새 `frontend/` 에서 layout **패턴만 차용** (코드 직접 import X). v1 잔재 X | ✅ |
| **POC 초기 LLM 우선** (project_llm_heavy_initial) | 대쉬보드 데이터 source 권고 = C (AI 생성). 정형 API 부재 → LLM 으로 채움 | ✅ |
| **사용자 도메인 지식 가정 X** (project_no_user_domain_assumption) | 채팅창 항상 우측 → 사용자가 DAG / schema / tool 몰라도 AI 가 매개. 대쉬보드 클릭만으로 컨텍스트 전달 | ✅ |
| **NL 점진 1차/2차/3차** (project_nl_edit_roadmap) | SideChatPanel 안에 NL 1차 → LLM Tool Routing 2차 → 메모리 패턴 3차 단계적 도입 가능 | ✅ |

**검증 1 결과**: ✅ **5 통찰 모두 정합**. 어긋남 0.

### 10.2 검증 2 — 백엔드 영향

| 영역 | 변경 필요? | 비고 |
|------|:---------:|------|
| LangGraph 4-Layer 에이전트 | ❌ | 그대로 |
| WebSocket (`/ws/agent`, `/ws/hitl`) | ❌ | spec 21 그대로, frontend 측 UI 만 변경 |
| `memory_entries` 테이블 | ❌ | spec 35 그대로 |
| `planner.Plan` / `PlannedTodo` | ❌ | ADR-010 + 62 §3.1 (Optional 3 필드) 이미 정합 |
| **마케팅 분석 API** (소재/채널/비용/...) | ⚠️ **사용자 결정 의존** | §5.2 4 옵션 |

**핵심**: **Layout 변경 자체는 백엔드 영향 0**. 데이터 source 결정 (§5.3) 만 백엔드 관련.

→ Sprint 0~5 (POC) = 백엔드 변경 없이 frontend 만 진행 가능.
→ Sprint 6+ (MVP) = 데이터 source 옵션 A/B 채택 시 백엔드 추가.

**검증 2 결과**: ✅ **백엔드 영향 최소. POC 단계 무영향**.

### 10.3 검증 3 — 점진 마이그레이션 가능성

| 단계 | 작업 | 시간 | Sprint |
|------|------|------|--------|
| 1 | Spec 60/61/62 갱신 (Workspace → v1 GlobalLayout) | ~30분 | 0 |
| 2 | frontend Sprint 0 코드 보강 — GlobalLayout / TopBar / Sidebar / SideChatPanel (Zustand 기반 포팅) | ~4~6h | 0~1 |
| 3 | TanStack Router 셋업 + 14 라우트 placeholder | ~2~3h | 1 |
| 4 | WebSocket 통합 (api/ws.ts + agent store) | ~3~4h | 1 |
| 5 | 첫 페이지 채우기 (`AgentChat` 또는 `CampaignHome`) | ~5~10h | 2 |
| 6 | 나머지 페이지 placeholder + 점진 채우기 | Sprint 별 | 2~6 |

**Big Bang 마이그레이션 X**. 각 페이지 / 영역 **독립 작업 가능**.

**검증 3 결과**: ✅ **완전 점진 가능. Sprint 별 가치 증명**.

### 10.4 종합 검증

3 축 검증 모두 ✅. 본 제안 (**v1 GlobalLayout 패턴 채택 + 도구 마이그레이션 + 신규 영역 추가**) 의 위험 신호 0.

**진행 권고**.

---

## 11. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-13 | 초안 — frontend_old 전수 조사 + 사용자 의도 매핑 + v2 통합안 + 데이터 source 4 옵션. v1 layout 이 사용자 의도와 완벽 정합 발견. spec 60/61/62 갱신 필요 항목 정리. **3 축 검증 (통찰 정합 / 백엔드 영향 / 점진 마이그레이션) 모두 통과** |
