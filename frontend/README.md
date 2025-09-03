# PharmAssist AI Frontend

제약회사 영업사원을 위한 AI 어시스턴트 프론트엔드

## 🎨 디자인 시스템

### 2025 트렌드 컬러 팔레트
- **Primary (Digital Lavender)**: `#A78BFA` - 주요 액션, 버튼
- **Secondary (Ethereal Blue)**: `#7DD3FC` - 보조 요소, 링크
- **Accent (Burnt Orange)**: `#FB923C` - 강조, 알림
- **Neutral (Mocha Mousse)**: `#A67C6D` - 배경, 텍스트

### 디자인 원칙
1. **Glass Morphism**: 반투명 배경과 블러 효과
2. **Gradient**: 부드러운 그라디언트 전환
3. **Micro Animations**: 섬세한 인터랙션 애니메이션
4. **Accessibility**: WCAG 2.1 AA 준수

## 🏗️ 아키텍처

### 기술 스택
- **React 18.3** + **TypeScript 5.5**
- **Vite**: 빌드 도구
- **Material-UI 5**: UI 컴포넌트
- **Zustand**: 상태 관리
- **React Query**: 서버 상태 관리
- **Framer Motion**: 애니메이션

### 폴더 구조
```
src/
├── components/          # UI 컴포넌트
│   ├── ChatInterface.tsx    # 메인 채팅 인터페이스
│   ├── MessageList.tsx      # 메시지 리스트
│   ├── AgentIndicator.tsx   # 에이전트 상태 표시
│   └── [확장 컴포넌트]
├── services/           # API 통신 레이어
│   ├── chatService.ts       # 채팅 API
│   └── [확장 서비스]
├── store/              # 전역 상태 관리
│   └── chatStore.ts         # 채팅 상태
├── hooks/              # 커스텀 훅
├── utils/              # 유틸리티 함수
├── types/              # TypeScript 타입 정의
└── styles/             # 스타일 및 테마
    ├── theme.ts            # MUI 테마
    └── global.css          # 전역 스타일
```

## 🔌 확장 가이드

### 1. 새로운 페이지 추가
```typescript
// src/pages/Analytics.tsx
import { useChatStore, chatActions } from '../store/chatStore';

export const Analytics = () => {
  const handleLoadAnalytics = () => {
    chatActions.loadPage('analytics');
    // 페이지 로딩 로직
  };
  
  return <div>Analytics Page</div>;
};
```

### 2. 복잡한 스피너 구현
```typescript
// src/components/AdvancedSpinner.tsx
import { useChatStore } from '../store/chatStore';

export const AdvancedSpinner = () => {
  const spinnerState = useChatStore(state => state.metadata.spinnerState);
  
  switch(spinnerState) {
    case 'loading':
      return <LoadingSpinner />;
    case 'processing':
      return <ProcessingAnimation />;
    case 'complete':
      return <SuccessAnimation />;
    default:
      return null;
  }
};

// 사용
chatActions.setSpinnerState('processing');
```

### 3. 파일 업로드 진행률
```typescript
// src/components/FileUpload.tsx
import { useChatStore, chatActions } from '../store/chatStore';

export const FileUpload = () => {
  const progress = useChatStore(state => state.metadata.uploadProgress);
  
  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    // 진행률 업데이트
    const xhr = new XMLHttpRequest();
    xhr.upload.onprogress = (e) => {
      const percent = (e.loaded / e.total) * 100;
      chatActions.setUploadProgress(percent);
    };
    
    // 업로드 로직
  };
  
  return <ProgressBar value={progress} />;
};
```

### 4. 멀티 에이전트 플로우 추적
```typescript
// src/components/AgentFlow.tsx
export const AgentFlow = () => {
  const flow = useChatStore(state => state.metadata.agentFlow);
  
  return (
    <Timeline>
      {flow?.map((step, idx) => (
        <TimelineItem key={idx}>
          <AgentStep agent={step.agent} status={step.status} />
        </TimelineItem>
      ))}
    </Timeline>
  );
};

// 사용
chatActions.trackAgentFlow([
  { agent: 'supervisor', status: 'completed', timestamp: new Date() },
  { agent: 'info_retrieval', status: 'processing', timestamp: new Date() }
]);
```

### 5. 실시간 스트리밍 메시지
```typescript
// src/hooks/useStreamChat.ts
export const useStreamChat = () => {
  const { addMessage, updateLastMessage } = useChatStore();
  
  const streamMessage = (text: string) => {
    const eventSource = chatService.streamMessage(text, sessionId, (chunk) => {
      updateLastMessage({ text: chunk });
    });
    
    return () => eventSource.close();
  };
  
  return { streamMessage };
};
```

### 6. 커스텀 테마 확장
```typescript
// src/styles/customTheme.ts
import { theme } from './theme';

export const customTheme = createTheme({
  ...theme,
  components: {
    ...theme.components,
    MuiButton: {
      variants: [
        {
          props: { variant: 'gradient' },
          style: {
            background: 'linear-gradient(135deg, #A78BFA 0%, #7DD3FC 100%)',
          }
        }
      ]
    }
  }
});
```

## 📡 API 연동

### 환경 변수 설정
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

### API 서비스 확장
```typescript
// src/services/analyticsService.ts
class AnalyticsService {
  async getSalesData(period: string) {
    return api.get(`/api/v1/analytics/sales?period=${period}`);
  }
  
  async getCustomerProfile(customerId: string) {
    return api.get(`/api/v1/analytics/customer/${customerId}`);
  }
}
```

## 🚀 시작하기

### 개발 서버
```bash
npm install
npm run dev
# http://localhost:3000
```

### 프로덕션 빌드
```bash
npm run build
npm run preview
```

### 테스트
```bash
npm run test
npm run test:coverage
```

### 코드 품질
```bash
npm run lint
npm run format
```

## 🔧 주요 설정 파일

### vite.config.ts
- 프록시 설정: `/api` → `http://localhost:8000`
- 별칭 설정: `@` → `src/`

### tsconfig.json
- Strict 모드 활성화
- Path mapping 설정

## 📦 주요 의존성

### 프로덕션
- `react`: UI 라이브러리
- `@mui/material`: UI 컴포넌트
- `zustand`: 상태 관리
- `@tanstack/react-query`: 서버 상태 관리
- `framer-motion`: 애니메이션
- `axios`: HTTP 클라이언트
- `react-markdown`: 마크다운 렌더링

### 개발
- `vite`: 빌드 도구
- `typescript`: 타입 체킹
- `eslint`: 코드 린팅
- `prettier`: 코드 포매팅

## 🎯 성능 최적화

### 코드 스플리팅
```typescript
const Analytics = lazy(() => import('./pages/Analytics'));
```

### 메모이제이션
```typescript
const MemoizedMessageList = memo(MessageList);
```

### 이미지 최적화
```typescript
<img loading="lazy" src={optimizedUrl} />
```

## 🐛 트러블슈팅

### CORS 이슈
프록시 설정 확인 (`vite.config.ts`)

### 상태 지속성
Zustand persist 미들웨어 사용 중

### 타입 에러
`tsconfig.json`의 strict 모드 확인

## 📄 라이선스
MIT

## 🤝 기여 가이드
1. Feature 브랜치 생성
2. 코드 작성 및 테스트
3. PR 제출

## 📞 문의
- 이슈: GitHub Issues
- 이메일: support@pharmassist.ai