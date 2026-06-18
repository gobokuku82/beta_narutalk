import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../app/store';
import { BudgetSimulationTab } from '../components/cost/BudgetSimulationTab';
import { TrendingDown, DollarSign, Edit3, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { setAgentContext, setInitialMessage } from '../features/agentChat/agentChatSlice';

interface EditModalData {
  keyword: string;
  channel: string;
  spend: number;
}

export const CostOptimization: React.FC = () => {
  const clientData = useSelector((state: RootState) => state.client.currentClientData);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const [editModal, setEditModal] = useState<EditModalData | null>(null);
  const [editModalAction, setEditModalAction] = useState<'stop' | 'budget' | null>(null);
  const [stopConfirmModal, setStopConfirmModal] = useState(false);
  const [budgetValue, setBudgetValue] = useState('');

  const handleEditClick = (keyword: string, channel: string, spend: number) => {
    setEditModal({ keyword, channel, spend });
    setEditModalAction(null);
  };

  const handleStopKeyword = () => {
    setEditModalAction('stop');
    setStopConfirmModal(true);
  };

  const confirmStop = () => {
    // 실제 중지 로직 구현
    console.log(`Stopping keyword: ${editModal?.keyword}`);
    setStopConfirmModal(false);
    setEditModal(null);
    setEditModalAction(null);
  };

  const handleBudgetChange = () => {
    setEditModalAction('budget');
  };

  const confirmBudgetChange = () => {
    // 실제 예산 변경 로직
    console.log(`Changing budget for ${editModal?.keyword} to ${budgetValue}`);
    setEditModal(null);
    setEditModalAction(null);
    setBudgetValue('');
  };

  const handleAIBudgetReallocation = () => {
    // AI 예산 재배분 버튼 클릭 시 에이전트 탭으로 이동 + 컨텍스트 전달
    const context = {
      type: 'budget_reallocation',
      currentAllocation: clientData?.budgetReallocation?.current,
      recommendedAllocation: clientData?.budgetReallocation?.recommended,
      expectedEffect: clientData?.budgetReallocation?.expectedEffect
    };

    // 현재 예산과 추천 예산 정보를 포함한 메시지 생성
    const currentBudgets = clientData?.budgetReallocation?.current || {
      naver: 780000, kakao: 510000, meta: 610000, google: 240000
    };
    const recommendedBudgets = clientData?.budgetReallocation?.recommended || {
      naver: 780000, kakao: 360000, meta: 460000, google: 540000
    };

    const message = `현재 채널별 예산 배분:
- 네이버: ₩${Math.round(currentBudgets.naver / 1000)}K
- 카카오: ₩${Math.round(currentBudgets.kakao / 1000)}K
- 메타: ₩${Math.round(currentBudgets.meta / 1000)}K
- 구글: ₩${Math.round(currentBudgets.google / 1000)}K

AI 추천 예산 재배분:
- 네이버: ₩${Math.round(recommendedBudgets.naver / 1000)}K
- 카카오: ₩${Math.round(recommendedBudgets.kakao / 1000)}K
- 메타: ₩${Math.round(recommendedBudgets.meta / 1000)}K
- 구글: ₩${Math.round(recommendedBudgets.google / 1000)}K

이 재배분안을 적용하여 ROAS를 개선하고 싶습니다. 분석과 실행을 진행해주세요.`;

    dispatch(setAgentContext(context));
    dispatch(setInitialMessage(message));
    navigate('/agent');
  };

  return (
    <div className="p-6 space-y-6">
      {/* 무전환 지출 분석 & AI 예산 재배분 제안 - 2열 */}
      <div className="grid grid-cols-2 gap-6">
        {/* 무전환 지출 분석 */}
        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-danger" />
              무전환 지출 분석
            </h3>
          </div>
          <div className="p-6">
            {/* 무전환 키워드 테이블 */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">키워드</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">매체</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">지출액</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">액션</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {clientData?.noConversionKeywords?.slice(0, 4).map((keyword, index) => (
                    <tr key={index} className="hover:bg-danger-bg">
                      <td className="px-3 py-2 text-sm">{keyword.keyword}</td>
                      <td className="px-3 py-2 text-sm">
                        <span className="inline-flex items-center gap-1">
                          <span className={`w-2 h-2 rounded-full ${
                            keyword.channel === 'naver' ? 'bg-naver' :
                            keyword.channel === 'kakao' ? 'bg-kakao' :
                            keyword.channel === 'meta' ? 'bg-meta' :
                            'bg-google'
                          }`}></span>
                          {keyword.channel === 'naver' ? '네이버' :
                           keyword.channel === 'kakao' ? '카카오' :
                           keyword.channel === 'meta' ? '메타' : '구글'}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-right text-danger font-semibold text-sm">
                        ₩{Math.round(keyword.spend / 1000)}K
                      </td>
                      <td className="px-3 py-2 text-center">
                        <button
                          onClick={() => handleEditClick(keyword.keyword, keyword.channel, keyword.spend)}
                          className="text-blue-600 hover:text-blue-700 text-xs font-medium flex items-center gap-1 mx-auto"
                        >
                          <Edit3 className="w-3 h-3" />
                          수정
                        </button>
                      </td>
                    </tr>
                  )) || (
                    <>
                      <tr className="hover:bg-danger-bg">
                        <td className="px-3 py-2 text-sm">화장품 세일</td>
                        <td className="px-3 py-2 text-sm">
                          <span className="inline-flex items-center gap-1">
                            <span className="w-2 h-2 bg-naver rounded-full"></span>
                            네이버
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right text-danger font-semibold text-sm">₩456K</td>
                        <td className="px-3 py-2 text-center">
                          <button
                            onClick={() => handleEditClick('화장품 세일', 'naver', 456000)}
                            className="text-blue-600 hover:text-blue-700 text-xs font-medium flex items-center gap-1 mx-auto"
                          >
                            <Edit3 className="w-3 h-3" />
                            수정
                          </button>
                        </td>
                      </tr>
                      <tr className="hover:bg-danger-bg">
                        <td className="px-3 py-2 text-sm">스킨케어 할인</td>
                        <td className="px-3 py-2 text-sm">
                          <span className="inline-flex items-center gap-1">
                            <span className="w-2 h-2 bg-google rounded-full"></span>
                            구글
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right text-danger font-semibold text-sm">₩312K</td>
                        <td className="px-3 py-2 text-center">
                          <button
                            onClick={() => handleEditClick('스킨케어 할인', 'google', 312000)}
                            className="text-blue-600 hover:text-blue-700 text-xs font-medium flex items-center gap-1 mx-auto"
                          >
                            <Edit3 className="w-3 h-3" />
                            수정
                          </button>
                        </td>
                      </tr>
                      <tr className="hover:bg-danger-bg">
                        <td className="px-3 py-2 text-sm">무료배송</td>
                        <td className="px-3 py-2 text-sm">
                          <span className="inline-flex items-center gap-1">
                            <span className="w-2 h-2 bg-kakao rounded-full"></span>
                            카카오
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right text-danger font-semibold text-sm">₩234K</td>
                        <td className="px-3 py-2 text-center">
                          <button
                            onClick={() => handleEditClick('무료배송', 'kakao', 234000)}
                            className="text-blue-600 hover:text-blue-700 text-xs font-medium flex items-center gap-1 mx-auto"
                          >
                            <Edit3 className="w-3 h-3" />
                            수정
                          </button>
                        </td>
                      </tr>
                      <tr className="hover:bg-danger-bg">
                        <td className="px-3 py-2 text-sm">뷰티 이벤트</td>
                        <td className="px-3 py-2 text-sm">
                          <span className="inline-flex items-center gap-1">
                            <span className="w-2 h-2 bg-meta rounded-full"></span>
                            메타
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right text-danger font-semibold text-sm">₩189K</td>
                        <td className="px-3 py-2 text-center">
                          <button
                            onClick={() => handleEditClick('뷰티 이벤트', 'meta', 189000)}
                            className="text-blue-600 hover:text-blue-700 text-xs font-medium flex items-center gap-1 mx-auto"
                          >
                            <Edit3 className="w-3 h-3" />
                            수정
                          </button>
                        </td>
                      </tr>
                    </>
                  )}
                </tbody>
              </table>
            </div>

            {/* 요약 카드 */}
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="p-3 bg-danger-bg rounded-lg">
                <p className="text-xs text-gray-600">총 무전환 지출</p>
                <p className="text-lg font-bold text-danger">₩1.19M</p>
                <p className="text-xs text-danger-dark mt-1">월 예산의 15%</p>
              </div>
              <div className="p-3 bg-warning-bg rounded-lg">
                <p className="text-xs text-gray-600">절감 가능액</p>
                <p className="text-lg font-bold text-warning">₩892K</p>
                <p className="text-xs text-warning-dark mt-1">즉시 중지 권고</p>
              </div>
            </div>

            <div className="mt-4 p-3 bg-warning-bg border border-warning/30 rounded-lg">
              <p className="text-xs text-warning-dark">
                <strong>AI 권고:</strong> 4개 키워드 즉시 중지 시 ROAS 12% 개선 예상
              </p>
            </div>
          </div>
        </div>

        {/* AI 예산 재배분 제안 (채널분석에서 이동) */}
        <div className="bg-white rounded-lg shadow border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold">AI 예산 재배분 제안</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-500 mb-3 font-semibold">현재 배분</p>
                <div className="space-y-3">
                  {clientData?.budgetReallocation?.current ? (
                    Object.entries(clientData.budgetReallocation.current).map(([channel, budget], index) => {
                      const channelLabels = {
                        naver: '네이버',
                        kakao: '카카오',
                        meta: '메타',
                        google: '구글'
                      };
                      return (
                        <div key={index} className="flex justify-between items-center">
                          <span className="text-sm">{channelLabels[channel as keyof typeof channelLabels]}</span>
                          <span className="text-sm font-medium">₩{Math.round(budget / 1000)}K</span>
                        </div>
                      );
                    })
                  ) : (
                    <>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">네이버</span>
                        <span className="text-sm font-medium">₩780K</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">카카오</span>
                        <span className="text-sm font-medium">₩510K</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">메타</span>
                        <span className="text-sm font-medium">₩610K</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">구글</span>
                        <span className="text-sm font-medium">₩240K</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-3 font-semibold">AI 추천 배분</p>
                <div className="space-y-3">
                  {clientData?.budgetReallocation?.recommended ? (
                    Object.entries(clientData.budgetReallocation.recommended).map(([channel, budget], index) => {
                      const channelLabels = {
                        naver: '네이버',
                        kakao: '카카오',
                        meta: '메타',
                        google: '구글'
                      };
                      const currentBudget = clientData?.budgetReallocation?.current?.[channel as keyof typeof clientData.budgetReallocation.current] || 0;
                      const diff = budget - currentBudget;
                      return (
                        <div key={index} className="flex justify-between items-center">
                          <span className="text-sm">{channelLabels[channel as keyof typeof channelLabels]}</span>
                          <span className={`text-sm font-medium ${diff > 0 ? 'text-success' : diff < 0 ? 'text-danger' : ''}`}>
                            ₩{Math.round(budget / 1000)}K {diff !== 0 && `(${diff > 0 ? '+' : ''}${Math.round(diff / 1000)}K)`}
                          </span>
                        </div>
                      );
                    })
                  ) : (
                    <>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">네이버</span>
                        <span className="text-sm font-medium">₩780K</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">카카오</span>
                        <span className="text-sm font-medium">₩360K (-150K)</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">메타</span>
                        <span className="text-sm font-medium text-red-600">₩460K (-150K)</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">구글</span>
                        <span className="text-sm font-medium text-green-600">₩540K (+300K)</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-800 font-medium">
                예상 효과: {clientData?.budgetReallocation?.expectedEffect
                  ? `ROAS +${clientData.budgetReallocation.expectedEffect.roasChange}%p, 전환 +${clientData.budgetReallocation.expectedEffect.conversionsChange}건`
                  : 'ROAS 385% → 412% (+27%p), 전환수 +18건, CPA -8%'}
              </p>
            </div>

            <button
              onClick={handleAIBudgetReallocation}
              className="w-full mt-6 bg-accent text-white py-3 rounded-lg font-medium hover:bg-accent/90 transition-colors"
            >
              AI 예산 재배분
            </button>
          </div>
        </div>
      </div>

      {/* 예산 재배치 시뮬레이션 - 전체 너비 */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-success" />
            예산 재배치 시뮬레이션
          </h3>
        </div>
        <div className="p-6">
          <BudgetSimulationTab />
        </div>
      </div>
      {/* 수정 모달 */}
      {editModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">키워드 수정</h3>
                <button
                  onClick={() => {
                    setEditModal(null);
                    setEditModalAction(null);
                  }}
                  className="p-1 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>

            <div className="p-6">
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">키워드: <span className="font-medium text-gray-900">{editModal.keyword}</span></p>
                <p className="text-sm text-gray-600">채널: <span className="font-medium text-gray-900">{editModal.channel === 'naver' ? '네이버' : editModal.channel === 'kakao' ? '카카오' : editModal.channel === 'meta' ? '메타' : '구글'}</span></p>
                <p className="text-sm text-gray-600">현재 지출: <span className="font-medium text-danger">₩{Math.round(editModal.spend / 1000)}K</span></p>
              </div>

              {!editModalAction && (
                <div className="space-y-3">
                  <button
                    onClick={handleStopKeyword}
                    className="w-full p-3 text-left bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">키워드 중지</p>
                        <p className="text-sm text-gray-500 mt-1">해당 키워드의 광고 집행을 즉시 중단합니다</p>
                      </div>
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </button>

                  <button
                    onClick={handleBudgetChange}
                    className="w-full p-3 text-left bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">예산 변경</p>
                        <p className="text-sm text-gray-500 mt-1">해당 키워드의 일일 예산을 조정합니다</p>
                      </div>
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </button>
                </div>
              )}

              {editModalAction === 'budget' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">새 일일 예산</label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">₩</span>
                      <input
                        type="text"
                        value={budgetValue}
                        onChange={(e) => setBudgetValue(e.target.value)}
                        placeholder="예: 50000"
                        className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setEditModalAction(null)}
                      className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
                    >
                      취소
                    </button>
                    <button
                      onClick={confirmBudgetChange}
                      disabled={!budgetValue}
                      className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                    >
                      변경
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 중지 확인 모달 */}
      {stopConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">키워드 중지 확인</h3>
            <p className="text-gray-600 mb-6">
              <span className="font-medium text-gray-900">{editModal?.keyword}</span> 키워드를 정말 중지하시겠습니까?
              <br />
              <span className="text-sm text-danger mt-2 block">이 작업은 즉시 적용되며 되돌릴 수 없습니다.</span>
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setStopConfirmModal(false);
                  setEditModalAction(null);
                }}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
              >
                취소
              </button>
              <button
                onClick={confirmStop}
                className="flex-1 px-4 py-2 bg-danger text-white rounded-lg font-medium hover:bg-danger-dark"
              >
                중지
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};