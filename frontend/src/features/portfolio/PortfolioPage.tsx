/**
 * PortfolioPage — 프레임워크 첫 진입 화면(시스템 랜딩).
 *
 * 구성: WelcomeHero(브랜드 + 한 줄 가치) / AgentLayerDiagram(4-Layer) /
 *       Page Group(프레임 페이지 안내) / PersonaCards.
 * (도메인 분석 페이지 + 부가 콘솔/리포트/설정 진입 카드는 프레임 추출 시 제거 — 2026-06-19)
 */
import {
  Briefcase,
  GitBranch,
  History,
  type LucideIcon,
} from 'lucide-react';
import { Link } from '@tanstack/react-router';

import { Card } from '@/components/ui/card';

import { AgentLayerDiagram } from './AgentLayerDiagram';
import { PersonaCards } from './PersonaCards';
import { WelcomeHero } from './WelcomeHero';

interface PageEntry {
  path: string;
  label: string;
  desc: string;
  icon: LucideIcon;
}

const FRAMEWORK_PAGES: PageEntry[] = [
  { path: '/portfolio', label: '포트폴리오', desc: '시스템 개요', icon: Briefcase },
  { path: '/workflow', label: '워크플로우', desc: '에이전트 작업 추적', icon: GitBranch },
  { path: '/conversations', label: '대화이력', desc: '지난 쿼리 기록', icon: History },
];

export function PortfolioPage() {
  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6">
      <WelcomeHero />
      <AgentLayerDiagram />
      <PageGroupSection
        label="프레임워크"
        sublabel="3 페이지 — 랜딩 + 에이전트"
        pages={FRAMEWORK_PAGES}
      />
      <PersonaCards />
    </div>
  );
}

function PageGroupSection({
  label,
  sublabel,
  pages,
}: {
  label: string;
  sublabel: string;
  pages: PageEntry[];
}) {
  return (
    <section className="flex flex-col gap-3">
      <header className="flex items-baseline justify-between gap-2">
        <h2 className="text-base font-semibold text-foreground">{label}</h2>
        <p className="font-mono text-2xs uppercase tracking-wider text-muted-foreground">
          {sublabel}
        </p>
      </header>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {pages.map((p) => (
          <PageCard key={p.path} entry={p} />
        ))}
      </div>
    </section>
  );
}

function PageCard({ entry }: { entry: PageEntry }) {
  const Icon = entry.icon;
  return (
    <Link to={entry.path} className="block">
      <Card className="flex h-full flex-col gap-2 p-4">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
          <span className="text-sm font-semibold text-foreground">{entry.label}</span>
        </div>
        <p className="text-xs leading-relaxed text-muted-foreground">{entry.desc}</p>
        <span className="mt-auto font-mono text-2xs tabular-nums text-muted-foreground/70">
          {entry.path}
        </span>
      </Card>
    </Link>
  );
}
