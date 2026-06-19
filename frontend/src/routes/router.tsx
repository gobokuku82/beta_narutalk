/**
 * Router — TanStack Router code-based.
 *
 * 프레임워크 골격: 시스템 랜딩(portfolio) + 워크플로우 캔버스 + 대화이력.
 * (도메인 분석 페이지 + 부가 콘솔/리포트/설정 페이지는 프레임 추출 시 제거 — 2026-06-19)
 */
import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
} from '@tanstack/react-router';

import { PortfolioPage } from '@/features/portfolio/PortfolioPage';
import { WorkflowPage } from '@/features/workflow/WorkflowPage';
import { ConversationsPage } from '@/features/conversations/ConversationsPage';
import { DbDesignPage } from '@/features/db_design/DbDesignPage';

import { RootLayout } from './RootLayout';

// 루트 라우트 (GlobalLayout 포함)
const rootRoute = createRootRoute({
  component: () => <RootLayout><Outlet /></RootLayout>,
});

// 인덱스 (/) → 포트폴리오(시스템 랜딩)
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: PortfolioPage,
});

const portfolioRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/portfolio',
  component: PortfolioPage,
});

const workflowRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/workflow',
  component: WorkflowPage,
});

const conversationsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/conversations',
  component: ConversationsPage,
});

const dbDesignRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/db-design',
  component: DbDesignPage,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  portfolioRoute,
  workflowRoute,
  conversationsRoute,
  dbDesignRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
