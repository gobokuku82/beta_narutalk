export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  visualization?: VisualizationData;
  metadata?: {
    agent_used?: string;
    error?: string;
    iteration_count?: number;
  };
}

export interface ChatSession {
  id: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  user_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  agent_used?: string;
  metadata?: Record<string, any>;
}

export interface VisualizationData {
  type: 'chart' | 'table' | 'custom' | 'html';
  data: any;
  config?: Record<string, any>;
}