import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../app/store';
import { updateWorkspace } from '../../features/settings/settingsSlice';
import { Button, Input } from '../common';
import { Upload, Save, Building2 } from 'lucide-react';

export const WorkspaceTab: React.FC = () => {
  const dispatch = useDispatch();
  const workspace = useSelector((state: RootState) => state.settings.workspace);
  const [formData, setFormData] = useState(workspace);
  const [logoPreview, setLogoPreview] = useState<string>(workspace.logoUrl);
  const [hasChanges, setHasChanges] = useState(false);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        setLogoPreview(result);
        setFormData(prev => ({ ...prev, logoUrl: result }));
        setHasChanges(true);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSave = () => {
    dispatch(updateWorkspace(formData));
    setHasChanges(false);
    // 실제로는 API 호출 후 성공 토스트 표시
    alert('워크스페이스 설정이 저장되었습니다.');
  };

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          <Building2 className="w-5 h-5" />
          워크스페이스 설정
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          회사 정보와 기본 설정을 관리합니다. 여기서 등록한 정보는 리포트 생성 시 자동으로 삽입됩니다.
        </p>
      </div>

      <div className="space-y-6">
        {/* 회사명 */}
        <div>
          <Input
            label="회사명"
            value={formData.companyName}
            onChange={(e) => handleInputChange('companyName', e.target.value)}
            placeholder="예: 마케팅프로"
            fullWidth
          />
        </div>

        {/* 로고 업로드 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            회사 로고
          </label>
          <div className="flex items-center gap-4">
            {logoPreview ? (
              <div className="w-24 h-24 border-2 border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                <img
                  src={logoPreview}
                  alt="Company logo"
                  className="w-full h-full object-contain"
                />
              </div>
            ) : (
              <div className="w-24 h-24 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50">
                <Building2 className="w-8 h-8 text-gray-400" />
              </div>
            )}
            <div>
              <input
                type="file"
                id="logo-upload"
                accept="image/*"
                onChange={handleLogoUpload}
                className="hidden"
              />
              <label htmlFor="logo-upload">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={(e) => {
                    e.preventDefault();
                    document.getElementById('logo-upload')?.click();
                  }}
                >
                  <Upload className="w-4 h-4" />
                  로고 업로드
                </Button>
              </label>
              <p className="text-xs text-gray-500 mt-1">
                PNG, JPG 형식 (최대 2MB)
              </p>
            </div>
          </div>
        </div>

        {/* 담당자 정보 */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-700">담당자 정보</h3>

          <Input
            label="담당자명"
            value={formData.contactName}
            onChange={(e) => handleInputChange('contactName', e.target.value)}
            placeholder="예: 홍길동"
            fullWidth
          />

          <Input
            label="이메일"
            type="email"
            value={formData.contactEmail}
            onChange={(e) => handleInputChange('contactEmail', e.target.value)}
            placeholder="예: hong@company.com"
            fullWidth
          />

          <Input
            label="전화번호"
            type="tel"
            value={formData.contactPhone}
            onChange={(e) => handleInputChange('contactPhone', e.target.value)}
            placeholder="예: 02-1234-5678"
            fullWidth
          />
        </div>

        {/* 리포트 설정 */}
        <div className="bg-info-bg rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            리포트 자동 삽입
          </h3>
          <p className="text-sm text-gray-600">
            위에서 입력한 회사명, 로고, 담당자 정보는 리포트 생성 시 자동으로 삽입됩니다.
            리포트 생성 화면에서 '로고·담당자명 자동 삽입' 옵션을 체크하면 적용됩니다.
          </p>
        </div>

        {/* 저장 버튼 */}
        <div className="flex justify-end pt-4 border-t border-gray-200">
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
    </div>
  );
};