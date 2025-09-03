import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Message from './Message';
import Spinner from './Spinner';
import { chatService } from '../services/api';

const ChatBot = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  // 메시지 영역 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

    try {
      // API 호출
      const response = await chatService.sendMessage(inputValue, sessionId);
      
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
    }
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
        <div className="status-indicator">
          <span className="status-dot"></span>
          <span>온라인</span>
        </div>
      </div>

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
        
        {isLoading && (
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