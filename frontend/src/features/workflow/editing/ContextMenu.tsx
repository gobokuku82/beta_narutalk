/**
 * ContextMenu — Workflow Canvas 노드 우클릭 메뉴 (W2 첫 인터랙션).
 *
 * 책임: editingStore.contextMenu 위치에 fixed 위치 메뉴 표시.
 *       항목 클릭 시 useWorkflowEditing 의 동작 호출 후 메뉴 닫음.
 *
 * 항목 (W2 진입):
 *   - 🗑 삭제 → sendTodoDelete
 *   - ✏ 수정 → openPropertyPanel
 *
 * spec: 62 §5.1 / ADR-012 §2.4
 */
import { useEffect } from 'react';
import { Trash2, Pencil } from 'lucide-react';
import { cn } from '@/lib/cn';
import { useEditingStore } from '../store/editingStore';
import { useWorkflowEditing } from './useWorkflowEditing';

export function ContextMenu() {
  const contextMenu = useEditingStore((s) => s.contextMenu);
  const { closeContextMenu, openPropertyPanel, deleteTodo } = useWorkflowEditing();

  // 외부 클릭 / ESC 로 닫기.
  useEffect(() => {
    if (!contextMenu) return;
    const onClickAway = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest('[data-workflow-context-menu]')) return;
      closeContextMenu();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeContextMenu();
    };
    // 약간 지연 — 우클릭 이벤트 자체가 click-away 로 트리거되는 것 방지.
    const t = setTimeout(() => {
      window.addEventListener('click', onClickAway);
      window.addEventListener('keydown', onKey);
    }, 0);
    return () => {
      clearTimeout(t);
      window.removeEventListener('click', onClickAway);
      window.removeEventListener('keydown', onKey);
    };
  }, [contextMenu, closeContextMenu]);

  if (!contextMenu) return null;

  const { x, y, nodeId } = contextMenu;

  const handleDelete = () => {
    deleteTodo(nodeId);
    closeContextMenu();
  };

  const handleEdit = () => {
    openPropertyPanel(nodeId);
    // openPropertyPanel 이 contextMenu 자동 닫음.
  };

  return (
    <div
      data-workflow-context-menu
      role="menu"
      aria-label="노드 동작"
      className={cn(
        'fixed z-50 min-w-[160px] rounded-panel border border-border bg-card shadow-panel',
        'py-1 text-sm',
      )}
      style={{ left: x, top: y }}
    >
      <button
        type="button"
        role="menuitem"
        onClick={handleEdit}
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-muted transition-colors"
      >
        <Pencil className="h-4 w-4" />
        수정
      </button>
      <button
        type="button"
        role="menuitem"
        onClick={handleDelete}
        className="w-full flex items-center gap-2 px-3 py-2 text-left text-destructive hover:bg-destructive/10 transition-colors"
      >
        <Trash2 className="h-4 w-4" />
        삭제
      </button>
    </div>
  );
}
