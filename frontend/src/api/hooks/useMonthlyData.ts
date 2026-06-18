/**
 * Dashboard1 hooks — `/api/dashboard1/*` 20 endpoint 의 TanStack Query 래퍼.
 *
 * 패턴: useMockData.ts 와 동일 (zod parse + STALE_MS + queryKey hierarchy).
 *
 * Step F6 (2026-05-27): client 인자 추가 (TopBar 클라이언트 드롭다운 store 자동 사용).
 *   - client 가 store 의 selectedClientId (없으면 'clumi' fallback)
 *   - URL 에 ?client=&period= 자동
 *   - queryKey 에 client 포함 → 변경 시 자동 refetch
 *
 * 사용 예:
 *   const { data, isLoading, error } = useMonthlyRevenue('2026-04');
 *   // store 의 selectedClientId 자동 사용
 *
 * 진실 소스: backend/api_v2/routes/clumi.py (20 endpoint, Pydantic Output 매핑)
 * spec: docs/_claude/architecture/frontend_dashboard1_2026-05-26.md §3.4 / §5 Step F6
 *
 * URL 경로는 backend rename 별도라 `/api/dashboard1/*` 그대로. 함수명/queryKey 만 monthly.
 *
 * Rename history:
 *   useClumi* → useDashboard1* (2026-05-27) → useMonthly* (2026-06-08)
 */
import { useQuery } from '@tanstack/react-query';
import type { z } from 'zod';

import { rest } from '../rest';
import {
  AdCostSchema,
  AgeSegmentSchema,
  AovMomSchema,
  AovSchema,
  CacSchema,
  CategoryDistSchema,
  ChannelDistSchema,
  GradeRevenueSchema,
  GradeTimeseriesSchema,
  MemberGuestSchema,
  MomRevenueSchema,
  NewMembersMomSchema,
  NewMembersSchema,
  PromoRevenueSchema,
  PromoRoasSchema,
  RepurchaseMomSchema,
  RevenueSchema,
  RoasSchema,
  SignupConversionSchema,
  UnknownShareSchema,
} from '@/features/monthly/types';
import { useNavigation } from '@/features/navigation/store';

const STALE_MS = 5 * 60_000;
const DEFAULT_CLIENT = 'clumi';

/** TopBar selectedClientId 자동 사용. 없으면 'clumi' fallback. */
function useCurrentClient(): string {
  const id = useNavigation((s) => s.selectedClientId);
  return id ?? DEFAULT_CLIENT;
}

async function fetchTyped<T extends z.ZodTypeAny>(path: string, schema: T): Promise<z.infer<T>> {
  const raw = await rest.get(path);
  return schema.parse(raw);
}

// =========================================================================
// Section 1. KPI 9
// =========================================================================

export function useMonthlyRevenue(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'kpi', 'revenue', client, period] as const,
    queryFn: () =>
      fetchTyped(`/api/dashboard1/kpi/revenue?client=${client}&period=${period}`, RevenueSchema),
    staleTime: STALE_MS,
  });
}

export function useMonthlyAdCost(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'kpi', 'ad-cost', client, period] as const,
    queryFn: () =>
      fetchTyped(`/api/dashboard1/kpi/ad-cost?client=${client}&period=${period}`, AdCostSchema),
    staleTime: STALE_MS,
  });
}

export function useMonthlyRoas(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'kpi', 'roas', client, period] as const,
    queryFn: () =>
      fetchTyped(`/api/dashboard1/kpi/roas?client=${client}&period=${period}`, RoasSchema),
    staleTime: STALE_MS,
  });
}

export function useMonthlyCac(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'kpi', 'cac', client, period] as const,
    queryFn: () =>
      fetchTyped(`/api/dashboard1/kpi/cac?client=${client}&period=${period}`, CacSchema),
    staleTime: STALE_MS,
  });
}

export function useMonthlyPromotionRevenue(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'kpi', 'promotion-revenue', client, period] as const,
    queryFn: () =>
      fetchTyped(
        `/api/dashboard1/kpi/promotion-revenue?client=${client}&period=${period}`,
        PromoRevenueSchema,
      ),
    staleTime: STALE_MS,
  });
}

export function useMonthlyPromotionRoas(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'kpi', 'promotion-roas', client, period] as const,
    queryFn: () =>
      fetchTyped(
        `/api/dashboard1/kpi/promotion-roas?client=${client}&period=${period}`,
        PromoRoasSchema,
      ),
    staleTime: STALE_MS,
  });
}

export function useMonthlyNewMembers(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'kpi', 'new-members', client, period] as const,
    queryFn: () =>
      fetchTyped(
        `/api/dashboard1/kpi/new-members?client=${client}&period=${period}`,
        NewMembersSchema,
      ),
    staleTime: STALE_MS,
  });
}

export function useMonthlyAov(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'kpi', 'aov', client, period] as const,
    queryFn: () =>
      fetchTyped(`/api/dashboard1/kpi/aov?client=${client}&period=${period}`, AovSchema),
    staleTime: STALE_MS,
  });
}

export function useMonthlySignupConversion(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'kpi', 'signup-conversion', client, period] as const,
    queryFn: () =>
      fetchTyped(
        `/api/dashboard1/kpi/signup-conversion?client=${client}&period=${period}`,
        SignupConversionSchema,
      ),
    staleTime: STALE_MS,
  });
}

// =========================================================================
// Section 2. MoM 4
// =========================================================================

export function useMonthlyMomRevenue(a: string, b: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'mom', 'revenue', client, a, b] as const,
    queryFn: () =>
      fetchTyped(`/api/dashboard1/mom/revenue?client=${client}&a=${a}&b=${b}`, MomRevenueSchema),
    staleTime: STALE_MS,
  });
}

export function useMonthlyMomRepurchase(a: string, b: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'mom', 'repurchase', client, a, b] as const,
    queryFn: () =>
      fetchTyped(`/api/dashboard1/mom/repurchase?client=${client}&a=${a}&b=${b}`, RepurchaseMomSchema),
    staleTime: STALE_MS,
  });
}

export function useMonthlyMomAov(a: string, b: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'mom', 'aov', client, a, b] as const,
    queryFn: () =>
      fetchTyped(`/api/dashboard1/mom/aov?client=${client}&a=${a}&b=${b}`, AovMomSchema),
    staleTime: STALE_MS,
  });
}

export function useMonthlyMomNewMembers(a: string, b: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'mom', 'new-members', client, a, b] as const,
    queryFn: () =>
      fetchTyped(
        `/api/dashboard1/mom/new-members?client=${client}&a=${a}&b=${b}`,
        NewMembersMomSchema,
      ),
    staleTime: STALE_MS,
  });
}

// =========================================================================
// Section 3-8. Segment 7
// =========================================================================

export function useMonthlyGrade(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'segment', 'grade', client, period] as const,
    queryFn: () =>
      fetchTyped(
        `/api/dashboard1/segment/grade?client=${client}&period=${period}`,
        GradeRevenueSchema,
      ),
    staleTime: STALE_MS,
  });
}

export function useMonthlyGradeTimeseries() {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'segment', 'grade-timeseries', client] as const,
    queryFn: () =>
      fetchTyped(`/api/dashboard1/segment/grade-timeseries?client=${client}`, GradeTimeseriesSchema),
    staleTime: STALE_MS,
  });
}

export function useMonthlyAge() {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'segment', 'age', client] as const,
    queryFn: () =>
      fetchTyped(`/api/dashboard1/segment/age?client=${client}`, AgeSegmentSchema),
    staleTime: STALE_MS,
  });
}

export function useMonthlyCategory(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'segment', 'category', client, period] as const,
    queryFn: () =>
      fetchTyped(
        `/api/dashboard1/segment/category?client=${client}&period=${period}`,
        CategoryDistSchema,
      ),
    staleTime: STALE_MS,
  });
}

export function useMonthlyChannel(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'segment', 'channel', client, period] as const,
    queryFn: () =>
      fetchTyped(
        `/api/dashboard1/segment/channel?client=${client}&period=${period}`,
        ChannelDistSchema,
      ),
    staleTime: STALE_MS,
  });
}

export function useMonthlyMemberGuest(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'segment', 'member-guest', client, period] as const,
    queryFn: () =>
      fetchTyped(
        `/api/dashboard1/segment/member-guest?client=${client}&period=${period}`,
        MemberGuestSchema,
      ),
    staleTime: STALE_MS,
  });
}

export function useMonthlyUnknownShare(period: string) {
  const client = useCurrentClient();
  return useQuery({
    queryKey: ['monthly', 'segment', 'unknown-share', client, period] as const,
    queryFn: () =>
      fetchTyped(
        `/api/dashboard1/segment/unknown-share?client=${client}&period=${period}`,
        UnknownShareSchema,
      ),
    staleTime: STALE_MS,
  });
}
