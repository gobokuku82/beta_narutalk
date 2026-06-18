import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../app/store';
import { updatePlan } from '../../features/settings/settingsSlice';
import { Button } from '../common';
import { CreditCard, Check, TrendingUp, Zap, Crown } from 'lucide-react';

const plans = [
  {
    id: 'starter',
    name: 'Starter',
    price: 99000,
    yearlyPrice: 990000,
    tokens: 50000,
    features: [
      '월 50,000 토큰',
      '클라이언트 3개까지',
      '기본 리포트 생성',
      '이메일 지원',
    ],
    icon: Zap,
    color: 'gray',
  },
  {
    id: 'professional',
    name: 'Professional',
    price: 299000,
    yearlyPrice: 2990000,
    tokens: 200000,
    features: [
      '월 200,000 토큰',
      '클라이언트 10개까지',
      '고급 리포트 생성',
      'API 우선 지원',
      'Slack 연동',
    ],
    icon: TrendingUp,
    color: 'accent',
    recommended: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    yearlyPrice: 'Custom',
    tokens: 'Unlimited',
    features: [
      '무제한 토큰',
      '무제한 클라이언트',
      '맞춤형 리포트',
      '전담 매니저',
      'SLA 보장',
      'On-premise 가능',
    ],
    icon: Crown,
    color: 'warning',
  },
];

export const PlanBillingTab: React.FC = () => {
  const dispatch = useDispatch();
  const plan = useSelector((state: RootState) => state.settings.plan);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>(plan.billingCycle);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  const handleUpgrade = (planId: string) => {
    setSelectedPlan(planId);
    setShowPaymentModal(true);
  };

  const handlePaymentUpdate = () => {
    // 실제로는 결제 API 호출
    alert('결제 정보가 업데이트되었습니다.');
    setShowPaymentModal(false);
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">플랜 및 결제</h2>
        <p className="text-sm text-gray-600 mt-1">
          서비스 플랜을 관리하고 결제 정보를 업데이트합니다
        </p>
      </div>

      {/* 현재 플랜 정보 */}
      <div className="bg-white rounded-lg p-6 mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">현재 플랜</h3>
            <div className="flex items-center gap-3 mb-4">
              <div className="px-3 py-1 bg-accent/10 text-accent rounded-full font-semibold">
                {plan.currentPlan === 'professional' ? 'Professional' :
                 plan.currentPlan === 'starter' ? 'Starter' : 'Enterprise'}
              </div>
              <span className="text-sm text-gray-600">
                {billingCycle === 'monthly' ? '월간 결제' : '연간 결제'}
              </span>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-gray-600">다음 결제일:</span>
                <span className="font-medium">{plan.nextBillingDate}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-600">결제 수단:</span>
                <span className="font-medium">{plan.paymentMethod}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-600">청구서 이메일:</span>
                <span className="font-medium">{plan.invoiceEmail}</span>
              </div>
            </div>
          </div>

          <Button variant="secondary" size="sm" onClick={() => setShowPaymentModal(true)}>
            <CreditCard className="w-4 h-4" />
            결제 정보 변경
          </Button>
        </div>
      </div>

      {/* 결제 주기 선택 */}
      <div className="flex justify-center mb-6">
        <div className="inline-flex items-center bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              billingCycle === 'monthly'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            월간 결제
          </button>
          <button
            onClick={() => setBillingCycle('yearly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              billingCycle === 'yearly'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            연간 결제
            <span className="ml-1 text-xs text-success">-20%</span>
          </button>
        </div>
      </div>

      {/* 플랜 목록 */}
      <div className="grid grid-cols-3 gap-6">
        {plans.map((planOption) => {
          const Icon = planOption.icon;
          const isCurrentPlan = plan.currentPlan === planOption.id;
          const price = billingCycle === 'monthly' ? planOption.price : planOption.yearlyPrice;

          return (
            <div
              key={planOption.id}
              className={`bg-white rounded-lg border-2 transition-all ${
                planOption.recommended
                  ? 'border-accent shadow-lg scale-105'
                  : isCurrentPlan
                  ? 'border-gray-300'
                  : 'border-gray-200'
              }`}
            >
              {planOption.recommended && (
                <div className="bg-accent text-white text-xs font-semibold text-center py-1.5 rounded-t-md">
                  추천
                </div>
              )}

              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Icon className={`w-8 h-8 text-${planOption.color === 'accent' ? 'accent' : planOption.color === 'warning' ? 'warning' : 'gray-400'}`} />
                  <h3 className="text-xl font-bold text-gray-900">
                    {planOption.name}
                  </h3>
                </div>

                <div className="mb-6">
                  {typeof price === 'number' ? (
                    <div>
                      <span className="text-3xl font-bold text-gray-900">
                        ₩{price.toLocaleString()}
                      </span>
                      <span className="text-gray-600">
                        /{billingCycle === 'monthly' ? '월' : '년'}
                      </span>
                    </div>
                  ) : (
                    <div className="text-2xl font-bold text-gray-900">
                      맞춤 견적
                    </div>
                  )}
                </div>

                <ul className="space-y-3 mb-6">
                  {planOption.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <Check className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>

                {isCurrentPlan ? (
                  <Button variant="secondary" disabled fullWidth>
                    현재 플랜
                  </Button>
                ) : planOption.id === 'enterprise' ? (
                  <Button variant="primary" fullWidth>
                    문의하기
                  </Button>
                ) : (
                  <Button
                    variant={planOption.recommended ? 'primary' : 'secondary'}
                    onClick={() => handleUpgrade(planOption.id)}
                    fullWidth
                  >
                    업그레이드
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 추가 토큰 구매 */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">추가 토큰 구매</h3>
        <p className="text-sm text-gray-600 mb-4">
          플랜의 기본 토큰이 부족한 경우 추가 토큰을 구매할 수 있습니다
        </p>

        <div className="flex gap-4">
          <div className="flex-1 bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">10,000 토큰</div>
            <div className="text-xl font-bold text-gray-900">₩50,000</div>
            <Button variant="secondary" size="sm" className="mt-3" fullWidth>
              구매
            </Button>
          </div>
          <div className="flex-1 bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">50,000 토큰</div>
            <div className="text-xl font-bold text-gray-900">₩200,000</div>
            <Button variant="secondary" size="sm" className="mt-3" fullWidth>
              구매
            </Button>
          </div>
          <div className="flex-1 bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">100,000 토큰</div>
            <div className="text-xl font-bold text-gray-900">₩350,000</div>
            <Button variant="secondary" size="sm" className="mt-3" fullWidth>
              구매
            </Button>
          </div>
        </div>
      </div>

      {/* 결제 정보 변경 모달 */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">결제 정보 변경</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  결제 수단
                </label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                  <option>신용카드</option>
                  <option>계좌이체</option>
                  <option>세금계산서</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  청구서 이메일
                </label>
                <input
                  type="email"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  defaultValue={plan.invoiceEmail}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button
                variant="ghost"
                onClick={() => setShowPaymentModal(false)}
              >
                취소
              </Button>
              <Button
                variant="primary"
                onClick={handlePaymentUpdate}
              >
                저장
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};