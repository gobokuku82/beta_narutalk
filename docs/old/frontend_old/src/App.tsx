import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './app/store';
import { GlobalLayout } from './components/layout/GlobalLayout';
import { CampaignHome } from './pages/CampaignHome';
import { ChannelAnalysis } from './pages/ChannelAnalysis';
import { CreativeAnalysis } from './pages/CreativeAnalysis';
import { HitlCenter } from './pages/HitlCenter';
import { PortfolioView } from './pages/PortfolioView';
import { AgentChat } from './pages/AgentChat';
import { CostOptimization } from './pages/CostOptimization';
import { Report } from './pages/Report';
import { Settings } from './pages/Settings';
import TrendAnalysis from './pages/TrendAnalysis';
import { Debug } from './Debug';
import ErrorBoundary from './components/common/ErrorBoundary';

// 초기 라우팅 경로를 결정하는 컴포넌트
const InitialRoute = () => {
  const navigationState = store.getState().navigation;

  // 저장된 네비게이션 상태에 따라 적절한 경로로 리다이렉트
  if (navigationState.context === 'portfolio') {
    return <Navigate to="/portfolio" replace />;
  } else if (navigationState.selectedClientId) {
    // 클라이언트가 선택된 경우 대시보드로
    return <Navigate to="/dashboard" replace />;
  }

  // 기본값: 포트폴리오
  return <Navigate to="/portfolio" replace />;
};

function App() {
  console.log('App component rendered');

  return (
    <Provider store={store}>
      <ErrorBoundary>
        <Router>
          <Routes>
            <Route path="/debug" element={<Debug />} />
            <Route path="/" element={<GlobalLayout />}>
              <Route index element={<InitialRoute />} />
              <Route path="dashboard" element={<CampaignHome />} />
              <Route path="analysis" element={<ChannelAnalysis />} />
              <Route path="trend" element={<TrendAnalysis />} />
              <Route path="creatives" element={<CreativeAnalysis />} />
              <Route path="hitl" element={<HitlCenter />} />
              <Route path="portfolio" element={<PortfolioView />} />
              <Route path="agent" element={<AgentChat />} />
              <Route path="cost" element={<CostOptimization />} />
              <Route path="report" element={<Report />} />
              <Route path="settings" element={<Settings />} />
              <Route path="performance" element={<Navigate to="/analysis" />} />
            </Route>
          </Routes>
        </Router>
      </ErrorBoundary>
    </Provider>
  );
}

export default App;
