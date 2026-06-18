import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../app/store';
import { updateKPISettings } from '../../features/settings/settingsSlice';
import { Button, Input } from '../common';
import { Target, TrendingUp, AlertTriangle, Save } from 'lucide-react';

export const KPISettingsTab: React.FC = () => {
  const dispatch = useDispatch();
  const kpiSettings = useSelector((state: RootState) => state.settings.kpiSettings);
  const [formData, setFormData] = useState(kpiSettings);
  const [hasChanges, setHasChanges] = useState(false);

  const handleInputChange = (field: string, value: number) => {
    const keys = field.split('.');

    if (keys.length === 2) {
      // statusThresholds 하위 필드 업데이트
      setFormData(prev => ({
        ...prev,
        statusThresholds: {
          ...prev.statusThresholds,
          [keys[1]]: value,
        },
      }));
    } else {
      // 최상위 필드 업데이트
      setFormData(prev => ({ ...prev, [field]: value }));
    }
    setHasChanges(true);
  };

  const handleSave = () => {
    dispatch(updateKPISettings(formData));
    setHasChanges(false);
    alert('KPI 설정이 저장되었습니다.');
  };

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          <Target className="w-5 h-5" />
          KPI 목표 설정
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          광고 성과 목표와 상태 임계값을 설정합니다
        </p>
      </div>

      {/* 주요 KPI 목표 설정 */}
      <div className="bg-white rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">주요 성과 목표</h3>

        <div className="grid grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ROAS 목표 (%)
            </label>
            <div className="relative">
              <Input
                type="number"
                value={formData.roasTarget}
                onChange={(e) => handleInputChange('roasTarget', Number(e.target.value))}
                placeholder="350"
                fullWidth
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">%</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              광고 수익률 목표값
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              CTR 목표 (%)
            </label>
            <div className="relative">
              <Input
                type="number"
                value={formData.ctrTarget}
                onChange={(e) => handleInputChange('ctrTarget', Number(e.target.value))}
                placeholder="5.0"
                step="0.1"
                fullWidth
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">%</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              클릭률 목표값
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              CPA 목표 (원)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">₩</span>
              <Input
                type="number"
                value={formData.cpaTarget}
                onChange={(e) => handleInputChange('cpaTarget', Number(e.target.value))}
                placeholder="10000"
                className="pl-8"
                fullWidth
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              획득당 비용 목표값
            </p>
          </div>
        </div>
      </div>

      {/* 상태 임계값 설정 */}
      <div className="bg-white rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">상태 뱃지 임계값</h3>
        <p className="text-sm text-gray-600 mb-6">
          ROAS 기준으로 대시보드와 소재 분석의 상태 뱃지 색상이 결정됩니다
        </p>

        <div className="space-y-6">
          {/* 성공 임계값 */}
          <div className="flex items-center gap-6">
            <div className="w-32">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-success rounded-full" />
                <span className="text-sm font-medium">정상 (녹색)</span>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-1">
              <span className="text-sm text-gray-600 whitespace-nowrap">ROAS</span>
              <Input
                type="number"
                value={formData.statusThresholds.success}
                onChange={(e) => handleInputChange('statusThresholds.success', Number(e.target.value))}
                className="w-24"
              />
              <span className="text-sm text-gray-600">% 이상</span>
            </div>
          </div>

          {/* 경고 임계값 */}
          <div className="flex items-center gap-6">
            <div className="w-32">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-warning rounded-full" />
                <span className="text-sm font-medium">주의 (노랑)</span>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-1">
              <span className="text-sm text-gray-600 whitespace-nowrap">ROAS</span>
              <Input
                type="number"
                value={formData.statusThresholds.warning}
                onChange={(e) => handleInputChange('statusThresholds.warning', Number(e.target.value))}
                className="w-24"
              />
              <span className="text-sm text-gray-600">% 이상 ~</span>
              <span className="font-medium">{formData.statusThresholds.success}%</span>
              <span className="text-sm text-gray-600">미만</span>
            </div>
          </div>

          {/* 위험 임계값 */}
          <div className="flex items-center gap-6">
            <div className="w-32">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-danger rounded-full" />
                <span className="text-sm font-medium">위험 (빨강)</span>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-1">
              <span className="text-sm text-gray-600 whitespace-nowrap">ROAS</span>
              <Input
                type="number"
                value={formData.statusThresholds.danger}
                onChange={(e) => handleInputChange('statusThresholds.danger', Number(e.target.value))}
                className="w-24"
              />
              <span className="text-sm text-gray-600">% 미만</span>
            </div>
          </div>
        </div>

        {/* 임계값 미리보기 */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">임계값 미리보기</h4>
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="h-2 bg-gradient-to-r from-danger via-warning to-success rounded-full" />
              <div className="flex justify-between mt-2">
                <span className="text-xs text-gray-600">0%</span>
                <span className="text-xs font-medium">{formData.statusThresholds.danger}%</span>
                <span className="text-xs font-medium">{formData.statusThresholds.warning}%</span>
                <span className="text-xs font-medium">{formData.statusThresholds.success}%+</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 소재 상태 임계값 */}
      <div className="bg-white rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">소재 상태 기준</h3>
        <p className="text-sm text-gray-600 mb-4">
          소재 분석 페이지의 상태 분류 기준입니다
        </p>

        <div className="space-y-4">
          <div className="p-3 bg-success/5 border border-success/20 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 bg-success/20 text-success text-xs font-semibold rounded">
                유지
              </span>
              <span className="text-sm text-gray-700">Winner</span>
            </div>
            <p className="text-xs text-gray-600">
              ROAS {formData.statusThresholds.success}% 이상인 고성과 소재
            </p>
          </div>

          <div className="p-3 bg-warning/5 border border-warning/20 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 bg-warning/20 text-warning text-xs font-semibold rounded">
                주시
              </span>
              <span className="text-sm text-gray-700">Monitoring</span>
            </div>
            <p className="text-xs text-gray-600">
              ROAS {formData.statusThresholds.warning}% ~ {formData.statusThresholds.success}% 사이의 중간 성과 소재
            </p>
          </div>

          <div className="p-3 bg-danger/5 border border-danger/20 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 bg-danger/20 text-danger text-xs font-semibold rounded">
                교체권고
              </span>
              <span className="text-sm text-gray-700">Replace</span>
            </div>
            <p className="text-xs text-gray-600">
              ROAS {formData.statusThresholds.danger}% 미만인 저성과 소재
            </p>
          </div>
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