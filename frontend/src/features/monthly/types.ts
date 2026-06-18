/**
 * C:LUMI types — backend Pydantic Output 20 모델과 짝.
 *
 * 진실 소스: backend/app/dream_agent/models/clumi_outputs.py
 *
 * Drift 방지: backend 모델 변경 시 본 파일도 함께 update.
 * 패턴: zod schema → z.infer 로 TypeScript type 추출 (api/schemas.ts 동일 컨벤션).
 *
 * 분류:
 *   KPI 9 (Section 1)
 *   MoM 4 (Section 2)
 *   Segment 7 (Section 3-8)
 *
 * spec: docs/_claude/frontend/clumi_2026_04_대시보드_계획서_2026-05-26.md §2.3 / §3.5
 */
import { z } from 'zod';

// ─────────────────────────────────────────────────────────────────
// Section 1. KPI 9
// ─────────────────────────────────────────────────────────────────

export const RevenueSchema = z.object({
  revenue_total: z.number().int(),
  active_orders_count: z.number().int(),
  period: z.string(),
});
export type Revenue = z.infer<typeof RevenueSchema>;

export const AdCostSchema = z.object({
  total_cost: z.number().int(),
  by_channel: z.record(z.number().int()),
  period: z.string(),
});
export type AdCost = z.infer<typeof AdCostSchema>;

export const RoasSchema = z.object({
  roas: z.number(),
  total_revenue: z.number().int(),
  total_marketing_cost: z.number().int(),
  period: z.string(),
});
export type Roas = z.infer<typeof RoasSchema>;

export const CacSchema = z.object({
  cac: z.number().int(),
  total_marketing_cost: z.number().int(),
  new_members_count: z.number().int(),
  period: z.string(),
});
export type Cac = z.infer<typeof CacSchema>;

export const PromoRevenueSchema = z.object({
  promotion_revenue: z.number().int(),
  promotion_share_pct: z.number(),
  promotion_orders_count: z.number().int(),
  total_revenue: z.number().int(),
  period: z.string(),
});
export type PromoRevenue = z.infer<typeof PromoRevenueSchema>;

export const PromoRoasSchema = z.object({
  promotion_roas: z.number(),
  promotion_revenue: z.number().int(),
  total_marketing_cost: z.number().int(),
  period: z.string(),
});
export type PromoRoas = z.infer<typeof PromoRoasSchema>;

export const NewMembersSchema = z.object({
  new_members_total: z.number().int(),
  new_members_by_channel: z.record(z.number().int()),
  period: z.string(),
});
export type NewMembers = z.infer<typeof NewMembersSchema>;

export const AovSchema = z.object({
  aov: z.number().int(),
  unique_buyers: z.number().int(),
  orders_count: z.number().int(),
  period: z.string(),
});
export type Aov = z.infer<typeof AovSchema>;

export const SignupConversionSchema = z.object({
  signup_conversion_pct: z.number(),
  signups: z.number().int(),
  sessions: z.number().int(),
  period: z.string(),
});
export type SignupConversion = z.infer<typeof SignupConversionSchema>;

// ─────────────────────────────────────────────────────────────────
// Section 2. MoM 4
// ─────────────────────────────────────────────────────────────────

export const MomRevenueSchema = z.object({
  period_a_revenue: z.number().int(),
  period_b_revenue: z.number().int(),
  delta_pct: z.number(),
  period_a: z.string(),
  period_b: z.string(),
});
export type MomRevenue = z.infer<typeof MomRevenueSchema>;

const RepurchaseStatsSchema = z.object({
  total_buyers: z.number().int(),
  existing_buyers: z.number().int(),
  new_buyers: z.number().int(),
  repurchase_rate: z.number(),
});
const RepurchaseDeltaSchema = z.object({
  total_buyers_pct: z.number(),
  existing_buyers_pct: z.number(),
  new_buyers_pct: z.number(),
  repurchase_rate_pp: z.number(),
});

export const RepurchaseMomSchema = z.object({
  period_a_stats: RepurchaseStatsSchema,
  period_b_stats: RepurchaseStatsSchema,
  delta: RepurchaseDeltaSchema,
  period_a: z.string(),
  period_b: z.string(),
});
export type RepurchaseMom = z.infer<typeof RepurchaseMomSchema>;

const AovStatsSchema = z.object({
  aov: z.number().int(),
  unique_buyers: z.number().int(),
  orders_count: z.number().int(),
});
const AovDeltaSchema = z.object({
  aov_pct: z.number(),
  buyers_pct: z.number(),
  orders_pct: z.number(),
});

export const AovMomSchema = z.object({
  period_a_stats: AovStatsSchema,
  period_b_stats: AovStatsSchema,
  delta: AovDeltaSchema,
  period_a: z.string(),
  period_b: z.string(),
});
export type AovMom = z.infer<typeof AovMomSchema>;

export const NewMembersMomSchema = z.object({
  period_a_total: z.number().int(),
  period_b_total: z.number().int(),
  delta_pct: z.number(),
  by_channel_a: z.record(z.number().int()),
  by_channel_b: z.record(z.number().int()),
  period_a: z.string(),
  period_b: z.string(),
});
export type NewMembersMom = z.infer<typeof NewMembersMomSchema>;

// ─────────────────────────────────────────────────────────────────
// Section 3-8. Segment 7
// ─────────────────────────────────────────────────────────────────

const GradeRowSchema = z.object({
  member_count: z.number().int(),
  member_share_pct: z.number(),
  buyer_count: z.number().int(),
  revenue: z.number().int(),
  revenue_share_pct: z.number(),
});
export type GradeRow = z.infer<typeof GradeRowSchema>;

export const GradeRevenueSchema = z.object({
  table: z.record(GradeRowSchema),
  total_members: z.number().int(),
  total_member_revenue: z.number().int(),
  silver_revenue: z.number().int(),
  welcome_member_share: z.number(),
  period: z.string(),
});
export type GradeRevenue = z.infer<typeof GradeRevenueSchema>;

const GradeSnapshotSchema = z.object({
  snapshot_date: z.string(),
  grade_counts: z.record(z.number().int()),
  total: z.number().int(),
});
export type GradeSnapshot = z.infer<typeof GradeSnapshotSchema>;

export const GradeTimeseriesSchema = z.object({
  timeline: z.array(GradeSnapshotSchema),
  latest_snapshot: GradeSnapshotSchema.nullable(),
  growth_rates: z.record(z.number().nullable()),
  snapshot_count: z.number().int(),
});
export type GradeTimeseries = z.infer<typeof GradeTimeseriesSchema>;

const AgeBucketRowSchema = z.object({
  count: z.number().int(),
  share_pct: z.number(),
});
export type AgeBucketRow = z.infer<typeof AgeBucketRowSchema>;

export const AgeSegmentSchema = z.object({
  table: z.record(AgeBucketRowSchema),
  total_members: z.number().int(),
  core_segment_35_44: z.number().int(),
});
export type AgeSegment = z.infer<typeof AgeSegmentSchema>;

const CategoryRowSchema = z.object({
  count: z.number().int(),
  revenue: z.number().int(),
});
export type CategoryRow = z.infer<typeof CategoryRowSchema>;

export const CategoryDistSchema = z.object({
  by_category: z.record(CategoryRowSchema),
  total_categories: z.number().int(),
  total_distributed_revenue: z.number().int(),
  period: z.string(),
});
export type CategoryDist = z.infer<typeof CategoryDistSchema>;

export const ChannelDistSchema = z.object({
  by_raw_channel: z.record(z.number().int()),
  by_group: z.record(z.number().int()),
  mapping: z.record(z.string()),
  period: z.string(),
});
export type ChannelDist = z.infer<typeof ChannelDistSchema>;

export const MemberGuestSchema = z.object({
  member_count: z.number().int(),
  guest_count: z.number().int(),
  total_active: z.number().int(),
  member_share_pct: z.number(),
  guest_share_pct: z.number(),
  period: z.string(),
});
export type MemberGuest = z.infer<typeof MemberGuestSchema>;

export const UnknownShareSchema = z.object({
  unknown_share_pct: z.number(),
  unknown_revenue: z.number().int(),
  total_revenue: z.number().int(),
  unknown_orders: z.number().int(),
});
export type UnknownShare = z.infer<typeof UnknownShareSchema>;
