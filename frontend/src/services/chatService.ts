import axios, { AxiosInstance } from 'axios';
import { ChatResponse, SendMessageParams } from '../types/chat';

class ChatService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        // 토큰 추가 (필요시)
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // 인증 오류 처리
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // 메시지 전송
  async sendMessage(message: string, sessionId?: string | null): Promise<ChatResponse> {
    try {
      const response = await this.api.post<ChatResponse>('/api/v1/chat', {
        message,
        session_id: sessionId,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '메시지 전송 실패');
    }
  }

  // 스트리밍 메시지 (SSE)
  streamMessage(message: string, sessionId?: string | null, onChunk?: (chunk: string) => void): EventSource {
    const params = new URLSearchParams({
      message,
      ...(sessionId && { session_id: sessionId }),
    });

    const eventSource = new EventSource(
      `${this.api.defaults.baseURL}/api/v1/chat/stream?${params}`
    );

    eventSource.onmessage = (event) => {
      if (onChunk) {
        onChunk(event.data);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };

    return eventSource;
  }

  // 파일 업로드
  async uploadFile(file: File, sessionId?: string | null): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }

    try {
      const response = await this.api.post('/api/v1/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '파일 업로드 실패');
    }
  }

  // 세션 관련
  async createSession(): Promise<{ session_id: string }> {
    try {
      const response = await this.api.post('/api/v1/session/create');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '세션 생성 실패');
    }
  }

  async getSession(sessionId: string): Promise<any> {
    try {
      const response = await this.api.get(`/api/v1/session/${sessionId}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '세션 조회 실패');
    }
  }

  // 에이전트 정보
  async getAvailableAgents(): Promise<any> {
    try {
      const response = await this.api.get('/api/v1/chat/agents');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '에이전트 정보 조회 실패');
    }
  }

  // 데이터베이스 쿼리
  async queryDatabase(query: string, dbType: 'vector' | 'analytics' | 'rules'): Promise<any> {
    try {
      const endpoint = {
        vector: '/api/v1/database/vector/search',
        analytics: '/api/v1/database/analytics/query',
        rules: '/api/v1/database/rules/check',
      }[dbType];

      const response = await this.api.post(endpoint, { query });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '데이터베이스 쿼리 실패');
    }
  }

  // 문서 생성
  async generateDocument(type: string, params: any): Promise<any> {
    try {
      const response = await this.api.post('/api/v1/documents/generate', {
        type,
        params,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '문서 생성 실패');
    }
  }

  // 규정 검사
  async checkCompliance(content: string, category?: string): Promise<any> {
    try {
      const response = await this.api.post('/api/v1/database/rules/check', {
        content,
        category: category || 'general',
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '규정 검사 실패');
    }
  }
}

export const chatService = new ChatService();