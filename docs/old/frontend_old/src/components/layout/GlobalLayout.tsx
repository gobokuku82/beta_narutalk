import React from 'react';
import { Outlet } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../app/store';
import { setChatPanelWidth } from '../../features/chatPanel/chatPanelSlice';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { SideChatPanel } from '../chat/SideChatPanel';

export const GlobalLayout: React.FC = () => {
  const dispatch = useDispatch();
  const { isOpen: isChatOpen, width: chatPanelWidth } = useSelector(
    (state: RootState) => state.chatPanel
  );
  const [isResizing, setIsResizing] = React.useState(false);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  React.useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const newWidth = window.innerWidth - e.clientX;
      dispatch(setChatPanelWidth(newWidth));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
    } else {
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };
  }, [isResizing, dispatch]);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <div
          className="flex-1 overflow-auto transition-all duration-300 ease-in-out"
          style={{ marginRight: isChatOpen ? `${chatPanelWidth}px` : '0' }}
        >
          <Outlet />
        </div>

        {/* Resizer */}
        {isChatOpen && (
          <div
            className={`fixed top-16 h-[calc(100vh-4rem)] w-1 bg-gray-300 hover:bg-accent transition-colors cursor-col-resize z-50 ${
              isResizing ? 'bg-accent' : ''
            }`}
            style={{ right: `${chatPanelWidth}px` }}
            onMouseDown={handleMouseDown}
          >
            <div className="absolute inset-y-0 left-[-2px] right-[-2px]" />
          </div>
        )}

        {/* Side Chat Panel - 레이아웃의 일부로 통합 */}
        <div
          className={`fixed top-16 right-0 h-[calc(100vh-4rem)] bg-gray-50 shadow-lg border-l border-gray-200 transition-transform duration-300 ease-in-out ${
            isChatOpen ? 'translate-x-0' : 'translate-x-full'
          }`}
          style={{ width: `${chatPanelWidth}px` }}
        >
          <SideChatPanel />
        </div>
      </div>
    </div>
  );
};