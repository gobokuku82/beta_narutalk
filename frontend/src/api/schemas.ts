/**
 * zod schemas — 백엔드 메시지 / 응답 / 모델의 frontend 측 검증.
 *
 * 진실 소스: backend Pydantic (planner.Plan / PlannedTodo, MemoryEntry 등)
 * spec: 63 §4~6 / ADR-010 (planner.Plan 단일화) / 35 (memory_entries)
 *
 * Drift 방지: 백엔드 모델 변경 시 본 파일도 함께 update.
 */
import { z } from 'zod';

// ─────────────────────────────────────────────────────────────────
// Plan / Todo — ADR-010 planner.Plan 단일화 기준
// ─────────────────────────────────────────────────────────────────

export const PositionSchema = z.object({
  x: z.number(),
  y: z.number(),
});

export const NodeTypeSchema = z.enum(['task', 'branch', 'join', 'start', 'end']);

export const PlannedTodoSchema = z.object({
  id: z.string(),
  task_type: z.string(),
  team: z.string().nullable().optional(),
  agent: z.string().nullable().optional(),
  tool: z.string().nullable().optional(),
  tool_params: z.record(z.unknown()).default({}),
  depends_on: z.array(z.string()).default([]),
  priority: z.number().int().default(1),
  rationale: z.string().default(''),
  // Workflow Canvas (spec 62) — Optional
  position: PositionSchema.nullable().optional(),
  node_type: NodeTypeSchema.default('task'),
  visualization_meta: z.record(z.unknown()).default({}),
});

export const PlanSchema = z.object({
  teams_selected: z.array(z.string()).default([]),
  todos: z.array(PlannedTodoSchema).default([]),
  dag: z.record(z.array(z.string())).default({}),
  plan_notes: z.string().default(''),
});

export type PlannedTodo = z.infer<typeof PlannedTodoSchema>;
export type Plan = z.infer<typeof PlanSchema>;

// ─────────────────────────────────────────────────────────────────
// Memory Entry — spec 35
// ─────────────────────────────────────────────────────────────────

export const MemoryScopeSchema = z.enum(['session', 'user', 'org', 'global']);
export const MemoryTypeSchema = z.enum([
  'conversation',
  'fact',
  'preference',
  'pattern',
  'feedback',
  'error_recovery',
  'clarification_history',
  'conversation_meta',
  'workflow_template', // spec 62 추가
]);

export const MemoryEntrySchema = z.object({
  id: z.string(),
  user_id: z.string(),
  scope_type: MemoryScopeSchema,
  scope_id: z.string().nullable(),
  conversation_id: z.string().nullable(),
  turn_id: z.string().nullable(),
  type: MemoryTypeSchema,
  content: z.record(z.unknown()), // JSONB (schema_version per type)
  created_at: z.string(),
  updated_at: z.string(),
});

export type MemoryEntry = z.infer<typeof MemoryEntrySchema>;

// Workflow Template content (memory_entries.type='workflow_template')
export const ParamSlotSchema = z.object({
  name: z.string(),
  type: z.enum(['string', 'number', 'boolean']),
  required: z.boolean(),
  description: z.string().optional(),
});

export const WorkflowTemplateContentSchema = z.object({
  schema_version: z.literal('v1'),
  name: z.string(),
  description: z.string(),
  todos: z.array(PlannedTodoSchema),
  dag: z.record(z.array(z.string())),
  param_slots: z.array(ParamSlotSchema).default([]),
  usage_count: z.number().int().default(0),
  last_used_at: z.string().nullable(),
  tags: z.array(z.string()).default([]),
});

// ─────────────────────────────────────────────────────────────────
// Response Attachment — backend ResponsePayload.attachments[] (Attachment pydantic)
// 진실 소스: backend schemas/response_payload.py Attachment. 다운로드 링크(url) 운반.
// ─────────────────────────────────────────────────────────────────

export const ResponseAttachmentSchema = z.object({
  kind: z.string(), // 'pdf' | 'ppt' | 'excel' | 'chart' | 'image' | 'link'
  path: z.string().nullish(),
  url: z.string().nullish(), // /api/files/download?p=... (data 밖이면 null)
  caption: z.string().nullish(),
  meta: z.record(z.unknown()).default({}),
});

export type ResponseAttachment = z.infer<typeof ResponseAttachmentSchema>;

// ─────────────────────────────────────────────────────────────────
// WebSocket Messages — spec 21 v1.4 정합
//
// 백엔드 emit 출처:
// - /ws/agent : backend/api_v2/ws_agent.py (run_turn, _build_*, callback bridge)
// - /ws/hitl  : backend/api_v2/ws_hitl.py
// ─────────────────────────────────────────────────────────────────

// /ws/agent — server → client

/**
 * node_event — 각 레이어 노드가 emit 한 State chunk.
 *
 * spec 21 §2.2: 평탄 구조 (data 가 layer/node_name 이 아니라 노드 emit 한 state dict).
 * data 내용은 노드별로 다름:
 *   cognitive  → {structured_query: {...}}
 *   planning   → {plan: {...}} (정상) 또는 {response: {...}} (reject)
 *   execution  → {execution_result: {...}, execution_progress: {...}}
 *   response   → {response: {...}}
 */
export const NodeEventSchema = z.object({
  type: z.literal('node_event'),
  node: z.enum(['cognitive', 'planning', 'execution', 'response']),
  conversation_id: z.string().optional(),
  turn_id: z.string().optional(),
  data: z.record(z.unknown()).default({}),
});

/**
 * complete — 그래프 종료 (turn 당 1회).
 *
 * spec 21 §2.2: data.status ∈ success|rejected|cancelled|aborted
 * status==aborted → reason 필드 (COGNITIVE_EMPTY_QUERY / hitl_timeout 등)
 */
export const CompleteSchema = z.object({
  type: z.literal('complete'),
  conversation_id: z.string().optional(),
  turn_id: z.string().optional(),
  data: z
    .object({
      status: z.enum(['success', 'rejected', 'cancelled', 'aborted']),
      response: z.record(z.unknown()).optional(),
      execution_result: z.record(z.unknown()).optional(),
      structured_query: z.record(z.unknown()).optional(),
      plan: PlanSchema.optional(),
      guard_warnings: z.array(z.record(z.unknown())).optional(),
      reason: z.string().optional(),
      message: z.string().optional(),
    })
    .passthrough(),
});

/**
 * hitl_request — plan_review interrupt 진입.
 *
 * spec 21 §2.2: data 에 plan/options/message + turn_id/conversation_id 복제 포함.
 * request_type 필드는 백엔드가 emit 하지 않음 (현재 plan_review 만 존재).
 */
export const HitlRequestSchema = z.object({
  type: z.literal('hitl_request'),
  conversation_id: z.string().optional(),
  turn_id: z.string().optional(),
  data: z
    .object({
      request_id: z.string(),
      plan: PlanSchema.optional(),
      options: z.array(z.string()).optional(),
      message: z.string().optional(),
      turn_id: z.string().optional(),
      conversation_id: z.string().optional(),
    })
    .passthrough(),
});

/**
 * paused — execution_pause interrupt 진입.
 *
 * spec 21 §2.2: data 에 progress 정보 + turn_id/conversation_id 복제.
 */
export const PausedSchema = z.object({
  type: z.literal('paused'),
  conversation_id: z.string().optional(),
  turn_id: z.string().optional(),
  data: z
    .object({
      request_id: z.string().optional(),
      completed: z.array(z.string()).optional(),
      total: z.number().int().optional(),
      current_phase: z.number().int().optional(),
      progress: z.record(z.unknown()).optional(),
      turn_id: z.string().optional(),
      conversation_id: z.string().optional(),
    })
    .passthrough(),
});

/**
 * resumed — wait_for_resume 반환 직후.
 *
 * spec 21 §2.2: data.action ∈ approve|modify|reject|continue|cancel
 * approve 라도 서버 내부 변환으로 modify 가 올 수 있음 (Phase 5).
 */
export const ResumedSchema = z.object({
  type: z.literal('resumed'),
  conversation_id: z.string().optional(),
  turn_id: z.string().optional(),
  data: z
    .object({
      action: z.enum(['approve', 'modify', 'reject', 'continue', 'cancel']),
    })
    .passthrough(),
});

/**
 * layer_start — Execution 진입 직후 (callback_manager bridge).
 * session_id = turn_id 값 (Sprint 12 호환).
 */
export const LayerStartSchema = z.object({
  type: z.literal('layer_start'),
  session_id: z.string().optional(),
  conversation_id: z.string().optional(),
  turn_id: z.string().optional(),
  timestamp: z.string().optional(),
  data: z
    .object({
      layer: z.string(),
    })
    .passthrough(),
});

/** todo_start — 개별 Todo 실행 시작. */
export const TodoStartSchema = z.object({
  type: z.literal('todo_start'),
  session_id: z.string().optional(),
  conversation_id: z.string().optional(),
  turn_id: z.string().optional(),
  timestamp: z.string().optional(),
  data: z
    .object({
      todo_id: z.string(),
      tool: z.string().optional(),
      task_type: z.string().optional(),
      agent: z.string().optional(),
    })
    .passthrough(),
});

/** todo_complete — 개별 Todo 종료. */
export const TodoCompleteSchema = z.object({
  type: z.literal('todo_complete'),
  session_id: z.string().optional(),
  conversation_id: z.string().optional(),
  turn_id: z.string().optional(),
  timestamp: z.string().optional(),
  data: z
    .object({
      todo_id: z.string(),
      status: z.string(),
      duration_ms: z.number().optional(),
      is_mock: z.boolean().optional(),
      summary: z.string().optional(),
      error: z.string().optional(),
    })
    .passthrough(),
});

/** progress — Phase 진행률. */
export const ProgressSchema = z.object({
  type: z.literal('progress'),
  session_id: z.string().optional(),
  conversation_id: z.string().optional(),
  turn_id: z.string().optional(),
  timestamp: z.string().optional(),
  data: z
    .object({
      completed: z.number().int(),
      total: z.number().int(),
      phase: z.number().int().optional(),
      phases_total: z.number().int().optional(),
    })
    .passthrough(),
});

// /ws/hitl — bidirectional (server → client 부분)

/**
 * hitl_ack — 명령 처리 확인.
 *
 * spec 21 §3.2: action 카탈로그 5종 (hitl_response / todo_modify / todo_delete / todo_add / todo_edit_nl).
 * accepted==false 시 reason ∈ turn_not_active / TODO_EDIT_NOT_PAUSED / INVALID_DAG / NL_INTENT_UNCLEAR / ...
 */
export const HitlAckSchema = z.object({
  type: z.literal('hitl_ack'),
  timestamp: z.string().optional(),
  data: z
    .object({
      request_id: z.string().optional(),
      session_id: z.string().optional(),
      todo_id: z.string().optional(),
      action: z.string(),
      accepted: z.boolean(),
      nl_action: z.enum(['remove', 'modify', 'add', 'reorder']).optional(),
      invalidated: z.array(z.string()).optional(),
      preserved: z.array(z.string()).optional(),
      restart_from: z.string().nullable().optional(),
      issues: z.array(z.string()).optional(),
      code: z.string().optional(),
      reason: z.string().optional(),
      plan: PlanSchema.optional(),
    })
    .passthrough(),
});

/**
 * connected — 양 채널 공통 (필드 셋이 다름).
 * /ws/agent : session_id + user_id + timestamp
 * /ws/hitl  : channel + user_id + timestamp
 */
export const ConnectedSchema = z.object({
  type: z.literal('connected'),
  channel: z.string().optional(),
  session_id: z.string().optional(),
  user_id: z.string().optional(),
  timestamp: z.string().optional(),
});

export const PongSchema = z.object({
  type: z.literal('pong'),
  timestamp: z.string().optional(),
});

/**
 * error — spec 21 §6 평탄 포맷 + /ws/hitl 일부 중첩(legacy) 케이스 호환.
 * 모든 필드 optional 로 풀어 양쪽 포맷 모두 수용.
 */
export const ErrorMessageSchema = z.object({
  type: z.literal('error'),
  code: z.string().optional(),
  layer: z.string().optional(),
  severity: z.string().optional(),
  message: z.string().optional(),
  detail: z.unknown().optional(),
  conversation_id: z.string().optional(),
  turn_id: z.string().optional(),
  timestamp: z.string().optional(),
  data: z
    .object({
      code: z.string().optional(),
      message: z.string().optional(),
      detail: z.unknown().optional(),
    })
    .passthrough()
    .optional(),
});

export const WSMessageSchema = z.discriminatedUnion('type', [
  NodeEventSchema,
  CompleteSchema,
  HitlRequestSchema,
  PausedSchema,
  ResumedSchema,
  LayerStartSchema,
  TodoStartSchema,
  TodoCompleteSchema,
  ProgressSchema,
  HitlAckSchema,
  ConnectedSchema,
  PongSchema,
  ErrorMessageSchema,
]);

export type WSMessage = z.infer<typeof WSMessageSchema>;
export type NodeEvent = z.infer<typeof NodeEventSchema>;
export type Complete = z.infer<typeof CompleteSchema>;
export type HitlRequest = z.infer<typeof HitlRequestSchema>;
export type Paused = z.infer<typeof PausedSchema>;
export type Resumed = z.infer<typeof ResumedSchema>;
export type LayerStart = z.infer<typeof LayerStartSchema>;
export type TodoStart = z.infer<typeof TodoStartSchema>;
export type TodoComplete = z.infer<typeof TodoCompleteSchema>;
export type ProgressMsg = z.infer<typeof ProgressSchema>;
export type HitlAck = z.infer<typeof HitlAckSchema>;
export type ErrorMessage = z.infer<typeof ErrorMessageSchema>;

// (2026-06-12 정리 전환 Sprint) 폐기된 mock API 스키마 블록(~241줄: mockResponseSchema +
// Mock*RowSchema 12종) 삭제 — 2026-05-28 /api/mock 폐기 후 참조 0. 복원은 git 히스토리.
