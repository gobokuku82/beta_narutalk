/**
 * 마케팅 성과 페이지 타입 — backend MarketingPerformanceOutput 미러 (Zod + infer).
 *
 * 진실 소스: backend/app/schemas/outputs/canonical.py
 * World-A canonical 정형 테이블(clumi.blended_computed·*_normalized) → /api/canonical/marketing-performance.
 */
import { z } from 'zod';

export const MarketingKpiSchema = z.object({
  total_ad_cost_krw: z.number(),
  total_msg_cost_krw: z.number(),
  total_marketing_cost_krw: z.number(),
  total_order_revenue_krw: z.number(),
  mer: z.number().nullable(),
  tacos_pct: z.number().nullable(),
});

export const AdChannelPerfSchema = z.object({
  channel: z.string(),
  ad_cost_krw: z.number(),
  impressions: z.number(),
  clicks: z.number(),
  conversion_count: z.number(),
  conversion_revenue_krw: z.number(),
  roas_x: z.number().nullable(),
  ctr_pct: z.number().nullable(),
  cpc_krw: z.number().nullable(),
  cvr_pct: z.number().nullable(),
});

export const MsgChannelPerfSchema = z.object({
  channel: z.string(),
  msg_cost_krw: z.number(),
  msg_target_count: z.number(),
  msg_conversion_count: z.number(),
  msg_conversion_revenue_krw: z.number(),
  msg_roi_pct: z.number().nullable(),
});

export const DailyPointSchema = z.object({
  report_date: z.string(),
  ad_cost_krw: z.number(),
  conversion_count: z.number(),
  conversion_revenue_krw: z.number(),
  roas_x: z.number().nullable(),
});

export const CampaignPerfSchema = z.object({
  channel: z.string(),
  campaign_id: z.string(),
  campaign_name: z.string().nullable(),
  ad_cost_krw: z.number(),
  conversion_count: z.number(),
  conversion_revenue_krw: z.number(),
  roas_x: z.number().nullable(),
  ctr_pct: z.number().nullable(),
  cpc_krw: z.number().nullable(),
  cvr_pct: z.number().nullable(),
});

export const MarketingPerformanceSchema = z.object({
  client: z.string(),
  period: z.string(),
  kpi: MarketingKpiSchema,
  ad_channels: z.array(AdChannelPerfSchema),
  campaigns: z.array(CampaignPerfSchema),
  msg_channels: z.array(MsgChannelPerfSchema),
  daily: z.array(DailyPointSchema),
});

export type MarketingPerformance = z.infer<typeof MarketingPerformanceSchema>;
export type AdChannelPerf = z.infer<typeof AdChannelPerfSchema>;
export type MsgChannelPerf = z.infer<typeof MsgChannelPerfSchema>;
export type CampaignPerf = z.infer<typeof CampaignPerfSchema>;

/** 채널 코드 → 표시 라벨. */
export const CHANNEL_LABEL: Record<string, string> = {
  meta: '메타',
  naver_sa: '네이버 검색',
  advoost: '네이버 GFA',
  kakao: '카카오',
  talktalk: '네이버 톡톡',
};

/** 채널 코드 → 차트 색 (globals.css 토큰). */
export const CHANNEL_FILL: Record<string, string> = {
  meta: 'hsl(var(--channel-meta))',
  naver_sa: 'hsl(var(--channel-naver))',
  advoost: 'hsl(var(--chart-3))',
  kakao: 'hsl(var(--channel-kakao))',
  talktalk: 'hsl(var(--chart-2))',
};

export const channelLabel = (ch: string): string => CHANNEL_LABEL[ch] ?? ch;
