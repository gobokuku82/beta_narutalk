/**
 * EditToolbar — 캔버스 우측 상단 편집 toolbar (W2).
 *
 * 책임: 마우스 우클릭 모르는 사용자를 위한 *명시적 진입점*.
 *       + 단계 추가 / 선택 삭제 2개 버튼.
 *
 * 활성 조건:
 *   - editable=true (paused 시점) → 표시
 *   - editable=false → 표시 안 함
 *
 * spec: 62 §5 / ADR-012 §2.6
 */
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEditingStore } from '../store/editingStore';
import { useWorkflowEditing } from './useWorkflowEditing';

interface EditToolbarProps {
  editable: boolean;
}

export function EditToolbar({ editable }: EditToolbarProps) {
  const selectedNodeId = useEditingStore((s) => s.selectedNodeId);
  const { addTodo, deleteTodo } = useWorkflowEditing();

  if (!editable) return null;

  const handleAdd = () => {
    // 기본 todo — 사용자가 PropertyPanel 에서 task_type/agent/tool 등 수정.
    // depends_on 시각 편집은 W4 (엣지 연결) 단계.
    addTodo({
      task_type: 'custom',
      agent: null,
      tool: null,
      tool_params: {},
      depends_on: [],
      priority: 1,
      rationale: '',
      node_type: 'task',
    });
  };

  const handleDelete = () => {
    if (selectedNodeId) deleteTodo(selectedNodeId);
  };

  return (
    <div className="absolute top-3 right-3 z-10 flex items-center gap-2 rounded-panel border border-border bg-card/95 backdrop-blur px-2 py-2 shadow-panel">
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={handleAdd}
        title="새 단계 추가"
      >
        <Plus className="h-4 w-4" />
        단계 추가
      </Button>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={handleDelete}
        disabled={!selectedNodeId}
        title={selectedNodeId ? `${selectedNodeId} 삭제` : '먼저 노드를 선택하세요'}
      >
        <Trash2 className="h-4 w-4" />
        선택 삭제
      </Button>
    </div>
  );
}
