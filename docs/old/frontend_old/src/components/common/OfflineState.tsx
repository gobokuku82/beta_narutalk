import React from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export interface OfflineStateProps {
  onRetry?: () => void;
  className?: string;
}

export const OfflineState: React.FC<OfflineStateProps> = ({
  onRetry,
  className = '',
}) => {
  const [isOnline, setIsOnline] = React.useState(navigator.onLine);

  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // 온라인 상태면 컴포넌트를 렌더링하지 않음
  if (isOnline) {
    return null;
  }

  const handleRetry = () => {
    if (navigator.onLine) {
      window.location.reload();
    }
    onRetry?.();
  };

  return (
    <div
      className={`fixed inset-0 bg-white z-50 flex items-center justify-center ${className}`}
    >
      <div className="text-center px-4">
        <WifiOff className="w-20 h-20 text-gray-400 mx-auto mb-6" />

        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          인터넷 연결이 끊어졌습니다
        </h2>

        <p className="text-gray-600 mb-8 max-w-md mx-auto">
          네트워크 연결을 확인하고 다시 시도해주세요.
          연결이 복구되면 자동으로 새로고침됩니다.
        </p>

        <Button
          variant="secondary"
          onClick={handleRetry}
          className="gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          다시 시도
        </Button>

        <div className="mt-8 text-sm text-gray-500">
          네트워크 상태:
          <span className="ml-2 font-medium text-danger">오프라인</span>
        </div>
      </div>
    </div>
  );
};

// 오프라인 배너 컴포넌트 (화면 상단에 표시)
export const OfflineBanner: React.FC = () => {
  const [isOnline, setIsOnline] = React.useState(navigator.onLine);

  React.useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // 온라인 복구 시 자동 새로고침 (선택사항)
      setTimeout(() => window.location.reload(), 1000);
    };
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (isOnline) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 bg-warning text-white py-2 px-4 z-50 shadow-lg">
      <div className="flex items-center justify-center gap-2">
        <WifiOff className="w-4 h-4" />
        <span className="text-sm font-medium">
          오프라인 상태입니다. 일부 기능이 제한될 수 있습니다.
        </span>
      </div>
    </div>
  );
};

export default OfflineState;