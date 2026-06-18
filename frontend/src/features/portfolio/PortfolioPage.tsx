/**
 * PortfolioPage — OctorAD 첫 진입 화면.
 *
 * 2026-06-12 v3 (계획서 적용): 6 섹션 → 4 섹션 단순화.
 *   1. WelcomeHero (Brand + 한 줄 가치) — Apple/Stripe 결, 좌측 옥스블러드 strip 1군데
 *   2. AgentLayerDiagram (데이터분석가 4-Layer) — 시스템 결 SVG
 *   3. Page Group (시스템 6 + 클라이언트 8) — 진입 안내
 *   4. PersonaCards (Data Analyst 활성 + Campaign Designer/Media Director 예정)
 *
 * 폐기: MirofishHeader / OverviewCard / YouTubeEmbed / FeatureCards (Page Group 과 중복).
 *
 * 디자인 시스템 정합:
 *   - PALETTE: Warm Neutral + 옥스블러드 단일 액센트 (Hero strip + 활성 Persona)
 *   - VOCABULARY: Welcome Hero / Layer Diagram / Page Group Card / Persona Card
 *   - feedback_no_ai_looking_ui (그라데이션·glow 0)
 *
 * spec: docs/reports/계획_첫진입페이지_재설계_2026-06-12.md
 *       project_data_analyst_4_layers / project_core_value_data_transformation
 */
import {
  Activity,
  BarChart3,
  Boxes,
  Brain,
  Briefcase,
  CalendarRange,
  Database,
  DollarSign,
  FileText,
  GitBranch,
  History,
  Home,
  Image as ImageIcon,
  TrendingUp,
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

const SYSTEM_PAGES: PageEntry[] = [
  { path: '/portfolio', label: '포트폴리오', desc: '다중 client 개요', icon: Briefcase },
  { path: '/report', label: '리포트', desc: 'PDF 리포트 생성', icon: FileText },
  { path: '/agent-observability', label: '에이전트', desc: '4-Layer 작동 관찰', icon: Activity },
  { path: '/memory', label: '메모리', desc: '장기 기억 관리', icon: Brain },
  { path: '/system', label: 'System', desc: '시스템 콘솔', icon: Database },
  { path: '/db', label: 'DB', desc: 'Data DB 콘솔', icon: Boxes },
];

const CLIENT_PAGES: PageEntry[] = [
  { path: '/dashboard', label: '대시보드', desc: '핵심 KPI 한눈에', icon: Home },
  { path: '/monthly', label: '월간 결산', desc: '월별 결산 + MoM', icon: CalendarRange },
  { path: '/channel', label: '채널', desc: '채널별 비교', icon: BarChart3 },
  { path: '/trend', label: '트렌드', desc: '시계열 추이', icon: TrendingUp },
  { path: '/creatives', label: '소재', desc: '광고 소재 분석', icon: ImageIcon },
  { path: '/cost', label: '비용', desc: '예산 페이싱', icon: DollarSign },
  { path: '/workflow', label: '워크플로우', desc: '에이전트 작업 추적', icon: GitBranch },
  { path: '/conversations', label: '대화이력', desc: '지난 쿼리 기록', icon: History },
];

export function PortfolioPage() {
  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6">
      <WelcomeHero />
      <AgentLayerDiagram />
      <PageGroupSection
        label="시스템 컨텍스트"
        sublabel="6 페이지 — 전체 운영 + 관찰"
        pages={SYSTEM_PAGES}
      />
      <PageGroupSection
        label="클라이언트 컨텍스트"
        sublabel="8 페이지 — client 별 분석 + 작업"
        pages={CLIENT_PAGES}
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
