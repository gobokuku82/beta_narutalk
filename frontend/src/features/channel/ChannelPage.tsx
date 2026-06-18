/**
 * ChannelPage — 채널 비교 + 전환 퍼널.
 *
 * 데이터 (2026-06-09 실데이터 배선): GET /api/dashboard1/channel-overview (Postgres 조립).
 *  - 채널별 ROAS/CPA/전환 = channel_table_detailed(T05), 스파크라인 = daily_performance 일별 roas
 *  - 목표 = channel_targets raw (채널별 ROAS/CPA 목표)
 *  - 역할(검색/소셜/디스플레이) = 도메인 분류 고정 매핑
 *  - 퍼널 = channel_funnel(C06) 3단계(노출→클릭→전환). 6단계(랜딩·장바구니·구매·재구매)는 후속.
 */
import { BarChart3 } from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { ChannelComparison, type ChannelPanel } from '@/components/viz/ChannelComparison';
import { FunnelChart } from '@/components/viz/FunnelChart';
import { ChartFrame } from '@/components/viz/ChartFrame';
import { useCurrentClient } from '@/api/clients';
import { useChannelOverview, type ChannelOverview } from '@/api/hooks/useChannelOverview';

const PERIOD = '2026-04';

const CHANNEL_LABEL: Record<string, string> = {
  naver: '네이버 검색', google: '구글', meta: '메타', kakao: '카카오',
};
const CHANNEL_COLOR: Record<string, string> = {
  naver: 'hsl(var(--channel-naver))',
  google: 'hsl(var(--channel-google))',
  meta: 'hsl(var(--channel-meta))',
  kakao: 'hsl(var(--channel-kakao))',
};
// 채널 역할 = 도메인 분류 (데이터 아님 — 고정 매핑)
const CHANNEL_ROLE: Record<string, string> = {
  naver: '검색 (수요 수확)',
  google: '검색 (수요 수확)',
  meta: '소셜 (수요 창출)',
  kakao: '디스플레이/소셜',
};

type Status = 'above' | 'below' | 'on';
const roasStatus = (a: number, t: number): Status => (a >= t ? 'above' : 'below');
const cpaStatus = (a: number, t: number): Status => (a <= t ? 'above' : 'below'); // CPA는 낮을수록 좋음

function buildPanels(d: ChannelOverview): ChannelPanel[] {
  return d.channels.map((c) => ({
    name: CHANNEL_LABEL[c.channel] ?? c.channel,
    color: CHANNEL_COLOR[c.channel] ?? 'hsl(var(--muted-foreground))',
    role: CHANNEL_ROLE[c.channel],
    sparkData: c.spark,
    metrics: [
      {
        label: 'ROAS',
        value: `${c.roas}%`,
        target:
          c.target_roas != null
            ? { label: `목표 ${c.target_roas}%`, status: roasStatus(c.roas, c.target_roas) }
            : undefined,
      },
      {
        label: 'CPA',
        value: `₩${c.cpa.toLocaleString('ko-KR')}`,
        target:
          c.target_cpa != null
            ? { label: `목표 ≤${c.target_cpa.toLocaleString('ko-KR')}`, status: cpaStatus(c.cpa, c.target_cpa) }
            : undefined,
      },
      { label: '전환', value: `${c.conversions}` },
    ],
  }));
}

export function ChannelPage() {
  const client = useCurrentClient();
  const { data, isLoading } = useChannelOverview(client, PERIOD);

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="채널"
        description={`채널 역할별 비교 + 전환 퍼널${client ? ` · ${client} ${PERIOD}` : ''}`}
        icon={BarChart3}
      />

      {!client ? (
        <p className="text-sm text-muted-foreground">상단에서 client를 선택하세요.</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">불러오는 중…</p>
      ) : !data ? (
        <p className="text-sm text-muted-foreground">데이터가 없습니다.</p>
      ) : (
        <>
          <ChannelComparison channels={buildPanels(data)} />

          <ChartFrame title="전환 퍼널" meta="전체 채널 합산 · 노출→클릭→전환" height={320} responsive={false}>
            <FunnelChart stages={data.funnel} />
          </ChartFrame>

          <div className="rounded-md bg-muted/40 px-4 py-3 text-2xs leading-relaxed text-muted-foreground">
            <p>
              <span className="font-medium text-foreground">읽는 법</span> — 채널을 *역할별로* 본다:
              검색(네이버/구글)은 즉시 ROAS↑ 정상, 메타는 소셜(수요 창출)이라 단기 ROAS 낮음이 자연스러움
              — 같은 ROAS 잣대로 메타를 "최악"이라 판단하면 어트리뷰션 함정. 각 지표는 채널별 목표 대비.
            </p>
            <p className="mt-1">데이터: Postgres 실데이터 ({data.client} {data.period}).</p>
          </div>
        </>
      )}
    </div>
  );
}
