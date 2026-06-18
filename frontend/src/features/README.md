# features/ — 도메인 모듈 (colocation)

각 폴더 = 하나의 도메인. **store + UI 컴포넌트 + hooks + types 가 한 폴더에**.

## 폴더 가이드

| 폴더 | 도메인 | Sprint | spec |
|------|--------|--------|------|
| `agent/` | 채팅 / 노드 이벤트 (WS 수신) | 2 | 61 §1.2 |
| `hitl/` | HITL / Plan review / Clarification | 2, 15-P1 | 61 §1.2 / ADR-015 |
| `workflow/` ⭐ | React Flow Canvas | 2 (W1) → 7+ (W4) | 62 |
| `conversations/` | 대화 목록 / sidebar | 4 (E2-5) | 35 |
| `attachments/` | 첨부 갤러리 | 4 | — |
| `memory/` | Memory View / Template Library | 5 | 35 / 62 (W3) |
| `session/` | WS 연결 / turn 상태 | 1 | 61 §1.2 |
| `settings/` | 테마 / 사용자 preference | 0 | 61 §4.5 |
| `auth/` | 인증 (Sprint 6+) | 6+ | 61 §1.2 |

## 컨벤션

각 features/{domain}/ 안에:

```
{domain}/
├─ store.ts                 # Zustand store (use{Domain}) — spec 61 §1.2
├─ {Component1}.tsx         # 도메인 UI 컴포넌트
├─ {Component2}.tsx
├─ hooks.ts                 # 커스텀 hooks (있을 경우)
├─ types.ts                 # 도메인 전용 타입
└─ index.ts                 # public API (선택적 barrel)
```

## 도메인 간 의존 금지

- features/{A} 가 features/{B} 를 직접 import 하지 않음
- 공유 필요 시 → api/ 또는 lib/ 또는 components/ui 로 옮김
- 도메인 간 통신 = WS 메시지 (백엔드 경유) 또는 props 또는 라우트 navigation

## 새 도메인 추가 시

1. `features/{name}/` 생성
2. `store.ts` 작성 — Zustand pattern (spec 61 §1.2)
3. UI 컴포넌트 작성
4. `routes/` 에서 import (필요 시)
5. 본 README 갱신

## 실험·버전 페이지 컨벤션 (`[tag]` 패턴)

데이터 트랙·디자인 트랙 진행 중에 *공존*해야 하는 테스트/버전 페이지 (예: `dashboard_v2/`, `agent_observability/`, `data_console/`) 는 **3곳만 손대면 추가/삭제** 가능하도록 표준화. 폐기 시 dead code 0건이 목표.

### 추가 (3곳)
1. `features/{name}_v{n}/` 폴더 + 페이지 컴포넌트 + **README** (삭제 체크리스트)
2. `routes/router.tsx` — `[tag]` 주석 + import + `createRoute` + `addChildren` 항목
3. `features/navigation/store.ts` — `CLIENT_TABS` 또는 `PORTFOLIO_TABS` 의 한 줄

### 삭제 / 승격 (역순)
1. `grep -rn '\[tag\]' src/` 으로 모든 흔적 한 번에 식별
2. router·store 항목 제거
3. 폴더 `rm -rf`
4. (v1→v2 승격 시) v1 폴더·route·tab 제거 + v2 폴더 rename + path 변경

### 컨벤션
- **폴더명**: `{feature}_v{n}` (underscore) 또는 `{feature}_{experiment}` (예: `agent_observability`)
- **태그**: `[{feature}-v{n}]` 또는 그룹 `[v{n}-pages]` (router 와 README 일치)
- **사이드바 group**: 같은 세대 같은 group (`'분석 v2'`, `'시스템'` 등)
- **공유 자산 의존 금지**: 다른 버전 폴더에서 직접 import ✗. 공유는 `components/`·`lib/` 로 승격 후

→ 메모리 룰: *v1/v2 섞임 금지 — 점진 추가 후 전환 Sprint*.
