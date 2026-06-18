/**
 * PropertyPanel — 노드 더블클릭 속성 편집 sheet (W2).
 *
 * 책임: editingStore.propertyPanelOpen 이 true 이고 selectedNodeId 가
 *       현 plan 의 todo 에 매칭되면 우측 sheet 열고 form 표시.
 *       저장 클릭 → sendTodoModify(turnId, todoId, changes) → 패널 닫음.
 *
 * 편집 필드 (Q4 결정):
 *   - rationale (textarea)
 *   - agent (input)
 *   - tool (input)
 *   - tool_params (textarea, JSON)
 *
 * spec: 62 §5.1 / ADR-012 §2.5
 */
import { useEffect, useMemo, useState } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useExecution } from '@/features/execution/store';
import { useEditingStore } from '../store/editingStore';
import { useWorkflowEditing } from './useWorkflowEditing';

function formatToolParams(params: Record<string, unknown> | undefined): string {
  if (!params || Object.keys(params).length === 0) return '{}';
  try {
    return JSON.stringify(params, null, 2);
  } catch {
    return '{}';
  }
}

export function PropertyPanel() {
  const open = useEditingStore((s) => s.propertyPanelOpen);
  const selectedNodeId = useEditingStore((s) => s.selectedNodeId);
  const plan = useExecution((s) => s.plan);
  const { closePropertyPanel, modifyTodo } = useWorkflowEditing();

  const todo = useMemo(() => {
    if (!selectedNodeId || !plan) return null;
    return plan.todos.find((t) => t.id === selectedNodeId) ?? null;
  }, [plan, selectedNodeId]);

  // 폼 상태 — 패널 열릴 때 todo 로부터 초기화.
  const [rationale, setRationale] = useState('');
  const [agent, setAgent] = useState('');
  const [tool, setTool] = useState('');
  const [toolParamsRaw, setToolParamsRaw] = useState('{}');
  const [paramsError, setParamsError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !todo) return;
    setRationale(todo.rationale ?? '');
    setAgent(todo.agent ?? '');
    setTool(todo.tool ?? '');
    setToolParamsRaw(formatToolParams(todo.tool_params));
    setParamsError(null);
  }, [open, todo]);

  const handleSave = () => {
    if (!todo) return;
    // tool_params JSON 파싱.
    let parsedParams: Record<string, unknown> = {};
    const trimmed = toolParamsRaw.trim();
    if (trimmed) {
      try {
        const parsed = JSON.parse(trimmed);
        if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
          setParamsError('tool_params 는 객체 형태여야 합니다.');
          return;
        }
        parsedParams = parsed as Record<string, unknown>;
      } catch {
        setParamsError('JSON 형식이 올바르지 않습니다.');
        return;
      }
    }

    // 변경된 필드만 송신 — 불변 필드 (id, task_type, depends_on 등) 는 보존.
    const changes: Record<string, unknown> = {};
    if ((todo.rationale ?? '') !== rationale) changes.rationale = rationale;
    if ((todo.agent ?? '') !== agent) changes.agent = agent || null;
    if ((todo.tool ?? '') !== tool) changes.tool = tool || null;
    if (formatToolParams(todo.tool_params) !== formatToolParams(parsedParams)) {
      changes.tool_params = parsedParams;
    }

    if (Object.keys(changes).length === 0) {
      // 변경 없음 — 그냥 닫음.
      closePropertyPanel();
      return;
    }

    modifyTodo(todo.id, changes);
    closePropertyPanel();
  };

  return (
    <Sheet open={open && !!todo} onOpenChange={(o) => !o && closePropertyPanel()}>
      <SheetContent side="right" className="w-full sm:max-w-md flex flex-col gap-4">
        <SheetHeader>
          <SheetTitle>노드 속성</SheetTitle>
          <SheetDescription>
            {todo && (
              <>
                <code className="text-xs">{todo.id}</code> · {todo.task_type}
              </>
            )}
          </SheetDescription>
        </SheetHeader>

        {todo && (
          <div className="flex-1 overflow-y-auto space-y-4">
            <div className="space-y-2">
              <Label htmlFor="pp-rationale">설명 (rationale)</Label>
              <Textarea
                id="pp-rationale"
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                rows={3}
                placeholder="이 단계의 목적 / 설명"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pp-agent">담당 agent</Label>
              <Input
                id="pp-agent"
                value={agent}
                onChange={(e) => setAgent(e.target.value)}
                placeholder="예: analyst, collector"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pp-tool">tool</Label>
              <Input
                id="pp-tool"
                value={tool}
                onChange={(e) => setTool(e.target.value)}
                placeholder="예: naver_collector"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pp-params">tool_params (JSON)</Label>
              <Textarea
                id="pp-params"
                value={toolParamsRaw}
                onChange={(e) => {
                  setToolParamsRaw(e.target.value);
                  setParamsError(null);
                }}
                rows={5}
                className="font-mono text-xs"
                placeholder='{"key": "value"}'
              />
              {paramsError && (
                <p className="text-xs text-destructive">{paramsError}</p>
              )}
            </div>

            <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t border-border">
              <p>
                선행: {todo.depends_on.length > 0 ? todo.depends_on.join(', ') : '없음'}
              </p>
              <p>node_type: <code>{todo.node_type ?? 'task'}</code></p>
              <p className="text-muted-foreground/70">
                id / task_type / depends_on 은 본 패널에서 수정 불가 (DAG 영향).
              </p>
            </div>
          </div>
        )}

        <SheetFooter className="gap-2 sm:gap-2">
          <Button variant="outline" onClick={closePropertyPanel}>
            취소
          </Button>
          <Button onClick={handleSave} disabled={!todo}>
            저장
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
