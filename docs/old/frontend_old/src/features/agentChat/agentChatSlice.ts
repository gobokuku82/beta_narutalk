import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import {
  PipelineStep,
  TodoItem,
  ChatMessage,
  SystemLog,
  LayerState,
  CognitiveOutput,
  PlanningOutput,
  ExecutionOutput,
  ResponseOutput,
  EngineMessage,
  LayerType,
  LayerStatus
} from '../../types';
import {
  MOCK_PIPELINE_STEPS,
  MOCK_TODOS,
  MOCK_CHAT_MESSAGES,
  MOCK_SYSTEM_LOGS
} from '../../constants/mock';

interface AgentContext {
  channel?: string;
  period?: string;
  retentionData?: Array<{ channel: string; retention: number }>;
  [key: string]: any;
}

interface AgentChatState {
  pipelineSteps: PipelineStep[];
  messages: ChatMessage[];
  todos: TodoItem[];
  logs: SystemLog[];
  previewContent: string | null;
  isRunning: boolean;
  controlMode: boolean;
  hitlPending: TodoItem | null;
  inputValue: string;
  // 4-layer 상태 추가
  layers: {
    cognitive: LayerState<CognitiveOutput>;
    planning: LayerState<PlanningOutput>;
    execution: LayerState<ExecutionOutput>;
    response: LayerState<ResponseOutput>;
  };
  wsConnected: boolean;
  currentLayer: LayerType | null;
  // 채팅 패널 상태 추가
  isOpen: boolean;
  context: AgentContext;
}

const initialState: AgentChatState = {
  pipelineSteps: MOCK_PIPELINE_STEPS,
  messages: MOCK_CHAT_MESSAGES,
  todos: MOCK_TODOS,
  logs: MOCK_SYSTEM_LOGS,
  previewContent: null,
  isRunning: false,
  controlMode: false,
  hitlPending: null,
  inputValue: '',
  layers: {
    cognitive: { status: 'idle', output: null, error: null },
    planning: { status: 'idle', output: null, error: null },
    execution: { status: 'idle', output: null, error: null },
    response: { status: 'idle', output: null, error: null },
  },
  wsConnected: false,
  currentLayer: null,
  // 채팅 패널 상태 초기값 추가
  isOpen: false,
  context: {},
};

const agentChatSlice = createSlice({
  name: 'agentChat',
  initialState,
  reducers: {
    sendMessage: (state, action: PayloadAction<string>) => {
      const newMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        cardType: 'text',
        content: action.payload,
        timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      };
      state.messages.push(newMessage);
      state.inputValue = '';
      state.isRunning = true;

      // todos는 백엔드의 planning layer에서 실제 계획이 오면 setTodos로 업데이트됨
      state.todos = [];

      // Reset layers for new task
      state.layers = {
        cognitive: { status: 'idle', output: null, error: null },
        planning: { status: 'idle', output: null, error: null },
        execution: { status: 'idle', output: null, error: null },
        response: { status: 'idle', output: null, error: null },
      };
    },
    addAiResponse: (state, action: PayloadAction<string>) => {
      const aiMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        cardType: 'text',
        content: action.payload,
        timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      };
      state.messages.push(aiMessage);
      state.isRunning = false;
    },
    confirmClarify: (state) => {
      // "맞아, 시작해" 클릭 시 — 에이전트 실행 시작
      state.isRunning = true;
      const msg: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        cardType: 'text',
        content: '맞아, 시작해',
        timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      };
      state.messages.push(msg);
    },
    selectGateChoice: (state, action: PayloadAction<{ choiceLabel: string }>) => {
      const msg: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        cardType: 'text',
        content: `${action.payload.choiceLabel}(으)로 진행해줘`,
        timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      };
      state.messages.push(msg);
    },
    updatePipelineStep: (state, action: PayloadAction<{ id: string; status: PipelineStep['status'] }>) => {
      const step = state.pipelineSteps.find(s => s.id === action.payload.id);
      if (step) {
        step.status = action.payload.status;
      }
    },
    toggleControlMode: (state) => {
      state.controlMode = !state.controlMode;
    },
    updateTodoItem: (state, action: PayloadAction<{ id: string; updates: Partial<TodoItem> }>) => {
      const todo = state.todos.find(t => t.id === action.payload.id);
      if (todo) {
        Object.assign(todo, action.payload.updates);
      }
    },
    setTodos: (state, action: PayloadAction<TodoItem[]>) => {
      console.log('[agentChatSlice] setTodos called with:', action.payload);
      state.todos = action.payload;
      // controlMode는 사용자가 명시적으로 활성화할 때만 켜짐
      console.log('[agentChatSlice] todos state after update:', state.todos);
    },
    setControlMode: (state, action: PayloadAction<boolean>) => {
      state.controlMode = action.payload;
    },
    approveTodo: (state) => {
      if (state.hitlPending) {
        state.hitlPending = null;
        state.controlMode = false;
      }
    },
    addLog: (state, action: PayloadAction<SystemLog>) => {
      state.logs.push(action.payload);
    },
    setPreviewContent: (state, action: PayloadAction<string | null>) => {
      state.previewContent = action.payload;
    },
    setInputValue: (state, action: PayloadAction<string>) => {
      state.inputValue = action.payload;
    },
    // Layer 관련 액션 추가
    updateLayerStatus: (state, action: PayloadAction<{ layer: LayerType; status: LayerStatus }>) => {
      const { layer, status } = action.payload;
      state.layers[layer].status = status;
      state.layers[layer].timestamp = new Date().toISOString();

      if (status === 'running') {
        state.currentLayer = layer;
      } else if (status === 'completed' || status === 'error') {
        // currentLayer가 현재 layer와 같으면 null로 재설정
        if (state.currentLayer === layer) {
          state.currentLayer = null;
        }
      }
    },
    updateLayerOutput: (state, action: PayloadAction<{ layer: LayerType; output: any }>) => {
      const { layer, output } = action.payload;
      state.layers[layer].output = output;
    },
    updateLayerError: (state, action: PayloadAction<{ layer: LayerType; error: string }>) => {
      const { layer, error } = action.payload;
      state.layers[layer].status = 'error';
      state.layers[layer].error = error;
    },
    processEngineMessage: (state, action: PayloadAction<EngineMessage>) => {
      const message = action.payload;

      if (message.data.status) {
        state.layers[message.layer].status = message.data.status;
      }

      if (message.data.output) {
        state.layers[message.layer].output = message.data.output;
      }

      if (message.data.todo) {
        state.todos = message.data.todo;
      }

      if (message.data.log) {
        state.logs.push({
          time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          message: message.data.log,
          type: message.type === 'error' ? 'error' : 'info',
        });
      }

      if (message.type === 'hitl') {
        state.controlMode = true;
        state.hitlPending = message.data.hitlRequest;
      }
    },
    setWsConnected: (state, action: PayloadAction<boolean>) => {
      state.wsConnected = action.payload;
    },
    resetLayers: (state) => {
      state.layers = {
        cognitive: { status: 'idle', output: null, error: null },
        planning: { status: 'idle', output: null, error: null },
        execution: { status: 'idle', output: null, error: null },
        response: { status: 'idle', output: null, error: null },
      };
      state.currentLayer = null;
    },
    // 채팅 패널 관련 액션 추가
    openChatPanel: (state) => {
      state.isOpen = true;
    },
    closeChatPanel: (state) => {
      state.isOpen = false;
    },
    toggleChatPanel: (state) => {
      state.isOpen = !state.isOpen;
    },
    setAgentContext: (state, action: PayloadAction<AgentContext>) => {
      state.context = action.payload;
    },
    clearAgentContext: (state) => {
      state.context = {};
    },
    // 초기 메시지 설정 액션 추가
    setInitialMessage: (state, action: PayloadAction<string>) => {
      state.inputValue = action.payload;
      // 선택적으로 메시지를 자동 전송할 수도 있습니다
      // 자동 전송을 원한다면 아래 주석 해제
      /*
      const newMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        cardType: 'text',
        content: action.payload,
        timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      };
      state.messages.push(newMessage);
      state.inputValue = '';
      state.isRunning = true;
      */
    },
  },
});

export const {
  sendMessage,
  addAiResponse,
  confirmClarify,
  selectGateChoice,
  updatePipelineStep,
  toggleControlMode,
  updateTodoItem,
  setTodos,
  setControlMode,
  approveTodo,
  addLog,
  setPreviewContent,
  setInputValue,
  updateLayerStatus,
  updateLayerOutput,
  updateLayerError,
  processEngineMessage,
  setWsConnected,
  resetLayers,
  // 채팅 패널 관련 액션 export 추가
  openChatPanel,
  closeChatPanel,
  toggleChatPanel,
  setAgentContext,
  clearAgentContext,
  setInitialMessage,
} = agentChatSlice.actions;

export default agentChatSlice.reducer;