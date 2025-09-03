import { useState, useCallback, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { v4 as uuidv4 } from 'uuid';
import { chatApi } from '../services/api';
import { Message, ChatRequest } from '../types/chat.types';
import { VisualizationService } from '../services/visualizationService';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessageMutation = useMutation({
    mutationFn: async (request: ChatRequest) => {
      return await chatApi.sendMessage(request);
    },
    onSuccess: (data) => {
      // Parse visualization data if present
      const visualization = VisualizationService.parseVisualization(data.response);
      
      const assistantMessage: Message = {
        id: uuidv4(),
        content: data.response,
        role: 'assistant',
        timestamp: new Date(),
        visualization,
        metadata: data.metadata,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setIsTyping(false);

      // Update session ID if provided
      if (data.session_id) {
        setSessionId(data.session_id);
      }
    },
    onError: (error) => {
      console.error('Failed to send message:', error);
      setIsTyping(false);
      
      const errorMessage: Message = {
        id: uuidv4(),
        content: 'Sorry, an error occurred. Please try again.',
        role: 'assistant',
        timestamp: new Date(),
        metadata: { error: error.message },
      };
      
      setMessages((prev) => [...prev, errorMessage]);
    },
  });

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      content,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    // Send to API
    await sendMessageMutation.mutateAsync({
      message: content,
      session_id: sessionId || undefined,
    });
  }, [sessionId, sendMessageMutation]);

  const streamMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Cancel any existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      content,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    // Create assistant message placeholder
    const assistantMessageId = uuidv4();
    const assistantMessage: Message = {
      id: assistantMessageId,
      content: '',
      role: 'assistant',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      await chatApi.streamChat(
        {
          message: content,
          session_id: sessionId || undefined,
        },
        (chunk) => {
          // Update assistant message with streamed content
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: msg.content + chunk }
                : msg
            )
          );
        }
      );
    } catch (error) {
      console.error('Stream error:', error);
    } finally {
      setIsTyping(false);
    }
  }, [sessionId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setSessionId(null);
  }, []);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsTyping(false);
    }
  }, []);

  return {
    messages,
    sessionId,
    isTyping,
    sendMessage,
    streamMessage,
    clearMessages,
    cancelStream,
    isLoading: sendMessageMutation.isPending,
  };
};