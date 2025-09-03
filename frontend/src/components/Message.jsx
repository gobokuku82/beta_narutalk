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

  return (
    <div className={`message ${message.role}`}>
      <div className="message-content">
        <div>{message.content}</div>
        
        {/* 시각화 데이터가 있으면 렌더링 */}
        {message.visualization && (
          <Visualization data={message.visualization} />
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