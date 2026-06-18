/**
 * clumi types — zod schema 회귀.
 *
 * 검증: backend 정답 17 의 실 JSON 모양과 zod schema 가 정합 (parse 통과 + extract).
 *       drift 발생 시 즉시 깨짐 (frontend ↔ backend 계약 강제).
 */
import { describe, expect, it } from 'vitest';

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
} from './types';

// ─────────────────────────────────────────────────────────────────
// KPI 9 — 정답값 17 의 backend HTTP 응답 모양 fixture
// ─────────────────────────────────────────────────────────────────

describe('KPI 9 schemas', () => {
  it('Revenue 119,539,660', () => {
    const r = RevenueSchema.parse({
      revenue_total: 119_539_660,
      active_orders_count: 1_919,
      period: '2026-04',
    });
    expect(r.revenue_total).toBe(119_539_660);
  });

  it('AdCost 18,306,923 — 5매체 by_channel', () => {
    const r = AdCostSchema.parse({
      total_cost: 18_306_923,
      by_channel: { meta: 9_235_826, naver_sa: 5_999_627, advoost: 3_000_000, kakao: 59_020, talktalk: 12_450 },
      period: '2026-04',
    });
    expect(r.total_cost).toBe(18_306_923);
    expect(r.by_channel.meta).toBe(9_235_826);
  });

  it('Roas 6.53', () => {
    const r = RoasSchema.parse({
      roas: 6.53, total_revenue: 119_539_660, total_marketing_cost: 18_306_923, period: '2026-04',
    });
    expect(r.roas).toBe(6.53);
  });

  it('Cac 30,512', () => {
    const r = CacSchema.parse({
      cac: 30_512, total_marketing_cost: 18_306_923, new_members_count: 600, period: '2026-04',
    });
    expect(r.cac).toBe(30_512);
  });

  it('PromoRevenue 43,400,360 (36.3%)', () => {
    const r = PromoRevenueSchema.parse({
      promotion_revenue: 43_400_360, promotion_share_pct: 36.3, promotion_orders_count: 700,
      total_revenue: 119_539_660, period: '2026-04',
    });
    expect(r.promotion_revenue).toBe(43_400_360);
    expect(r.promotion_share_pct).toBe(36.3);
  });

  it('PromoRoas 2.37', () => {
    const r = PromoRoasSchema.parse({
      promotion_roas: 2.37, promotion_revenue: 43_400_360, total_marketing_cost: 18_306_923, period: '2026-04',
    });
    expect(r.promotion_roas).toBe(2.37);
  });

  it('NewMembers 600 + 채널 dict', () => {
    const r = NewMembersSchema.parse({
      new_members_total: 600,
      new_members_by_channel: { naver_search: 196, meta_instagram: 166, direct: 82 },
      period: '2026-04',
    });
    expect(r.new_members_total).toBe(600);
  });

  it('Aov 62,293', () => {
    const r = AovSchema.parse({
      aov: 62_293, unique_buyers: 1_386, orders_count: 1_919, period: '2026-04',
    });
    expect(r.aov).toBe(62_293);
  });

  it('SignupConversion 2.50%', () => {
    const r = SignupConversionSchema.parse({
      signup_conversion_pct: 2.50, signups: 600, sessions: 24_000, period: '2026-04',
    });
    expect(r.signup_conversion_pct).toBe(2.5);
  });
});

// ─────────────────────────────────────────────────────────────────
// MoM 4
// ─────────────────────────────────────────────────────────────────

describe('MoM 4 schemas', () => {
  it('MomRevenue +50.5%', () => {
    const r = MomRevenueSchema.parse({
      period_a_revenue: 79_412_109, period_b_revenue: 119_539_660, delta_pct: 50.5,
      period_a: '2026-03', period_b: '2026-04',
    });
    expect(r.delta_pct).toBe(50.5);
  });

  it('RepurchaseMom existing +19.2 / new +1.4 / rate +2.8pp', () => {
    const r = RepurchaseMomSchema.parse({
      period_a_stats: { total_buyers: 1_206, existing_buyers: 919, new_buyers: 287, repurchase_rate: 76.2 },
      period_b_stats: { total_buyers: 1_386, existing_buyers: 1_095, new_buyers: 291, repurchase_rate: 79.0 },
      delta: { total_buyers_pct: 14.9, existing_buyers_pct: 19.2, new_buyers_pct: 1.4, repurchase_rate_pp: 2.8 },
      period_a: '2026-03', period_b: '2026-04',
    });
    expect(r.delta.existing_buyers_pct).toBe(19.2);
    expect(r.delta.new_buyers_pct).toBe(1.4);
    expect(r.period_b_stats.repurchase_rate).toBe(79.0);
  });

  it('AovMom orders +42.6 / aov +5.6', () => {
    const r = AovMomSchema.parse({
      period_a_stats: { aov: 58_999, unique_buyers: 1_206, orders_count: 1_346 },
      period_b_stats: { aov: 62_293, unique_buyers: 1_386, orders_count: 1_919 },
      delta: { aov_pct: 5.6, buyers_pct: 14.9, orders_pct: 42.6 },
      period_a: '2026-03', period_b: '2026-04',
    });
    expect(r.delta.orders_pct).toBe(42.6);
  });

  it('NewMembersMom -0.2%', () => {
    const r = NewMembersMomSchema.parse({
      period_a_total: 601, period_b_total: 600, delta_pct: -0.2,
      by_channel_a: { meta_instagram: 200 }, by_channel_b: { meta_instagram: 166 },
      period_a: '2026-03', period_b: '2026-04',
    });
    expect(r.delta_pct).toBe(-0.2);
  });
});

// ─────────────────────────────────────────────────────────────────
// Segment 7
// ─────────────────────────────────────────────────────────────────

describe('Segment 7 schemas', () => {
  it('GradeRevenue — SILVER 65,757,080 + WELCOME 74.5%', () => {
    const r = GradeRevenueSchema.parse({
      table: {
        VIP: { member_count: 0, member_share_pct: 0, buyer_count: 0, revenue: 0, revenue_share_pct: 0 },
        GOLD: { member_count: 28, member_share_pct: 0.3, buyer_count: 28, revenue: 8_511_200, revenue_share_pct: 7.5 },
        SILVER: { member_count: 600, member_share_pct: 7.1, buyer_count: 571, revenue: 65_757_080, revenue_share_pct: 57.8 },
        REGULAR: { member_count: 1_539, member_share_pct: 18.1, buyer_count: 787, revenue: 39_496_930, revenue_share_pct: 34.7 },
        WELCOME: { member_count: 6_333, member_share_pct: 74.5, buyer_count: 0, revenue: 0, revenue_share_pct: 0 },
      },
      total_members: 8_500, total_member_revenue: 113_765_210,
      silver_revenue: 65_757_080, welcome_member_share: 74.5,
      period: '2026-04',
    });
    expect(r.silver_revenue).toBe(65_757_080);
    expect(r.table['WELCOME']?.member_share_pct).toBe(74.5);
  });

  it('GradeTimeseries 4시점 (6,680 → 8,500)', () => {
    const r = GradeTimeseriesSchema.parse({
      timeline: [
        { snapshot_date: '2026-01-31', grade_counts: { WELCOME: 6_680 }, total: 6_680 },
        { snapshot_date: '2026-02-28', grade_counts: { WELCOME: 7_299 }, total: 7_299 },
        { snapshot_date: '2026-03-31', grade_counts: { WELCOME: 7_900 }, total: 7_900 },
        { snapshot_date: '2026-04-30', grade_counts: { WELCOME: 6_333, SILVER: 600 }, total: 8_500 },
      ],
      latest_snapshot: { snapshot_date: '2026-04-30', grade_counts: { WELCOME: 6_333 }, total: 8_500 },
      growth_rates: { WELCOME: -5.2, SILVER: null },
      snapshot_count: 4,
    });
    expect(r.snapshot_count).toBe(4);
    expect(r.timeline[3]?.total).toBe(8_500);
  });

  it('AgeSegment 35-44 합 2,884', () => {
    const r = AgeSegmentSchema.parse({
      table: {
        '40-44': { count: 1_455, share_pct: 17.1 },
        '35-39': { count: 1_429, share_pct: 16.8 },
      },
      total_members: 8_500, core_segment_35_44: 2_884,
    });
    expect(r.core_segment_35_44).toBe(2_884);
  });

  it('CategoryDist — 스킨케어 67,652,216', () => {
    const r = CategoryDistSchema.parse({
      by_category: {
        '스킨케어': { count: 1_400, revenue: 67_652_216 },
        '클렌징': { count: 497, revenue: 19_126_163 },
      },
      total_categories: 5, total_distributed_revenue: 119_539_657, period: '2026-04',
    });
    expect(r.by_category['스킨케어']?.revenue).toBe(67_652_216);
  });

  it('ChannelDist — Naver 530 + Meta 388', () => {
    const r = ChannelDistSchema.parse({
      by_raw_channel: { unknown: 481, naver_search: 283, direct: 273 },
      by_group: { Naver: 530, Unknown: 481, Meta: 388, Direct: 273 },
      mapping: { unknown: 'Unknown', naver_search: 'Naver' },
      period: '2026-04',
    });
    expect(r.by_group.Naver).toBe(530);
  });

  it('MemberGuest 1,779 / 140', () => {
    const r = MemberGuestSchema.parse({
      member_count: 1_779, guest_count: 140, total_active: 1_919,
      member_share_pct: 92.7, guest_share_pct: 7.3, period: '2026-04',
    });
    expect(r.member_count).toBe(1_779);
    expect(r.guest_count).toBe(140);
  });

  it('UnknownShare 39.8%', () => {
    const r = UnknownShareSchema.parse({
      unknown_share_pct: 39.8, unknown_revenue: 47_539_330, total_revenue: 119_539_660, unknown_orders: 481,
    });
    expect(r.unknown_share_pct).toBe(39.8);
  });
});

// ─────────────────────────────────────────────────────────────────
// drift detector — 누락 필드 → throw
// ─────────────────────────────────────────────────────────────────

describe('drift detection', () => {
  it('필수 필드 누락 시 throw — Revenue missing revenue_total', () => {
    expect(() =>
      RevenueSchema.parse({ active_orders_count: 1_919, period: '2026-04' }),
    ).toThrow();
  });

  it('잘못된 타입 → throw — Roas roas as string', () => {
    expect(() =>
      RoasSchema.parse({
        roas: '6.53', total_revenue: 1, total_marketing_cost: 1, period: '2026-04',
      }),
    ).toThrow();
  });
});
