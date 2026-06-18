# ADR-005: Sprint 12 Legacy `_run_agent` 경로 처리 정책

## Status

Accepted (2026-04-27)

## Context

`backend/api_v2/ws_agent.py` 에는 두 개의 완전히 다른 쿼리 처리 경로가 공존:

| 경로 | 함수 | 라인 수 | 사용 여부 |
|------|------|--------|----------|
| Sprint 13 신경로 | `_graph_runner_with_resume` | ~260 | ✅ 현 대시보드 사용 |
| Sprint 12 legacy | `_run_agent` | **~350** | ❌ 사용 안 함 |

**검증** (2026-04-23 grep):
- `dashboard/index.html`: `type:"start"` 송신 0건
- `dashboard/index_legacy.html`: `type:"start"` 1건 (아카이브 only)

즉 `_run_agent` 는 **완전한 dead code** 임. Sprint 12 가 Sprint 13 query 경로로 전환된 후 legacy 경로는 호출되지 않음.

`21_WEBSOCKET_PROTOCOL.md` §8 에 명시:
> Sprint 14 regression 완료까지 유지. 신규 개발은 `query` 사용.

`type:"start"` 분기는 `stream_endpoint` 에 그대로 남아있어 **임의의 외부 클라이언트가 legacy 경로 호출 가능** 한 상태. 이론적 보안/일관성 위험은 작지만 코드 가독성 + 미래 개발자 혼선 비용은 누적.

A3 Phase 5 작업 중 [`docs/_claude/sprint14_a3_missed_points.md`](../../_claude/sprint14_a3_missed_points.md) §A 에서 이 처리 방향이 결정 누락 상태였음을 발견. 사용자 결정: **옵션 A — 이번 A3 에 건드리지 않고 별도 정리 Sprint 에서 삭제**.

## Decision

`_run_agent` 와 `type:"start"` 분기를 **현 시점에는 보존**, **별도 cleanup sprint 에서 일괄 삭제** 한다.

### 즉시 (Sprint 14 A3) — 현상 유지

- `_run_agent` 함수 유지
- `stream_endpoint` 의 `elif msg_type == "start":` 분기 유지
- `dashboard/index_legacy.html` 유지

이번에 건드리지 않는 이유:
- A3 scope (편집 경로 통합) 와 직교
- 사용자 §5 "크게 생각할 것 없음" 원칙 준수
- 기능적 해악 없음 (dead code)

### 단기 (A3 브라우저 검증 완료 후 — Sprint 14 마무리 시점) — 경고 추가

- `stream_endpoint` 의 `elif msg_type == "start":` 진입 시 `logger.warning("deprecated path: type=start, will be removed in Sprint 15+")` 추가
- 21_WEBSOCKET_PROTOCOL §8 의 "Sprint 14 regression 완료 후 제거" 표현을 **"Sprint 15 cleanup sprint 제거 예정"** 으로 명확화

### 중기 (Sprint 15 cleanup sprint) — 일괄 삭제

다음을 한 커밋으로 삭제:
- `ws_agent.py::_run_agent` 함수 전체 (~350줄)
- `stream_endpoint` 의 `elif msg_type == "start":` 분기
- `dashboard/index_legacy.html` 파일
- `21_WEBSOCKET_PROTOCOL` 의 legacy 관련 절 정리

검증:
- 삭제 전 grep 으로 `_run_agent` / `type:"start"` 잔존 참조 0건 확인
- regression 통과 (Sprint 13 + 14 모든 테스트)

### 추가 — `backend/app/dream_agent/_old_v1/` 폴더 정책 (2026-04-27 보강)

코드 리뷰 중 `backend/app/dream_agent/_old_v1/` 폴더 발견:

- 33개 파일 — Sprint 13 이전 v1 구현 (cognitive / planning / execution / response / llm_manager)
- import 참조 0건 (`grep -rn "_old_v1" backend --include="*.py"` 결과 없음)
- 완전한 dead code 이지만 **참고 자료** 로서 가치는 있음 (사용자 결정 — "구지 안 봐도 되지만 필요하면 참고하는 폴더")

**정책**:
- **현 시점**: 그대로 유지 (참고용)
- **삭제 시점**: 별도 결정. POC 마무리 (Sprint 17+) 또는 사용자 명시 결정 시
- **import 금지**: 실제 production 코드는 `_old_v1` 에서 import 하지 않음. 유지보수 대상 아님
- **TODO 주석 무시**: `_old_v1/cognitive/cognitive_node.py:71, 233` 등 TODO 는 v2 에 영향 없음

**ADR-005 의 cleanup sprint (Sprint 15) 범위에는 포함하지 않음** — `_old_v1/` 는 사용자 결정에 따라 명시 삭제 시까지 보존.

## Consequences

### 좋은 점 (현 정책)

- **A3 scope 보호**: 통합 작업과 cleanup 분리 — 한 PR 의 책임 단일
- **위험 분산**: legacy 삭제로 인한 회귀 발생 시 책임 명확
- **사용자 §5 부합**: "크게 생각할 것 없음" 원칙 — 즉시 삭제 욕구 억제

### 나쁜 점 / 비용

- **dead code 잔류**: 350줄 잡음. 새 개발자 혼선 가능
- **삭제 일정 미확정**: "Sprint 15+" 라는 모호함. ADR-006 등으로 cleanup sprint 자체를 명시 필요

### 위험

- **잊혀짐 위험**: cleanup sprint 자체가 안 잡히면 무기한 잔류. 본 ADR 이 reminder 역할
- **legacy 우연한 사용**: 누군가 dashboard/index_legacy.html 을 실수로 배포에 포함하면 사용됨 — Sprint 15 cleanup 시점에 같이 삭제

## Alternatives Considered

### Alt-1. 즉시 삭제 (옵션 B)

이번 A3 와 함께 350줄 삭제.

- 장점: 코드 350줄 즉시 깔끔. 사용자 §1 "통로 하나" 인식과 코드 일치
- 단점: A3 scope 초과. PR 책임 분산. 사용자 §5 "크게 생각할 것 없음" 위배
- **불채택**

### Alt-2. 무기한 보존

"언제 지울지 결정 안 함, 그냥 둠".

- 장점: 결정 부담 없음
- 단점: dead code 영구 잔류. 본 ADR 의 존재 이유 (결정 누락 방지) 와 모순
- **불채택**

### Alt-3. Feature flag 로 비활성화 (런타임 차단)

`stream_endpoint` 에서 `if msg_type == "start" and not settings.LEGACY_ENABLED: return error`.

- 장점: 코드 보존하면서 런타임 차단
- 단점: 코드는 여전히 잔류. flag 자체가 새 부담
- **불채택** — Alt-3 가 의미 있으려면 외부에 legacy 경로 사용하는 클라이언트가 있을 때. 본 케이스는 그런 클라 없음

## Related

- **발견 문서**: [`docs/_claude/sprint14_a3_missed_points.md`](../../_claude/sprint14_a3_missed_points.md) §A
- **Walkthrough**: [`docs/walkthroughs/sprint14_a3_walkthrough.md`](../../walkthroughs/sprint14_a3_walkthrough.md) — `_run_agent` 미언급 (의도적, 신경로만 설명)
- **WebSocket 계약**: `21_WEBSOCKET_PROTOCOL_v1.5.md` §8 (legacy 정책)
- **삭제 대상 코드**:
  - `backend/api_v2/ws_agent.py::_run_agent` (L676~1026)
  - `backend/api_v2/ws_agent.py::stream_endpoint` 의 `elif msg_type == "start":` 분기
  - `dashboard/index_legacy.html`
- **관련 ADR**: ADR-001 (Phase 5 변경은 신경로만 영향)

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-27 | 초안 + Accepted. 즉시 (현상 유지) / 단기 (경고 추가) / 중기 (Sprint 15 일괄 삭제) 3단계 정책 명시 |
| 2026-04-27 | `_old_v1/` 폴더 정책 추가 — 참고용 보존, 삭제는 별도 결정 (Sprint 15 cleanup 범위 X) |
