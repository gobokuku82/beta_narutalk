import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../app/store';
import { UserRole } from '../features/auth/authSlice';
import {
  Building2,
  Users,
  UserPlus,
  Coins,
  CreditCard,
  Target,
  Bell,
  Shield
} from 'lucide-react';

// 탭 컴포넌트들 import
import { WorkspaceTab } from '../components/settings/WorkspaceTab';
import { ClientManagementTab } from '../components/settings/ClientManagementTab';
import { MemberManagementTab } from '../components/settings/MemberManagementTab';
import { TokenUsageTab } from '../components/settings/TokenUsageTab';
import { PlanBillingTab } from '../components/settings/PlanBillingTab';
import { KPISettingsTab } from '../components/settings/KPISettingsTab';
import { NotificationSettingsTab } from '../components/settings/NotificationSettingsTab';

interface SettingsTab {
  id: string;
  label: string;
  icon: React.ElementType;
  component: React.ComponentType;
  adminOnly: boolean;
}

const settingsTabs: SettingsTab[] = [
  {
    id: 'workspace',
    label: '워크스페이스',
    icon: Building2,
    component: WorkspaceTab,
    adminOnly: false,
  },
  {
    id: 'clients',
    label: '클라이언트 관리',
    icon: Users,
    component: ClientManagementTab,
    adminOnly: true,
  },
  {
    id: 'members',
    label: '멤버 관리',
    icon: UserPlus,
    component: MemberManagementTab,
    adminOnly: true,
  },
  {
    id: 'tokens',
    label: '토큰 사용량',
    icon: Coins,
    component: TokenUsageTab,
    adminOnly: false,
  },
  {
    id: 'billing',
    label: '플랜/결제',
    icon: CreditCard,
    component: PlanBillingTab,
    adminOnly: true,
  },
  {
    id: 'kpi',
    label: 'KPI 목표 설정',
    icon: Target,
    component: KPISettingsTab,
    adminOnly: true,
  },
  {
    id: 'notifications',
    label: '알림 설정',
    icon: Bell,
    component: NotificationSettingsTab,
    adminOnly: true,
  },
];

export const Settings: React.FC = () => {
  const userRole = useSelector((state: RootState) => state.auth.role);
  const [activeTab, setActiveTab] = useState('workspace');

  // Admin 권한 체크 (director, ceo는 Admin으로 간주)
  const isAdmin = userRole === 'director' || userRole === 'ceo';

  // 사용자 권한에 따라 표시할 탭 필터링
  const availableTabs = settingsTabs.filter(
    tab => !tab.adminOnly || isAdmin
  );

  const activeTabData = availableTabs.find(tab => tab.id === activeTab);
  const ActiveComponent = activeTabData?.component;

  return (
    <div className="h-full bg-gray-50">
      <div className="p-6">
        {/* 헤더 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">설정</h1>
          <p className="text-sm text-gray-600 mt-1">
            워크스페이스와 서비스 설정을 관리합니다
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm">
          <div className="flex border-b border-gray-200">
            {/* 탭 네비게이션 */}
            <div className="w-64 border-r border-gray-200 bg-gray-50">
              <nav className="p-4 space-y-1">
                {availableTabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;

                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`
                        w-full flex items-center gap-3 px-4 py-2.5 rounded-lg
                        transition-colors text-left
                        ${isActive
                          ? 'bg-white text-accent shadow-sm border border-gray-200'
                          : 'text-gray-600 hover:bg-white hover:text-gray-900'
                        }
                      `}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />
                      <span className="font-medium">{tab.label}</span>
                      {tab.adminOnly && (
                        <Shield className="w-3.5 h-3.5 text-gray-400 ml-auto" />
                      )}
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* 탭 콘텐츠 */}
            <div className="flex-1 p-6">
              {ActiveComponent && <ActiveComponent />}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;