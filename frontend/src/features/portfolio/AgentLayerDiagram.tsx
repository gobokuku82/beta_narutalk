/**
 * AgentLayerDiagram — 데이터분석가 4-Layer 비즈니스 가치 흐름 시각화.
 *
 * Data → Analysis → Decision → Execution (사용자 정의 4 레이어).
 * Gartner Analytics 표준 매핑: Descriptive / Diagnostic+Predictive / Prescriptive / Operational+Adaptive.
 * inline SVG (외부 라이브러리 0), 가로 4 노드 + 화살표.
 *
 * 2026-06-10 v2: 백엔드 Agent 내부 4-Layer (Cognitive/Planning/Execution/Response) 결 →
 *   비즈니스 가치 흐름 (정보→분석→의사결정→실행) 로 재정의. 사용자 본인 정체성 정의.
 *
 * spec: VOCABULARY §2 Layer Diagram (v8 신설).
 *       PALETTE §8.2 B (hairline) + J (좌측 액센트).
 *       project_data_analyst_4_layers memory (예정).
 */
import { cn } from '@/lib/cn';

interface Layer {
  key: string;
  label: string;
  ko: string;
  desc: string;
}

const LAYERS: Layer[] = [
  { key: 'data',      label: 'Data',      ko: '데이터',   desc: '사실 기반의 측정과 정제' },
  { key: 'analysis',  label: 'Analysis',  ko: '분석',     desc: '원인 진단과 미래 예측' },
  { key: 'decision',  label: 'Decision',  ko: '의사결정', desc: '옵션 평가와 선택 확정' },
  { key: 'execution', label: 'Execution', ko: '실행',     desc: '운영 전환과 결과 학습' },
];

interface AgentLayerDiagramProps {
  className?: string;
}

export function AgentLayerDiagram({ className }: AgentLayerDiagramProps) {
  return (
    <div className={cn('rounded-card border border-border bg-card p-6', className)}>
      <div className="mb-4 flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold text-foreground">데이터분석가</h3>
        <span className="text-xs text-muted-foreground">
          raw 데이터 분석에서 행동까지
        </span>
      </div>

      {/* 노드 4 + 화살표 — grid 로 균등 배치, 마지막 노드는 화살표 없음 */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr]">
        {LAYERS.map((layer, i) => (
          <ArrowFragment key={layer.key} layer={layer} isLast={i === LAYERS.length - 1} />
        ))}
      </div>
    </div>
  );
}

function ArrowFragment({ layer, isLast }: { layer: Layer; isLast: boolean }) {
  return (
    <>
      <LayerNode layer={layer} />
      {!isLast && (
        <div
          aria-hidden
          className="flex shrink-0 items-center justify-center text-muted-foreground/60"
        >
          <ArrowRightIcon />
        </div>
      )}
    </>
  );
}

function LayerNode({ layer }: { layer: Layer }) {
  return (
    <div className="rounded-card border border-border bg-muted/40 p-3 transition duration-200 hover:bg-muted/60">
      <p className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">
        {layer.label}
      </p>
      <p className="mt-1 text-sm font-semibold text-foreground">{layer.ko}</p>
      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{layer.desc}</p>
    </div>
  );
}

function ArrowRightIcon() {
  // 가로 화살표 — 모바일에서는 hidden (grid 가 1 column 됨)
  return (
    <svg
      width="20"
      height="12"
      viewBox="0 0 20 12"
      fill="none"
      className="hidden md:block"
    >
      <path
        d="M0 6 L16 6 M11 1 L16 6 L11 11"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
