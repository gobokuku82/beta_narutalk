# routes/ — 라우트 컴포넌트 (code-based)

> **현 구현 = TanStack Router code-based** (`router.tsx` 단일 진실).
> Sprint 0 의 file-based 컨벤션 박제 (`__root.tsx` / `conversations/$id.tsx` 등) 는 **시도 후 폐기**, code-based 채택.
> 2026-06-02: `routes/conversations/` `routes/settings/` 빈 폴더 (file-based 잔존) 폐기 + 본 README 갱신.
> 2026-06-08 (1): v2 → 정식 승격 — dashboard·channel·trend·creative·cost 새 컴포넌트로 교체. dashboard1 + `/v2/*` 5 라우트 폐기.
> 2026-06-08 (2): dashboard1 백엔드 실데이터 → `/monthly` (월간 결산) 로 승격. dashboard1 폴더 → monthly rename, hooks useDashboard1* → useMonthly*, 9 컴포넌트 viz/* 리스킨.
> 2026-06-09: 페이지 재구성 — `/agent` + `/hitl` 폐기 (-2). TopBar 라벨 "포트폴리오" → "시스템". 5 페이지 (report·memory·agent-observability·system·db) CLIENT → SYSTEM 그룹 이동. SideChatPanel `Maximize2` 버튼 폐기.

## 단일 진실 = `router.tsx`

모든 라우트 정의 = `createRoute()` 호출. 15 라우트 박제.

## 현 라우트 매트릭스 (15)

| 경로 | 화면 (컴포넌트) | features 폴더 | 컨텍스트 |
|---|---|---|---|
| `/` | PortfolioPage (index → /portfolio) | `portfolio/` | 시스템 |
| `/portfolio` | PortfolioPage | `portfolio/` | 시스템 |
| `/report` | ReportPage | `report/` | 시스템 |
| `/dashboard` | DashboardPage (MetricChainStrip + ChartFrame) | `dashboard/` | 클라이언트 |
| `/monthly` | MonthlyPage (Hero MetricChain + 4 트랙, 실데이터) | `monthly/` | 클라이언트 |
| `/channel` | ChannelPage (ChannelComparison + FunnelChart) | `channel/` | 클라이언트 |
| `/trend` | TrendPage (ChartFrame · 이중 축) | `trend/` | 클라이언트 |
| `/creatives` | CreativePage (DataTable) | `creative/` | 클라이언트 |
| `/cost` | CostPage (PacingWidget + DataTable) | `cost/` | 클라이언트 |
| `/workflow` | WorkflowPage | `workflow/` | 클라이언트 |
| `/memory` | MemoryPage | `memory/` | 시스템 |
| `/conversations` | ConversationsPage | `conversations/` | 클라이언트 |
| `/agent-observability` | AgentObservabilityPage **([agent-observability])** | `agent_observability/` | 시스템 |
| `/system` | SystemConsolePage **([system-console])** | `system_console/` | 시스템 |
| `/db` | DataConsolePage **([data-console])** | `data_console/` | 시스템 |
| `/settings` | SettingsPage | `settings/` | (공통) |

**폐기 (2026-06-09)**: ~~`/agent` (AgentChatPage)~~ · ~~`/hitl` (HitlCenterPage)~~ — 라우트·페이지·feature 폴더 모두 제거. 단 `features/agent/{SideChatPanel·chatPanelStore·store·…}` 는 GlobalLayout·useWebSocket·agent_observability 가 사용 → 보존.

spec 박제 = `docs/agent_specs/61_frontend_architecture_v1.0.md` §2.

## 실험·버전 라우트 컨벤션 (`[tag]` 패턴)

테스트/버전 라우트(`[agent-observability]`·`[system-console]`·`[data-console]` 등)는 **3곳만 손대면 추가·삭제** 가능하도록 표준화:

| 위치 | 추가 시 | 삭제 시 |
|---|---|---|
| `features/{name}/` | 폴더 + 페이지 + 폴더 README (체크리스트 박제) | `rm -rf` |
| `router.tsx` | `[tag]` 주석 + import + `createRoute` + `addChildren` | `grep [tag]` → 4 줄 제거 |
| `features/navigation/store.ts` | `CLIENT_TABS` 또는 `SYSTEM_TABS` (구 PORTFOLIO_TABS) 의 한 줄 + group | 해당 줄 제거 |

→ 폐기 시 `grep [tag]` 한 번으로 모든 흔적이 잡힘. 폴더별 README 에 상세 체크리스트. 메모리 룰 *v1/v2 섞임 금지 — 점진 추가 후 전환 Sprint*.

## 라우트 추가 시

1. `features/{name}/` 또는 적절한 폴더에 페이지 컴포넌트 작성 (예: `XPage.tsx`)
2. `router.tsx` 에:
   - import 추가
   - `createRoute({ getParentRoute, path, component })` 정의
   - `routeTree.addChildren([...])` 에 추가
3. 본 README 라우트 매트릭스 갱신
4. spec 61 §2 갱신

## file-based 채택하지 않은 이유 (자취 박제)

Sprint 0 PoC 결과 = code-based 가 본 프로젝트에 정합:
- 모든 라우트가 `router.tsx` 한 곳에 모여 있어 자취 추적 쉬움
- 동적 import / lazy loading 도 code-based 에서 자유 (현 POC = 全 eager import)
- file-based 의 파일 트리 = 자동 라우트 = 본 프로젝트 규모에 over-engineering

→ `routes/` 폴더는 `router.tsx` + `RootLayout.tsx` + 본 README 만 유지.
