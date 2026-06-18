import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../app/store';
import {
  setWsConnected,
  updateLayerStatus,
  updateLayerOutput,
  addLog,
  resetLayers,
  addAiResponse,
  setTodos,
  updateTodoItem,
} from '../features/agentChat/agentChatSlice';

export const useAgentWebSocket = () => {
  const dispatch = useDispatch();
  const todos = useSelector((state: RootState) => state.agentChat.todos);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number>();
  const [sessionId] = useState(() => Math.random().toString(36).substring(7));
  const lastResponseRef = useRef<string | null>(null);

  const connect = () => {
    // 이미 연결되어 있으면 재연결하지 않음
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      const wsUrl = `ws://localhost:8000/api/agent/ws/${sessionId}`;
      console.log('Connecting to WebSocket:', wsUrl);

      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket connected to backend');
        dispatch(setWsConnected(true));
        dispatch(addLog({
          time: new Date().toLocaleTimeString('ko-KR'),
          message: '백엔드 에이전트 연결 성공',
          type: 'success',
        }));
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('WebSocket message received:', message);

          // 백엔드 메시지 타입에 따라 처리
          switch (message.type) {
            case 'connected':
              console.log('WebSocket connected with session:', message.session_id);
              break;

            case 'layer_start':
              dispatch(updateLayerStatus({
                layer: message.layer,
                status: 'running'
              }));

              // execution 레이어가 시작되면 첫 번째 pending todo를 실행 중으로 표시
              if (message.layer === 'execution') {
                const pendingTodo = todos.find(t => t.status === 'pending');
                if (pendingTodo) {
                  dispatch(updateTodoItem({
                    id: pendingTodo.id,
                    updates: { status: 'running' }
                  }));
                }
              }

              dispatch(addLog({
                time: new Date().toLocaleTimeString('ko-KR'),
                message: `[${message.layer}] 레이어 시작`,
                type: 'info',
              }));
              break;

            case 'layer_update':
              dispatch(updateLayerStatus({
                layer: message.layer,
                status: message.status
              }));
              if (message.output) {
                dispatch(updateLayerOutput({
                  layer: message.layer,
                  output: message.output
                }));
              }
              break;

            case 'layer_complete':
              dispatch(updateLayerStatus({
                layer: message.layer,
                status: 'completed'
              }));

              // execution 레이어가 완료되면 실행 중인 todo를 완료로 표시
              if (message.layer === 'execution') {
                const runningTodo = todos.find(t => t.status === 'running');
                if (runningTodo) {
                  dispatch(updateTodoItem({
                    id: runningTodo.id,
                    updates: { status: 'done' }
                  }));
                }
              }

              console.log(`Layer ${message.layer} completed with output:`, message.output);

              if (message.output) {
                dispatch(updateLayerOutput({
                  layer: message.layer,
                  output: message.output
                }));

                // response layer 완료 시 채팅 메시지 추가
                if (message.layer === 'response') {
                  console.log('Response layer output:', message.output);
                  console.log('Response result detail:', JSON.stringify(message.output.response_result, null, 2));

                  // 다양한 응답 구조를 처리
                  let responseText = null;

                  // response_result 안의 response 객체 확인
                  if (message.output.response_result) {
                    const result = message.output.response_result;
                    console.log('Checking response_result:', result);

                    if (result.response) {
                      console.log('Found response object:', result.response);
                      // text 필드가 있는 경우 (실제 응답 구조)
                      if (result.response.text) {
                        responseText = result.response.text;
                      } else if (result.response.clarification_question) {
                        responseText = result.response.clarification_question;
                      } else if (result.response.message) {
                        responseText = result.response.message;
                      }
                    } else if (result.clarification_question) {
                      responseText = result.clarification_question;
                    } else if (result.message) {
                      responseText = result.message;
                    }
                  }

                  if (responseText && responseText !== lastResponseRef.current) {
                    console.log('Adding AI response:', responseText);
                    lastResponseRef.current = responseText;
                    dispatch(addAiResponse(responseText));
                  } else {
                    console.log('No response text found or duplicate');
                  }
                }

                // planning layer 완료 시 todos 업데이트
                if (message.layer === 'planning') {
                  console.log('Planning layer output structure:', JSON.stringify(message.output, null, 2));
                  console.log('Planning layer output keys:', Object.keys(message.output || {}));

                  let todos = null;

                  // 다양한 경로에서 todos 찾기
                  if (message.output.planning_result?.plan?.todos) {
                    console.log('Found todos in planning_result.plan.todos');
                    todos = message.output.planning_result.plan.todos;
                  } else if (message.output.plan?.todos) {
                    console.log('Found todos in plan.todos');
                    todos = message.output.plan.todos;
                  } else if (message.output.todos) {
                    console.log('Found todos in todos');
                    todos = message.output.todos;
                  } else if (message.output.planning_result) {
                    console.log('Found planning_result but no todos, checking structure:', message.output.planning_result);
                  }

                  if (todos && Array.isArray(todos)) {
                    console.log('Updating todos:', todos);
                    console.log('Raw todo data:', JSON.stringify(todos, null, 2));

                    // TodoItem 형식으로 변환
                    const formattedTodos = todos.map((todo: any, index: number) => {
                      const formatted = {
                        id: todo.id || todo.todo_id || `todo-${Date.now()}-${index}`,
                        label: todo.label || todo.title || todo.description || todo.task || todo.content || '작업',
                        status: todo.status || 'pending',
                        tags: todo.tags || todo.tool ? [todo.tool] : [],
                        requiresHitl: todo.requires_hitl || todo.requiresHitl || todo.requires_approval || false
                      };
                      console.log(`Formatted todo ${index}:`, formatted);
                      return formatted;
                    });

                    console.log('Dispatching setTodos with:', formattedTodos);
                    dispatch(setTodos(formattedTodos));
                  } else {
                    console.log('No todos found in planning output');
                  }
                }
              }

              // Execution 단계의 출력 처리 - todo 상태 업데이트
              if (message.layer === 'execution' && message.output) {
                console.log('Execution layer output received:', message.output);
                console.log('Execution output keys:', Object.keys(message.output || {}));
                console.log('Execution output structure:', JSON.stringify(message.output, null, 2));

                // execution에서 업데이트된 todos 찾기
                if (message.output.todos && Array.isArray(message.output.todos)) {
                  console.log('Found updated todos in execution layer:', message.output.todos);

                  const updatedTodos = message.output.todos;

                  // 각 업데이트된 todo에 대해 상태 업데이트
                  updatedTodos.forEach((updatedTodo: any) => {
                    console.log('Updating todo status:', updatedTodo.id, updatedTodo.status);
                    dispatch(updateTodoItem({
                      id: updatedTodo.id,
                      updates: { status: updatedTodo.status || 'completed' }
                    }));
                  });
                } else {
                  console.log('No todo updates found in execution output');
                  console.log('Checking for todos in different paths...');

                  // 다른 경로에서도 todos 찾기 시도
                  if (message.output.execution_results) {
                    console.log('Found execution_results:', message.output.execution_results);
                  }
                }
              }

              dispatch(addLog({
                time: new Date().toLocaleTimeString('ko-KR'),
                message: `[${message.layer}] 레이어 완료`,
                type: 'success',
              }));
              break;

            case 'task_update':
              // Todo 상태 업데이트로 대체
              if (message.task_id && message.status) {
                dispatch(updateTodoItem({
                  id: message.task_id,
                  updates: { status: message.status }
                }));
              }
              break;

            case 'complete':
              console.log('Agent complete with result:', message.result);
              console.log('Complete result detail:', JSON.stringify(message.result, null, 2));

              dispatch(addLog({
                time: new Date().toLocaleTimeString('ko-KR'),
                message: '작업 완료',
                type: 'success',
              }));

              // 최종 결과 처리 - 다양한 응답 구조 처리
              if (message.result) {
                let finalResponse = null;

                // response 객체 확인
                if (message.result.response) {
                  console.log('Found response in result:', message.result.response);

                  if (typeof message.result.response === 'string') {
                    finalResponse = message.result.response;
                  } else if (message.result.response.text) {
                    // text 필드가 있는 경우 (실제 응답 구조)
                    finalResponse = message.result.response.text;
                  } else if (message.result.response.clarification_question) {
                    finalResponse = message.result.response.clarification_question;
                  } else if (message.result.response.message) {
                    finalResponse = message.result.response.message;
                  }
                } else if (message.result.clarification_question) {
                  finalResponse = message.result.clarification_question;
                } else if (message.result.message) {
                  finalResponse = message.result.message;
                }

                if (finalResponse && !finalResponse.includes('처리하고 있습니다') && finalResponse !== lastResponseRef.current) {
                  console.log('Adding final response:', finalResponse);
                  lastResponseRef.current = finalResponse;
                  dispatch(addAiResponse(finalResponse));
                } else {
                  console.log('No final response found or duplicate, finalResponse:', finalResponse);
                }
              }

              // 실행 상태는 addAiResponse에서 자동으로 false로 설정됨
              break;

            case 'error':
              dispatch(addLog({
                time: new Date().toLocaleTimeString('ko-KR'),
                message: `오류: ${message.error}`,
                type: 'error',
              }));
              break;

            case 'hitl_request':
              // HITL 요청 처리
              console.log('HITL request:', message);
              dispatch(updateLayerStatus({
                layer: 'execution',
                status: 'waiting_hitl'
              }));
              dispatch(addLog({
                time: new Date().toLocaleTimeString('ko-KR'),
                message: `[HITL] ${message.message}`,
                type: 'warn',
              }));
              break;

            case 'log':
              dispatch(addLog({
                time: new Date().toLocaleTimeString('ko-KR'),
                message: message.message,
                type: message.level as any,
              }));
              break;

            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onclose = () => {
        dispatch(setWsConnected(false));
        dispatch(addLog({
          time: new Date().toLocaleTimeString('ko-KR'),
          message: '백엔드 연결 끊김',
          type: 'warn',
        }));

        // 5초 후 재연결 시도
        reconnectTimeout.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 5000) as unknown as number;
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        dispatch(addLog({
          time: new Date().toLocaleTimeString('ko-KR'),
          message: 'WebSocket 연결 오류',
          type: 'error',
        }));
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

  const sendMessage = async (message: any) => {
    console.log('sendMessage called with:', message);
    console.log('Session ID:', sessionId);

    // 이전 응답 참조 초기화
    lastResponseRef.current = null;

    // 레이어 초기화
    dispatch(resetLayers());

    // Cognitive 레이어 시작
    dispatch(updateLayerStatus({
      layer: 'cognitive',
      status: 'running'
    }));

    try {
      const requestBody = {
        session_id: sessionId,
        message: typeof message === 'string' ? message : message.message,
        language: 'ko',
      };

      console.log('Sending request to backend:', requestBody);

      // REST API를 통해 에이전트 실행 요청
      const response = await fetch('http://localhost:8000/api/agent/run-async', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Agent run started:', result);
      console.log('WebSocket current state:', ws.current?.readyState);

      // WebSocket이 연결되어 있지 않으면 연결
      if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
        console.log('WebSocket not connected, reconnecting...');
        connect();
      }
    } catch (error) {
      console.error('Failed to start agent:', error);
      dispatch(addLog({
        time: new Date().toLocaleTimeString('ko-KR'),
        message: '에이전트 실행 실패',
        type: 'error',
      }));
    }
  };

  useEffect(() => {
    let isActive = true;

    const initConnection = () => {
      if (isActive) {
        connect();
      }
    };

    initConnection();

    return () => {
      isActive = false;
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.close();
        ws.current = null;
      }
    };
  }, [sessionId]); // sessionId를 의존성에 추가

  return { sendMessage, sessionId };
};