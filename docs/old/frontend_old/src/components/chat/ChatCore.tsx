import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../app/store';
import {
  sendMessage,
  confirmClarify,
  selectGateChoice,
  toggleControlMode,
  setInputValue,
  addAiResponse,
} from '../../features/agentChat/agentChatSlice';
import { Send, X, ChevronUp, Check, Circle, Loader2, AlertCircle } from 'lucide-react';
import { Badge } from '../common/Badge';
import type { GateChoice, ChatMessage } from '../../types';
import { MessageRenderer } from '../agentChat/MessageRenderer';

interface ChatCoreProps {
  className?: string;
  compact?: boolean; // 사이드 패널용 컴팩트 모드
  showHeader?: boolean; // 헤더 표시 여부
}

export const ChatCore: React.FC<ChatCoreProps> = ({
  className = '',
  compact = false,
  showHeader = true
}) => {
  const dispatch = useDispatch();
  const {
    messages,
    todos,
    controlMode,
    inputValue,
  } = useSelector((state: RootState) => state.agentChat);

  const handleSendMessage = () => {
    if (inputValue.trim()) {
      dispatch(sendMessage(inputValue));
      // 시뮬레이션: AI 응답 생성
      setTimeout(() => {
        simulateAIResponse(inputValue);
      }, 1000);
    }
  };

  const simulateAIResponse = (message: string) => {
    const aiResponse: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      cardType: 'text',
      content: generateAIResponse(message),
      timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
    };
    dispatch(addAiResponse(aiResponse));
  };

  const generateAIResponse = (message: string): string => {
    const msg = message.toLowerCase();

    if (msg.includes('성과') && msg.includes('분석')) {
      return `📊 **성과 분석 완료**

현재 캠페인 성과를 분석했습니다:
- **통합 ROAS**: 385% (목표 대비 +10%)
- **주요 채널**: 네이버 421%, 구글 510%
- **개선 필요**: 메타 채널 CTR 개선 필요

상세 분석을 원하시면 '매체 분석' 탭을 확인하세요.`;
    } else if (msg.includes('소재') && (msg.includes('만들') || msg.includes('생성'))) {
      return `🎨 **소재 생성 준비 완료**

네이버 검색 광고 소재 3종을 생성했습니다.
HITL 승인 대기 중입니다.

승인 후 자동으로 매체에 업로드됩니다.`;
    } else if (msg.includes('예산')) {
      return `💰 **예산 최적화 제안**

AI 분석 기반 예산 재배분안:
- 메타 → 구글로 200K 이동
- 예상 ROAS: 385% → 448% (+63%p)

'비용 최적화' 탭에서 상세 내용을 확인하세요.`;
    } else {
      return `요청하신 "${message}"에 대한 처리를 완료했습니다.

추가로 도움이 필요하시면 말씀해주세요.`;
    }
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header - 조건부 렌더링 */}
      {showHeader && (
        <div className="px-4 py-3 bg-white border-b border-gray-200 flex items-center justify-between">
          <h3 className="font-semibold">ADALLPIN Agent</h3>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full" />
            <span className="text-xs text-green-600 font-medium">Connected</span>
          </div>
        </div>
      )}

      {/* Control Mode */}
      {controlMode && (
        <div className="bg-green-50 border-b border-green-200">
          <div
            className="px-4 py-3 bg-green-100 flex items-center justify-between cursor-pointer"
            onClick={() => dispatch(toggleControlMode())}
          >
            <div>
              <h4 className="font-semibold text-green-800">Control Mode</h4>
              <p className="text-xs text-green-600 mt-1">HITL 승인 대기 중</p>
            </div>
            <ChevronUp className="w-4 h-4 text-green-700" />
          </div>
          <div className="p-4 space-y-2">
            {todos.map((todo, index) => (
              <div key={todo.id} className="flex items-center gap-2">
                <span className="text-xs text-gray-500 w-4">{index + 1}</span>
                {todo.status === 'done' ? (
                  <Check className="w-4 h-4 text-green-600" />
                ) : todo.status === 'running' ? (
                  <Loader2 className="w-4 h-4 text-accent animate-spin" />
                ) : (
                  <Circle className="w-4 h-4 text-gray-400" />
                )}
                <span className={`text-sm flex-1 ${
                  todo.status === 'done' ? 'line-through text-gray-400' : ''
                }`}>
                  {todo.label}
                </span>
                {todo.tags.map(tag => (
                  <Badge key={tag} variant="info" size="sm">{tag}</Badge>
                ))}
                {todo.requiresHitl && (
                  <AlertCircle className="w-4 h-4 text-amber-500" />
                )}
              </div>
            ))}
            <div className="flex gap-2 mt-4">
              <button className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm">
                취소
              </button>
              <button className="flex-1 px-3 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                승인 & 재개
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(message => {
          // ClarifyCard
          if (message.cardType === 'clarify' && message.clarifyPlan) {
            const plan = message.clarifyPlan;
            return (
              <div key={message.id} className="bg-info-bg border border-accent rounded-xl p-3 max-w-[95%]">
                <p className="text-xs font-semibold text-accent uppercase tracking-wide mb-2">
                  🤔 이렇게 이해했어요 — 맞나요?
                </p>
                <p className="text-sm font-semibold mb-2">{plan.summary}</p>
                <div className="bg-white/70 rounded-lg p-2 mb-3 space-y-1">
                  {plan.steps.map((step, i) => (
                    <p key={i} className="text-xs text-gray-600 flex gap-2">
                      <span className="text-accent font-semibold flex-shrink-0">{i + 1}</span>
                      {step}
                    </p>
                  ))}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => dispatch(confirmClarify())}
                    className="px-3 py-1.5 bg-accent text-white text-xs rounded-lg font-semibold hover:bg-accent/90"
                  >
                    맞아, 시작해
                  </button>
                  <button className="px-3 py-1.5 border border-gray-300 text-xs rounded-lg text-gray-600 hover:bg-gray-50">
                    수정할게
                  </button>
                </div>
              </div>
            );
          }

          // GateCard
          if (message.cardType === 'gate' && message.gateChoices) {
            return (
              <div key={message.id} className="bg-amber-50 border border-amber-400 rounded-xl p-3 max-w-[95%]">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                  <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide">
                    잠깐 — 방향 결정이 필요해요
                  </p>
                </div>
                <p className="text-sm font-semibold mb-3 whitespace-pre-line">{message.gateQuestion}</p>
                <div className="grid grid-cols-2 gap-2 mb-3">
                  {message.gateChoices.map((choice: GateChoice) => (
                    <button
                      key={choice.id}
                      onClick={() => dispatch(selectGateChoice({ choiceLabel: choice.label }))}
                      className={`p-2 rounded-lg border text-left hover:border-green-400 hover:bg-green-50 transition-colors ${
                        choice.effectType === 'good'
                          ? 'border-green-300 bg-green-50/50'
                          : 'border-gray-200 bg-white'
                      }`}
                    >
                      <p className="text-xs font-semibold mb-1">{choice.label}</p>
                      <p className="text-xs text-gray-400 mb-1">{choice.subLabel}</p>
                      <p className={`text-xs ${
                        choice.effectType === 'good' ? 'text-green-600' :
                        choice.effectType === 'warn' ? 'text-amber-600' : 'text-gray-500'
                      }`}>
                        {choice.effect}
                      </p>
                    </button>
                  ))}
                </div>
                <p className="text-xs text-gray-400 text-right cursor-pointer hover:text-gray-600">
                  선택 없이 AI 판단으로 진행 →
                </p>
              </div>
            );
          }

          // 일반 텍스트 버블
          return (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] rounded-lg ${
                message.role === 'user' ? 'bg-accent text-white px-4 py-2' : 'bg-white'
              }`}>
                {message.role === 'assistant' ? (
                  <div className="px-4 py-3">
                    <MessageRenderer content={message.content || ''} />
                    <p className="text-xs text-gray-400 mt-3">
                      {message.timestamp}
                    </p>
                  </div>
                ) : (
                  <>
                    <p className="text-sm whitespace-pre-line">{message.content}</p>
                    <p className="text-xs mt-1 opacity-80">
                      {message.timestamp}
                    </p>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t border-gray-200">
        {/* Example Questions - 컴팩트 모드에서는 2개만 표시 */}
        <div className="mb-3 flex gap-2 flex-wrap">
          <button
            onClick={() => {
              dispatch(setInputValue('이번 달 성과를 분석해줘'));
              setTimeout(handleSendMessage, 100);
            }}
            className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-xs hover:bg-gray-200 transition-colors"
          >
            📊 성과 분석
          </button>
          <button
            onClick={() => {
              dispatch(setInputValue('예산 재배분 추천해줘'));
              setTimeout(handleSendMessage, 100);
            }}
            className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-xs hover:bg-gray-200 transition-colors"
          >
            💰 예산 최적화
          </button>
          {!compact && (
            <>
              <button
                onClick={() => {
                  dispatch(setInputValue('네이버 소재 3종 새로 만들어줘'));
                  setTimeout(handleSendMessage, 100);
                }}
                className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-xs hover:bg-gray-200 transition-colors"
              >
                🎨 소재 생성
              </button>
              <button
                onClick={() => {
                  dispatch(setInputValue('타겟 오디언스 분석해줘'));
                  setTimeout(handleSendMessage, 100);
                }}
                className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-xs hover:bg-gray-200 transition-colors"
              >
                🎯 타겟 분석
              </button>
            </>
          )}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => dispatch(setInputValue(e.target.value))}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="무엇을 도와드릴까요?"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          />
          <button
            onClick={() => dispatch(setInputValue(''))}
            className="p-2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
          <button
            onClick={handleSendMessage}
            className="p-2 bg-accent text-white rounded-lg hover:bg-accent/90"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};