import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './contexts/ThemeContext';
import { ChatBot } from './components/ChatBot/ChatBot';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <div className="min-h-screen bg-gradient-to-br from-light-bg via-primary-50/10 to-secondary-50/10 dark:from-dark-bg dark:via-primary-900/10 dark:to-secondary-900/10">
          {/* Background Pattern */}
          <div className="fixed inset-0 opacity-30 dark:opacity-10">
            <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 via-transparent to-secondary-500/5" />
            <div className="absolute inset-0" style={{
              backgroundImage: `radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.05) 0%, transparent 50%),
                               radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.05) 0%, transparent 50%),
                               radial-gradient(circle at 40% 40%, rgba(16, 185, 129, 0.03) 0%, transparent 50%)`,
            }} />
          </div>
          
          {/* Main Content */}
          <div className="relative z-10 flex flex-col items-center justify-center min-h-screen p-4">
            <div className="text-center mb-8">
              <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent mb-4">
                AI Assistant
              </h1>
              <p className="text-gray-600 dark:text-gray-400 text-lg md:text-xl max-w-2xl mx-auto">
                제약회사 영업사원을 위한 인텔리전트 AI 어시스턴트
              </p>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 max-w-6xl w-full mb-8">
              <FeatureCard
                title="정보 검색"
                description="의약품 정보 및 학술자료 즉시 검색"
                icon="🔍"
              />
              <FeatureCard
                title="문서 생성"
                description="제안서 및 보고서 자동 작성"
                icon="📝"
              />
              <FeatureCard
                title="규정 검사"
                description="컴플라이언스 실시간 체크"
                icon="⚖️"
              />
              <FeatureCard
                title="데이터 분석"
                description="판매 실적 및 트렌드 분석"
                icon="📊"
              />
            </div>

            {/* Demo Instructions */}
            <div className="glassmorphism dark:glassmorphism-dark rounded-xl p-6 max-w-md">
              <h2 className="text-xl font-semibold mb-3 text-gray-800 dark:text-gray-200">
                시작하기
              </h2>
              <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                <li className="flex items-start">
                  <span className="mr-2">1.</span>
                  <span>우측 하단의 채팅 버튼을 클릭하세요</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">2.</span>
                  <span>질문을 입력하고 Enter를 누르세요</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">3.</span>
                  <span>AI가 즉시 답변을 제공합니다</span>
                </li>
              </ul>
            </div>
          </div>

          {/* ChatBot */}
          <ChatBot position="bottom-right" />
        </div>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

// Feature Card Component
const FeatureCard: React.FC<{ title: string; description: string; icon: string }> = ({
  title,
  description,
  icon,
}) => {
  return (
    <div className="glassmorphism dark:glassmorphism-dark rounded-xl p-6 hover:scale-105 transition-transform duration-300">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">{title}</h3>
      <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
    </div>
  );
};

export default App;