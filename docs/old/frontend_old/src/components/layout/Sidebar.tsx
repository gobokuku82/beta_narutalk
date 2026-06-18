import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../app/store';
import { setCurrentTab } from '../../features/navigation/navigationSlice';
import {
  Home,
  BarChart3,
  Image,
  UserCheck,
  Briefcase,
  MessageSquare,
  DollarSign,
  FileText,
  Settings,
  HelpCircle,
  LogOut,
  TrendingUp,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const { availableTabs } = useSelector((state: RootState) => state.navigation);

  // 아이콘 매핑
  const iconMap = {
    portfolio: Briefcase,
    dashboard: Home,
    analysis: BarChart3,
    trend: TrendingUp,
    creatives: Image,
    hitl: UserCheck,
    agent: MessageSquare,
    cost: DollarSign,
    report: FileText,
  };

  const menuItems = availableTabs.map(tab => ({
    icon: iconMap[tab.id as keyof typeof iconMap] || Home,
    label: tab.label,
    path: tab.path,
    id: tab.id,
  }));

  const bottomItems = [
    { icon: Settings, label: '설정' },
    { icon: HelpCircle, label: '도움말' },
    { icon: LogOut, label: '로그아웃' },
  ];

  return (
    <div className="w-20 bg-gray-900 h-full flex flex-col">
      <div className="flex-1 py-2 overflow-y-auto">
        {menuItems.map((item, index) => {
          const isActive = location.pathname === item.path;
          return (
            <button
              key={index}
              onClick={() => {
                navigate(item.path);
                dispatch(setCurrentTab(item.id));
              }}
              className={`w-full py-2.5 flex flex-col items-center gap-0.5 transition-colors ${
                isActive
                  ? 'text-white bg-gray-800 border-l-2 border-accent'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
              title={item.label}
            >
              <item.icon className="w-4 h-4" />
              <span className="text-[10px] leading-tight">{item.label}</span>
            </button>
          );
        })}
      </div>

      <div className="border-t border-gray-700 py-4">
        {bottomItems.map((item, index) => (
          <button
            key={index}
            className="w-full py-3 flex justify-center text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            title={item.label}
            onClick={() => {
              if (item.label === '설정') {
                navigate('/settings');
              }
              // 다른 버튼들의 동작은 추후 구현
            }}
          >
            <item.icon className="w-5 h-5" />
          </button>
        ))}
      </div>
    </div>
  );
};