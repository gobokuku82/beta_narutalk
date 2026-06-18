import React from 'react';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';

interface AlertItemProps {
  type: 'danger' | 'warning' | 'info';
  title: string;
  description: string;
  onClick?: () => void;
}

export const AlertItem: React.FC<AlertItemProps> = ({ type, title, description, onClick }) => {
  const styles = {
    danger: {
      bg: 'bg-danger-bg',
      border: 'border-danger/30',
      icon: AlertCircle,
      iconColor: 'text-danger',
      titleColor: 'text-danger-dark',
    },
    warning: {
      bg: 'bg-warning-bg',
      border: 'border-warning/30',
      icon: AlertTriangle,
      iconColor: 'text-warning',
      titleColor: 'text-warning-dark',
    },
    info: {
      bg: 'bg-info-bg',
      border: 'border-info/30',
      icon: Info,
      iconColor: 'text-info',
      titleColor: 'text-info',
    },
  };

  const style = styles[type];
  const Icon = style.icon;

  return (
    <div
      className={`p-4 rounded-lg border ${style.bg} ${style.border} ${
        onClick ? 'cursor-pointer hover:shadow-sm transition-shadow' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex gap-3">
        <Icon className={`w-5 h-5 ${style.iconColor} flex-shrink-0 mt-0.5`} />
        <div className="flex-1">
          <h4 className={`font-semibold text-sm ${style.titleColor}`}>{title}</h4>
          <p className="text-sm text-gray-600 mt-1">{description}</p>
        </div>
      </div>
    </div>
  );
};