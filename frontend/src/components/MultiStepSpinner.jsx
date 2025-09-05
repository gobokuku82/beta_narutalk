import React, { useEffect, useState } from 'react';
import './MultiStepSpinner.css';

const MultiStepSpinner = ({ 
  currentStep, 
  totalSteps, 
  agents, 
  activeAgent, 
  message,
  isVisible 
}) => {
  const [animationClass, setAnimationClass] = useState('');

  useEffect(() => {
    if (currentStep > 0) {
      setAnimationClass('step-transition');
      setTimeout(() => setAnimationClass(''), 500);
    }
  }, [currentStep]);

  if (!isVisible) return null;

  // 에이전트 정보 매핑
  const agentInfo = {
    info_retrieval: { 
      name: '정보 검색', 
      icon: '🔍', 
      color: '#4A90E2',
      description: '약물 정보 및 고객 데이터 검색 중...'
    },
    doc_generation: { 
      name: '문서 생성', 
      icon: '📄', 
      color: '#50C878',
      description: '보고서 및 제안서 작성 중...'
    },
    compliance: { 
      name: '규정 확인', 
      icon: '⚖️', 
      color: '#FFB84D',
      description: 'KFDA/FDA 규정 준수 확인 중...'
    },
    analytics: { 
      name: '데이터 분석', 
      icon: '📊', 
      color: '#9B59B6',
      description: '매출 트렌드 및 KPI 분석 중...'
    }
  };

  // 진행률 계산
  const progressPercentage = totalSteps > 0 ? (currentStep / totalSteps) * 100 : 0;

  return (
    <div className="multi-step-spinner">
      {/* 상단 헤더 */}
      <div className="spinner-header">
        <h3>AI 어시스턴트 처리 중</h3>
        <p className="step-counter">
          단계 {currentStep} / {totalSteps}
        </p>
      </div>

      {/* 진행 바 */}
      <div className="progress-container">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        <div className="progress-percentage">{Math.round(progressPercentage)}%</div>
      </div>

      {/* 에이전트 단계 표시 */}
      <div className="agent-steps">
        {agents && agents.map((agent, index) => {
          const info = agentInfo[agent] || { name: agent, icon: '🤖', color: '#666' };
          const stepNumber = index + 1;
          const isActive = activeAgent === agent;
          const isCompleted = stepNumber < currentStep;
          const isPending = stepNumber > currentStep;

          return (
            <div 
              key={agent} 
              className={`agent-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''} ${isPending ? 'pending' : ''}`}
            >
              <div className="step-indicator" style={{ borderColor: isActive ? info.color : '' }}>
                <span className="step-number">{stepNumber}</span>
              </div>
              <div className="step-content">
                <div className="agent-icon">{info.icon}</div>
                <div className="agent-name">{info.name}</div>
                {isActive && (
                  <div className="agent-description">{info.description}</div>
                )}
              </div>
              {index < agents.length - 1 && (
                <div className={`step-connector ${isCompleted ? 'completed' : ''}`} />
              )}
            </div>
          );
        })}
      </div>

      {/* 나루토 스피너 */}
      <div className="naruto-container">
        <div 
          className={`naruto-spinner ${animationClass}`}
          style={{
            transform: `translateX(${progressPercentage}%)`,
          }}
        >
          <img 
            src="/gif/naru.gif" 
            alt="Processing..." 
            className="naruto-gif"
          />
        </div>
        <div className="spinner-track" />
      </div>

      {/* 현재 처리 메시지 */}
      {message && (
        <div className="processing-message">
          <div className="message-content">
            <span className="message-icon">💬</span>
            <span className="message-text">{message}</span>
          </div>
        </div>
      )}

      {/* 로딩 애니메이션 */}
      <div className="loading-dots">
        <div className="dot"></div>
        <div className="dot"></div>
        <div className="dot"></div>
      </div>
    </div>
  );
};

export default MultiStepSpinner;