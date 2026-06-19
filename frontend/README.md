# DreamAgent — Frontend

Vite + React 19 + TypeScript strict + Tailwind v4 + shadcn/ui + Zustand + TanStack Query + React Flow.

> 진실 소스 = spec: [docs/agent_specs/60_frontend_overview_v1.0.md](../docs/agent_specs/60_frontend_overview_v1.0.md) 진입점.

## 빠른 시작

```bash
# 의존성 설치 (pnpm 권장)
pnpm install

# shadcn/ui primitives 설치 (최초 1회)
pnpm dlx shadcn@latest init
pnpm dlx shadcn@latest add button dialog dropdown-menu input select tabs tooltip toast resizable sheet form card badge separator scroll-area

# 백엔드 서버 먼저 기동 (다른 터미널)
cd ../backend && uv run python run_server.py

# Dev 서버
pnpm dev
# → http://localhost:5173

# 빌드 / 타입체크 / 테스트
pnpm build
pnpm typecheck
pnpm test
pnpm test:e2e
```

## 폴더 구조

```
frontend/
├─ src/
│  ├─ main.tsx                # 진입점
│  ├─ App.tsx                 # 라우터 root
│  ├─ routes/                 # 라우트 컴포넌트 (TanStack Router)
│  ├─ components/
│  │  ├─ ui/                  # shadcn/ui primitives (CLI 설치)
│  │  ├─ layout/              # GlobalLayout / TopBar / Sidebar
│  │  └─ markdown/            # MarkdownRenderer
│  ├─ features/               # 도메인 모듈 (store + UI colocated)
│  │  ├─ agent/               # 채팅 / 노드 이벤트
│  │  ├─ hitl/                # HITL / Plan review
│  │  ├─ workflow/            # ⭐ React Flow Canvas (spec 62)
│  │  ├─ conversations/       # 대화 목록
│  │  ├─ attachments/         # 첨부 (Sprint 4+)
│  │  ├─ memory/              # Memory view (Sprint 5+)
│  │  ├─ session/             # WS 연결 / turn 상태
│  │  ├─ settings/            # 테마 / preference
│  │  └─ auth/                # 인증 (Sprint 6+)
│  ├─ api/                    # 백엔드 통신 (spec 63)
│  │  ├─ rest.ts              # fetch wrapper
│  │  ├─ ws.ts                # WebSocket 2 채널 클라이언트
│  │  ├─ schemas.ts           # zod schemas
│  │  ├─ queryKeys.ts         # TanStack Query keys
│  │  ├─ errors.ts            # BackendError
│  │  ├─ errorMessages.ts     # 사용자 친화 메시지
│  │  └─ hooks/               # TanStack Query hooks
│  ├─ lib/                    # 순수 헬퍼 (cn / dagre / format)
│  ├─ styles/                 # globals.css (Tailwind + 토큰)
│  └─ test/                   # Vitest 셋업 + MSW
├─ public/
├─ package.json
├─ vite.config.ts
├─ tailwind.config.ts
├─ tsconfig.{json,app.json,node.json}
├─ components.json            # shadcn/ui 설정
└─ .env.example
```

## 관련 spec

| 번호 | 문서 |
|------|------|
| [60](../docs/agent_specs/60_frontend_overview_v1.0.md) | Frontend Overview (Tech Stack + Vision + Roadmap) |
| [61](../docs/agent_specs/61_frontend_architecture_v1.0.md) | Architecture (State / Routing / Component / Design System) |
| [62](../docs/agent_specs/62_workflow_canvas_design_v1.0.md) | Workflow Canvas (React Flow) ⭐ |
| [63](../docs/agent_specs/63_frontend_backend_contract_v1.0.md) | Backend Contract (WS / REST / zod) |

## 학습 가이드 (frontend 모르는 경우)

[`60 §4 학습 곡선`](../docs/agent_specs/60_frontend_overview_v1.0.md#4-학습-곡선--frontend-모름-고려) 참고. ~3주 학습으로 Sprint 0~2 진행 가능.

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-13 | 초기 셋업 — Vite + React 19 + TypeScript strict + Tailwind + 디렉터리 구조 + zod schema / API client 스켈레톤 + Vitest/MSW |
