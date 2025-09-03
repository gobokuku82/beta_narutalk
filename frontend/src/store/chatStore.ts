import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { Message } from '../types/chat';

interface ChatState {
  messages: Message[];
  sessionId: string | null;
  isConnected: boolean;
  currentAgent: string | null;
  
  // Actions
  addMessage: (message: Message) => void;
  updateLastMessage: (updates: Partial<Message>) => void;
  clearMessages: () => void;
  setSessionId: (sessionId: string) => void;
  setConnected: (connected: boolean) => void;
  setCurrentAgent: (agent: string | null) => void;
  
  // 확장성을 위한 메타데이터
  metadata: Record<string, any>;
  setMetadata: (key: string, value: any) => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        messages: [],
        sessionId: null,
        isConnected: true,
        currentAgent: null,
        metadata: {},

        addMessage: (message) =>
          set((state) => ({
            messages: [...state.messages, message],
          })),

        updateLastMessage: (updates) =>
          set((state) => {
            const messages = [...state.messages];
            if (messages.length > 0) {
              const lastMessage = { ...messages[messages.length - 1], ...updates };
              messages[messages.length - 1] = lastMessage;
            }
            return { messages };
          }),

        clearMessages: () =>
          set({
            messages: [],
            sessionId: null,
          }),

        setSessionId: (sessionId) =>
          set({ sessionId }),

        setConnected: (connected) =>
          set({ isConnected: connected }),

        setCurrentAgent: (agent) =>
          set({ currentAgent: agent }),

        setMetadata: (key, value) =>
          set((state) => ({
            metadata: {
              ...state.metadata,
              [key]: value,
            },
          })),
      }),
      {
        name: 'pharma-chat-store',
        partialize: (state) => ({
          messages: state.messages.slice(-50), // 최근 50개 메시지만 저장
          sessionId: state.sessionId,
        }),
      }
    )
  )
);

// 확장 가능한 액션들
export const chatActions = {
  // 페이지 로드 액션
  loadPage: async (pageId: string) => {
    const store = useChatStore.getState();
    store.setMetadata('loadingPage', true);
    
    try {
      // 페이지 로드 로직
      console.log(`Loading page: ${pageId}`);
      // await pageService.load(pageId);
      
      store.setMetadata('currentPage', pageId);
    } catch (error) {
      console.error('Failed to load page:', error);
    } finally {
      store.setMetadata('loadingPage', false);
    }
  },

  // 복잡한 스피너 상태 관리
  setSpinnerState: (state: 'idle' | 'loading' | 'processing' | 'complete') => {
    const store = useChatStore.getState();
    store.setMetadata('spinnerState', state);
  },

  // 파일 업로드 진행률
  setUploadProgress: (progress: number) => {
    const store = useChatStore.getState();
    store.setMetadata('uploadProgress', progress);
  },

  // 멀티 에이전트 상태 추적
  trackAgentFlow: (flow: Array<{ agent: string; status: string; timestamp: Date }>) => {
    const store = useChatStore.getState();
    store.setMetadata('agentFlow', flow);
  },
};