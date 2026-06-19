/**
 * PersonaCards — 멀티 페르소나 비전 (3 카드 그리드).
 *
 * Data Analyst (활성, 현재 DreamAgent) + Campaign Designer (예정) + Media Director (예정).
 * 활성 = 옥스블러드 좌측 strip + 진한 텍스트. 예정 = dimmed + "예정" 라벨.
 *
 * 디자인 결: Card hover 자동 (VOCABULARY H1~H4) + 좌측 strip (PALETTE J) — 활성만.
 *
 * spec: VOCABULARY §2 Persona Card (v12 신설).
 *       계획서 docs/reports/계획_첫진입페이지_재설계_2026-06-12.md §5.3 (C5=ii).
 */
import { BarChart3, Image as ImageIcon, Sparkles, type LucideIcon } from 'lucide-react';
import { cn } from '@/lib/cn';

interface Persona {
  key: string;
  label: string;
  ko: string;
  desc: string;
  icon: LucideIcon;
  active: boolean;
}

const PERSONAS: Persona[] = [
  {
    key: 'four-layer',
    label: '4-Layer',
    ko: '4-레이어 파이프라인',
    desc: 'cognitive → planning → execution → response.',
    icon: BarChart3,
    active: true,
  },
  {
    key: 'workflow',
    label: 'Workflow',
    ko: '워크플로우 캔버스',
    desc: 'todo · DAG 기반 작업 추적 · 편집.',
    icon: Sparkles,
    active: true,
  },
  {
    key: 'memory',
    label: 'Memory',
    ko: '대화 · 메모리',
    desc: '체크포인트 기반 대화이력 · 복원.',
    icon: ImageIcon,
    active: true,
  },
];

export function PersonaCards() {
  return (
    <section className="flex flex-col gap-3">
      <header className="flex items-baseline justify-between gap-2">
        <h2 className="font-mono text-2xs uppercase tracking-wider text-muted-foreground">
          Personas
        </h2>
        <p className="font-mono text-2xs uppercase tracking-wider text-muted-foreground/70">
          3 core
        </p>
      </header>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {PERSONAS.map((p) => (
          <PersonaCard key={p.key} persona={p} />
        ))}
      </div>
    </section>
  );
}

function PersonaCard({ persona }: { persona: Persona }) {
  const Icon = persona.icon;
  return (
    <article
      className={cn(
        'flex flex-col gap-2 rounded-lg border bg-card p-4 shadow-sm transition duration-200',
        persona.active
          ? 'border-border border-l-2 border-l-primary hover:-translate-y-0.5 hover:bg-primary/4 hover:ring-1 hover:ring-primary/40'
          : 'border-border opacity-60',
      )}
      aria-current={persona.active ? 'true' : undefined}
    >
      <header className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Icon
            className={cn(
              'h-4 w-4 shrink-0',
              persona.active ? 'text-primary' : 'text-muted-foreground',
            )}
            aria-hidden
          />
          <p className="font-mono text-2xs uppercase tracking-wider text-muted-foreground">
            {persona.label}
          </p>
        </div>
        {!persona.active && (
          <span className="rounded-sm border border-border bg-muted/40 px-2 py-1 font-mono text-2xs uppercase tracking-wider text-muted-foreground">
            예정
          </span>
        )}
      </header>
      <h3
        className={cn(
          'text-base font-semibold tracking-tight',
          persona.active ? 'text-foreground' : 'text-muted-foreground',
        )}
      >
        {persona.ko}
      </h3>
      <p className="text-xs leading-relaxed text-muted-foreground">{persona.desc}</p>
    </article>
  );
}
