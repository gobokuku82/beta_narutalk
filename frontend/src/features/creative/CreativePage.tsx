/**
 * CreativePage — 소재 성과 표.
 *
 * 데이터 (2026-06-09 실데이터 배선): GET /api/dashboard1/creative-overview (Postgres 조립).
 *  - 소재별 CTR/CVR/ROAS/Freq = creatives raw
 *  - 피로(fatigue) = frequency≥3.5 유도 (표준 광고피로 휴리스틱)
 *  - ROAS in-cell 막대·히트, Freq heat(낮을수록 좋음), 정렬·평균 footer.
 */
import type { ReactNode } from 'react';
import { Image } from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { DataTable, type DataTableColumn } from '@/components/viz/DataTable';
import { useCurrentClient } from '@/api/clients';
import { useCreativeOverview, type CreativeOverview } from '@/api/hooks/useCreativeOverview';

const PERIOD = '2026-04';

type Creative = CreativeOverview['creatives'][number];

const CHANNEL_LABEL: Record<string, string> = {
  naver: '네이버', kakao: '카카오', meta: '메타', google: '구글',
};
const CHANNEL_COLOR: Record<string, string> = {
  naver: 'hsl(var(--channel-naver))',
  kakao: 'hsl(var(--channel-kakao))',
  meta: 'hsl(var(--channel-meta))',
  google: 'hsl(var(--channel-google))',
};

function ChannelTag({ ch }: { ch: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span
        aria-hidden
        className="h-2 w-2 rounded-full"
        style={{ background: CHANNEL_COLOR[ch] ?? 'hsl(var(--muted-foreground))' }}
      />
      <span className="text-xs">{CHANNEL_LABEL[ch] ?? ch}</span>
    </span>
  );
}

const COLUMNS: DataTableColumn<Creative>[] = [
  { key: 'id', label: 'ID', sortable: false },
  { key: 'name', label: '소재명', sortable: false },
  { key: 'channel', label: '채널', format: (v): ReactNode => <ChannelTag ch={v as string} /> },
  { key: 'ctr', label: 'CTR', align: 'right', format: (v) => `${v}%`, heat: { direction: 'high', goodAt: 3.0, badAt: 1.5 } },
  { key: 'cvr', label: 'CVR', align: 'right', format: (v) => `${v}%`, heat: { direction: 'high', goodAt: 3.0, badAt: 1.5 } },
  { key: 'roas', label: 'ROAS', align: 'right', format: (v) => `${v}%`, bar: {}, heat: { direction: 'high', goodAt: 600, badAt: 250 } },
  { key: 'frequency', label: 'Freq', align: 'right', format: (v) => (v as number).toFixed(1), heat: { direction: 'low', goodAt: 2.5, badAt: 4.0 } },
  {
    key: 'fatigue',
    label: '피로',
    align: 'center',
    sortable: false,
    format: (v): ReactNode =>
      v ? (
        <span className="text-xs font-medium text-destructive">피로</span>
      ) : (
        <span className="text-muted-foreground">—</span>
      ),
  },
];

export function CreativePage() {
  const client = useCurrentClient();
  const { data, isLoading } = useCreativeOverview(client, PERIOD);
  const creatives = data?.creatives ?? [];

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="소재"
        description={`소재별 성과 (ROAS 막대·히트·피로)${client ? ` · ${client} ${PERIOD}` : ''}`}
        icon={Image}
      />

      {!client ? (
        <p className="text-sm text-muted-foreground">상단에서 client를 선택하세요.</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">불러오는 중…</p>
      ) : creatives.length === 0 ? (
        <p className="text-sm text-muted-foreground">소재 데이터가 없습니다.</p>
      ) : (
        <>
          <DataTable
            columns={COLUMNS}
            rows={creatives}
            defaultSort={{ key: 'roas', desc: true }}
            footerAvg={['ctr', 'cvr', 'roas', 'frequency']}
          />

          <div className="rounded-md bg-muted/40 px-4 py-3 text-2xs leading-relaxed text-muted-foreground">
            <p>
              <span className="font-medium text-foreground">읽는 법</span> — ROAS는 in-cell 막대 + 히트색,
              Freq는 *낮을수록 좋음*(높으면 노출 피로) → 피로 플래그(frequency≥3.5). 컬럼 헤더 클릭 정렬,
              평균은 합계행 자동 집계.
            </p>
            <p className="mt-1">데이터: Postgres 실데이터 ({data?.client} {data?.period}).</p>
          </div>
        </>
      )}
    </div>
  );
}
