import React from 'react';
import { motion } from 'framer-motion';
import { User, Bot, Clock } from 'lucide-react';
import { Message } from '../../types/chat.types';
import { VisualizationRenderer } from '../Visualizations/VisualizationRenderer';

interface ChatMessageProps {
  message: Message;
  index: number;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, index }) => {
  const isUser = message.role === 'user';
  
  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} max-w-[85%] md:max-w-[70%]`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <motion.div
            whileHover={{ scale: 1.1 }}
            className={`w-10 h-10 rounded-full flex items-center justify-center ${
              isUser
                ? 'bg-gradient-to-r from-primary-500 to-primary-600'
                : 'bg-gradient-to-r from-secondary-500 to-secondary-600'
            } shadow-lg`}
          >
            {isUser ? (
              <User className="w-5 h-5 text-white" />
            ) : (
              <Bot className="w-5 h-5 text-white" />
            )}
          </motion.div>
        </div>

        {/* Message Content */}
        <div className="flex flex-col">
          {/* Message Bubble */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            className={`px-4 py-3 rounded-2xl ${
              isUser
                ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white'
                : 'glassmorphism dark:glassmorphism-dark'
            } shadow-md`}
          >
            <p className={`whitespace-pre-wrap ${isUser ? 'text-white' : 'text-gray-800 dark:text-gray-200'}`}>
              {message.content}
            </p>

            {/* Visualization if present */}
            {message.visualization && (
              <div className="mt-3 border-t border-white/20 pt-3">
                <VisualizationRenderer data={message.visualization} />
              </div>
            )}
          </motion.div>

          {/* Timestamp and Metadata */}
          <div className={`flex items-center mt-1 text-xs text-gray-500 dark:text-gray-400 ${
            isUser ? 'justify-end' : 'justify-start'
          }`}>
            <Clock className="w-3 h-3 mr-1" />
            <span>{formatTime(message.timestamp)}</span>
            {message.metadata?.agent_used && (
              <span className="ml-2 px-2 py-0.5 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded-full">
                {message.metadata.agent_used}
              </span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};