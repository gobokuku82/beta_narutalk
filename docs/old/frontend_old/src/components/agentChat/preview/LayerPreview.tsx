import React from 'react';
import { ChevronDown, ChevronUp, Check, Loader2, AlertCircle, Clock } from 'lucide-react';
import type { LayerType, LayerStatus } from '../../../types';

interface LayerPreviewProps {
  layer: LayerType;
  status: LayerStatus;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

export const LayerPreview: React.FC<LayerPreviewProps> = ({
  layer,
  status,
  expanded,
  onToggle,
  children,
}) => {
  const getLayerInfo = () => {
    switch (layer) {
      case 'cognitive':
        return { label: '의도분석', color: 'bg-blue-500', bgLight: 'bg-blue-50' };
      case 'planning':
        return { label: '계획수립', color: 'bg-green-500', bgLight: 'bg-green-50' };
      case 'execution':
        return { label: '실행', color: 'bg-amber-500', bgLight: 'bg-amber-50' };
      case 'response':
        return { label: '결과생성', color: 'bg-purple-500', bgLight: 'bg-purple-50' };
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <Check className="w-4 h-4 text-green-600" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'waiting_hitl':
        return <Clock className="w-4 h-4 text-amber-600" />;
      default:
        return <div className="w-4 h-4 rounded-full bg-gray-300" />;
    }
  };

  const info = getLayerInfo();

  return (
    <div className={`border rounded-lg overflow-hidden ${
      status === 'running' ? 'border-blue-400 shadow-sm' :
      status === 'error' ? 'border-red-400' :
      status === 'waiting_hitl' ? 'border-amber-400' :
      'border-gray-200'
    }`}>
      <button
        onClick={onToggle}
        className={`w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors ${
          status === 'running' ? info.bgLight : ''
        }`}
      >
        <div className="flex items-center gap-3">
          <div className={`w-2 h-8 ${info.color} rounded`} />
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="font-medium text-sm">{info.label}</span>
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {expanded && (
        <div className="border-t border-gray-200 p-4 bg-gray-50/50">
          {children}
        </div>
      )}
    </div>
  );
};