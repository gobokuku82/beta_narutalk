import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from '@tanstack/react-router';
import { Toaster } from 'sonner';
import { router } from './routes/router';
import { useSession } from './features/session/store';
import { useAgent } from './features/agent/store';
import './styles/globals.css';

// localStorage 에서 conversation_id 복원 (App mount 1회).
useSession.getState().hydrate();
// 직전 대화가 있으면 부팅 복원 스피너를 첫 렌더부터 켬 — "빈 상태 한 프레임" 깜빡임 방지 (세션연속성 UX).
// 실제 fetch 종료(성공·0건·실패)는 RootLayout 의 finally 가 끔.
if (useSession.getState().conversationId) useAgent.getState().setRestoring(true);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // 30s
      retry: 1,
    },
  },
});

const rootEl = document.getElementById('root');
if (!rootEl) {
  throw new Error('Root element #root not found in index.html');
}

createRoot(rootEl).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster position="top-right" />
    </QueryClientProvider>
  </StrictMode>,
);
