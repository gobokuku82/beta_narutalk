/**
 * ToolPalette — workflow 페이지 좌측 도킹. 90 tool 카탈로그 검색·필터·표시.
 *
 * 분류 = catalog YAML 의 `category` (33/* 박제 8 카테고리, 작업 ④-L5 단일 박제 정합).
 * 백엔드 admin.py 가 tool.category 노출 → frontend 는 직접 사용 (fine-grained 분류 로직 폐기).
 *
 * 데이터: useAdminCatalog (/api/admin/catalog)
 * 위치: features/workflow/ToolPalette.tsx (workflow 의 sub 컴포넌트)
 *
 * spec: docs/_claude/architecture/frontend_dashboard1_2026-05-26.md §5 Step F7
 */
import { useMemo, useState } from 'react';
import { ChevronDown, ChevronRight, Search, AlertCircle, Loader2 } from 'lucide-react';

import { useAdminCatalog, type ToolMeta } from '@/api/hooks/useAdminCatalog';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/cn';

const GROUP_ORDER = [
  'collection',
  'normalization',
  'cleaning',
  'preprocessing',
  'metrics',
  'comparison',
  'analysis',
  'report',
];

interface ToolCardProps {
  tool: ToolMeta;
}

function ToolCard({ tool }: ToolCardProps) {
  return (
    <div
      className="group rounded-md border border-border bg-card p-2 hover:bg-muted/50 cursor-grab active:cursor-grabbing transition-colors"
      title={`${tool.description}\n\nparams: ${tool.parameters.map((p) => p.name).join(', ') || '(none)'}\nproduces: ${tool.produces.join(', ') || '(none)'}\ndeps: ${tool.dependencies.join(', ') || '(none)'}`}
      draggable
      onDragStart={(e) => {
        // Step F7 후속 — 드래그 → 캔버스에 노드 추가 (PlannedTodo 생성).
        // 현재 표시만, 데이터 transfer 만 설정.
        e.dataTransfer.setData('application/x-tool-name', tool.name);
        e.dataTransfer.effectAllowed = 'copy';
      }}
    >
      <div className="flex items-start justify-between gap-1">
        <p className="text-2xs font-medium text-foreground truncate flex-1">
          {tool.name}
        </p>
        {tool.requires_approval && (
          <Badge variant="outline" className="text-2xs px-1 py-0 h-3.5">
            HITL
          </Badge>
        )}
      </div>
      <p className="text-2xs text-muted-foreground line-clamp-2 mt-0.5">
        {tool.description}
      </p>
    </div>
  );
}

interface GroupSectionProps {
  group: string;
  tools: ToolMeta[];
  defaultOpen?: boolean;
}

function GroupSection({ group, tools, defaultOpen = true }: GroupSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  if (tools.length === 0) return null;
  return (
    <div className="border-b border-border last:border-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 text-2xs font-semibold uppercase tracking-wide text-muted-foreground hover:bg-muted/50"
      >
        <span className="flex items-center gap-1">
          {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          {group}
        </span>
        <span className="text-2xs tabular-nums">{tools.length}</span>
      </button>
      {open && (
        <div className="px-2 pb-2 flex flex-col gap-1">
          {tools.map((t) => (
            <ToolCard key={t.name} tool={t} />
          ))}
        </div>
      )}
    </div>
  );
}

export function ToolPalette() {
  const { data, isLoading, error } = useAdminCatalog();
  const [search, setSearch] = useState('');

  const grouped = useMemo<Record<string, ToolMeta[]>>(() => {
    if (!data?.tools) return {};
    const q = search.trim().toLowerCase();
    const filtered = q
      ? data.tools.filter(
          (t) => t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q),
        )
      : data.tools;
    const out: Record<string, ToolMeta[]> = {};
    for (const t of filtered) {
      const g = t.category;
      (out[g] ||= []).push(t);
    }
    return out;
  }, [data, search]);

  const totalShown = useMemo(
    () => Object.values(grouped).reduce((a, b) => a + b.length, 0),
    [grouped],
  );

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="px-3 py-2 border-b border-border flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wide">Tool Palette</h3>
          <Badge variant="outline" className="text-2xs tabular-nums">
            {data ? `${totalShown}/${data.total}` : '-'}
          </Badge>
        </div>
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="이름·설명 검색"
            className="w-full h-7 pl-7 pr-2 text-2xs rounded-sm border border-input bg-background focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            <span className="text-xs">로딩 중...</span>
          </div>
        )}
        {error && (
          <div className="flex items-center gap-2 px-3 py-2 text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span className="text-xs">로드 실패: {(error as Error).message}</span>
          </div>
        )}
        {data && (
          <div className={cn('flex flex-col')}>
            {GROUP_ORDER.map((g) => (
              <GroupSection key={g} group={g} tools={grouped[g] ?? []} defaultOpen />
            ))}
            {/* GROUP_ORDER 외 그룹 (fallback) */}
            {Object.keys(grouped)
              .filter((g) => !GROUP_ORDER.includes(g))
              .map((g) => (
                <GroupSection key={g} group={g} tools={grouped[g] ?? []} />
              ))}
            {totalShown === 0 && (
              <p className="px-3 py-4 text-2xs text-center text-muted-foreground">
                일치하는 tool 없음
              </p>
            )}
          </div>
        )}
      </div>

      <div className="px-3 py-2 border-t border-border text-2xs text-muted-foreground">
        F7 — 드래그 → 캔버스 노드 추가는 후속 작업 (현재 표시만).
      </div>
    </div>
  );
}
