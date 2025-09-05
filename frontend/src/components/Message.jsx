import React from 'react';
import Visualization from './Visualization';

const Message = ({ message }) => {
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ko-KR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // 에이전트와 도구 정보 추출
  const getAgentInfo = () => {
    if (message.metadata?.agent_outputs) {
      const agents = Object.keys(message.metadata.agent_outputs);
      return agents;
    }
    return [];
  };

  const getToolsUsed = () => {
    const tools = [];
    if (message.metadata?.agent_outputs) {
      Object.values(message.metadata.agent_outputs).forEach(output => {
        if (output.tools_used) {
          tools.push(...output.tools_used);
        }
      });
    }
    return [...new Set(tools)]; // 중복 제거
  };

  const agents = getAgentInfo();
  const tools = getToolsUsed();

  return (
    <div className={`message ${message.role}`}>
      <div className="message-content">
        {/* 에이전트/도구 정보 표시 */}
        {message.role === 'assistant' && (agents.length > 0 || tools.length > 0) && (
          <div className="message-metadata">
            {agents.length > 0 && (
              <div className="agents-used">
                <span className="metadata-label">사용된 에이전트:</span>
                {agents.map((agent, idx) => (
                  <span key={idx} className="agent-badge">{agent}</span>
                ))}
              </div>
            )}
            {tools.length > 0 && (
              <div className="tools-used">
                <span className="metadata-label">사용된 도구:</span>
                {tools.map((tool, idx) => (
                  <span key={idx} className="tool-badge">{tool}</span>
                ))}
              </div>
            )}
          </div>
        )}
        
        <div className="message-text">{message.content}</div>
        
        {/* 시각화 데이터가 있으면 렌더링 */}
        {message.visualization && (
          <Visualization data={message.visualization} />
        )}
        
        {/* 분석 결과 표시 */}
        {message.metadata?.agent_outputs?.analytics && (
          <div className="analytics-results">
            {message.metadata.agent_outputs.analytics.insights && (
              <div className="insights">
                <h4>주요 인사이트:</h4>
                <ul>
                  {message.metadata.agent_outputs.analytics.insights.map((insight, idx) => (
                    <li key={idx}>{insight}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        
        {message.timestamp && (
          <div className="message-time">
            {formatTime(message.timestamp)}
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;