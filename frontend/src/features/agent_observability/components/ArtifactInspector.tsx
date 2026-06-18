/**
 * ArtifactInspector — 각 레이어 경계의 중간 산출물(structured_query/plan/execution_result/response).
 *
 * 사용자 요구 R6(중간 산출물) + R8(레이어별 체크) + R11(data input/output) 검증용.
 *  node_event.data 에서 추출한 raw JSON 을 탭으로 펼쳐 본다.
 * Phase 1 = JSON 트리(읽기). Phase 2+ 에서 diff/스키마 검증 뱃지 추가 예정(§9).
 */
import { useState } from 'react';
import { cn } from '@/lib/cn';
import type { ObsArtifacts } from '../hooks/useAgentObservability';

type TabKey = keyof ObsArtifacts;

const TABS: { key: TabKey; label: string; layer: string }[] = [
  { key: 'structured_query', label: 'structured_query', layer: '인지' },
  { key: 'plan', label: 'plan', layer: '계획' },
  { key: 'execution_result', label: 'execution_result', layer: '실행' },
  { key: 'response', label: 'response', layer: '응답' },
];

function toJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

interface ArtifactInspectorProps {
  artifacts: ObsArtifacts;
}

export function ArtifactInspector({ artifacts }: ArtifactInspectorProps) {
  const [active, setActive] = useState<TabKey>('structured_query');
  const value = artifacts[active];
  const present = value !== undefined && value !== null;

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-card">
      <div className="flex flex-wrap gap-1 border-b border-border px-2 py-2">
        {TABS.map((t) => {
          const has = artifacts[t.key] !== undefined && artifacts[t.key] !== null;
          return (
            <button
              key={t.key}
              type="button"
              onClick={() => setActive(t.key)}
              className={cn(
                'rounded-md px-2.5 py-1 text-xs font-medium transition-colors',
                active === t.key
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted',
              )}
            >
              <span className="mr-1 opacity-60">{t.layer}</span>
              {t.label}
              {has && active !== t.key && (
                <span className="ml-1 inline-block h-1.5 w-1.5 rounded-full bg-primary align-middle" />
              )}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-auto p-3">
        {present ? (
          <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-relaxed text-foreground">
            {toJson(value)}
          </pre>
        ) : (
          <div className="px-2 py-6 text-center text-sm text-muted-foreground">
            아직 산출물이 없습니다. 해당 레이어가 완료되면 채워집니다.
          </div>
        )}
      </div>
    </div>
  );
}
