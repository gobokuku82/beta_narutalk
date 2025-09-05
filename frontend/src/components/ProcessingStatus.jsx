import React from 'react';

const ProcessingStatus = ({ status, agents, tools }) => {
  if (!status) return null;

  return (
    <div className="processing-status">
      <div className="status-header">
        <span className="status-icon">⚡</span>
        <span className="status-text">처리 중...</span>
      </div>
      
      {agents && agents.length > 0 && (
        <div className="active-agents">
          <span className="label">활성 에이전트:</span>
          <div className="agent-list">
            {agents.map((agent, idx) => (
              <div key={idx} className="agent-item">
                <span className="agent-icon">🤖</span>
                <span className="agent-name">{agent}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {tools && tools.length > 0 && (
        <div className="active-tools">
          <span className="label">실행 중인 도구:</span>
          <div className="tool-list">
            {tools.map((tool, idx) => (
              <div key={idx} className="tool-item">
                <span className="tool-icon">🔧</span>
                <span className="tool-name">{tool}</span>
                <span className="tool-status">실행 중</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="processing-animation">
        <div className="pulse"></div>
        <div className="pulse"></div>
        <div className="pulse"></div>
      </div>
    </div>
  );
};

export default ProcessingStatus;