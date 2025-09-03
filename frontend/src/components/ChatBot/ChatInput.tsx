import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Paperclip, Mic, StopCircle, Smile } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading = false,
  disabled = false,
  placeholder = "Type your message..."
}) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (message.trim() && !disabled && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // TODO: Implement voice recording
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full glassmorphism dark:glassmorphism-dark rounded-2xl p-3"
    >
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        {/* Attachment Button */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          type="button"
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          disabled={disabled || isLoading}
        >
          <Paperclip className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </motion.button>

        {/* Message Input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            className="w-full px-4 py-2 bg-white dark:bg-gray-800 rounded-xl 
                     border border-gray-200 dark:border-gray-700
                     focus:outline-none focus:ring-2 focus:ring-primary-500
                     resize-none max-h-32 scrollbar-thin
                     placeholder-gray-400 dark:placeholder-gray-500
                     text-gray-900 dark:text-gray-100
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-all duration-200"
            rows={1}
          />
          
          {/* Character Count */}
          {message.length > 0 && (
            <div className="absolute bottom-1 right-2 text-xs text-gray-400">
              {message.length}/1000
            </div>
          )}
        </div>

        {/* Emoji Button */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          type="button"
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          disabled={disabled || isLoading}
        >
          <Smile className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </motion.button>

        {/* Voice Recording Button */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          type="button"
          onClick={toggleRecording}
          className={`p-2 rounded-lg transition-colors ${
            isRecording
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : 'hover:bg-gray-100 dark:hover:bg-gray-800'
          }`}
          disabled={disabled || isLoading}
        >
          {isRecording ? (
            <StopCircle className="w-5 h-5" />
          ) : (
            <Mic className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          )}
        </motion.button>

        {/* Send Button */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          type="submit"
          disabled={!message.trim() || disabled || isLoading}
          className={`p-2 rounded-lg transition-all duration-200 ${
            message.trim() && !disabled && !isLoading
              ? 'bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white shadow-lg'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
          }`}
        >
          <Send className="w-5 h-5" />
        </motion.button>
      </form>

      {/* Recording Indicator */}
      {isRecording && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="flex items-center mt-2 text-red-500"
        >
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse mr-2" />
          <span className="text-sm">Recording...</span>
        </motion.div>
      )}
    </motion.div>
  );
};