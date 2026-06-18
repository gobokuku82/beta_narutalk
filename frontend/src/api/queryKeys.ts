/**
 * TanStack Query Key 규약 — 일관된 invalidation 위한 hierarchical key.
 *
 * spec: 61 §1.4
 */
export const queryKeys = {
  conversations: {
    all: ['conversations'] as const,
    list: () => [...queryKeys.conversations.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.conversations.all, 'detail', id] as const,
  },
  turns: {
    all: ['turns'] as const,
    list: (conversationId: string) => [...queryKeys.turns.all, 'list', conversationId] as const,
    detail: (id: string) => [...queryKeys.turns.all, 'detail', id] as const,
  },
  memory: {
    all: ['memory'] as const,
    byScope: (userId: string, scope: string) => [...queryKeys.memory.all, userId, scope] as const,
    workflowTemplates: (userId: string) =>
      [...queryKeys.memory.all, userId, 'workflow_template'] as const,
    detail: (id: string) => [...queryKeys.memory.all, 'detail', id] as const,
  },
  attachments: {
    list: (turnId: string) => ['attachments', turnId] as const,
  },
} as const;
