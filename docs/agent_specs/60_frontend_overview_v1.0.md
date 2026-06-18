# 60. Frontend Overview — Tech Stack + Vision UX + Roadmap

| 항목 | 내용 |
|------|------|
| 버전 | v1.0 |
| 작성일 | 2026-05-12 |
| 상태 | Accepted |
| 영역 | 60대 — 프론트엔드 진입점 (다른 60대 문서들의 기준) |
| 의존 | [00_vision_and_intent.md](00_vision_and_intent.md) (north star) |
| 후속 | 61 Architecture / 62 Workflow Canvas (✅) / 63 Backend Contract |

---

## 0. 본 문서의 역할

OctorAD Frontend 의 **전체 그림** — Tech Stack 결정 / Vision UX 원칙 / Sprint 단위 Roadmap.

60대 다른 문서들 (61/62/63) 은 본 문서를 진입점으로 한다. 60 은 "**무엇을 / 왜 / 언제**", 다른 문서는 "**어떻게**".

> 본 문서는 [`docs/_claude/new_frontend/`](../_claude/new_frontend/) 14 문서 (탐색 자취) 의 정제 결과. 정식 진실 소스.

---

## 1. Vision 매핑 — Frontend 가 담당하는 영역

### 1.1 가설 사슬 (vision 00)

| 가설 | Frontend 역할 |
|------|--------------|
| **H0** 의도 모호성 | 자연어 입력 → 즉시 시각화 → "이거 맞아?" 확인 UI |
| **H1** 발견 | 자유 대화 채팅 + Plan review modal + Workflow Canvas |
| **H2** 학습 | 사용자가 편집한 내역 백엔드로 전달 (메모리 시스템과 협력) |
| **H3** 패턴화 | "저장" 버튼 + Workflow Template 라이브러리 |
| **H4** **맞춤화** ⭐ | "분석" 한 마디 → 저장된 패턴 자동 호출 / 추천 |

→ Frontend 는 **vision 의 모든 가설을 사용자가 체감하는 표면**.

### 1.2 5 UX 원칙 (vision 도출)

[`docs/_claude/new_frontend/03_ux_principles_from_vision.md`](../_claude/new_frontend/03_ux_principles_from_vision.md) 의 5 원칙 정제:

| # | 원칙 | 의미 | 적용 |
|---|------|------|------|
| **1** | 자유 대화 우선 | 사용자가 사전 학습 없이 자연어로 모든 것 가능 | 채팅 UI / NL 편집 textarea |
| **2** | 도메인 지식 가정 X | DAG / schema / tool 강요 안 함 | 시각화로 보여주되 사용자가 모를 수 있는 부분 친절히 안내 |
| **3** | 시각화 + 자연어 공존 | 두 입력 모두 같은 백엔드 → 사용자가 편한 방식 선택 | Workflow Canvas + NL 편집 동시 |
| **4** | HITL = pause | 시스템이 멈춤 + 사용자 개입 가능 | Plan review modal / Execution pause / Clarification HITL |
| **5** | 학습 누적 시각화 | 사용한 패턴이 점점 똑똑해짐을 보여줌 | Memory view / Workflow Template Library |

→ 본 5 원칙이 **모든 컴포넌트 / 상호작용 결정의 기준**.

---

## 2. Tech Stack 결정 — 옵션 A (트렌드 적극 반영) [최종 검증 2026-06-01]

> ✅ **2026-06-01 정합 박제**: frontend/package.json + 실 코드 = §2.1 Tech Stack 표 정합. v1 → v2 마이그레이션 완료 (commit `fba80fd` + `d99c5b6` + `220150c` + `a055993`). v1 코드 (5 페이지 중 ChannelAnalysisPage = 마지막 잔존) 폐기 완료 + 5 v2 페이지 = pipeline 산출 기반.

[`docs/_claude/new_frontend/12_tech_stack_analysis.md`](../_claude/new_frontend/12_tech_stack_analysis.md) 분석 결과 **옵션 A** 채택 — 사용자 통찰 "확장/변경 용이성" 부합.

### 2.1 핵심 결정 표

| 카테고리 | 선택 | 패키지 | 버전 |
|---------|------|--------|------|
| (2026-05-13 v1.1) | Layout 패턴 | v1 GlobalLayout (TopBar + Sidebar + Outlet + SideChatPanel 호출형) | [기존 frontend_old](../old/frontend_old/) 검증 |
| (2026-05-13 v1.1) | 데이터 source (POC) | mock CSV → 백엔드 mock API 서빙 | [data/description/mock/INDEX.md](../../data/description/mock/INDEX.md) |
| **빌드** | Vite | `vite` | ^5 |
| **프레임워크** | React 19 | `react`, `react-dom` | ^19 |
| **언어** | TypeScript strict | `typescript` | ^5.4 |
| **CSS** | Tailwind v3 | `tailwindcss` | ^3.4 (실제 설치 버전 — 검증 사이클 3 정정. v4 아님) |
| **컴포넌트 시스템** | shadcn/ui (Radix + Tailwind copy-paste) | `npx shadcn@latest` | — |
| **아이콘** | lucide-react | `lucide-react` | ^0.4 |
| **폰트** | Pretendard (한국 표준) | `pretendard` 또는 CDN | — |
| **상태 (UI)** | **Zustand** | `zustand` | ^5 |
| **상태 (서버)** | **TanStack Query** | `@tanstack/react-query` | ^5 |
| **라우터** | TanStack Router 또는 React Router v7 | `@tanstack/react-router` 또는 `react-router` v7 | — |
| **검증** | zod | `zod` | ^3 |
| **폼** | react-hook-form + zod | `react-hook-form`, `@hookform/resolvers` | ^7 / ^3 |
| **테이블** | TanStack Table | `@tanstack/react-table` | ^8 |
| **차트** | Recharts | `recharts` | ^2 |
| **마크다운** | react-markdown + remark-gfm | `react-markdown`, `remark-gfm` | ^9 / ^4 |
| **토스트** | Sonner | `sonner` | ^1 |
| **그래프 캔버스** ⭐ | **@xyflow/react (React Flow)** | `@xyflow/react` | ^12 |
| **자동 레이아웃** ⭐ | dagre | `dagre`, `@types/dagre` | ^0.8 |
| **3-패널 레이아웃** | shadcn/ui Resizable | (shadcn CLI) | — |
| **테스트 (단위)** | Vitest + Testing Library | `vitest`, `@testing-library/react` | ^2 / ^16 |
| **테스트 (E2E)** | Playwright | `@playwright/test` | ^1.4 |
| **테스트 (mock)** | MSW | `msw` | ^2 |
| **컴포넌트 갤러리** | Storybook 8 (선택, MVP+) | `storybook` | ^8 |
| **린트/포맷** | ESLint + Prettier (또는 Biome 검토) | `eslint`, `prettier` | — |
| **패키지 매니저** | pnpm | — | — |

### 2.2 신규 추가 영역 (workflow-node UI 위함)

`docs/_claude/new_frontend/12_tech_stack_analysis.md` 의 기존 분석에 **3 패키지 추가**:

| 패키지 | 역할 | 출처 |
|--------|------|------|
| `@xyflow/react` | 노드-엣지 캔버스 (n8n/Zapier 표준) | [62 §2.1](62_workflow_canvas_design_v1.2.md) |
| `dagre` | DAG 자동 레이아웃 | [62 §2.2](62_workflow_canvas_design_v1.2.md) |
| `react-hook-form` | 폼 관리 (이전 §2.15 보강) | 신규 |

### 2.3 의존성 부풀림 방지

[`docs/_claude/new_frontend/11_tech_stack.md`](../_claude/new_frontend/11_tech_stack.md) §10 의 체크리스트 유지:
- 신규 의존 추가 시 PR 사유 명시
- 기존 도구로 가능한지 먼저 검토
- bundle size 영향 측정 (`vite-bundle-visualizer`)

### 2.4 기존 v1 와의 차이 (Redux → Zustand 등)

| 영역 | v1 (기존) | v2 (Sprint 15+) | 사유 |
|------|----------|----------------|------|
| 상태 | Redux Toolkit (13.8KB) | Zustand (1.16KB) | 12배 작음, 코드량 절반 |
| 서버 통신 | RTK Query | TanStack Query | Zustand 와 짝, 2026 표준 |
| 컴포넌트 | Radix 직접 | shadcn/ui | 디자인 시스템 0 부담 |
| CSS | Tailwind v3 | Tailwind v3.4 | shadcn/ui 호환 (v4 검토했으나 v3.4 채택 — 검증 사이클 3 정정) |
| 폼 | useState 직접 | react-hook-form + zod | 성능 + 검증 |

→ **신규 trash dashboard 만들 때 적용**. 현재 vanilla dashboard 는 v1 잔재 (점진 폐기).

### 2.5 디렉터리 구조 (Sprint 0 시작 시)

```
frontend/
├─ src/
│  ├─ main.tsx              # 진입점
│  ├─ App.tsx               # 라우터 root
│  ├─ routes/               # TanStack Router 또는 React Router v7
│  │  ├─ index.tsx          # / (홈)
│  │  ├─ workspace.tsx      # /workspace (메인 채팅)
│  │  ├─ memory.tsx         # /memory (Sprint 15 P1)
│  │  └─ templates.tsx      # /templates (W3, Sprint 15 P1)
│  ├─ components/
│  │  ├─ ui/                # shadcn/ui 컴포넌트 (button.tsx 등)
│  │  ├─ workflow/          # WorkflowCanvas / NodeLibrary / PropertyPanel (62)
│  │  ├─ chat/              # ChatThread / MessageCard / ClarificationModal
│  │  ├─ memory/            # MemoryView / TemplateCard
│  │  └─ layout/            # AppShell / Sidebar
│  ├─ stores/               # Zustand stores
│  │  ├─ workflow.ts        # 노드 / 엣지 / position
│  │  ├─ chat.ts            # 메시지 / turn 상태
│  │  └─ session.ts         # 인증 / 사용자
│  ├─ api/                  # TanStack Query hooks + WS 클라이언트
│  │  ├─ ws.ts              # /ws/agent + /ws/hitl
│  │  ├─ rest.ts            # REST endpoint
│  │  └─ schemas.ts         # zod schema (백엔드 컨트랙트)
│  ├─ lib/                  # 유틸
│  │  ├─ dagre.ts           # 자동 레이아웃 헬퍼
│  │  └─ cn.ts              # clsx + tailwind-merge
│  └─ styles/
│     └─ globals.css        # Tailwind directives + 디자인 토큰
├─ public/
├─ index.html
├─ vite.config.ts
├─ tailwind.config.ts
├─ tsconfig.json
└─ package.json
```

→ Sprint 0 (1주) 완료 시 본 구조 생성.

---

## 3. Roadmap — Sprint 단위

[`docs/_claude/new_frontend/07_implementation_roadmap.md`](../_claude/new_frontend/07_implementation_roadmap.md) 정제. 총 7 Sprint (~10주).

### 3.1 Sprint 매트릭스

| Sprint | 영역 | 기간 | 백엔드 의존 | 주요 산출 |
|--------|------|------|------------|----------|
| **0** | 기반 / 디자인 시스템 | 1주 | — | Vite/React 19/TS/Tailwind v3.4/shadcn/ui 설치, 라우터, ESLint, MSW |
| **1** | WebSocket 통신 / 백엔드 컨트랙트 | 1주 | Sprint 14 ✅ | zod 스키마 (백엔드 21 매핑), WS 클라이언트, TanStack Query hooks |
| **2** | 워크스페이스 / 핵심 화면 | 2주 | Sprint 14 ✅ | Chat thread / Plan review modal / **W1 Workflow Canvas (read-only)** |
| **3** | HITL / Plan 편집 | 2주 | Sprint 14 ✅ | 🗑/드래그/✏️ + NL textarea / cascade 시각화 / **W2 시각적 편집** |
| **4** | 대화 관리 / Attachment | 1주 | Sprint 15 E2 (메모리) | Conversation sidebar (#6) / 첨부 갤러리 |
| **5** | Memory View / 학습 시각화 | 1주 | Sprint 15 E1+E2 | **W3 Workflow Template Library** / Memory view / Clarification modal |
| **6** | 운영 / 인증 / 안정화 | 2주 | Sprint 16+ | Auth / Multi-tenant / Performance / Accessibility |
| **7+** | MVP 후 진화 | 지속 | — | **W4 노드 라이브러리** / branch/join 노드 / 모바일 |

### 3.2 Workflow Canvas Phase 매핑 (62)

| 62 Phase | Sprint | 시간 |
|----------|--------|------|
| **W1** Read-only 시각화 | 2 | ~3~5일 |
| **W2** 시각적 편집 | 3 | ~1~2주 |
| **W3** Save / Library | 5 | ~3~5일 |
| **W4** 노드 라이브러리 | 7+ | ~1~2주 |

### 3.3 마일스톤

| 시점 | 마일스톤 |
|------|---------|
| Sprint 0 종료 | 빈 dashboard 빌드 가능, shadcn 컴포넌트 1개 동작 |
| Sprint 1 종료 | WebSocket 연결 / 백엔드 컨트랙트 검증 |
| Sprint 2 종료 | 자연어 → Plan 시각화 (read-only) 흐름 작동 |
| Sprint 3 종료 | **사용자가 모든 편집 가능** (시각적 + NL) |
| Sprint 4 종료 | 대화 이력 / 멀티 turn 지원 |
| Sprint 5 종료 | **vision H4 맞춤화 가시화** (Template Library) |
| Sprint 6 종료 | **MVP 출시 가능 상태** |

---

## 4. 학습 곡선 — Frontend 모름 고려

사용자가 "react/vite 만 안다" 출발점 가정.

| 우선순위 | 학습 항목 | 시간 | Vision 기여 |
|:---:|-----------|------|------------|
| 1 | TypeScript 기초 (필수) | 1주 | ⭐⭐⭐⭐⭐ |
| 2 | Tailwind v3.4 + utility 사고 | 3일 | ⭐⭐⭐⭐⭐ |
| 3 | shadcn/ui (CLI / 컴포넌트) | 1일 | ⭐⭐⭐⭐ |
| 4 | Zustand (Redux 대비 매우 단순) | 반나절 | ⭐⭐⭐⭐ |
| 5 | TanStack Query | 1일 | ⭐⭐⭐⭐ |
| 6 | **React Flow (@xyflow/react)** ⭐ | 2~3일 | ⭐⭐⭐⭐⭐ vision 핵심 |
| 7 | dagre / react-hook-form | 1일 | ⭐⭐⭐ |
| 8 | TanStack Router | 1일 | ⭐⭐⭐ |
| 9 | Vitest / Playwright / MSW | 1주 | ⭐⭐⭐ |

→ **총 ~3주 학습** 으로 Sprint 0~2 진행 가능. React Flow 가 평생 자산.

---

## 5. 보안 고려 (최소)

| 영역 | 대응 |
|------|------|
| XSS | react-markdown + remark-gfm (자체 구현 금지) |
| WebSocket auth | Sprint 6+ (인증 추가 시) |
| CORS | 백엔드 FastAPI 설정 (이미 처리) |
| 환경 변수 | `.env` `.env.production` 분리 / `import.meta.env.VITE_*` 만 노출 |
| Bundle 보안 | `pnpm audit` CI 통과 |

→ POC 단계 최소. MVP 진입 시 Sprint 6 보강.

---

## 6. 호환성 / 브라우저 지원

- **데스크탑 우선** (W1~W3): Chrome 120+ / Firefox 120+ / Safari 17+ / Edge 120+
- **모바일** (W4, Sprint 7+): 별도 결정. Workflow Canvas 는 데스크탑 가정
- **반응형 breakpoint**: Tailwind 기본 (sm 640px / md 768px / lg 1024px / xl 1280px / 2xl 1536px)

---

## 7. Risk / Mitigations

| Risk | 완화 |
|------|------|
| React 19 안정성 (출시 직후) | Sprint 0 시점 stable 확인. 문제 시 React 18 fallback |
| TanStack Router 미성숙 → React Router v7 검토 | Sprint 0 PoC 1일 후 결정 |
| shadcn/ui 디자인 일관성 (copy-paste 패턴) | 디자인 토큰 (Tailwind config) 으로 통합 |
| React Flow 학습 비용 | 공식 예제 + 62 문서 / Sprint 2 에서 W1 PoC |
| frontend 개발자 부재 (사용자 1인) | 학습 곡선 §4 + AI 페어 (Claude) 보조 |
| Sprint 5 (Memory View) 가 백엔드 Sprint 15 P1 의존 | 백엔드 우선 진행 / frontend Sprint 4 와 병행 가능한 영역 분리 |

---

## 8. 백엔드와의 협력 — 추적 가이드

### 8.1 진실 소스 매핑

| 백엔드 (진실 소스) | Frontend 측 (계약 검증) |
|-------------------|----------------------|
| `backend/app/core/error_codes.py` | `frontend/src/api/error_codes.ts` (zod) |
| `backend/api_v2/ws_*.py` 메시지 | `frontend/src/api/schemas.ts` (zod) |
| `21_WEBSOCKET_PROTOCOL_v1.5.md` | 63 Frontend Backend Contract (예정) |
| `planner.Plan / PlannedTodo` | `frontend/src/api/schemas.ts` Plan/Todo zod |

### 8.2 Drift 방지

- zod 스키마 = 백엔드 Pydantic 모델과 1:1
- Doc-Code Contract Test (DC) — 백엔드 측 이미 존재. Frontend 측은 Sprint 1 에서 도입 검토
- 백엔드 변경 시 frontend zod 도 함께 업데이트 (PR 체크리스트)

---

## 9. 관련 문서

### 9.1 60대 (Frontend)
- [60_frontend_overview_v1.0.md](60_frontend_overview_v1.0.md) — 본 문서 (진입점)
- *61 (예정)* — Frontend Architecture (State / Routing / Component / Design System)
- [62_workflow_canvas_design_v1.2.md](62_workflow_canvas_design_v1.2.md) — Workflow Canvas (React Flow) ⭐
- *63 (예정)* — Frontend Backend Contract (frontend 측 WS/REST 사용)

### 9.2 백엔드 연관
- [00_vision_and_intent.md](00_vision_and_intent.md) — north star
- [21_WEBSOCKET_PROTOCOL_v1.5.md](21_WEBSOCKET_PROTOCOL_v1.5.md) — WS 메시지 계약
- [22_error_codes_v1.1.md](22_error_codes_v1.1.md) — 에러 카탈로그
- [30_DATA_MODELS_v1.1.md](30_DATA_MODELS_v1.1.md) — Pydantic 모델
- [35_DB_SCHEMA_v1.0.md](35_DB_SCHEMA_v1.0.md) — memory_entries 등

### 9.3 ADR
- [ADR-002](adr/ADR-002_nl_edit_phased_roadmap.md) — NL 1·2·3차
- [ADR-010](adr/ADR-010_plan_schema_unification.md) — planner.Plan 단일화
- *ADR-015 (예정)* — 메모리 + Clarification 통합

### 9.4 탐색 자취 (참고용, 정식 아님)
- [docs/_claude/new_frontend/](../_claude/new_frontend/) — 14 문서
  - 03 UX 원칙 (본 문서 §1.2 정제)
  - 04 State Architecture (61 정제 예정)
  - 05 Routing / Layout (61 정제 예정)
  - 06 Component Inventory (61 정제 예정)
  - 07 Implementation Roadmap (본 문서 §3 정제)
  - 08 Design System (61 정제 예정)
  - 09 Message Card System (61 정제 예정)
  - 11 Tech Stack (본 문서 §2 정제)
  - 12 Tech Stack Analysis (본 문서 §2 정제)
  - 13 Option C Implementation Plan

---

## 10. 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-05-12 | 초안 — vision H1~H4 매핑 + 5 UX 원칙 + Tech Stack 결정 (옵션 A 트렌드 적극) + 7 Sprint roadmap (W1~W4 Workflow Canvas Phase 매핑) + 학습 곡선 (~3주) + 보안 / 호환성 / Risk. 60대 진입점 역할. _claude/new_frontend/ 14 문서를 정제 |
| v1.1 | 2026-05-13 | **Layout 패턴 변경** — v1 GlobalLayout (TopBar + Sidebar + Outlet + SideChatPanel 호출형) 채택. 기존 Conversation-first 에서 Dashboard + Side Chat 으로 정정. 사용자 통찰 "동료 화면 + 채팅 지시". **데이터 source 결정** — POC = data/mock/ 12 CSV → 백엔드 mock API. spec 66 신규 (v1→v2 migration map) 참조 |
| v1.1 (검증 정정) | 2026-05-15 | **프론트 통합 전 문서↔실제 코드 검증 (사이클 3).** §2.1/§2.4 Tailwind 버전 정정 — 문서는 v4 라 했으나 `frontend/package.json` 실제 = `tailwindcss ^3.4.0`. 라우터는 `@tanstack/react-router ^1.45` 로 이미 결정됨 (문서의 "또는 React Router v7 — PoC 후 결정" 은 해소된 상태). 상세: `reports/agent_specs_verification_2026-05-15.md` §사이클3 |
