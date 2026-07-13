# api/ — 백엔드 통신 계층

진실 소스 = backend ([21 WS](../../../docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md) / [20 REST](../../../docs/agent_specs/20_INTERFACE_CONTRACT_v1.1.md) / [22 Error](../../../docs/agent_specs/22_error_codes_v1.1.md))
spec: [63 Frontend Backend Contract](../../../docs/agent_specs/63_frontend_backend_contract_v1.0.md)

## 파일 가이드

| 파일 | 역할 |
|------|------|
| `rest.ts` | fetch wrapper + BackendError 통합 |
| `ws.ts` | WebSocket 2 채널 클라이언트 (agent + hitl) + 자동 재연결 |
| `schemas.ts` | zod schema — Plan/Memory/WorkflowTemplate + WS 메시지 |
| `queryKeys.ts` | TanStack Query Key 규약 |
| `errors.ts` | `BackendError` 클래스 |
| `errorMessages.ts` | error code → 한국어 친화 메시지 |
| `hooks/` | TanStack Query hooks (useConversations / useTurns / useMemory / ...) |

## Drift 방지

백엔드 변경 시 본 폴더 동기화 (PR 체크리스트):

- [ ] `21_WEBSOCKET_PROTOCOL.md` 변경 → `schemas.ts` (WS 메시지) update
- [ ] `20_INTERFACE_CONTRACT.md` 변경 → `hooks/` (REST endpoint) update
- [ ] `22_error_codes.py` 변경 → `errorMessages.ts` update
- [ ] `planner.PlannedTodo` / `Plan` 변경 → `schemas.ts` (Plan) update
- [ ] `memory_entries.type` 추가 → `schemas.ts` (MemoryTypeSchema) update

→ Sprint 1 에서 `DC-FE-1~5` (frontend Doc-Code Contract Test) 도입 검토.

## 사용 예

### REST
```typescript
import { rest } from '@/api/rest';
import { ConversationListSchema } from '@/api/schemas';

const data = await rest.get('/api/conversations');
const conversations = ConversationListSchema.parse(data); // zod 검증
```

### WebSocket
```typescript
import { connectAgent, connectHitl, sendHitlMessage } from '@/api/ws';

connectAgent((msg) => {
  // msg 는 이미 zod 검증됨 (WSMessageSchema)
  // store action 호출
});
```

### TanStack Query Hook
```typescript
// hooks/useConversations.ts
import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../queryKeys';
import { rest } from '../rest';

export function useConversations() {
  return useQuery({
    queryKey: queryKeys.conversations.list(),
    queryFn: () => rest.get('/api/conversations'),
    staleTime: 30 * 1000,
  });
}
```
