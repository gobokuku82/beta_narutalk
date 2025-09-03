import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Maximize2, Minimize2, Moon, Sun, RefreshCw } from 'lucide-react';
import { useChat } from '../../hooks/useChat';
import { useTheme } from '../../contexts/ThemeContext';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface ChatBotProps {
  defaultOpen?: boolean;
  position?: 'bottom-right' | 'bottom-left' | 'center';
}

export const ChatBot: React.FC<ChatBotProps> = ({ 
  defaultOpen = false,
  position = 'bottom-right' 
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { theme, toggleTheme } = useTheme();
  const {
    messages,
    isTyping,
    sendMessage,
    clearMessages,
    isLoading,
  } = useChat();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'center': 'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2'
  };

  const chatWindowClasses = isFullscreen
    ? 'fixed inset-0 w-full h-full rounded-none'
    : `fixed ${positionClasses[position]} w-full max-w-md h-[600px] md:w-[400px] lg:w-[450px]`;

  return (
    <>
      {/* Floating Action Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsOpen(true)}
            className={`fixed ${positionClasses[position]} p-4 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-full shadow-2xl hover:shadow-3xl transition-all duration-300 z-50`}
          >
            <MessageCircle className="w-6 h-6" />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={`${chatWindowClasses} glassmorphism dark:glassmorphism-dark rounded-2xl shadow-2xl flex flex-col z-50`}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full flex items-center justify-center">
                    <MessageCircle className="w-5 h-5 text-white" />
                  </div>
                  <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white dark:border-gray-800" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">AI Assistant</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Always here to help</p>
                </div>
              </div>

              {/* Header Actions */}
              <div className="flex items-center gap-2">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={clearMessages}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  title="Clear messages"
                >
                  <RefreshCw className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={toggleTheme}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  title="Toggle theme"
                >
                  {theme === 'dark' ? (
                    <Sun className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  ) : (
                    <Moon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  )}
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  title="Toggle fullscreen"
                >
                  {isFullscreen ? (
                    <Minimize2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  ) : (
                    <Maximize2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  )}
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setIsOpen(false)}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <X className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </motion.button>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
                  <MessageCircle className="w-16 h-16 mb-4 opacity-20" />
                  <p className="text-center">Start a conversation!<br />Ask me anything...</p>
                </div>
              ) : (
                <>
                  {messages.map((message, index) => (
                    <ChatMessage key={message.id} message={message} index={index} />
                  ))}
                  {isTyping && (
                    <div className="flex justify-start mb-4">
                      <div className="glassmorphism dark:glassmorphism-dark rounded-2xl p-3">
                        <LoadingSpinner size="sm" text="" />
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <ChatInput
                onSendMessage={sendMessage}
                isLoading={isLoading || isTyping}
                placeholder="Type your message..."
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};