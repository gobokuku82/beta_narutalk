import React from 'react';
import { AlertCircle, WifiOff, ServerCrash, ShieldOff, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps {
  type?: 'api' | 'network' | 'server' | 'permission' | 'generic';
  title?: string;
  description?: string;
  onRetry?: () => void;
  showRetry?: boolean;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  type = 'generic',
  title,
  description,
  onRetry,
  showRetry = true,
  className = '',
}) => {
  const getErrorConfig = () => {
    switch (type) {
      case 'api':
        return {
          icon: <AlertCircle className="w-16 h-16 text-danger" />,
          defaultTitle: 'API 연결 실패',
          defaultDescription: '데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.',
        };
      case 'network':
        return {
          icon: <WifiOff className="w-16 h-16 text-gray-400" />,
          defaultTitle: '네트워크 연결 끊김',
          defaultDescription: '인터넷 연결을 확인해주세요.',
        };
      case 'server':
        return {
          icon: <ServerCrash className="w-16 h-16 text-warning" />,
          defaultTitle: '서버 오류',
          defaultDescription: '서버에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.',
        };
      case 'permission':
        return {
          icon: <ShieldOff className="w-16 h-16 text-gray-400" />,
          defaultTitle: '접근 권한 없음',
          defaultDescription: '이 페이지에 접근할 권한이 없습니다.',
        };
      case 'generic':
      default:
        return {
          icon: <AlertCircle className="w-16 h-16 text-danger" />,
          defaultTitle: '오류가 발생했습니다',
          defaultDescription: '문제가 지속되면 관리자에게 문의하세요.',
        };
    }
  };

  const config = getErrorConfig();

  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}>
      <div className="mb-4">{config.icon}</div>

      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {title || config.defaultTitle}
      </h3>

      <p className="text-sm text-gray-500 text-center max-w-sm mb-6">
        {description || config.defaultDescription}
      </p>

      {showRetry && onRetry && (
        <Button
          variant="secondary"
          onClick={onRetry}
          className="gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          다시 시도
        </Button>
      )}
    </div>
  );
};

export default ErrorState;