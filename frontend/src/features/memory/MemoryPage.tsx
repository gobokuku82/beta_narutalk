/**
 * MemoryPage — 누적 학습 메모리 + Workflow Template Library.
 *
 * Sprint 3 (화면설계 + mock 구동). 메모리 API 는 Sprint 5+ — 현재 로컬 샘플.
 * type 별 탭 필터 + 메모리 카드 그리드.
 */
import { useMemo, useState } from 'react';
import {
  Brain,
  Heart,
  Repeat,
  Workflow,
  Lightbulb,
  MessageSquareText,
  type LucideIcon,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/cn';

type MemoryType =
  | 'preference'
  | 'pattern'
  | 'workflow_template'
  | 'fact'
  | 'feedback';

interface MemoryItem {
  id: string;
  type: MemoryType;
  title: string;
  body: string;
  scope: string;
  updatedAt: string;
  usageCount?: number;
}

const TYPE_META: Record<
  MemoryType,
  { label: string; icon: LucideIcon; chip: string }
> = {
  preference: { label: '선호', icon: Heart, chip: 'bg-channel-google/15 text-channel-google' },
  pattern: { label: '패턴', icon: Repeat, chip: 'bg-channel-meta/15 text-channel-meta' },
  workflow_template: {
    label: '워크플로우',
    icon: Workflow,
    chip: 'bg-accent text-accent-foreground',
  },
  fact: { label: '사실', icon: Lightbulb, chip: 'bg-warning/20 text-warning' },
  feedback: {
    label: '피드백',
    icon: MessageSquareText,
    chip: 'bg-channel-naver/15 text-channel-naver',
  },
};

// 로컬 샘플 — 백엔드 memory_entries API 연동 시 교체.
const SAMPLE_MEMORY: MemoryItem[] = [
  {
    id: 'mem_1',
    type: 'preference',
    title: '리포트 정렬 기준',
    body: '성과 리포트는 항상 ROAS 내림차순으로 정렬해서 보여주기를 선호함.',
    scope: 'user',
    updatedAt: '2026-05-12',
  },
  {
    id: 'mem_2',
    type: 'pattern',
    title: '네이버 주말 전환 패턴',
    body: '네이버 캠페인은 주말 CVR 이 평일 대비 평균 22% 높게 나타남. 주말 예산 비중 상향 검토.',
    scope: 'org',
    updatedAt: '2026-05-10',
  },
  {
    id: 'mem_3',
    type: 'workflow_template',
    title: '주간 성과 리포트 생성',
    body: '채널 성과 수집 → 캠페인 집계 → 요약 작성 → 마크다운 출력. 매주 월요일 실행.',
    scope: 'org',
    updatedAt: '2026-05-13',
    usageCount: 14,
  },
  {
    id: 'mem_4',
    type: 'fact',
    title: '블루밍글로우 주력 카테고리',
    body: '블루밍글로우의 매출 비중 1위 카테고리는 스킨케어, 2위는 클렌징.',
    scope: 'org',
    updatedAt: '2026-05-08',
  },
  {
    id: 'mem_5',
    type: 'feedback',
    title: '퍼널 차트 표시 방식',
    body: '전환 퍼널은 전체 합산보다 매체별로 분리해서 보는 것을 선호한다고 피드백함.',
    scope: 'user',
    updatedAt: '2026-05-11',
  },
  {
    id: 'mem_6',
    type: 'workflow_template',
    title: '소재 피로도 점검',
    body: 'creatives 조회 → is_fatigue 필터 → 교체 후보 정리 → 승인 요청.',
    scope: 'org',
    updatedAt: '2026-05-09',
    usageCount: 6,
  },
  {
    id: 'mem_7',
    type: 'pattern',
    title: '메타 소재 피로 주기',
    body: '메타 광고 소재는 집행 12~14일 차에 CTR 이 급락하는 경향. 2주 주기 교체 권장.',
    scope: 'org',
    updatedAt: '2026-05-07',
  },
  {
    id: 'mem_8',
    type: 'preference',
    title: '커뮤니케이션 톤',
    body: '분석 결과는 결론 먼저, 근거는 뒤에. 표보다 핵심 수치 강조를 선호.',
    scope: 'user',
    updatedAt: '2026-05-06',
  },
];

const FILTERS: Array<{ value: string; label: string }> = [
  { value: 'all', label: '전체' },
  { value: 'preference', label: '선호' },
  { value: 'pattern', label: '패턴' },
  { value: 'workflow_template', label: '워크플로우' },
  { value: 'fact', label: '사실' },
  { value: 'feedback', label: '피드백' },
];

export function MemoryPage() {
  const [filter, setFilter] = useState('all');

  const items = useMemo(
    () =>
      filter === 'all'
        ? SAMPLE_MEMORY
        : SAMPLE_MEMORY.filter((m) => m.type === filter),
    [filter],
  );

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="메모리"
        description="누적 학습 (선호 / 패턴 / 사실) + Workflow Template Library"
        icon={Brain}
      />

      <Tabs value={filter} onValueChange={setFilter}>
        <TabsList>
          {FILTERS.map((f) => (
            <TabsTrigger key={f.value} value={f.value}>
              {f.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((m) => {
          const meta = TYPE_META[m.type];
          const Icon = meta.icon;
          return (
            <Card key={m.id} className="card-hover">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div
                    className={cn(
                      'flex h-9 w-9 items-center justify-center rounded-xl',
                      meta.chip,
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <Badge variant="outline">{meta.label}</Badge>
                </div>
                <p className="mt-3 text-sm font-bold">{m.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  {m.body}
                </p>
                <div className="mt-3 flex items-center gap-2 text-2xs text-muted-foreground">
                  <span className="rounded-sm bg-muted px-2 py-1 font-medium">
                    {m.scope}
                  </span>
                  <span>·</span>
                  <span>{m.updatedAt}</span>
                  {m.usageCount != null && (
                    <>
                      <span>·</span>
                      <span>{m.usageCount}회 사용</span>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {items.length === 0 && (
        <p className="text-sm text-muted-foreground">해당 유형의 메모리가 없습니다.</p>
      )}

    </div>
  );
}
