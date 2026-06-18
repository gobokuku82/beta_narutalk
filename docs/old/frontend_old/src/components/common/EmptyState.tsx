import React from 'react';
import { FileX, Search, Package, Inbox } from 'lucide-react';
import { Button } from './Button';

export interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: 'file' | 'search' | 'package' | 'inbox' | React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = '데이터가 없습니다',
  description = '표시할 내용이 없습니다.',
  icon = 'inbox',
  action,
  className = '',
}) => {
  const getIcon = () => {
    if (React.isValidElement(icon)) {
      return icon;
    }

    const iconClass = 'w-16 h-16 text-gray-300';

    switch (icon) {
      case 'file':
        return <FileX className={iconClass} />;
      case 'search':
        return <Search className={iconClass} />;
      case 'package':
        return <Package className={iconClass} />;
      case 'inbox':
      default:
        return <Inbox className={iconClass} />;
    }
  };

  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}>
      <div className="mb-4">{getIcon()}</div>

      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {title}
      </h3>

      <p className="text-sm text-gray-500 text-center max-w-sm mb-6">
        {description}
      </p>

      {action && (
        <Button
          variant="primary"
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
};

export default EmptyState;