/**
 * 사용자 친화 에러 메시지 — backend error code → 한국어 안내.
 *
 * 진실 소스: backend/api_v2/error_codes.py
 * spec: 22_error_codes_v1.1.md / 63 §7
 *
 * Drift 방지: 백엔드 error_codes.py 추가 시 본 파일도 함께 update (PR 체크리스트).
 */
export const ErrorCodeMessages: Record<string, string> = {
  INVALID_MESSAGE: '⚠️ 잘못된 메시지 형식입니다.',
  TODO_EDIT_NOT_PAUSED: '⚠️ 편집하려면 일시정지 상태가 필요합니다.',
  INVALID_DAG: '⚠️ 작업 의존 관계에 오류가 있습니다.',
  NL_INTENT_UNCLEAR: '⚠️ 어떤 작업을 원하시는지 이해하지 못했습니다. 다시 시도해주세요.',
  PLAN_REQUEST_NONE: '⚠️ 처리할 요청을 찾을 수 없습니다.',
  TURN_NOT_ACTIVE: '⚠️ 새로 시작해주세요. 이전 작업이 종료되었습니다.',
  SESSION_NOT_FOUND: '⚠️ 세션을 찾을 수 없습니다.',
  LAYER_GUARD_FATAL: '⚠️ 내부 처리 오류가 발생했습니다.',
  HITL_TIMEOUT: '⏱ 응답 시간이 초과되어 자동 종료되었습니다.',
  LLM_UNAVAILABLE: '🔌 AI 서비스가 일시적으로 중단되었습니다. 잠시 후 다시 시도해주세요.',
  INTERNAL_ERROR: '⚠️ 서버 오류가 발생했습니다.',
};

export function getErrorMessage(code: string | undefined, fallback?: string): string {
  if (!code) return fallback ?? '⚠️ 알 수 없는 오류';
  return ErrorCodeMessages[code] ?? fallback ?? `⚠️ 알 수 없는 오류 (${code})`;
}
