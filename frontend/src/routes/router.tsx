/**
 * Router — TanStack Router code-based.
 *
 * 15 라우트 (시스템 6 + 분석 6 + AI 2 + 설정 1).
 * 2026-06-08 (1): v2 → 정식 승격 — dashboard·channel·trend·creative·cost 새 컴포넌트로 교체. dashboard1 + /v2/* 5 폐기.
 * 2026-06-08 (2): dashboard1 백엔드 실데이터 → /monthly (월간 결산) 로 승격.
 * 2026-06-09:    페이지 재구성 — /agent + /hitl 폐기 (-2). label "포트폴리오" → "시스템".
 *                 5 페이지 (report·memory·agent-observability·system·db) CLIENT → SYSTEM 그룹 이동.
 * spec: 61 §2.1 / docs/reports/페이지_재구성_계획서_2026-06-09.md
 */
import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
} from '@tanstack/react-router';

// 시스템 컨텍스트 공용 (포트폴리오 + 리포트)
import { PortfolioPage } from '@/features/portfolio/PortfolioPage';
import { ReportPage } from '@/features/report/ReportPage';

// 분석 6 (2026-06-08 v2 승격 + monthly 승격)
import { DashboardPage } from '@/features/dashboard/DashboardPage';
import { MonthlyPage } from '@/features/monthly/MonthlyPage';
// [marketing-performance] 신설 (2026-06-17) — World-A canonical 정형 테이블 첫 수직 슬라이스. 삭제 시: 본 import + marketingPerformanceRoute + addChildren 항목 제거.
import { MarketingPerformancePage } from '@/features/marketing-performance/MarketingPerformancePage';
// [data-catalog] 신설 (2026-06-17) — canonical 데이터 전체 펼쳐보기(메뉴얼). 삭제 시: 본 import + dataCatalogRoute + addChildren 항목 제거.
import { DataCatalogPage } from '@/features/data_catalog/DataCatalogPage';
import { ChannelPage } from '@/features/channel/ChannelPage';
import { TrendPage } from '@/features/trend/TrendPage';
import { CreativePage } from '@/features/creative/CreativePage';
import { CostPage } from '@/features/cost/CostPage';

// AI 2 (2026-06-09 agent 삭제 후)
import { WorkflowPage } from '@/features/workflow/WorkflowPage';
import { MemoryPage } from '@/features/memory/MemoryPage';
import { ConversationsPage } from '@/features/conversations/ConversationsPage';

// [agent-observability] 신설 (2026-06-05) — 에이전트 작동 관찰. 삭제 시: 본 import + agentObservabilityRoute + addChildren 항목 제거.
import { AgentObservabilityPage } from '@/features/agent_observability/AgentObservabilityPage';

// [system-console] db_console에서 개명 (2026-06-07). 삭제 시: 본 import + systemConsoleRoute + addChildren 항목 제거.
import { SystemConsolePage } from '@/features/system_console/SystemConsolePage';

// [data-console] 신설 (2026-06-07) — Data DB(client 정형 데이터) 콘솔. 삭제 시: 본 import + dataConsoleRoute + addChildren 항목 제거.
import { DataConsolePage } from '@/features/data_console/DataConsolePage';

import { SettingsPage } from '@/features/settings/SettingsPage';

import { RootLayout } from './RootLayout';

// 루트 라우트 (GlobalLayout 포함)
const rootRoute = createRootRoute({
  component: () => <RootLayout><Outlet /></RootLayout>,
});

// 인덱스 (/) → /portfolio
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: PortfolioPage,
});

// 시스템 컨텍스트 — 포트폴리오 + 리포트 (관찰·시스템·DB 라우트는 아래)
const portfolioRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/portfolio',
  component: PortfolioPage,
});

const reportRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/report',
  component: ReportPage,
});

// 클라이언트 컨텍스트 — 분석 6
const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  component: DashboardPage,
});

const monthlyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/monthly',
  component: MonthlyPage,
});

// [marketing-performance] World-A canonical 정형 테이블 첫 페이지 (수직 슬라이스).
const marketingPerformanceRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/marketing-performance',
  component: MarketingPerformancePage,
});

// [data-catalog] canonical 데이터 전체 펼쳐보기 (메뉴얼/카탈로그).
const dataCatalogRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/data-catalog',
  component: DataCatalogPage,
});

const channelRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/channel',
  component: ChannelPage,
});

const trendRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/trend',
  component: TrendPage,
});

const creativesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/creatives',
  component: CreativePage,
});

const costRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/cost',
  component: CostPage,
});

// AI 2 (2026-06-09 agent 삭제 후)
const workflowRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/workflow',
  component: WorkflowPage,
});

const memoryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/memory',
  component: MemoryPage,
});

const conversationsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/conversations',
  component: ConversationsPage,
});

// [agent-observability] 신설 (2026-06-05) — 에이전트 작동 관찰 대시보드.
const agentObservabilityRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/agent-observability',
  component: AgentObservabilityPage,
});

// [system-console] Postgres System DB 무-SQL 조회/삭제/수정 콘솔.
const systemConsoleRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/system',
  component: SystemConsolePage,
});

// [data-console] Data DB(client 정형 데이터) 무-SQL 콘솔.
const dataConsoleRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/db',
  component: DataConsolePage,
});

// 설정
const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  portfolioRoute,
  reportRoute,
  dashboardRoute,
  monthlyRoute,
  marketingPerformanceRoute, // [marketing-performance] 삭제 시 이 줄 제거
  dataCatalogRoute, // [data-catalog] 삭제 시 이 줄 제거
  channelRoute,
  trendRoute,
  creativesRoute,
  costRoute,
  workflowRoute,
  memoryRoute,
  conversationsRoute,
  agentObservabilityRoute, // [agent-observability] 삭제 시 이 줄 제거
  systemConsoleRoute, // [system-console] 삭제 시 이 줄 제거
  dataConsoleRoute, // [data-console] 삭제 시 이 줄 제거
  settingsRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
