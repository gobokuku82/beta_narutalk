# POC Legacy Documents

> **Status**: 이력 보존 (archive) — Sprint 13 Integration 이전 설계
> 이동일: 2026-04-21

## 폴더 목적

POC 초기 설계 의도 보존. Sprint 13 Integration 이후 구조를 반영하지 않으므로 **실제 개발 참조로는 사용 금지**.

## 파일 목록 및 대체 문서

| POC 문서 | 역할 | Sprint 13+ 대체 |
|----------|------|----------------|
| `DATA_MODELS_poc.md` | Pydantic 모델 / Core Enum / Agent·Tool 정의 | `DATA_MODELS_v1.0.md` (격상 + Sprint 10~13 반영) |
| `INTERFACE_CONTRACT_poc.md` | REST API + Layer Contract | `INTERFACE_CONTRACT_v1.0.md` (Sprint 15 REST 확장 placeholder 포함) |
| `WEBSOCKET_PROTOCOL_poc.md` | WebSocket 프로토콜 (`ws/stream` + `ws/hitl`) | `WEBSOCKET_PROTOCOL_v1.0.md` (현재 `/ws/agent` + `/ws/hitl` + Sprint 13 이벤트) |

## 주요 차이 (왜 대체됐나)

- **엔드포인트 이름 변경**: `ws/stream` → `/ws/agent` (Sprint 12)
- **Session 식별 체계**: 단일 `session_id` → `user_id`/`conversation_id`/`turn_id` 분리 (Sprint 13)
- **이벤트 포맷**: `layer_start`/`layer_complete` → `node_event` (Sprint 13 I10)
- **WS 멀티플렉싱**: 세션당 1 WS → `ConnectionManager` user_id fan-out (Sprint 13 T1)
- **HITL Signal**: `Event.wait/set` → `asyncio.Queue` FIFO (Sprint 13 I7)
- **Layer Guard**: 없음 → `layer_guard.py` + JSONL 로그 (Sprint 13 I11-a)

## 정리 계획

- **Sprint 15+**: 전면 재검토 — 완전 삭제 또는 현 문서로 통합
- 당분간 **읽기 전용 아카이브** 상태로 유지

---

*참조: `docs/_claude/checkpointer/sprint13_i11_i12_plan.md` §4.2.2*
