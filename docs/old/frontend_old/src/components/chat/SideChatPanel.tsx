import React from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { closeChatPanel } from '../../features/chatPanel/chatPanelSlice';
import { X, Maximize2 } from 'lucide-react';
import { ChatCore } from './ChatCore';

export const SideChatPanel: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const handleClose = () => {
    dispatch(closeChatPanel());
  };

  const handleFullScreen = () => {
    // 에이전트 탭으로 이동 (동일 세션 유지)
    navigate('/agent');
    dispatch(closeChatPanel());
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Panel Header */}
      <div className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-gray-800">ADALLPIN Agent</h3>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-xs text-green-600 font-medium">Connected</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleFullScreen}
            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors group"
            title="전체화면"
          >
            <Maximize2 className="w-5 h-5 text-gray-500 group-hover:text-gray-700" />
          </button>
          <button
            onClick={handleClose}
            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Chat Content */}
      <div className="flex-1 overflow-hidden">
        <ChatCore compact showHeader={false} />
      </div>
    </div>
  );
};