export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  agent?: string;
  isError?: boolean;
  metadata?: Record<string, any>;
  attachments?: Attachment[];
}

export interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  agent_used?: string;
  metadata?: {
    iteration_count?: number;
    error?: string;
    [key: string]: any;
  };
}

export interface SendMessageParams {
  message: string;
  session_id?: string | null;
  user_id?: string;
}

export interface Agent {
  name: string;
  description: string;
  capabilities: string[];
  status?: 'active' | 'inactive' | 'processing';
}

export interface Session {
  id: string;
  created_at: Date;
  updated_at: Date;
  messages: Message[];
  metadata?: Record<string, any>;
}