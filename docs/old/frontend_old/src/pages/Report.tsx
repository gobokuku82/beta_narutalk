import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../app/store';
import { CustomTemplateTab } from '../components/report/CustomTemplateTab';
import { FileText, Upload, Download, Clock, CheckCircle } from 'lucide-react';
import { MOCK_KPI } from '../constants/mock';
import {
  setSelectedFormat,
  startReportGeneration,
  updateGenerationProgress,
  completeReportGeneration,
  setWorkspaceSettings,
  toggleIncludeWorkspaceInfo,
} from '../features/report/reportSlice';
// import { addNotification } from '../features/navigation/navigationSlice';

export const Report: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const [selectedTemplate, setSelectedTemplate] = useState<'report' | 'client' | 'internal' | 'custom'>('report');
  const [selectedOptions, setSelectedOptions] = useState<string[]>([
    'KPI 요약', '채널별 성과', '소재 분석', '비용 최적화'
  ]);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [showGeneratingModal, setShowGeneratingModal] = useState(false);

  // Redux에서 상태 가져오기
  const { selectedClient } = useSelector((state: RootState) => state.client);
  const {
    selectedFormat,
    isGenerating,
    generationProgress,
    generationStatus,
    recentReports,
    workspaceSettings,
    includeWorkspaceInfo
  } = useSelector((state: RootState) => state.report);
  const kpiData = MOCK_KPI;

  // 컴포넌트 마운트 시 워크스페이스 설정 로드 (Supabase 연동 시뮬레이션)
  useEffect(() => {
    // TODO: 실제 Supabase에서 워크스페이스 설정 로드
    const mockWorkspaceSettings = {
      companyName: 'ADALLPIN',
      logo: '/logo.png',
      contactName: '김지수',
      contactEmail: 'jisooo@adallpin.com',
      contactPhone: '02-1234-5678'
    };
    dispatch(setWorkspaceSettings(mockWorkspaceSettings));
  }, [dispatch]);

  // 옵션 변경 시 애니메이션 트리거
  useEffect(() => {
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), 300);
    return () => clearTimeout(timer);
  }, [selectedOptions, selectedTemplate, selectedFormat]);

  const toggleOption = (option: string) => {
    setSelectedOptions(prev =>
      prev.includes(option)
        ? prev.filter(o => o !== option)
        : [...prev, option]
    );
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // 허용된 파일 형식 체크
      const allowedExtensions = ['.xlsx', '.xls', '.pptx', '.ppt', '.docx', '.doc'];
      const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

      if (!allowedExtensions.includes(fileExtension)) {
        alert('허용된 파일 형식이 아닙니다. (.xlsx, .pptx, .docx 만 가능)');
        return;
      }

      setUploadedFile(file);
      setSelectedTemplate('custom');
    }
  };

  const handleGenerateReport = async () => {
    setShowGeneratingModal(true);
    dispatch(startReportGeneration());

    // 보고서 생성 시뮬레이션 (실제로는 백엔드 API 호출)
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 300));

      let status = '보고서를 생성 중입니다';
      if (i === 20) status = '데이터를 수집하고 있습니다';
      if (i === 40) status = '템플릿을 적용하고 있습니다';
      if (i === 60) status = '차트를 생성하고 있습니다';
      if (i === 80) status = '최종 검토를 진행하고 있습니다';
      if (i === 100) status = '보고서 생성이 완료되었습니다';

      dispatch(updateGenerationProgress({ progress: i, status }));
    }

    // 파일명 생성 규칙: 클라이언트명_기간_작성일.확장자
    const clientName = typeof selectedClient === 'string' ? selectedClient : '코스모스뷰티';
    const today = new Date();
    const dateStr = `${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`;
    const fileName = `${clientName}_202403_${dateStr}.${selectedFormat.toLowerCase()}`;

    // 보고서 생성 완료
    const newReport = {
      id: Date.now().toString(),
      title: selectedTemplate === 'custom' ? uploadedFile?.name || '커스텀 보고서' : `${getTemplateTitle()} - 3월`,
      clientName,
      dateRange: '2024.03.01 - 2024.03.31',
      createdAt: new Date().toISOString(),
      fileName,
      format: selectedFormat,
    };

    dispatch(completeReportGeneration(newReport));

    // 알림 추가 - TODO: 알림 기능 구현 필요
    // dispatch(addNotification({
    //   id: Date.now().toString(),
    //   type: 'success',
    //   title: '리포트 생성 완료',
    //   message: `${fileName} 파일이 생성되었습니다.`,
    //   timestamp: new Date().toISOString(),
    //   isRead: false,
    // }));

    // 파일 다운로드 시뮬레이션
    setTimeout(() => {
      const link = document.createElement('a');
      link.href = '#'; // 실제로는 생성된 파일 URL
      link.download = fileName;
      link.click();

      setShowGeneratingModal(false);
    }, 1000);
  };

  const getTemplateTitle = () => {
    const titles = {
      report: '성과 보고서',
      client: '클라이언트 보고서',
      internal: '내부 분석 보고서',
      custom: '커스텀 보고서'
    };
    return titles[selectedTemplate];
  };

  const getClientName = () => {
    if (typeof selectedClient === 'string') {
      return selectedClient;
    }
    return '코스모스 뷰티';
  };

  const handleDownloadReport = (report: typeof recentReports[0]) => {
    // 다운로드 시뮬레이션
    const link = document.createElement('a');
    link.href = '#'; // 실제로는 저장된 파일 URL
    link.download = report.fileName;
    link.click();
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* 페이지 헤더 */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">보고서 생성</h1>
        <p className="text-sm text-gray-600 mt-1">템플릿을 선택하고 보고서를 자동으로 생성합니다</p>
      </div>

      {/* 2분할 레이아웃 */}
      <div className="flex gap-6">
        {/* 좌측: 옵션 설정 영역 (45%) */}
        <div className="w-[45%]">
          <div className="bg-white rounded-lg shadow-sm p-6">
            {/* 템플릿 선택 */}
            <div className="mb-6">
              <h3 className="text-base font-medium text-gray-900 mb-4">템플릿 선택</h3>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setSelectedTemplate('report')}
                  className={`p-4 rounded-lg border text-center transition-all ${
                    selectedTemplate === 'report'
                      ? 'border-accent bg-accent/10'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <FileText className={`w-6 h-6 mx-auto mb-2 ${
                    selectedTemplate === 'report' ? 'text-accent' : 'text-gray-400'
                  }`} />
                  <div className="font-medium text-sm">성과 보고서</div>
                  <div className="text-xs text-gray-500 mt-1">주간/월간용</div>
                </button>

                <button
                  onClick={() => setSelectedTemplate('client')}
                  className={`p-4 rounded-lg border text-center transition-all ${
                    selectedTemplate === 'client'
                      ? 'border-accent bg-accent/10'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <FileText className={`w-6 h-6 mx-auto mb-2 ${
                    selectedTemplate === 'client' ? 'text-accent' : 'text-gray-400'
                  }`} />
                  <div className="font-medium text-sm">클라이언트</div>
                  <div className="text-xs text-gray-500 mt-1">대외 발송용</div>
                </button>

                <button
                  onClick={() => setSelectedTemplate('internal')}
                  className={`p-4 rounded-lg border text-center transition-all ${
                    selectedTemplate === 'internal'
                      ? 'border-accent bg-accent/10'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <FileText className={`w-6 h-6 mx-auto mb-2 ${
                    selectedTemplate === 'internal' ? 'text-accent' : 'text-gray-400'
                  }`} />
                  <div className="font-medium text-sm">내부 분석</div>
                  <div className="text-xs text-gray-500 mt-1">상세 데이터</div>
                </button>

                <label className={`relative p-4 rounded-lg border text-center transition-all cursor-pointer ${
                  selectedTemplate === 'custom'
                    ? 'border-accent bg-accent/10'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}>
                  <input
                    type="file"
                    onChange={handleFileUpload}
                    accept=".xlsx,.xls,.pptx,.ppt,.docx,.doc"
                    className="hidden"
                  />
                  <Upload className={`w-6 h-6 mx-auto mb-2 ${
                    selectedTemplate === 'custom' ? 'text-accent' : 'text-gray-400'
                  }`} />
                  <div className="font-medium text-sm">내 양식</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {uploadedFile ? uploadedFile.name.substring(0, 10) + '...' : '파일 업로드'}
                  </div>
                </label>
              </div>
            </div>

            {/* 내 양식 선택 시 CustomTemplateTab 표시 */}
            {selectedTemplate === 'custom' ? (
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-700">
                    업로드된 템플릿: {uploadedFile?.name}
                  </h3>
                  <button
                    onClick={() => setSelectedTemplate('report')}
                    className="text-sm text-accent hover:text-accent/80"
                  >
                    기본 템플릿으로 변경
                  </button>
                </div>
                <CustomTemplateTab />
              </div>
            ) : (
              <>
                {/* 포함할 데이터 */}
                <div className="mb-6">
                  <h3 className="text-base font-medium text-gray-900 mb-4">
                    포함할 데이터
                    <span className="text-sm font-normal text-gray-500 ml-2">({selectedOptions.length}개 선택)</span>
                  </h3>
                  <div className="grid grid-cols-2 gap-2">
                    {['KPI 요약', '채널별 성과', '소재 분석', '비용 최적화', '트렌드', 'AI 인사이트'].map(option => (
                      <label key={option} className="flex items-center gap-2 p-2.5 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-all">
                        <input
                          type="checkbox"
                          checked={selectedOptions.includes(option)}
                          onChange={() => toggleOption(option)}
                          className="w-4 h-4 text-accent rounded flex-shrink-0"
                        />
                        <span className="text-sm">{option}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* 출력 형식 - 라디오 버튼으로 변경 */}
                <div className="mb-6">
                  <h3 className="text-base font-medium text-gray-900 mb-4">출력 형식</h3>
                  <div className="space-y-2">
                    {(['PDF', 'PPT', 'EXCEL'] as const).map(format => (
                      <label
                        key={format}
                        className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-all"
                      >
                        <input
                          type="radio"
                          name="outputFormat"
                          checked={selectedFormat === format}
                          onChange={() => dispatch(setSelectedFormat(format))}
                          className="w-4 h-4 text-accent"
                        />
                        <span className="text-sm font-medium">{format}</span>
                        <span className="text-xs text-gray-500 ml-auto">
                          {format === 'PDF' && '인쇄 및 공유용'}
                          {format === 'PPT' && '프레젠테이션용'}
                          {format === 'EXCEL' && '데이터 분석용'}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* 로고·담당자명 자동 삽입 옵션 */}
                {workspaceSettings && (
                  <div className="mb-6">
                    <label className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-all">
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={includeWorkspaceInfo}
                          onChange={() => dispatch(toggleIncludeWorkspaceInfo())}
                          className="w-4 h-4 text-accent rounded"
                        />
                        <div>
                          <span className="text-sm font-medium">회사 정보 자동 삽입</span>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {workspaceSettings.companyName} 로고, {workspaceSettings.contactName} 담당자명
                          </p>
                        </div>
                      </div>
                    </label>
                  </div>
                )}
              </>
            )}

            {/* 생성 버튼 */}
            <button
              onClick={handleGenerateReport}
              disabled={isGenerating}
              className="w-full bg-accent text-white py-3 rounded-lg font-medium hover:bg-accent/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="w-4 h-4" />
              {selectedTemplate === 'custom' ? '내 양식으로 보고서 생성' : '보고서 생성'}
            </button>

            {/* 최근 생성 이력 */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-base font-medium text-gray-900 mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-600" />
                최근 생성 이력
              </h3>
              <div className="space-y-2">
                {recentReports.length > 0 ? (
                  recentReports.slice(0, 5).map(report => (
                    <div key={report.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <FileText className="w-3 h-3 text-gray-400" />
                        <div>
                          <p className="text-xs font-medium">{report.title}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(report.createdAt).toLocaleDateString('ko-KR')} {new Date(report.createdAt).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDownloadReport(report)}
                        className="text-xs text-accent hover:text-accent/90"
                      >
                        다운로드
                      </button>
                    </div>
                  ))
                ) : (
                  <>
                    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <FileText className="w-3 h-3 text-gray-400" />
                        <div>
                          <p className="text-xs font-medium">3월 2주차 주간 보고서</p>
                          <p className="text-xs text-gray-500">2024.03.15 14:30</p>
                        </div>
                      </div>
                      <button className="text-xs text-accent hover:text-accent/90">다운로드</button>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <FileText className="w-3 h-3 text-gray-400" />
                        <div>
                          <p className="text-xs font-medium">2월 월간 성과 보고서</p>
                          <p className="text-xs text-gray-500">2024.03.01 10:00</p>
                        </div>
                      </div>
                      <button className="text-xs text-accent hover:text-accent/90">다운로드</button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 우측: 실시간 미리보기 패널 (55%) */}
        <div className="w-[55%]">
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            {/* 미리보기 헤더 */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="font-medium text-gray-900">미리보기</h3>
              <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                selectedFormat === 'PDF' ? 'bg-red-100 text-red-700' :
                selectedFormat === 'PPT' ? 'bg-orange-100 text-orange-700' :
                'bg-green-100 text-green-700'
              }`}>
                {selectedFormat}
              </span>
            </div>

            {/* 미리보기 내용 - 실제 문서처럼 */}
            <div className="h-[calc(100vh-300px)] overflow-y-auto bg-gray-100 p-8">
              {selectedOptions.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-400">
                  <FileText className="w-12 h-12 mb-3" />
                  <p className="text-sm">데이터를 선택해주세요</p>
                </div>
              ) : (
                <div className="mx-auto" style={{ maxWidth: '600px' }}>
                  {/* 문서 페이지 */}
                  <div className={`bg-white transition-all duration-300 ${isAnimating ? 'opacity-50 scale-95' : 'opacity-100 scale-100'}`}
                    style={{
                      boxShadow: '0 4px 24px rgba(0,0,0,0.12)',
                      minHeight: '842px' // A4 비율
                    }}>
                    <div className="p-12">
                      {/* 헤더 */}
                      <div className="mb-8 pb-4 border-b border-gray-300">
                        <div className="flex justify-between items-start">
                          <div>
                            {includeWorkspaceInfo && workspaceSettings && (
                              <div className="mb-3">
                                <div className="text-xs text-gray-500">{workspaceSettings.companyName}</div>
                              </div>
                            )}
                            <h1 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                              {getClientName()}
                            </h1>
                            <h2 className="text-2xl font-bold text-gray-900">{getTemplateTitle()}</h2>
                            <p className="text-sm text-gray-600 mt-2">2024년 3월 1일 - 31일</p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-gray-500">작성일</p>
                            <p className="text-sm font-medium">{new Date().toLocaleDateString('ko-KR')}</p>
                            {includeWorkspaceInfo && workspaceSettings && (
                              <p className="text-xs text-gray-500 mt-2">담당: {workspaceSettings.contactName}</p>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* 목차 */}
                      <div className="mb-8">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">목차</h3>
                        <div className="space-y-2">
                          {selectedOptions.map((option, index) => (
                            <div key={option} className="flex items-center text-sm">
                              <span className="w-8">{index + 1}.</span>
                              <span className="flex-1">{option}</span>
                              <span className="flex-1 border-b border-dotted border-gray-300 mx-2"></span>
                              <span className="text-gray-500">{index + 2}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <hr className="my-8 border-gray-300" />

                      {/* KPI 요약 섹션 */}
                      {selectedOptions.includes('KPI 요약') && (
                        <div className="mb-8">
                          <h3 className="text-lg font-bold text-gray-900 mb-4">1. 핵심 성과 지표</h3>
                          <div className="grid grid-cols-2 gap-4">
                            <div className="border border-gray-300 rounded p-4">
                              <div className="text-xs text-gray-500 mb-1">ROAS</div>
                              <div className="text-2xl font-bold text-gray-900">{kpiData?.roas || 385}%</div>
                              <div className="text-xs text-green-600 mt-1">↑ {kpiData?.roasChange || 12}%</div>
                            </div>
                            <div className="border border-gray-300 rounded p-4">
                              <div className="text-xs text-gray-500 mb-1">전환수</div>
                              <div className="text-2xl font-bold text-gray-900">{kpiData?.conversions || 247}</div>
                              <div className="text-xs text-gray-500 mt-1">CPA ₩{(kpiData?.cpa || 8664).toLocaleString()}</div>
                            </div>
                            <div className="border border-gray-300 rounded p-4">
                              <div className="text-xs text-gray-500 mb-1">광고비</div>
                              <div className="text-2xl font-bold text-gray-900">₩{((kpiData?.spend || 2140000) / 10000).toFixed(0)}만</div>
                              <div className="text-xs text-gray-500 mt-1">예산 {kpiData?.spendBudget || 71}%</div>
                            </div>
                            <div className="border border-gray-300 rounded p-4">
                              <div className="text-xs text-gray-500 mb-1">월목표 달성</div>
                              <div className="text-2xl font-bold text-gray-900">{kpiData?.monthlyAchievement || 63}%</div>
                              <div className="text-xs text-gray-500 mt-1">예측 {kpiData?.monthlyPrediction || 104}%</div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* 채널별 성과 섹션 - 간소화 */}
                      {selectedOptions.includes('채널별 성과') && (
                        <div className="mb-8">
                          <h3 className="text-lg font-bold text-gray-900 mb-4">2. 채널별 성과</h3>
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-300">
                                <th className="text-left py-2">채널</th>
                                <th className="text-right py-2">ROAS</th>
                                <th className="text-right py-2">CTR</th>
                                <th className="text-right py-2">광고비</th>
                                <th className="text-right py-2">상태</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr className="border-b border-gray-200">
                                <td className="py-2">네이버</td>
                                <td className="text-right">421%</td>
                                <td className="text-right">3.2%</td>
                                <td className="text-right">₩78만</td>
                                <td className="text-right text-green-600">우수</td>
                              </tr>
                              <tr className="border-b border-gray-200">
                                <td className="py-2">카카오</td>
                                <td className="text-right">298%</td>
                                <td className="text-right">2.1%</td>
                                <td className="text-right">₩51만</td>
                                <td className="text-right text-amber-600">주의</td>
                              </tr>
                              <tr className="border-b border-gray-200">
                                <td className="py-2">메타</td>
                                <td className="text-right">201%</td>
                                <td className="text-right">1.4%</td>
                                <td className="text-right">₩61만</td>
                                <td className="text-right text-red-600">개선</td>
                              </tr>
                              <tr className="border-b border-gray-200">
                                <td className="py-2">구글</td>
                                <td className="text-right">510%</td>
                                <td className="text-right">5.1%</td>
                                <td className="text-right">₩24만</td>
                                <td className="text-right text-green-600">최우수</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      )}

                      {/* 페이지 번호 */}
                      <div className="absolute bottom-12 left-0 right-0 text-center text-sm text-gray-500">
                        1 / 5
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 보고서 생성 중 모달 */}
      {showGeneratingModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <div className="text-center">
              {generationProgress < 100 ? (
                <>
                  <div className="mb-4">
                    <div className="w-16 h-16 mx-auto border-4 border-accent/20 border-t-accent rounded-full animate-spin"></div>
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{generationStatus}</h3>
                  <div className="mt-4">
                    <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-accent h-full transition-all duration-300"
                        style={{ width: `${generationProgress}%` }}
                      ></div>
                    </div>
                    <p className="text-sm text-gray-500 mt-2">{generationProgress}% 완료</p>
                  </div>
                </>
              ) : (
                <>
                  <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">보고서 생성 완료!</h3>
                  <p className="text-sm text-gray-600">잠시 후 자동으로 다운로드됩니다.</p>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 애니메이션 스타일 */}
      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </div>
  );
};