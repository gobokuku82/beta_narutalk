/**
 * WorkflowPage — Workflow Canvas (`/workflow` 라우트).
 *
 * Phase 매핑:
 *   - W1: read-only 시각화 (canvas/)
 *   - W2: 시각적 편집 (editing/ + store/) — ADR-012 진행 중
 *
 * paused 게이트:
 *   - useExecution.isPaused === true 일 때만 편집 활성 (computeCanEdit).
 *   - 비-paused 상태는 read-only + 안내 배너.
 *
 * spec: 62 §2 / §5 / ADR-012
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Info, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { WorkflowCanvas } from './canvas/WorkflowCanvas';
import { ContextMenu } from './editing/ContextMenu';
import { PropertyPanel } from './editing/PropertyPanel';
import { EditToolbar } from './editing/EditToolbar';
import { BatchedToolbar } from './editing/BatchedToolbar';
import { useWorkflowEditing } from './editing/useWorkflowEditing';
import { wouldAddEdgeCreateCycle } from './editing/cycleGuard';
import { useEditingStore } from './store/editingStore';
import { ToolPalette } from './ToolPalette';
import { useExecution, computeCanEdit } from '@/features/execution/store';
import { useSession } from '@/features/session/store';
import { useHitl } from '@/features/hitl/store';
import type { LayoutDirection } from '@/lib/dagre';

export function WorkflowPage() {
  const [direction, setDirection] = useState<LayoutDirection>('TB');
  const [paletteOpen, setPaletteOpen] = useState(true); // F7 — tool palette 도킹 toggle
  const plan = useExecution((s) => s.plan);
  const isPaused = useExecution((s) => s.isPaused);
  const turnId = useSession((s) => s.turnId);
  const editable = computeCanEdit(isPaused, turnId);

  // cascade tint — useHitl.cascadeResult.invalidated 가 직전 편집의 downstream.
  const cascadeResult = useHitl((s) => s.cascadeResult);
  const invalidatedIds = useMemo<string[]>(() => {
    const v = cascadeResult?.invalidated;
    return Array.isArray(v) ? v : [];
  }, [cascadeResult]);

  // batched 시각화 — pendingOps 에서 delete/modify 대상 id 추출 (Stage 6).
  const pendingOps = useEditingStore((s) => s.pendingOps);
  const pendingDeleteIds = useMemo<string[]>(
    () => pendingOps.filter((op) => op.kind === 'delete').map((op) => op.todoId),
    [pendingOps],
  );
  const pendingModifyIds = useMemo<string[]>(
    () => pendingOps.filter((op) => op.kind === 'modify').map((op) => op.todoId),
    [pendingOps],
  );

  // turn 종료 시 (turnId 변경) editingStore 자동 reset — batched 큐가 stale 되는 것 방지.
  // Q: NL 편집은 turnId 유지 채 plan 만 갱신 — pendingOps 가 stale 일 수 있으나
  //    POC 단계에선 사용자가 시각적으로 인지 (대기 배지 노드가 사라지면 알아챔).
  useEffect(() => {
    return () => {
      useEditingStore.getState().reset();
    };
  }, [turnId]);

  const {
    selectNode,
    openContextMenu,
    openPropertyPanel,
    connectEdge,
    disconnectEdge,
    modifyTodo,
  } = useWorkflowEditing();

  // position 변경은 자주 발생 — debounce 300ms.
  // 같은 nodeId 의 연속 드래그는 마지막 위치만 송신.
  const dragTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const handleNodeDragEnd = useCallback(
    (nodeId: string, position: { x: number; y: number }) => {
      const timers = dragTimersRef.current;
      const existing = timers.get(nodeId);
      if (existing) clearTimeout(existing);
      const t = setTimeout(() => {
        modifyTodo(nodeId, { position });
        timers.delete(nodeId);
      }, 300);
      timers.set(nodeId, t);
    },
    [modifyTodo],
  );

  const hasPlan = !!plan && plan.todos.length > 0;
  const showNonPausedHint = hasPlan && !editable;

  return (
    <div className="h-full flex flex-col">
      {/* Page Header */}
      <div className="px-6 py-4 border-b border-border flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPaletteOpen((v) => !v)}
            title={paletteOpen ? 'Tool palette 숨김' : 'Tool palette 열기'}
            className="h-7 w-7 p-0"
          >
            {paletteOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
          </Button>
          <h1 className="text-xl font-bold tracking-tight">워크플로우 캔버스</h1>
          <Badge variant={editable ? 'default' : 'secondary'}>
            {editable ? 'W2 · 편집 가능' : 'W1 · 읽기 전용'}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={direction === 'TB' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setDirection('TB')}
            disabled={!plan}
          >
            세로 ↓
          </Button>
          <Button
            variant={direction === 'LR' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setDirection('LR')}
            disabled={!plan}
          >
            가로 →
          </Button>
        </div>
      </div>

      {/* 비-paused 안내 배너 */}
      {showNonPausedHint && (
        <div className="px-6 py-2 border-b border-border bg-muted/50 text-xs text-muted-foreground flex items-center gap-2">
          <Info className="h-3.5 w-3.5 shrink-0" />
          <span>
            편집은 <strong>일시정지 상태</strong> 에서 가능합니다. 채팅창에서{' '}
            <code className="rounded-sm bg-background px-1">[⏸ 중지]</code> 를 눌러 일시정지하면 노드 우클릭 / 더블클릭 / toolbar 가 활성화됩니다.
          </span>
        </div>
      )}

      {/* Body — Tool palette (좌) + Canvas (우) */}
      <div className="flex-1 min-h-0 flex">
        {/* F7 — Tool Palette 좌측 도킹 (W4 = 노드 팔레트) */}
        {paletteOpen && (
          <aside className="w-64 border-r border-border flex-shrink-0">
            <ToolPalette />
          </aside>
        )}

        {/* Canvas */}
        <div className="flex-1 min-w-0 relative">
        {hasPlan ? (
          <>
            <WorkflowCanvas
              plan={plan}
              direction={direction}
              editable={editable}
              invalidatedIds={invalidatedIds}
              pendingDeleteIds={pendingDeleteIds}
              pendingModifyIds={pendingModifyIds}
              onNodeSelect={selectNode}
              onNodeContextMenu={(nodeId, e) => {
                openContextMenu(nodeId, { x: e.clientX, y: e.clientY });
              }}
              onNodeDoubleClick={openPropertyPanel}
              onEdgeConnect={(source, target) => {
                // Stage 2 — cycle 사전 차단. DFS 로 검증, cycle 이면 sonner 안내 + 드롭 거부.
                if (plan && wouldAddEdgeCreateCycle(plan, source, target)) {
                  toast.error(`순환 의존 — ${source} → ${target} 연결 시 cycle 이 생깁니다.`);
                  return;
                }
                connectEdge(source, target);
              }}
              onEdgeClick={(edge) => {
                if (window.confirm(`의존성 끊기: ${edge.source} → ${edge.target} ?`)) {
                  disconnectEdge(edge.source, edge.target);
                }
              }}
              onNodeDragEnd={handleNodeDragEnd}
            />
            <EditToolbar editable={editable} />
            <BatchedToolbar editable={editable} />
          </>
        ) : (
          <div className="h-full flex flex-col items-center justify-center gap-2 px-6 text-center">
            <p className="text-base text-muted-foreground">
              활성 plan 이 없습니다.
            </p>
            <p className="text-sm text-muted-foreground">
              우측 채팅 패널에서 질문을 시작하면 AI 가 수립한 계획이 여기에 표시됩니다.
            </p>
          </div>
        )}
        <ContextMenu />
        <PropertyPanel />
        </div>
      </div>

      {/* Footer 안내 */}
      <div className="px-6 py-2 border-t border-border text-xs text-muted-foreground flex-shrink-0">
        W1 = 읽기 전용 / W2 = 시각적 편집 (일시정지) / W2′ = 엣지·드래그·묶음 적용 / W3 = Save/Library / W4 = 노드 팔레트 (F7 부분 완성 — 표시·검색 ✓ / 드래그 후속).
      </div>
    </div>
  );
}
