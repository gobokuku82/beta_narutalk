import React from 'react';

interface ProgressBarProps {
  value: number; // 0~100
  color?: 'green' | 'blue' | 'amber' | 'red';
  showLabel?: boolean;
  height?: 'sm' | 'md';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  color = 'blue',
  showLabel = false,
  height = 'md',
}) => {
  const colorStyles = {
    green: 'bg-success',
    blue: 'bg-luminous-blue',
    amber: 'bg-warning',
    red: 'bg-danger',
  };

  const heightStyles = {
    sm: 'h-1',
    md: 'h-2',
  };

  const safeValue = Math.min(100, Math.max(0, value));

  return (
    <div className="w-full">
      <div className={`w-full bg-gray-200 rounded-full ${heightStyles[height]}`}>
        <div
          className={`${colorStyles[color]} ${heightStyles[height]} rounded-full transition-all duration-300 ease-out`}
          style={{ width: `${safeValue}%` }}
        />
      </div>
      {showLabel && (
        <div className="flex justify-end mt-1">
          <span className="text-xs text-gray-600">{safeValue}%</span>
        </div>
      )}
    </div>
  );
};