import axios from 'axios';
import type { ChatRequest, ChatResponse } from '../types/chat.types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/api/v1/chat/', request);
    return response.data;
  },

  getAgents: async () => {
    const response = await apiClient.get('/api/v1/chat/agents');
    return response.data;
  },

  createSession: async (userId?: string) => {
    const response = await apiClient.post('/api/v1/session/create', { user_id: userId });
    return response.data;
  },

  getSession: async (sessionId: string) => {
    const response = await apiClient.get(`/api/v1/session/${sessionId}`);
    return response.data;
  },

  streamChat: async (request: ChatRequest, onMessage: (chunk: string) => void) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Stream request failed');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) return;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      onMessage(chunk);
    }
  },
};

export default apiClient;