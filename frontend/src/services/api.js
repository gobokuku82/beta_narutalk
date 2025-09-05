import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API 서비스
export const chatService = {
  // 메시지 전송
  sendMessage: async (message, sessionId = null) => {
    try {
      const response = await api.post('/api/v1/chat/', {
        message: message,
        session_id: sessionId
      });
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // 복합 질의 전송 (여러 에이전트 사용)
  sendComplexQuery: async (query, sessionId = null, agents = null) => {
    try {
      const response = await api.post('/api/v1/chat/complex', {
        query: query,
        session_id: sessionId,
        agents: agents
      });
      return response.data;
    } catch (error) {
      console.error('Complex Query Error:', error);
      throw error;
    }
  },

  // 에이전트 목록 조회
  getAgents: async () => {
    try {
      const response = await api.get('/api/v1/chat/agents');
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // 도구 목록 조회
  getTools: async () => {
    try {
      const response = await api.get('/api/v1/chat/tools');
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  // 세션 생성
  createSession: async () => {
    try {
      const response = await api.post('/api/v1/session/create');
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }
};

export default api;