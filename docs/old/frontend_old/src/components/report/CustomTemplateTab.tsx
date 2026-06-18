import React, { useState, useRef } from 'react';
import { Upload, X, FileText, Download } from 'lucide-react';

export const CustomTemplateTab: React.FC = () => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [outputFormat, setOutputFormat] = useState<'pdf' | 'docx' | 'excel' | 'pptx'>('pdf');
  const [selectedOptions, setSelectedOptions] = useState<string[]>([
    'KPI 요약', '채널별 성과', '소재 분석', '비용 최적화', '트렌드', '벤치마킹', 'Goal Pacing'
  ]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.docx') || file.name.endsWith('.pptx')) {
        setUploadedFile(file);
      } else {
        alert('docx 또는 pptx 파일만 업로드 가능합니다.');
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadedFile(e.target.files[0]);
    }
  };

  const toggleOption = (option: string) => {
    setSelectedOptions(prev =>
      prev.includes(option)
        ? prev.filter(o => o !== option)
        : [...prev, option]
    );
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return Math.round(bytes / 1024) + ' KB';
    return Math.round(bytes / 1048576) + ' MB';
  };

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* 좌측: 업로드 + 출력 형식 */}
      <div className="space-y-6">
        <h3 className="text-lg font-semibold">내 양식으로 생성</h3>

        {/* 파일 업로드 영역 */}
        <div>
          <h4 className="font-medium text-sm mb-3">양식 업로드</h4>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-indigo-600 bg-indigo-50'
                : uploadedFile
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".docx,.pptx"
              onChange={handleFileSelect}
              className="hidden"
            />

            {uploadedFile ? (
              <div className="space-y-3">
                <FileText className="w-12 h-12 mx-auto text-green-600" />
                <div>
                  <p className="font-medium text-sm">{uploadedFile.name}</p>
                  <p className="text-xs text-gray-500">{formatFileSize(uploadedFile.size)}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setUploadedFile(null);
                  }}
                  className="inline-flex items-center gap-1 text-red-600 hover:text-red-700 text-sm"
                >
                  <X className="w-4 h-4" />
                  제거
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <Upload className="w-12 h-12 mx-auto text-gray-400" />
                <div>
                  <p className="font-medium text-sm">docx / pptx 드래그 또는 클릭</p>
                  <p className="text-xs text-gray-500 mt-1">AI가 양식 구조를 자동 분석합니다</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 출력 형식 선택 */}
        <div>
          <h4 className="font-medium text-sm mb-3">출력 형식</h4>
          <div className="grid grid-cols-2 gap-3">
            {[
              { value: 'pdf' as const, label: 'PDF' },
              { value: 'docx' as const, label: 'DOCX' },
              { value: 'excel' as const, label: 'EXCEL' },
              { value: 'pptx' as const, label: 'PPTX' }
            ].map(format => (
              <button
                key={format.value}
                onClick={() => setOutputFormat(format.value)}
                className={`p-3 rounded-lg border-2 transition-all ${
                  outputFormat === format.value
                    ? 'border-indigo-600 bg-indigo-50 text-indigo-600'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <span className="font-medium text-sm">{format.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* AI 분석 정보 */}
        {uploadedFile && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>AI 분석 중:</strong> 양식 구조를 분석하여 자동으로 데이터를 매핑합니다.
              차트, 표, 텍스트 영역이 자동으로 인식됩니다.
            </p>
          </div>
        )}
      </div>

      {/* 우측: 포함할 데이터 선택 */}
      <div className="space-y-6">
        <h4 className="font-medium text-sm">포함할 데이터 선택</h4>

        <div className="space-y-3">
          {['KPI 요약', '채널별 성과', '소재 분석', '비용 최적화', '트렌드', '벤치마킹', 'Goal Pacing'].map(option => (
            <label
              key={option}
              className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedOptions.includes(option)}
                onChange={() => toggleOption(option)}
                className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
              />
              <div className="flex-1">
                <span className="text-sm font-medium">{option}</span>
                {option === 'KPI 요약' && (
                  <p className="text-xs text-gray-500 mt-1">ROAS, 전환수, 광고비, CPA 등</p>
                )}
                {option === '채널별 성과' && (
                  <p className="text-xs text-gray-500 mt-1">네이버, 카카오, 메타, 구글 성과</p>
                )}
                {option === '소재 분석' && (
                  <p className="text-xs text-gray-500 mt-1">소재별 CTR, CVR, 피로도</p>
                )}
                {option === '비용 최적화' && (
                  <p className="text-xs text-gray-500 mt-1">예산 효율성, 무전환 지출</p>
                )}
                {option === '트렌드' && (
                  <p className="text-xs text-gray-500 mt-1">일별/주별 성과 추이</p>
                )}
                {option === '벤치마킹' && (
                  <p className="text-xs text-gray-500 mt-1">업종 평균 대비 성과</p>
                )}
                {option === 'Goal Pacing' && (
                  <p className="text-xs text-gray-500 mt-1">목표 달성률 및 예측</p>
                )}
              </div>
            </label>
          ))}
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span className="text-sm text-gray-600">선택된 항목</span>
          <span className="font-semibold">{selectedOptions.length}개</span>
        </div>
      </div>

      {/* 하단 버튼 (전체 너비) */}
      <div className="col-span-2 flex gap-3">
        <button
          disabled={!uploadedFile}
          className={`flex-1 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
            uploadedFile
              ? 'bg-indigo-600 text-white hover:bg-indigo-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          <Download className="w-4 h-4" />
          양식 분석 후 {outputFormat.toUpperCase()} 생성 ({selectedOptions.length}개 항목)
        </button>
        <button
          disabled={!uploadedFile}
          className={`px-6 py-3 rounded-lg font-medium transition-colors ${
            uploadedFile
              ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
        >
          미리보기
        </button>
      </div>
    </div>
  );
};