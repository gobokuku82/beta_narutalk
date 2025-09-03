import React from 'react';
import {
  Box,
  Avatar,
  Typography,
  Paper,
  Skeleton,
  Fade,
} from '@mui/material';
import {
  SmartToy as BotIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Message } from '../types/chat';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading }) => {
  return (
    <Box
      sx={{
        flex: 1,
        overflowY: 'auto',
        p: 3,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {messages.map((message, index) => (
        <Fade in key={message.id} timeout={300}>
          <Box
            component={motion.div}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            sx={{
              display: 'flex',
              gap: 2,
              alignItems: 'flex-start',
              flexDirection: message.sender === 'user' ? 'row-reverse' : 'row',
            }}
          >
            <Avatar
              sx={{
                bgcolor: message.sender === 'user' 
                  ? 'linear-gradient(135deg, #FB923C 0%, #EA580C 100%)' 
                  : 'linear-gradient(135deg, #A78BFA 0%, #7DD3FC 100%)',
                width: 36,
                height: 36,
              }}
            >
              {message.sender === 'user' ? <PersonIcon /> : <BotIcon />}
            </Avatar>

            <Paper
              elevation={0}
              sx={{
                p: 2,
                maxWidth: '70%',
                borderRadius: 3,
                background: message.sender === 'user'
                  ? 'linear-gradient(135deg, #A78BFA 0%, #7DD3FC 100%)'
                  : message.isError
                  ? '#FEE2E2'
                  : '#F8F9FA',
                color: message.sender === 'user' ? 'white' : 'text.primary',
                position: 'relative',
                '&::before': message.sender === 'user' ? {
                  content: '""',
                  position: 'absolute',
                  right: -8,
                  top: 16,
                  width: 0,
                  height: 0,
                  borderTop: '8px solid transparent',
                  borderBottom: '8px solid transparent',
                  borderLeft: '8px solid #7DD3FC',
                } : {
                  content: '""',
                  position: 'absolute',
                  left: -8,
                  top: 16,
                  width: 0,
                  height: 0,
                  borderTop: '8px solid transparent',
                  borderBottom: '8px solid transparent',
                  borderRight: '8px solid #F8F9FA',
                },
              }}
            >
              {message.agent && (
                <Typography
                  variant="caption"
                  sx={{
                    display: 'inline-block',
                    px: 1,
                    py: 0.5,
                    borderRadius: 1,
                    background: 'rgba(167, 139, 250, 0.1)',
                    color: 'primary.main',
                    mb: 1,
                  }}
                >
                  {getAgentLabel(message.agent)}
                </Typography>
              )}
              
              <Box
                sx={{
                  '& p': { margin: 0, lineHeight: 1.6 },
                  '& ul, & ol': { pl: 2, my: 1 },
                  '& li': { mb: 0.5 },
                  '& code': {
                    background: message.sender === 'user' 
                      ? 'rgba(255, 255, 255, 0.2)' 
                      : 'rgba(0, 0, 0, 0.05)',
                    padding: '2px 6px',
                    borderRadius: 4,
                    fontSize: '0.9em',
                  },
                  '& pre': {
                    background: message.sender === 'user' 
                      ? 'rgba(255, 255, 255, 0.2)' 
                      : 'rgba(0, 0, 0, 0.05)',
                    p: 1.5,
                    borderRadius: 2,
                    overflowX: 'auto',
                  },
                }}
              >
                <ReactMarkdown>{message.text}</ReactMarkdown>
              </Box>

              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  mt: 1,
                  opacity: 0.7,
                }}
              >
                {formatTime(message.timestamp)}
              </Typography>
            </Paper>
          </Box>
        </Fade>
      ))}

      {isLoading && (
        <Box display="flex" gap={2} alignItems="flex-start">
          <Avatar
            sx={{
              bgcolor: 'linear-gradient(135deg, #A78BFA 0%, #7DD3FC 100%)',
              width: 36,
              height: 36,
            }}
          >
            <BotIcon />
          </Avatar>
          <Paper
            elevation={0}
            sx={{
              p: 2,
              borderRadius: 3,
              background: '#F8F9FA',
              width: '60%',
            }}
          >
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="body2" color="text.secondary">
                AI가 생각하는 중
              </Typography>
              <span className="typing-dots" />
            </Box>
            <Box mt={1}>
              <Skeleton variant="text" width="100%" />
              <Skeleton variant="text" width="80%" />
              <Skeleton variant="text" width="60%" />
            </Box>
          </Paper>
        </Box>
      )}
    </Box>
  );
};

function getAgentLabel(agent: string): string {
  const labels: Record<string, string> = {
    info_retrieval: '🔍 정보검색',
    doc_generation: '📝 문서생성',
    compliance: '⚖️ 규정검사',
    analytics: '📊 데이터분석',
    supervisor: '🎯 조정자',
  };
  return labels[agent] || agent;
}

function formatTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - new Date(date).getTime();
  const minutes = Math.floor(diff / 60000);
  
  if (minutes < 1) return '방금 전';
  if (minutes < 60) return `${minutes}분 전`;
  
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  
  return new Date(date).toLocaleDateString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default MessageList;