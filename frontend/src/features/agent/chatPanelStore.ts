/**
 * Chat Panel store — SideChatPanel 의 열림 / 너비 상태.
 *
 * v1 (Redux) chatPanelSlice 의 Zustand 포팅.
 * spec: 61 §1.2 / 66 §4.1
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ChatPanelState {
  isOpen: boolean;
  width: number; // 300~600px
  toggle: () => void;
  open: () => void;
  close: () => void;
  setWidth: (w: number) => void;
}

const MIN_WIDTH = 300;
const MAX_WIDTH = 600;

export const useChatPanel = create<ChatPanelState>()(
  persist(
    (set) => ({
      isOpen: false,
      width: 400,
      toggle: () => set((s) => ({ isOpen: !s.isOpen })),
      open: () => set({ isOpen: true }),
      close: () => set({ isOpen: false }),
      setWidth: (w) =>
        set({ width: Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, w)) }),
    }),
    {
      name: 'chat-panel',
      // 2026-06-10 fix: isOpen 은 persist X — 새로고침 시 default false 로 복원.
      // (이전: isOpen 도 저장돼서 새로고침 후 패널/박스 자동 복원 — "박스 안 없어지는 버그".)
      partialize: (state) => ({ width: state.width }),
    },
  ),
);
