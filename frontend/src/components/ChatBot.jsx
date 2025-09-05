import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Message from './Message';
import Spinner from './Spinner';
import ProcessingStatus from './ProcessingStatus';
import { chatService } from '../services/api';

const ChatBot = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isComplexMode, setIsComplexMode] = useState(false);
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [availableAgents, setAvailableAgents] = useState([]);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [activeAgents, setActiveAgents] = useState([]);
  const [activeTools, setActiveTools] = useState([]);
  const messagesEndRef = useRef(null);

  // 메시지 영역 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 에이전트 목록 로드
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const response = await chatService.getAgents();
        setAvailableAgents(response.agents || []);
      } catch (error) {
        console.error('Failed to load agents:', error);
      }
    };
    loadAgents();
  }, []);

  // 메시지 전송
  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: uuidv4(),
      content: inputValue,
      role: 'user',
      timestamp: new Date().toISOString()
    };

    // 사용자 메시지 추가
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    
    // 처리 상태 초기화
    setProcessingStatus('processing');
    setActiveAgents([]);
    setActiveTools([]);

    try {
      let response;
      
      // 복합 모드인 경우
      if (isComplexMode && selectedAgents.length > 0) {
        // 선택된 에이전트 표시
        setActiveAgents(selectedAgents);
        response = await chatService.sendComplexQuery(inputValue, sessionId, selectedAgents);
      } else {
        // 일반 모드
        response = await chatService.sendMessage(inputValue, sessionId);
      }
      
      // 사용된 에이전트와 도구 업데이트
      if (response.metadata?.agent_outputs) {
        const agents = Object.keys(response.metadata.agent_outputs);
        setActiveAgents(agents);
        
        const tools = [];
        Object.values(response.metadata.agent_outputs).forEach(output => {
          if (output.tools_used) {
            tools.push(...output.tools_used);
          }
        });
        setActiveTools([...new Set(tools)]);
      }
      
      // 세션 ID 업데이트
      if (response.session_id) {
        setSessionId(response.session_id);
      }

      // 시각화 데이터 파싱
      let visualization = null;
      if (response.metadata?.visualization) {
        visualization = response.metadata.visualization;
      }

      // AI 응답 추가
      const aiMessage = {
        id: uuidv4(),
        content: response.response,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        visualization: visualization,
        metadata: response.metadata
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      // 에러 메시지 추가
      const errorMessage = {
        id: uuidv4(),
        content: '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.',
        role: 'assistant',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setProcessingStatus(null);
      setActiveAgents([]);
      setActiveTools([]);
    }
  };

  // 에이전트 선택 토글
  const toggleAgentSelection = (agent) => {
    setSelectedAgents(prev => {
      if (prev.includes(agent)) {
        return prev.filter(a => a !== agent);
      }
      return [...prev, agent];
    });
  };

  // Enter 키 처리
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // 메시지 초기화
  const clearMessages = () => {
    setMessages([]);
    setSessionId(null);
  };

  return (
    <div className="chat-container">
      {/* 헤더 */}
      <div className="chat-header">
        <h1>AI Assistant</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <button 
            className="complex-query-button"
            onClick={() => setIsComplexMode(!isComplexMode)}
            disabled={isLoading}
          >
            {isComplexMode ? '일반 모드' : '복합 질의'}
          </button>
          <div className="status-indicator">
            <span className="status-dot"></span>
            <span>온라인</span>
          </div>
        </div>
      </div>
      
      {/* 복합 모드 에이전트 선택 */}
      {isComplexMode && (
        <div style={{ 
          padding: '10px 20px', 
          background: '#f8f9fa',
          borderBottom: '1px solid #e0e0e0'
        }}>
          <div style={{ fontSize: '14px', marginBottom: '8px', color: '#666' }}>
            사용할 에이전트 선택:
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {availableAgents.map(agent => (
              <button
                key={agent}
                onClick={() => toggleAgentSelection(agent)}
                style={{
                  padding: '5px 12px',
                  border: '1px solid #007bff',
                  borderRadius: '15px',
                  background: selectedAgents.includes(agent) ? '#007bff' : 'white',
                  color: selectedAgents.includes(agent) ? 'white' : '#007bff',
                  cursor: 'pointer',
                  fontSize: '13px'
                }}
                disabled={isLoading}
              >
                {agent}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 메시지 영역 */}
      <div className="messages-container">
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#999', padding: '50px' }}>
            <p>안녕하세요! 무엇을 도와드릴까요?</p>
            <p style={{ fontSize: '14px', marginTop: '10px' }}>
              의약품 정보, 문서 작성, 데이터 분석 등을 지원합니다.
            </p>
          </div>
        )}
        
        {messages.map(message => (
          <Message key={message.id} message={message} />
        ))}
        
        {isLoading && processingStatus && (
          <ProcessingStatus 
            status={processingStatus}
            agents={activeAgents}
            tools={activeTools}
          />
        )}
        
        {isLoading && !processingStatus && (
          <Spinner 
            show={true} 
            text="AI가 응답을 생성하고 있습니다..." 
          />
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <div className="input-container">
        <div className="input-wrapper">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="메시지를 입력하세요..."
            className="message-input"
            disabled={isLoading}
          />
          <button 
            onClick={sendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="send-button"
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatBot;