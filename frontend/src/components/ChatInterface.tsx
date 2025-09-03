import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  CircularProgress,
  Fade,
  Grow,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  AttachFile as AttachIcon,
  Mic as MicIcon,
  MoreVert as MoreIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import MessageList from './MessageList';
import AgentIndicator from './AgentIndicator';
import { useChatStore } from '../store/chatStore';
import { chatService } from '../services/chatService';
import toast from 'react-hot-toast';

const ChatInterface: React.FC = () => {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  
  const { messages, addMessage, updateLastMessage, sessionId, setSessionId } = useChatStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    
    // 사용자 메시지 추가
    addMessage({
      id: Date.now().toString(),
      text: userMessage,
      sender: 'user',
      timestamp: new Date(),
    });

    setIsLoading(true);
    
    try {
      // API 호출
      const response = await chatService.sendMessage(userMessage, sessionId);
      
      // 세션 ID 저장
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }
      
      // 사용된 에이전트 표시
      if (response.agent_used) {
        setCurrentAgent(response.agent_used);
        setTimeout(() => setCurrentAgent(null), 3000);
      }
      
      // 봇 응답 추가
      addMessage({
        id: (Date.now() + 1).toString(),
        text: response.response,
        sender: 'bot',
        timestamp: new Date(),
        agent: response.agent_used,
      });
      
    } catch (error: any) {
      console.error('Error sending message:', error);
      toast.error(error.message || '메시지 전송에 실패했습니다.');
      
      addMessage({
        id: (Date.now() + 1).toString(),
        text: '죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        sender: 'bot',
        timestamp: new Date(),
        isError: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: 900,
        height: '90vh',
        maxHeight: 800,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* 헤더 */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          background: 'linear-gradient(135deg, #A78BFA 0%, #7DD3FC 100%)',
          borderRadius: '24px 24px 0 0',
          color: 'white',
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
              }}
            >
              <BotIcon />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight={700}>
                PharmAssist AI
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                제약 영업 AI 어시스턴트
              </Typography>
            </Box>
          </Box>
          <Box display="flex" gap={1}>
            {currentAgent && <AgentIndicator agent={currentAgent} />}
            <IconButton sx={{ color: 'white' }}>
              <MoreIcon />
            </IconButton>
          </Box>
        </Box>
      </Paper>

      {/* 메시지 영역 */}
      <Paper
        elevation={0}
        sx={{
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 0,
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
        }}
      >
        <MessageList messages={messages} isLoading={isLoading} />
        <div ref={messagesEndRef} />
      </Paper>

      {/* 입력 영역 */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderRadius: '0 0 24px 24px',
          background: 'white',
          borderTop: '1px solid rgba(0, 0, 0, 0.05)',
        }}
      >
        <Box display="flex" gap={1} alignItems="flex-end">
          <IconButton color="primary" size="small">
            <AttachIcon />
          </IconButton>
          
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="메시지를 입력하세요..."
            variant="outlined"
            disabled={isLoading}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
                background: '#F8F9FA',
                '& fieldset': {
                  border: 'none',
                },
                '&:hover': {
                  background: '#F3F4F6',
                },
                '&.Mui-focused': {
                  background: '#FFFFFF',
                  '& fieldset': {
                    border: '2px solid',
                    borderColor: 'primary.main',
                  },
                },
              },
            }}
          />
          
          <IconButton color="primary" size="small">
            <MicIcon />
          </IconButton>
          
          <IconButton
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            sx={{
              background: 'linear-gradient(135deg, #A78BFA 0%, #7DD3FC 100%)',
              color: 'white',
              '&:hover': {
                background: 'linear-gradient(135deg, #8B5CF6 0%, #0EA5E9 100%)',
              },
              '&:disabled': {
                background: '#E5E5E5',
                color: '#999',
              },
            }}
          >
            {isLoading ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
          </IconButton>
        </Box>

        {/* 빠른 액션 칩 */}
        <Box display="flex" gap={1} mt={1.5} flexWrap="wrap">
          {['의약품 정보 검색', '제안서 작성', '규정 확인', '판매 분석'].map((action) => (
            <Chip
              key={action}
              label={action}
              onClick={() => setInput(action)}
              variant="outlined"
              size="small"
              sx={{
                borderColor: 'rgba(167, 139, 250, 0.3)',
                '&:hover': {
                  borderColor: 'primary.main',
                  background: 'rgba(167, 139, 250, 0.05)',
                },
              }}
            />
          ))}
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatInterface;