import React, { useState } from 'react';
import { Sparkles } from 'lucide-react';

interface AiTagProps {
  tooltip?: string;
}

export const AiTag: React.FC<AiTagProps> = ({ tooltip = "AI가 전일 대비 데이터 패턴을 분석한 예측값입니다" }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative inline-block">
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 bg-luminous-blue/10 text-luminous-blue text-xs font-medium rounded-full cursor-help transition-colors hover:bg-luminous-blue/20"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <Sparkles className="w-3 h-3" />
        AI
      </span>
      {showTooltip && (
        <div className="absolute z-50 bottom-full mb-2 left-1/2 transform -translate-x-1/2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap shadow-lg">
          <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full">
            <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900" />
          </div>
          {tooltip}
        </div>
      )}
    </div>
  );
};