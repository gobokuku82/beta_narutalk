import React from 'react';
import { FileText, Image, BarChart3, FileSpreadsheet, Video, Sparkles } from 'lucide-react';
import type { ResponseOutput } from '../../../types';

interface ResponsePreviewProps {
  data: ResponseOutput | null;
}

export const ResponsePreview: React.FC<ResponsePreviewProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="text-center py-8 text-sm text-gray-400">
        <Sparkles className="w-8 h-8 mx-auto mb-2 text-gray-300 animate-pulse" />
        <div>결과 생성 대기 중...</div>
      </div>
    );
  }

  const getOutputIcon = () => {
    switch (data?.outputType) {
      case 'text':
        return <FileText className="w-5 h-5 text-gray-600" />;
      case 'image':
        return <Image className="w-5 h-5 text-blue-600" />;
      case 'graph':
        return <BarChart3 className="w-5 h-5 text-green-600" />;
      case 'ppt':
        return <FileSpreadsheet className="w-5 h-5 text-orange-600" />;
      case 'mov':
        return <Video className="w-5 h-5 text-purple-600" />;
      default:
        return <FileText className="w-5 h-5 text-gray-600" />;
    }
  };

  const renderPreview = () => {
    if (!data || !data.outputType) {
      return null;
    }

    switch (data.outputType) {
      case 'text':
        return (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <pre className="text-sm whitespace-pre-wrap font-sans">
              {data.preview || data.data}
            </pre>
          </div>
        );

      case 'image':
        return (
          <div className="space-y-3">
            {/* 생성된 소재 목록 */}
            {Array.isArray(data.preview) && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-700 mb-2">생성된 광고 소재</div>
                {data.preview.map((asset: any, index: number) => (
                  <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                      <Image className="w-6 h-6 text-gray-500" />
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium">{asset.name}</div>
                      <div className="text-xs text-gray-500">{asset.type?.toUpperCase()} • {data.format}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* 추가 정보 */}
            {data.data && (
              <div className="space-y-3">
                {data.data.summary && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="text-sm">{data.data.summary}</div>
                  </div>
                )}

                {data.data.metrics && (
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-white border border-gray-200 rounded-lg p-2 text-center">
                      <div className="text-xs text-gray-500">예상 CTR</div>
                      <div className="text-sm font-semibold">{data.data.metrics.predictedCtr}</div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded-lg p-2 text-center">
                      <div className="text-xs text-gray-500">예상 CPA</div>
                      <div className="text-sm font-semibold">{data.data.metrics.predictedCpa}</div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded-lg p-2 text-center">
                      <div className="text-xs text-gray-500">신뢰도</div>
                      <div className="text-sm font-semibold">
                        {(data.data.metrics.confidenceScore * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                )}

                {data.data.nextSteps && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xs font-medium text-gray-700 mb-2">다음 단계</div>
                    <ul className="space-y-1">
                      {data.data.nextSteps.map((step: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2 text-xs text-gray-600">
                          <span className="text-blue-500 mt-0.5">→</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        );

      case 'graph':
        return (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="h-48 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <BarChart3 className="w-12 h-12 mx-auto mb-2" />
                <div className="text-sm">차트 렌더링 영역</div>
              </div>
            </div>
          </div>
        );

      case 'ppt':
        return (
          <div className="space-y-3">
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <FileSpreadsheet className="w-6 h-6 text-orange-600" />
                <div>
                  <div className="font-medium text-sm">프레젠테이션 생성 완료</div>
                  <div className="text-xs text-gray-500">{data.format}</div>
                </div>
              </div>
              {data.preview?.slides && (
                <div className="text-xs text-gray-600 space-y-1">
                  <div>• 슬라이드 수: {data.preview.slides}장</div>
                  <div>• 파일 크기: {data.preview.fileSize || 'N/A'}</div>
                </div>
              )}
            </div>
            <button className="w-full px-4 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700 transition-colors">
              다운로드
            </button>
          </div>
        );

      case 'mov':
        return (
          <div className="space-y-3">
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <Video className="w-6 h-6 text-purple-600" />
                <div>
                  <div className="font-medium text-sm">동영상 생성 완료</div>
                  <div className="text-xs text-gray-500">{data.format || 'MP4'}</div>
                </div>
              </div>
            </div>
            {data.preview?.duration && (
              <div className="text-xs text-gray-600">
                재생시간: {data.preview.duration}
              </div>
            )}
          </div>
        );

      default:
        return (
          <div className="bg-gray-50 rounded-lg p-4 text-center text-sm text-gray-500">
            결과물 미리보기 준비 중...
          </div>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* 출력 타입 헤더 */}
      {data?.outputType && (
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          {getOutputIcon()}
          <div>
            <div className="font-medium text-sm">결과물 타입: {data.outputType.toUpperCase()}</div>
            {data.format && (
              <div className="text-xs text-gray-500">형식: {data.format}</div>
            )}
          </div>
        </div>
      )}

      {/* 미리보기 영역 */}
      {renderPreview()}
    </div>
  );
};