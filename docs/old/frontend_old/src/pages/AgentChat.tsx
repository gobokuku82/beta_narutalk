import React, { useState, useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../app/store';
import {
  sendMessage,
  confirmClarify,
  selectGateChoice,
  toggleControlMode,
  setInputValue,
  updateLayerStatus,
  setControlMode,
  approveTodo,
} from '../features/agentChat/agentChatSlice';
import { Send, Square, ChevronUp, Check, Circle, Loader2, AlertCircle, Wifi, WifiOff, ChevronDown, ChevronRight, X, Edit2, CheckCircle, XCircle } from 'lucide-react';
import { Badge } from '../components/common/Badge';
import type { GateChoice, LayerType, ChatMessage } from '../types';
import { LayerPreview } from '../components/agentChat/preview/LayerPreview';
import { CognitivePreview } from '../components/agentChat/preview/CognitivePreview';
import { PlanningPreview } from '../components/agentChat/preview/PlanningPreview';
import { ResponsePreview } from '../components/agentChat/preview/ResponsePreview';
import ErrorBoundary from '../components/common/ErrorBoundary';
import { useAgentWebSocket } from '../hooks/useAgentWebSocket';
import { MessageRenderer } from '../components/agentChat/MessageRenderer';

// HITL 인라인 카드 컴포넌트
const HitlInlineCard: React.FC<{
  itemId: string;
  title: string;
  description: string;
  stage: string;
  recommendation: string;
  onApprove: () => void;
  onModify: () => void;
  onReject: () => void;
}> = ({ itemId, title, description, stage, recommendation, onApprove, onModify, onReject }) => {
  const [showModifyInput, setShowModifyInput] = useState(false);
  const [modifyText, setModifyText] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const handleModify = () => {
    if (modifyText) {
      // WebSocket으로 수정 내용 전송
      onModify();
      setShowModifyInput(false);
      setModifyText('');
    }
  };

  const handleReject = () => {
    if (rejectReason) {
      // WebSocket으로 반려 사유 전송
      onReject();
      setShowRejectInput(false);
      setRejectReason('');
    }
  };

  return (
    <div className="bg-warning-bg border border-warning rounded-xl p-4 my-3">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-warning" />
            <span className="text-sm font-semibold text-warning-dark">HITL 승인 필요</span>
            <Badge variant="warning" size="sm">{stage}</Badge>
          </div>
          <h4 className="font-semibold text-sm mb-1">{title}</h4>
          <p className="text-xs text-gray-600 mb-2">{description}</p>
          <div className="bg-white/70 rounded-lg px-3 py-2">
            <p className="text-xs text-gray-700">
              <strong>AI 추천:</strong> {recommendation}
            </p>
          </div>
        </div>
      </div>

      {/* 수정 입력 */}
      {showModifyInput && (
        <div className="mb-3 p-3 bg-white rounded-lg">
          <textarea
            value={modifyText}
            onChange={(e) => setModifyText(e.target.value)}
            className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-luminous-blue"
            rows={2}
            placeholder="수정 사항을 입력하세요"
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleModify}
              className="px-3 py-1 text-xs bg-luminous-blue text-white rounded hover:bg-amore-blue"
            >
              수정 전송
            </button>
            <button
              onClick={() => setShowModifyInput(false)}
              className="px-3 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
            >
              취소
            </button>
          </div>
        </div>
      )}

      {/* 반려 입력 */}
      {showRejectInput && (
        <div className="mb-3 p-3 bg-danger-bg rounded-lg">
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            className="w-full px-2 py-1 text-xs border border-danger/30 rounded focus:ring-1 focus:ring-danger"
            rows={2}
            placeholder="반려 사유를 입력하세요"
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleReject}
              className="px-3 py-1 text-xs bg-danger text-white rounded hover:bg-danger-dark"
            >
              반려 확정
            </button>
            <button
              onClick={() => setShowRejectInput(false)}
              className="px-3 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
            >
              취소
            </button>
          </div>
        </div>
      )}

      {/* 액션 버튼 */}
      {!showModifyInput && !showRejectInput && (
        <div className="flex gap-2 mt-3">
          <button
            onClick={onApprove}
            className="flex-1 px-3 py-1.5 bg-success text-white text-xs rounded-lg font-medium hover:bg-success-dark flex items-center justify-center gap-1"
          >
            <CheckCircle className="w-3 h-3" />
            승인
          </button>
          <button
            onClick={() => setShowModifyInput(true)}
            className="flex-1 px-3 py-1.5 bg-gray-600 text-white text-xs rounded-lg font-medium hover:bg-gray-700 flex items-center justify-center gap-1"
          >
            <Edit2 className="w-3 h-3" />
            수정
          </button>
          <button
            onClick={() => setShowRejectInput(true)}
            className="flex-1 px-3 py-1.5 bg-danger text-white text-xs rounded-lg font-medium hover:bg-danger-dark flex items-center justify-center gap-1"
          >
            <XCircle className="w-3 h-3" />
            반려
          </button>
        </div>
      )}
    </div>
  );
};

// 실행 에이전트 정보를 반환하는 헬퍼 함수
const getAgentInfo = (agentId: string) => {
  const agents: Record<string, any> = {
    'data_analysis_agent': {
      name: '데이터 분석',
      description: '수집 ~ 분석',
      icon: '📊',
      iconBg: 'bg-blue-100',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-300',
      tools: {
        // 수집 도구
        'naver_collector': { name: '네이버 수집', group: '수집', icon: '🔍' },
        'youtube_collector': { name: '유튜브 수집', group: '수집', icon: '📹' },
        'tiktok_collector': { name: '틱톡 수집', group: '수집', icon: '🎵' },
        'oliveyoung_collector': { name: '올리브영 수집', group: '수집', icon: '🛍️' },
        'naver_ads_collector': { name: '네이버 광고', group: '성과', icon: '📈' },
        'meta_ads_collector': { name: '메타 광고', group: '성과', icon: '📊' },
        'brief_parser': { name: '요서 파싱', group: '수집', icon: '📝' },
        // 전처리 도구
        'text_preprocessor': { name: '텍스트 전처리', group: '전처리', icon: '🔧' },
        'emoji_handler': { name: '이모지 처리', group: '전처리', icon: '😊' },
        'format_normalizer': { name: '포맷 통일', group: '전처리', icon: '📐' },
        'kpi_format_parser': { name: 'KPI 파싱', group: '전처리', icon: '📉' },
        // ML 분석 도구
        'sentiment_analyzer': { name: '감성 분석', group: 'ML', icon: '💭' },
        'keyword_extractor': { name: '키워드 추출', group: 'ML', icon: '🔑' },
        'clustering_analyzer': { name: '클러스터링', group: 'ML', icon: '🎯' },
        'trend_detector': { name: '트렌드 탐지', group: 'ML', icon: '📈' },
        'kpi_trend_analyzer': { name: 'KPI 트렌드', group: 'ML', icon: '📊' },
        'keyword_optimizer': { name: '키워드 최적화', group: 'ML', icon: '🎯' },
        // LLM 분석 도구
        'llm_sentiment_analyzer': { name: 'LLM 감성분석', group: 'LLM', icon: '🤖' },
        'insight_extractor': { name: '인사이트 추출', group: 'LLM', icon: '💡' },
        'competitor_analyzer': { name: '경쟁사 분석', group: 'LLM', icon: '🥊' },
        'trend_interpreter': { name: '트렌드 해석', group: 'LLM', icon: '📖' },
        'summary_generator': { name: '요약 생성', group: 'LLM', icon: '📝' },
        'ml_analysis_reporter': { name: 'ML 해석', group: 'LLM', icon: '📊' },
        'kpi_insight_generator': { name: 'KPI 인사이트', group: 'LLM', icon: '💬' }
      }
    },
    'report_agent': {
      name: '보고서 생성',
      description: '인사이트 → PDF',
      icon: '📄',
      iconBg: 'bg-green-100',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-300',
      tools: {
        'insight_synthesizer': { name: '인사이트 종합', group: '분석', icon: '🔗' },
        'report_writer': { name: '보고서 작성', group: '생성', icon: '✍️' },
        'chart_generator': { name: '차트 생성', group: '시각화', icon: '📊' },
        'template_selector': { name: '템플릿 선택', group: '포맷', icon: '🎨' },
        'pdf_converter': { name: 'PDF 변환', group: '출력', icon: '📑' }
      }
    },
    'image_creation_agent': {
      name: '이미지 생성',
      description: '광고 이미지 + 슬로건',
      icon: '🎨',
      iconBg: 'bg-purple-100',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-300',
      tools: {
        'ad_prompt_generator': { name: '프롬프트 생성', group: '이미지', icon: '💭' },
        'ad_image_generator': { name: '이미지 생성', group: '이미지', icon: '🖼️' },
        'quality_checker': { name: '품질 검증', group: '이미지', icon: '✅' },
        'brand_guideline_analyzer': { name: '브랜드 가이드', group: '이미지', icon: '📏' },
        'slogan_generator': { name: '슬로건 생성', group: '슬로건', icon: '💬' },
        'slogan_rag_search': { name: '슬로건 검색', group: '슬로건', icon: '🔍' },
        'slogan_evaluator': { name: '슬로건 평가', group: '슬로건', icon: '⭐' },
        'slogan_overlay': { name: '슬로건 합성', group: '합성', icon: '🔤' },
        'image_resizer': { name: '이미지 리사이징', group: '공유', icon: '📐' },
        'thumbnail_creator': { name: '썸네일 생성', group: '공유', icon: '🖼️' }
      }
    },
    'video_creation_agent': {
      name: '영상 제작',
      description: '스토리보드 → 영상',
      icon: '🎬',
      iconBg: 'bg-orange-100',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-300',
      tools: {
        'storyboard_planner': { name: '스토리보드', group: '기획', icon: '📋' },
        'frame_image_generator': { name: '프레임 생성', group: '생성', icon: '🎞️' },
        'video_compositor': { name: '영상 합성', group: '편집', icon: '🎥' },
        'voice_generator': { name: '음성 생성', group: '오디오', icon: '🎙️' },
        'video_merger': { name: '영상 병합', group: '편집', icon: '🎬' },
        'subtitle_generator': { name: '자막 생성', group: '편집', icon: '💬' },
        'brand_guideline_analyzer': { name: '브랜드 가이드', group: '공유', icon: '📏' }
      }
    }
  };

  return agents[agentId] || {
    name: agentId,
    description: '실행 중',
    icon: '⚡',
    iconBg: 'bg-gray-100',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-300',
    tools: {}
  };
};

// Tool 그룹별 색상 매핑
const getToolGroupColor = (group: string) => {
  const colors: Record<string, string> = {
    '수집': 'bg-blue-100 text-blue-700',
    '성과': 'bg-indigo-100 text-indigo-700',
    '전처리': 'bg-gray-100 text-gray-700',
    'ML': 'bg-green-100 text-green-700',
    'LLM': 'bg-purple-100 text-purple-700',
    '분석': 'bg-cyan-100 text-cyan-700',
    '생성': 'bg-pink-100 text-pink-700',
    '시각화': 'bg-yellow-100 text-yellow-700',
    '이미지': 'bg-rose-100 text-rose-700',
    '슬로건': 'bg-amber-100 text-amber-700',
    '기획': 'bg-teal-100 text-teal-700',
    '편집': 'bg-orange-100 text-orange-700',
    '오디오': 'bg-lime-100 text-lime-700',
    '공유': 'bg-slate-100 text-slate-700'
  };
  return colors[group] || 'bg-gray-100 text-gray-700';
};

export const AgentChat: React.FC = () => {
  const dispatch = useDispatch();
  const { sendMessage: sendWsMessage } = useAgentWebSocket();
  const {
    messages,
    todos,
    controlMode,
    inputValue,
    layers,
    wsConnected,
    currentLayer,
    isRunning,
  } = useSelector((state: RootState) => state.agentChat);

  // 현재 선택된 클라이언트 가져오기
  const currentClient = useSelector((state: RootState) => state.client.selectedClient);

  // Redux 상태 변경 로깅 추가
  useEffect(() => {
    console.log('[AgentChat] Redux todos updated:', todos);
    console.log('[AgentChat] Redux todos length:', todos.length);
    console.log('[AgentChat] Redux todos detail:', JSON.stringify(todos, null, 2));
  }, [todos]);

  useEffect(() => {
    console.log('[AgentChat] Redux layers updated:', layers);
    console.log('[AgentChat] Cognitive output:', layers.cognitive?.output);
    console.log('[AgentChat] Planning output:', layers.planning?.output);
    console.log('[AgentChat] Execution output:', layers.execution?.output);
    console.log('[AgentChat] Response output:', layers.response?.output);
  }, [layers]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);

  // 아코디언 상태
  const [expandedLayers, setExpandedLayers] = React.useState<Record<LayerType, boolean>>({
    cognitive: false,
    planning: false,
    execution: true,
    response: false,
  });

  // 패널 리사이징 상태
  const [chatPanelWidth, setChatPanelWidth] = React.useState(30);
  const [taskPanelWidth, setTaskPanelWidth] = React.useState(40);
  const [isResizingChat, setIsResizingChat] = React.useState(false);
  const [isResizingTask, setIsResizingTask] = React.useState(false);

  // 채팅 스크롤 처리
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    setIsUserScrolling(false);
    setShowScrollButton(false);
  };

  // 스크롤 이벤트 처리
  const handleScroll = () => {
    if (!messagesContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;

    setIsUserScrolling(!isAtBottom);
    setShowScrollButton(!isAtBottom);
  };

  // 새 메시지 수신 시 자동 스크롤
  useEffect(() => {
    if (!isUserScrolling) {
      scrollToBottom();
    }
  }, [messages]);

  // 메시지 전송 처리 (실행 중 일시정지 포함)
  const handleSendMessage = () => {
    if (isRunning) {
      // 실행 중이면 일시정지
      dispatch({ type: 'agentChat/pauseExecution' });

      // WebSocket으로 일시정지 명령 전송 (JSON 형태로)
      const pauseCommand = { type: 'pause' };
      sendWsMessage(JSON.stringify(pauseCommand));

      // 입력창에 텍스트가 있으면 그대로 유지 (사용자가 새 메시지를 입력 중일 수 있음)
      // HITL처럼 일시정지 후 바로 새 지시를 보낼 수 있도록

    } else if (inputValue.trim()) {
      // 클라이언트 컨텍스트 자동 추가
      let messageWithContext = inputValue;
      if (currentClient && currentClient !== '전체 포트폴리오') {
        // 메시지에 클라이언트명이 없으면 자동 추가
        if (!inputValue.includes(currentClient)) {
          messageWithContext = `[${currentClient}] ${inputValue}`;
        }
      }

      // 메시지 전송
      dispatch(sendMessage(messageWithContext));

      // 백엔드로 메시지 전송 (텍스트 형태로)
      sendWsMessage(messageWithContext);  // 백엔드 에이전트 실행
    }
  };

  // HITL 처리 함수들
  const handleHitlApprove = (itemId: string) => {
    // WebSocket으로 승인 전송
    sendWsMessage(JSON.stringify({
      type: 'hitl_approve',
      itemId,
    }));
    // 에이전트 재개
    dispatch({ type: 'agentChat/resumeExecution' });
  };

  const handleHitlModify = (itemId: string) => {
    // 에이전트 탭에 맥락 전달하며 재실행
    sendWsMessage(JSON.stringify({
      type: 'hitl_modify',
      itemId,
    }));
  };

  const handleHitlReject = (itemId: string) => {
    // WebSocket으로 반려 전송
    sendWsMessage(JSON.stringify({
      type: 'hitl_reject',
      itemId,
    }));
  };

  const simulateAgentExecution = (message: string) => {
    // 기존 시뮬레이션 코드 유지...
    setTimeout(() => {
      dispatch(updateLayerStatus({ layer: 'cognitive', status: 'running' }));
    }, 500);

    // ... (기존 시뮬레이션 코드)
  };

  const generateAIResponse = (message: string): string => {
    const msg = message.toLowerCase();
    // 기존 응답 생성 로직 유지...
    if (msg.includes('성과') && msg.includes('분석')) {
      return `📊 **핵심 요약**...`;
    }
    return `요청하신 작업을 처리하고 있습니다...`;
  };

  const getTaskStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'done':
        return <Check className="w-4 h-4 text-success" />;
      case 'in_progress':
      case 'running':
        return <Loader2 className="w-4 h-4 text-accent animate-spin" />;
      default:
        return <Circle className="w-4 h-4 text-gray-400" />;
    }
  };

  // 리사이징 핸들러들 (기존 코드 유지)
  const handleChatResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingChat(true);
  };

  const handleTaskResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingTask(true);
  };

  React.useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingChat) return;
      const newWidth = (e.clientX / window.innerWidth) * 100;
      if (newWidth >= 20 && newWidth <= 50) {
        setChatPanelWidth(newWidth);
        const remainingWidth = 100 - newWidth;
        const minOtherPanelsWidth = 40;
        if (remainingWidth < minOtherPanelsWidth) {
          setChatPanelWidth(60);
        } else {
          const maxTaskWidth = remainingWidth - 20;
          if (taskPanelWidth > maxTaskWidth) {
            setTaskPanelWidth(maxTaskWidth);
          }
        }
      }
    };

    const handleMouseUp = () => {
      setIsResizingChat(false);
    };

    if (isResizingChat) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      if (!isResizingTask) {
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
      }
    };
  }, [isResizingChat, taskPanelWidth]);

  React.useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingTask) return;
      const totalUsedWidth = (e.clientX / window.innerWidth) * 100;
      const newTaskWidth = totalUsedWidth - chatPanelWidth;
      const previewWidth = 100 - chatPanelWidth - newTaskWidth;
      if (newTaskWidth >= 20 && previewWidth >= 20) {
        setTaskPanelWidth(newTaskWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizingTask(false);
    };

    if (isResizingTask) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      if (!isResizingChat) {
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
      }
    };
  }, [isResizingTask, chatPanelWidth]);

  return (
    <ErrorBoundary>
      <div className="h-full flex">
        {/* Chat Panel */}
        <div
          className="bg-gray-50 border-r border-gray-200 flex flex-col h-full"
          style={{ width: `${chatPanelWidth}%` }}
        >
          <div className="px-6 py-4 bg-white border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-semibold">ADALLPIN Agent</h3>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-success rounded-full" />
              <span className="text-xs text-success font-medium">Connected</span>
            </div>
          </div>

          {/* Control Mode */}
          {controlMode && (
            <div className="bg-success-bg border-b border-success">
              <div
                className="px-4 py-3 bg-success-bg flex items-center justify-between cursor-pointer"
                onClick={() => dispatch(toggleControlMode())}
              >
                <div>
                  <h4 className="font-semibold text-success-dark">Control Mode</h4>
                  <p className="text-xs text-success mt-1">HITL 승인 대기 중</p>
                </div>
                <ChevronUp className="w-4 h-4 text-success-dark" />
              </div>
              <div className="p-4 space-y-2">
                {todos.map((todo, index) => (
                  <div key={todo.id} className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 w-4">{index + 1}</span>
                    {getTaskStatusIcon(todo.status)}
                    <span className={`text-sm flex-1 ${
                      todo.status === 'done' ? 'line-through text-gray-400' : ''
                    }`}>
                      {todo.label}
                    </span>
                    {todo.tags.map(tag => (
                      <Badge key={tag} variant="info" size="sm">{tag}</Badge>
                    ))}
                    {todo.requiresHitl && (
                      <AlertCircle className="w-4 h-4 text-warning" />
                    )}
                  </div>
                ))}
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => dispatch(setControlMode(false))}
                    className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm"
                  >
                    취소
                  </button>
                  <button
                    onClick={() => {
                      dispatch(setControlMode(false)); // 컨트롤 창 닫기
                      dispatch(approveTodo()); // HITL 승인 처리
                      // 에이전트 재개 로직 추가 필요
                    }}
                    className="flex-1 px-3 py-2 bg-success text-white rounded text-sm hover:bg-success-dark"
                  >
                    승인 & 재개
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Messages */}
          <div
            ref={messagesContainerRef}
            onScroll={handleScroll}
            className="flex-1 overflow-y-auto p-4 space-y-3 relative"
          >
            {messages.map(message => {
              // HITL 인라인 카드
              if (message.cardType === 'hitl' && message.hitlData) {
                return (
                  <HitlInlineCard
                    key={message.id}
                    itemId={message.hitlData.id}
                    title={message.hitlData.title}
                    description={message.hitlData.description}
                    stage={message.hitlData.stage}
                    recommendation={message.hitlData.recommendation}
                    onApprove={() => handleHitlApprove(message.hitlData!.id)}
                    onModify={() => handleHitlModify(message.hitlData!.id)}
                    onReject={() => handleHitlReject(message.hitlData!.id)}
                  />
                );
              }

              // ClarifyCard
              if (message.cardType === 'clarify' && message.clarifyPlan) {
                const plan = message.clarifyPlan;
                return (
                  <div key={message.id} className="bg-info-bg border border-info rounded-xl p-3 max-w-[95%]">
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
                        className="px-3 py-1.5 bg-accent text-white text-xs rounded-lg font-semibold hover:bg-accent"
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
                  <div key={message.id} className="bg-warning-bg border border-warning rounded-xl p-3 max-w-[95%]">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-2 h-2 rounded-full bg-warning animate-pulse" />
                      <p className="text-xs font-semibold text-warning-dark uppercase tracking-wide">
                        잠깐 — 방향 결정이 필요해요
                      </p>
                    </div>
                    <p className="text-sm font-semibold mb-3 whitespace-pre-line">{message.gateQuestion}</p>
                    <div className="grid grid-cols-2 gap-2 mb-3">
                      {message.gateChoices.map((choice: GateChoice) => (
                        <button
                          key={choice.id}
                          onClick={() => dispatch(selectGateChoice({ choiceLabel: choice.label }))}
                          className={`p-2 rounded-lg border text-left hover:border-success hover:bg-success-bg transition-colors ${
                            choice.effectType === 'good'
                              ? 'border-success bg-success-bg/50'
                              : 'border-gray-200 bg-white'
                          }`}
                        >
                          <p className="text-xs font-semibold mb-1">{choice.label}</p>
                          <p className="text-xs text-gray-400 mb-1">{choice.subLabel}</p>
                          <p className={`text-xs ${
                            choice.effectType === 'good' ? 'text-success' :
                            choice.effectType === 'warn' ? 'text-warning' : 'text-gray-500'
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

              // 일반 텍스트 메시지
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
            <div ref={messagesEndRef} />

            {/* 스크롤 다운 버튼 */}
            {showScrollButton && (
              <button
                onClick={scrollToBottom}
                className="fixed bottom-24 right-8 p-2 bg-white shadow-lg rounded-full hover:shadow-xl transition-all"
              >
                <ChevronDown className="w-5 h-5 text-gray-600" />
              </button>
            )}
          </div>

          {/* Input */}
          <div className="p-4 bg-white border-t border-gray-200">
            {/* 예시 질문 버튼들 - 실제 서비스에서는 제거 예정 (CLAUDE.md 참고) */}
            <div className="flex flex-wrap gap-2 mb-3">
              <button
                onClick={() => {
                  let question = '이번 달 캠페인 성과 분석해줘';
                  if (currentClient && currentClient !== '전체 포트폴리오') {
                    question = `[${currentClient}] ${question}`;
                  }
                  dispatch(setInputValue(question));
                  dispatch(sendMessage(question));
                  sendWsMessage(question);  // 텍스트로 전송
                }}
                className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-xs text-gray-700 rounded-lg transition-colors"
                disabled={isRunning}
              >
                💡 캠페인 성과 분석
              </button>
              <button
                onClick={() => {
                  let question = '네이버 광고 CTR 개선 방안 제안해줘';
                  if (currentClient && currentClient !== '전체 포트폴리오') {
                    question = `[${currentClient}] ${question}`;
                  }
                  dispatch(setInputValue(question));
                  dispatch(sendMessage(question));
                  sendWsMessage(question);  // 텍스트로 전송
                }}
                className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-xs text-gray-700 rounded-lg transition-colors"
                disabled={isRunning}
              >
                📈 CTR 개선 방안
              </button>
              <button
                onClick={() => {
                  let question = '신규 광고 소재 3종 만들어줘';
                  if (currentClient && currentClient !== '전체 포트폴리오') {
                    question = `[${currentClient}] ${question}`;
                  }
                  dispatch(setInputValue(question));
                  dispatch(sendMessage(question));
                  sendWsMessage(question);  // 텍스트로 전송
                }}
                className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-xs text-gray-700 rounded-lg transition-colors"
                disabled={isRunning}
              >
                🎨 소재 생성
              </button>
              <button
                onClick={() => {
                  let question = '월 예산을 채널별로 재배분해줘';
                  if (currentClient && currentClient !== '전체 포트폴리오') {
                    question = `[${currentClient}] ${question}`;
                  }
                  dispatch(setInputValue(question));
                  dispatch(sendMessage(question));
                  sendWsMessage(question);  // 텍스트로 전송
                }}
                className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-xs text-gray-700 rounded-lg transition-colors"
                disabled={isRunning}
              >
                💰 예산 재배분
              </button>
            </div>

            <div className="flex gap-2 items-end">
              <textarea
                value={inputValue}
                onChange={(e) => dispatch(setInputValue(e.target.value))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (!isRunning && inputValue.trim()) {
                      handleSendMessage();
                    } else if (isRunning) {
                      handleSendMessage(); // 정지 처리
                    }
                  }
                }}
                placeholder={isRunning ? "메시지를 입력하거나 ⬛를 눌러 일시정지" : "무엇을 도와드릴까요?"}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent resize-none min-h-[40px] max-h-[120px]"
                disabled={false} // 항상 활성화
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
                rows={1}
                style={{
                  height: 'auto',
                  overflowY: inputValue.split('\n').length > 3 ? 'auto' : 'hidden'
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = Math.min(target.scrollHeight, 120) + 'px';
                }}
              />
              <button
                onClick={() => dispatch(setInputValue(''))}
                className="p-2 text-gray-400 hover:text-gray-600 mb-1"
              >
                <X className="w-5 h-5" />
              </button>
              <button
                onClick={handleSendMessage}
                className={`p-2 rounded-lg transition-colors mb-1 ${
                  isRunning
                    ? 'bg-danger text-white hover:bg-danger-dark'
                    : 'bg-accent text-white hover:bg-accent'
                }`}
                title={isRunning ? '일시정지 (⏸)' : '전송 (Enter)'}
              >
                {isRunning ? <Square className="w-5 h-5" /> : <Send className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* First Resizer */}
        <div
          className={`w-1 bg-gray-300 hover:bg-accent transition-colors relative cursor-col-resize ${
            isResizingChat ? 'bg-accent' : ''
          }`}
          onMouseDown={handleChatResizeStart}
        >
          <div className="absolute inset-y-0 left-[-2px] right-[-2px] z-10" />
        </div>

        {/* Task Panel */}
        <div
          className="bg-white flex flex-col h-full"
          style={{ width: `${taskPanelWidth}%` }}
        >
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-3 flex-1">
                <h3 className="font-semibold">작업 내용</h3>
                <span className={`text-sm font-medium ${
                  todos.every((t: any) => t.status === 'completed') ? 'text-success-dark' : 'text-gray-600'
                }`}>
                  ({todos.filter((t: any) => t.status === 'completed').length}/{todos.length})
                </span>

                {/* Progress Bar - 작업 내용 옆에 배치 */}
                {todos.length > 0 && (
                  <div className="flex items-center gap-2 flex-1 max-w-md ml-4">
                    <div className="flex-1">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-success h-2 rounded-full transition-all duration-300"
                          style={{
                            width: `${(todos.filter((t: any) => t.status === 'completed').length / todos.length) * 100}%`
                          }}
                        />
                      </div>
                    </div>
                    <span className="text-sm font-medium text-success-dark min-w-[45px] text-right">
                      {Math.round((todos.filter((t: any) => t.status === 'completed').length / todos.length) * 100)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            <div className="space-y-2">
              {todos.length === 0 && isRunning ? (
                <div className="flex items-center justify-center h-32">
                  <div className="text-center">
                    <div className="flex items-center gap-2 text-gray-500">
                      <div className="animate-spin h-4 w-4 border-2 border-info border-t-transparent rounded-full"></div>
                      <span className="text-sm">Todo 생성 중...</span>
                    </div>
                  </div>
                </div>
              ) : (
                todos.map((todo: any, index: number) => (
                  <div
                    key={todo.id}
                    className={`flex items-start gap-3 p-3 rounded-lg transition-all ${
                      (todo.status === 'running' || todo.status === 'in_progress') ? 'bg-info-bg border border-info' :
                      (todo.status === 'done' || todo.status === 'completed') ? 'opacity-60' : ''
                    }`}
                  >
                    <div className="pt-1">
                      {getTaskStatusIcon(todo.status)}
                    </div>
                    <div className="flex-1">
                      <p className={`text-sm ${(todo.status === 'done' || todo.status === 'completed') ? 'text-gray-500' : ''}`}>
                        {index + 1}. {todo.label}
                      </p>
                      {todo.result && (
                        <p className="text-xs text-gray-400 mt-1">→ {todo.result}</p>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Second Resizer */}
        <div
          className={`w-1 bg-gray-300 hover:bg-accent transition-colors relative cursor-col-resize ${
            isResizingTask ? 'bg-accent' : ''
          }`}
          onMouseDown={handleTaskResizeStart}
        >
          <div className="absolute inset-y-0 left-[-2px] right-[-2px] z-10" />
        </div>

        {/* 아코디언 미리보기 패널 */}
        <div
          className="bg-gray-50 flex flex-col h-full"
          style={{ width: `${100 - chatPanelWidth - taskPanelWidth}%` }}
        >
          <div className="px-6 py-4 bg-white border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">단계별 결과 미리보기</h3>
              <div className="flex items-center gap-2">
                {wsConnected ? (
                  <div className="flex items-center gap-1 text-xs text-success">
                    <Wifi className="w-3 h-3" />
                    <span>연결됨</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-xs text-gray-400">
                    <WifiOff className="w-3 h-3" />
                    <span>연결 대기</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {/* 의도분석 단계 */}
            <ErrorBoundary>
              {layers.cognitive && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                  <button
                    onClick={() => setExpandedLayers(prev => ({ ...prev, cognitive: !prev.cognitive }))}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        layers.cognitive.status === 'completed' ? 'bg-success' :
                        layers.cognitive.status === 'running' ? 'bg-luminous-blue animate-pulse' :
                        'bg-gray-300'
                      }`} />
                      <span className="font-medium">의도분석</span>
                      {layers.cognitive.status === 'running' && (
                        <Loader2 className="w-4 h-4 animate-spin text-luminous-blue" />
                      )}
                    </div>
                    {expandedLayers.cognitive ? <ChevronUp className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                  {expandedLayers.cognitive && layers.cognitive.output && (
                    <div className="px-4 py-3 border-t border-gray-200">
                      <div className="space-y-3">
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">AI 의도 분석</h4>
                          <p className="text-sm text-gray-600">
                            {(layers.cognitive.output as any).intent?.summary ||
                             (layers.cognitive.output as any).context_summary ||
                             '의도 분석 중...'}
                          </p>
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <span className="text-xs text-gray-500">작업 유형</span>
                            <p className="text-sm font-medium">
                              {(layers.cognitive.output as any).intent?.domain ||
                               (layers.cognitive.output as any).domain ||
                               '분석'}
                            </p>
                          </div>
                          <div>
                            <span className="text-xs text-gray-500">대상</span>
                            <p className="text-sm font-medium">
                              {(layers.cognitive.output as any).intent?.category ||
                               (layers.cognitive.output as any).category ||
                               '캠페인'}
                            </p>
                          </div>
                          <div>
                            <span className="text-xs text-gray-500">신뢰도</span>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-success h-2 rounded-full"
                                  style={{ width: `${(layers.cognitive.output.confidence || 0) * 100}%` }}
                                />
                              </div>
                              <span className="text-xs font-medium">
                                {Math.round((layers.cognitive.output.confidence || 0) * 100)}%
                              </span>
                            </div>
                          </div>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">추천 도구</h4>
                          <div className="flex flex-wrap gap-2">
                            {(layers.cognitive.output as any).suggested_tools?.length > 0 ? (
                              (layers.cognitive.output as any).suggested_tools.map((tool: string, idx: number) => (
                                <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                                  {tool}
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-gray-500">분석 중...</span>
                            )}
                          </div>
                        </div>
                        {(layers.cognitive.output as any).context_summary && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-700 mb-2">맥락 요약</h4>
                            <p className="text-sm text-gray-600">
                              {(layers.cognitive.output as any).context_summary}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </ErrorBoundary>

            {/* 계획수립 단계 */}
            <ErrorBoundary>
              {layers.planning && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                  <button
                    onClick={() => setExpandedLayers(prev => ({ ...prev, planning: !prev.planning }))}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        layers.planning.status === 'completed' ? 'bg-success' :
                        layers.planning.status === 'running' ? 'bg-luminous-blue animate-pulse' :
                        'bg-gray-300'
                      }`} />
                      <span className="font-medium">계획수립</span>
                      {layers.planning.status === 'running' && (
                        <Loader2 className="w-4 h-4 animate-spin text-luminous-blue" />
                      )}
                    </div>
                    {expandedLayers.planning ? <ChevronUp className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                  {expandedLayers.planning && layers.planning.output && (
                    <div className="px-4 py-3 border-t border-gray-200">
                      <div className="space-y-3">
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">실행 전략</h4>
                          <p className="text-sm text-gray-600">
                            {(layers.planning.output as any).planning_result?.plan?.strategy === 'parallel' ? '병렬 실행' :
                             (layers.planning.output as any).plan?.strategy === 'parallel' ? '병렬 실행' : '순차 실행'}
                          </p>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">작업 목록</h4>
                          <ol className="space-y-1">
                            {((layers.planning.output as any).planning_result?.plan?.todos ||
                              (layers.planning.output as any).plan?.todos ||
                              (layers.planning.output as any).todos || []).map((todo: any, i: number) => (
                              <li key={i} className="text-xs text-gray-600 flex items-start gap-2">
                                <span className="text-luminous-blue font-medium">{i + 1}.</span>
                                <span>{todo.task || todo.label || todo.description || '작업'}</span>
                              </li>
                            ))}
                          </ol>
                        </div>
                        {((layers.planning.output as any).planning_result?.plan?.estimated_duration_sec ||
                          (layers.planning.output as any).plan?.estimated_duration_sec) && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-700 mb-2">예상 소요 시간</h4>
                            <p className="text-sm text-gray-600">
                              약 {Math.ceil(((layers.planning.output as any).planning_result?.plan?.estimated_duration_sec ||
                                            (layers.planning.output as any).plan?.estimated_duration_sec) / 60)}분
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </ErrorBoundary>

            {/* 실행 단계 */}
            <ErrorBoundary>
              {layers.execution && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                  <button
                    onClick={() => setExpandedLayers(prev => ({ ...prev, execution: !prev.execution }))}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        layers.execution.status === 'completed' ? 'bg-success' :
                        layers.execution.status === 'running' ? 'bg-luminous-blue animate-pulse' :
                        'bg-gray-300'
                      }`} />
                      <span className="font-medium">실행</span>
                      {layers.execution.status === 'running' && (
                        <Loader2 className="w-4 h-4 animate-spin text-luminous-blue" />
                      )}
                    </div>
                    {expandedLayers.execution ? <ChevronUp className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                  {expandedLayers.execution && layers.execution.output && (
                    <div className="px-4 py-3 border-t border-gray-200">
                      <div className="space-y-3">
                        {/* 활성화된 에이전트 표시 - 나중에 백엔드에서 selected_agents 받아서 표시 */}
                        {(() => {
                          // 백엔드에서 받을 데이터: (layers.execution.output as any).selected_agents
                          // 현재는 목업 데이터 사용
                          const mockSelectedAgents = ['data_analysis_agent', 'report_agent'];
                          const selectedAgents = (layers.execution.output as any).selected_agents || mockSelectedAgents;

                          return (
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 mb-2">활성화된 실행 에이전트</h4>
                              <div className="grid grid-cols-2 gap-2">
                                {selectedAgents.map((agentId: string) => {
                                  const agentInfo = getAgentInfo(agentId);
                                  return (
                                    <div key={agentId} className={`rounded-lg p-2 border-2 ${agentInfo.borderColor} ${agentInfo.bgColor}`}>
                                      <div className="flex items-center gap-2">
                                        <div className={`w-8 h-8 rounded-full ${agentInfo.iconBg} flex items-center justify-center text-lg`}>
                                          {agentInfo.icon}
                                        </div>
                                        <div className="flex-1">
                                          <div className="text-xs font-semibold">{agentInfo.name}</div>
                                          <div className="text-xs text-gray-600">{agentInfo.description}</div>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          );
                        })()}

                        {/* 실행 중 도구 표시 - 목업 */}
                        {(() => {
                          // 백엔드에서 받을 데이터: (layers.execution.output as any).active_tools
                          // 현재는 목업 데이터
                          const mockActiveTools = {
                            'data_analysis_agent': ['naver_collector', 'sentiment_analyzer', 'keyword_extractor'],
                            'report_agent': ['insight_synthesizer', 'chart_generator']
                          };
                          const activeTools = (layers.execution.output as any).active_tools || mockActiveTools;

                          return (
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 mb-2">실행 중인 도구</h4>
                              <div className="space-y-2">
                                {Object.entries(activeTools).map(([agentId, tools]: [string, any]) => {
                                  const agentInfo = getAgentInfo(agentId);
                                  return (
                                    <div key={agentId} className={`rounded-lg border ${agentInfo.borderColor} overflow-hidden`}>
                                      <div className={`px-2 py-1 ${agentInfo.bgColor} flex items-center gap-2`}>
                                        <span className="text-xs">{agentInfo.icon}</span>
                                        <span className="text-xs font-medium">{agentInfo.name}</span>
                                      </div>
                                      <div className="px-2 py-2 bg-white">
                                        <div className="flex flex-wrap gap-1">
                                          {tools.map((toolId: string, idx: number) => {
                                            const toolInfo = agentInfo.tools[toolId];
                                            if (toolInfo) {
                                              return (
                                                <span key={idx} className={`px-2 py-0.5 text-xs rounded flex items-center gap-1 ${getToolGroupColor(toolInfo.group)}`}>
                                                  <span>{toolInfo.icon}</span>
                                                  <span>{toolInfo.name}</span>
                                                </span>
                                              );
                                            }
                                            return (
                                              <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">
                                                {toolId}
                                              </span>
                                            );
                                          })}
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          );
                        })()}


                        {/* 전체 진행 상태 */}
                        {(layers.execution.output as any).todos && (
                          <div className="bg-gradient-to-r from-gray-50 to-white rounded-lg p-3 border border-gray-200">
                            <h4 className="text-sm font-medium text-gray-700 mb-2">전체 작업 진행률</h4>
                            <div className="flex items-center gap-3">
                              <div className="flex-1">
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                                    style={{
                                      width: `${((layers.execution.output as any).todos.filter((t: any) => t.status === 'completed').length / (layers.execution.output as any).todos.length) * 100}%`
                                    }}
                                  />
                                </div>
                              </div>
                              <span className="text-sm font-medium text-gray-700">
                                {(layers.execution.output as any).todos.filter((t: any) => t.status === 'completed').length} / {(layers.execution.output as any).todos.length}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </ErrorBoundary>

            {/* 결과생성 단계 */}
            <ErrorBoundary>
              {layers.response && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                  <button
                    onClick={() => setExpandedLayers(prev => ({ ...prev, response: !prev.response }))}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        layers.response.status === 'completed' ? 'bg-success' :
                        layers.response.status === 'running' ? 'bg-luminous-blue animate-pulse' :
                        'bg-gray-300'
                      }`} />
                      <span className="font-medium">결과생성</span>
                      {layers.response.status === 'running' && (
                        <Loader2 className="w-4 h-4 animate-spin text-luminous-blue" />
                      )}
                    </div>
                    {expandedLayers.response ? <ChevronUp className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                  {expandedLayers.response && layers.response.output && (
                    <div className="px-4 py-3 border-t border-gray-200">
                      <div className="space-y-3">
                        {(layers.response.output as any).response_result?.response && (
                          <>
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 mb-2">응답 요약</h4>
                              <p className="text-sm text-gray-600">
                                {(layers.response.output as any).response_result.response.summary ||
                                 '응답을 생성하는 중입니다...'}
                              </p>
                            </div>
                            {(layers.response.output as any).response_result.response.text && (
                              <div>
                                <h4 className="text-sm font-medium text-gray-700 mb-2">상세 응답</h4>
                                <p className="text-sm text-gray-600 whitespace-pre-wrap">
                                  {(layers.response.output as any).response_result.response.text}
                                </p>
                              </div>
                            )}
                            {(layers.response.output as any).response_result.response.next_actions?.length > 0 && (
                              <div>
                                <h4 className="text-sm font-medium text-gray-700 mb-2">다음 단계 액션</h4>
                                <div className="space-y-2">
                                  {(layers.response.output as any).response_result.response.next_actions.map((action: string, idx: number) => (
                                    <label key={idx} className="flex items-start gap-2">
                                      <input type="checkbox" className="mt-0.5" />
                                      <span className="text-sm text-gray-600">{action}</span>
                                    </label>
                                  ))}
                                </div>
                              </div>
                            )}
                          </>
                        )}
                        {!(layers.response.output as any).response_result?.response && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-700 mb-2">최종 결과</h4>
                            <p className="text-sm text-gray-600">
                              작업이 완료되었습니다.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};