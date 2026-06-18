import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../app/store';
import { updateNotifications } from '../../features/settings/settingsSlice';
import { Button, Input } from '../common';
import { Bell, Mail, Hash, Plus, X, Save } from 'lucide-react';

export const NotificationSettingsTab: React.FC = () => {
  const dispatch = useDispatch();
  const notifications = useSelector((state: RootState) => state.settings.notifications);
  const [formData, setFormData] = useState(notifications);
  const [hasChanges, setHasChanges] = useState(false);
  const [newRecipient, setNewRecipient] = useState('');

  const handleToggle = (field: string, value: boolean) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...(prev as any)[parent],
          [child]: value,
        },
      }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
    setHasChanges(true);
  };

  const handleAddRecipient = () => {
    if (!newRecipient.trim() || !newRecipient.includes('@')) return;

    setFormData(prev => ({
      ...prev,
      recipients: [...prev.recipients, newRecipient],
    }));
    setNewRecipient('');
    setHasChanges(true);
  };

  const handleRemoveRecipient = (email: string) => {
    setFormData(prev => ({
      ...prev,
      recipients: prev.recipients.filter(r => r !== email),
    }));
    setHasChanges(true);
  };

  const handleSave = () => {
    dispatch(updateNotifications(formData));
    setHasChanges(false);
    alert('알림 설정이 저장되었습니다.');
  };

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          <Bell className="w-5 h-5" />
          알림 설정
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          중요 이벤트 알림 방법과 수신자를 설정합니다
        </p>
      </div>

      {/* 알림 채널 설정 */}
      <div className="bg-white rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">알림 채널</h3>

        <div className="space-y-4">
          {/* 이메일 알림 */}
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center gap-3">
              <Mail className="w-5 h-5 text-gray-400" />
              <div>
                <div className="font-medium text-gray-900">이메일 알림</div>
                <p className="text-sm text-gray-600">
                  중요 이벤트를 이메일로 받습니다
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.emailEnabled}
                onChange={(e) => handleToggle('emailEnabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
            </label>
          </div>

          {/* Slack 알림 */}
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center gap-3">
              <Hash className="w-5 h-5 text-gray-400" />
              <div>
                <div className="font-medium text-gray-900">Slack 알림</div>
                <p className="text-sm text-gray-600">
                  Slack 채널로 실시간 알림을 받습니다
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.slackEnabled}
                onChange={(e) => handleToggle('slackEnabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
            </label>
          </div>
        </div>
      </div>

      {/* 알림 조건 설정 */}
      <div className="bg-white rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">알림 조건</h3>

        <div className="space-y-3">
          <label className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={formData.conditions.roasBelowTarget}
                onChange={(e) => handleToggle('conditions.roasBelowTarget', e.target.checked)}
                className="w-4 h-4 text-accent rounded"
              />
              <div>
                <div className="text-sm font-medium text-gray-900">ROAS 목표 미달</div>
                <p className="text-xs text-gray-600">
                  ROAS가 목표값 아래로 떨어질 때 알림
                </p>
              </div>
            </div>
          </label>

          <label className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={formData.conditions.budgetExceeded}
                onChange={(e) => handleToggle('conditions.budgetExceeded', e.target.checked)}
                className="w-4 h-4 text-accent rounded"
              />
              <div>
                <div className="text-sm font-medium text-gray-900">예산 초과</div>
                <p className="text-xs text-gray-600">
                  일일 예산의 90% 이상 소진 시 알림
                </p>
              </div>
            </div>
          </label>

          <label className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={formData.conditions.creativePoorPerformance}
                onChange={(e) => handleToggle('conditions.creativePoorPerformance', e.target.checked)}
                className="w-4 h-4 text-accent rounded"
              />
              <div>
                <div className="text-sm font-medium text-gray-900">소재 성과 저하</div>
                <p className="text-xs text-gray-600">
                  소재가 교체권고 상태로 변경될 때 알림
                </p>
              </div>
            </div>
          </label>

          <label className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={formData.conditions.hitlPending}
                onChange={(e) => handleToggle('conditions.hitlPending', e.target.checked)}
                className="w-4 h-4 text-accent rounded"
              />
              <div>
                <div className="text-sm font-medium text-gray-900">사용자 개입 대기</div>
                <p className="text-xs text-gray-600">
                  AI가 사용자 승인을 기다릴 때 알림
                </p>
              </div>
            </div>
          </label>
        </div>

        {/* 알림 임계값 */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            토큰 사용량 알림 임계값
          </label>
          <div className="flex items-center gap-3">
            <Input
              type="number"
              value={formData.alertThreshold}
              onChange={(e) => {
                setFormData(prev => ({ ...prev, alertThreshold: Number(e.target.value) }));
                setHasChanges(true);
              }}
              className="w-24"
            />
            <span className="text-sm text-gray-600">% 이상 사용 시 알림</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            토큰을 설정한 비율 이상 사용하면 알림을 받습니다
          </p>
        </div>
      </div>

      {/* 수신자 설정 */}
      <div className="bg-white rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">알림 수신자</h3>

        <div className="mb-4">
          <div className="flex gap-2">
            <Input
              type="email"
              value={newRecipient}
              onChange={(e) => setNewRecipient(e.target.value)}
              placeholder="email@example.com"
              className="flex-1"
            />
            <Button
              variant="secondary"
              onClick={handleAddRecipient}
              disabled={!newRecipient.trim() || !newRecipient.includes('@')}
            >
              <Plus className="w-4 h-4" />
              추가
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          {formData.recipients.map((email) => (
            <div
              key={email}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <span className="text-sm text-gray-900">{email}</span>
              <button
                onClick={() => handleRemoveRecipient(email)}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>
          ))}
          {formData.recipients.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">
              알림 수신자가 없습니다
            </p>
          )}
        </div>
      </div>

      {/* 알림 테스트 */}
      <div className="bg-info-bg rounded-lg p-4 mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h4 className="text-sm font-semibold text-gray-700">알림 테스트</h4>
            <p className="text-xs text-gray-600 mt-1">
              현재 설정으로 테스트 알림을 발송합니다
            </p>
          </div>
          <Button variant="secondary" size="sm">
            테스트 발송
          </Button>
        </div>
      </div>

      {/* 저장 버튼 */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={!hasChanges}
        >
          <Save className="w-4 h-4" />
          변경사항 저장
        </Button>
      </div>
    </div>
  );
};