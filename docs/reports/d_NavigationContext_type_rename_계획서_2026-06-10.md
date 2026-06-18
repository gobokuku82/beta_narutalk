# (d) NavigationContext type 'portfolio' → 'system' rename — 계획서 (2026-06-10)

> 결정 후보 (d) 의 별도 계획서. 사용자 지적 "d가 문제" + "프론트 작업과 DB 작업 대조" 정합.

## 1. 의도

| 측면 | 내용 |
|---|---|
| 문제 | 코드 type `'portfolio'` + UI label "시스템" — **의미 drift** (개발자 헷갈림) |
| 변경 | `NavigationContext = 'portfolio' \| 'client'` → `'system' \| 'client'` |
| 효과 | 코드 ↔ UI 의미 일치. 미래 개발자 자취 추적 ↑ |

## 2. 영향 범위 — 프론트 + localStorage (DB 없음)

### 2.1 백엔드 / DB 영향 점검

```
grep -rnE "portfolio|navigation_context|NavigationContext" backend/app --include='*.py'
→ 0 건 (백엔드 의존성 없음)
```

→ **백엔드 작업 0**. (d) 는 순수 프론트엔드 + localStorage 작업.

### 2.2 프론트엔드 영향 (10 호출처)

| 파일 | 변경 | 줄 수 |
|---|---|---|
| `features/navigation/store.ts` | `NavigationContext` type · `'portfolio'` literal × 3 (context default·setContext·setClient·onRehydrateStorage) | 7 |
| `components/layout/TopBar.tsx` | `import NavigationContext` · `CONTEXTS` 배열의 value `'portfolio'` | 3 |

### 2.3 localStorage migration (위험 영역)

**현 상태**: zustand persist 가 localStorage `navigation` key 에 저장.
```json
{
  "state": {
    "context": "portfolio",  ← 이전 사용자 세션
    "selectedClientId": null,
    ...
  }
}
```

**rename 후**: 코드는 `'system'` 만 인식. 기존 `'portfolio'` 값 → type guard 실패 → 기본값 fallback → 사용자 첫 진입 상태로 강제 리셋.

**migration helper 필요**: localStorage 에서 `'portfolio'` 감지 시 `'system'` 으로 변환.

## 3. 실행 절차 — 4 단계

### Step 1 · migration helper 작성

`features/navigation/store.ts` 의 `persist` 옵션에 `migrate` 콜백 추가:

```ts
persist(
  (set) => ({ /* ... */ }),
  {
    name: 'navigation',
    version: 2,  // 신설 — 이전 version 1 (또는 undefined) 에서 migrate
    migrate: (persistedState: unknown, version: number) => {
      // version 0/1 (이전) 의 'portfolio' → version 2 의 'system'
      const state = persistedState as Record<string, unknown>;
      if (state.context === 'portfolio') {
        state.context = 'system';
      }
      return state;
    },
    partialize: (state) => ({ /* ... */ }),
    onRehydrateStorage: () => (state) => {
      if (state) {
        state.availableTabs =
          state.context === 'system' ? SYSTEM_TABS : CLIENT_TABS;
      }
    },
  },
)
```

→ migration 한 번만 실행, 이후 localStorage 가 `'system'` 으로 저장됨.

### Step 2 · type + 모든 호출처 일괄 rename

```ts
// store.ts
export type NavigationContext = 'system' | 'client';

// initial state
context: 'system',
availableTabs: SYSTEM_TABS,

// setContext
setContext: (ctx) =>
  set({
    context: ctx,
    availableTabs: ctx === 'system' ? SYSTEM_TABS : CLIENT_TABS,
  }),

// setClient
setClient: (id, name) =>
  set({
    selectedClientId: id,
    selectedClientName: name,
    context: id ? 'client' : 'system',
    availableTabs: id ? CLIENT_TABS : SYSTEM_TABS,
  }),
```

```tsx
// TopBar.tsx
const CONTEXTS: Array<{ value: NavigationContext; label: string; path: string }> = [
  { value: 'system', label: '시스템', path: '/portfolio' },
  { value: 'client', label: '클라이언트', path: '/dashboard' },
];
```

### Step 3 · 검증

#### 3.1 자동 검증 (CI 통과)

| # | 검증 | 명령 | Pass 조건 |
|---|---|---|---|
| A1 | TypeScript 컴파일 | `pnpm build` | exit 0, type literal 통일됐는가 (`'portfolio'` 잔존 0) |
| A2 | 디자인 토큰 + Sidebar/Router 정합 | `pnpm audit:all` | 모든 룰 통과 |
| A3 | 잔존 grep (정성) | `grep -rE "'portfolio'" frontend/src` | 0 건 또는 의도된 주석만 |

#### 3.2 수동 검증 — 5 시나리오 매칭 표

| # | 시나리오 | 사전 조건 (localStorage `navigation`) | 액션 | 기대 상태 (after) | 검증 방법 (DevTools) | Pass 조건 |
|---|---|---|---|---|---|---|
| **S1** | **신규 사용자** | (없음 / `{}`) | 첫 접속 (`/portfolio`) | `state.context = 'system'`, `availableTabs = SYSTEM_TABS`, sidebar SYSTEM 6 항목, TopBar 토글 = "시스템" 활성 | `localStorage.getItem('navigation')` → state.context 확인 / sidebar 항목 6 / TopBar label | context = `'system'` 정확, sidebar SYSTEM 6 표시 |
| **S2** | **기존 사용자 마이그레이션** | `{state: {context: 'portfolio', ...}, version: 1}` | 첫 접속 | migrate 콜백 발동 → `state.context = 'system'`, localStorage 새로 저장됨 (`version: 2`) | localStorage 비교 (before/after), `state.version` 2 | migrate 한 번만 실행, localStorage `'system'` 으로 변환 |
| **S3** | **토글 클릭 — system → client** | `{context: 'system'}` | TopBar "클라이언트" 클릭 | `state.context = 'client'`, `availableTabs = CLIENT_TABS`, sidebar 분석 6 + 에이전트 2 표시 | sidebar 항목 8 / `/dashboard` 이동 / TopBar "클라이언트" 활성 | 토글 즉시 반영, sidebar/navigate 정합 |
| **S4** | **토글 클릭 — client → system** | `{context: 'client'}` | TopBar "시스템" 클릭 | `state.context = 'system'`, SYSTEM_TABS 6 표시 | sidebar 항목 6 / `/portfolio` 이동 / TopBar "시스템" 활성 | 토글 역방향 정합 |
| **S5** | **클라이언트 드롭다운 선택** | `{context: 'system', selectedClientId: null}` | clumi 선택 (TopBar 드롭다운) | `state.context = 'client'` (자동 전환), `selectedClientId = 'clumi'`, CLIENT_TABS 표시 | sidebar 자동 갱신, TopBar "클라이언트" 자동 활성 | setClient 호출이 context 자동 전환 |
| **S6** | **새로고침 후 state 유지** | S3 후 상태 (`context: 'client'`) | F5 새로고침 | `state.context = 'client'` 유지, availableTabs = CLIENT_TABS rehydrate | onRehydrateStorage 콜백 작동 / sidebar 갱신 | localStorage state 그대로 복원 |

#### 3.3 회귀 검증 (이전 작업 영향)

| # | 검증 | Pass 조건 |
|---|---|---|
| R1 | Sidebar collapsed/expanded toggle (Phase 1, 2026-06-09) | `isSidebarExpanded` state 영향 없음 |
| R2 | 5 페이지 SYSTEM 이동 (commit `9a12c7a`) | SYSTEM_TABS 6 항목 정합 |
| R3 | Brand 워드마크 (`◈ OctorAD ·`) | TopBar 좌측 표시 영향 없음 |
| R4 | SideChatPanel onFullScreen 폐기 (commit `9a12c7a`) | 채팅 패널 정상 작동 |
| R5 | hitl/store 보존 (commit `c6c1bd9`) | useWebSocket / WorkflowPage 정상 |

#### 3.4 검증 절차 흐름

```
1. localStorage 초기화 (개발자 도구 → Application → Storage → Clear)
2. 시나리오 S1 수동 검증 → Pass 기록
3. localStorage 에 portfolio 값 주입 (이전 사용자 시뮬레이션)
   localStorage.setItem('navigation', JSON.stringify({
     state: { context: 'portfolio', selectedClientId: null, ..., currentTab: 'portfolio' },
     version: 1
   }))
4. 새로고침 → 시나리오 S2 (migrate) 검증
5. S3 → S4 → S5 → S6 순서 검증
6. R1~R5 회귀 확인
```

#### 3.5 Fail 시 대응

| Fail 시나리오 | 원인 후보 | 대응 |
|---|---|---|
| S2 migrate 작동 안 함 | `version` 설정 누락 또는 잘못된 비교 | migrate 콜백 단위 테스트 추가 후 재실행 |
| S3/S4 토글 후 sidebar 안 바뀜 | availableTabs 재계산 누락 | setContext 의 availableTabs 갱신 확인 |
| S5 드롭다운 선택해도 context 그대로 | setClient 의 context 분기 누락 | setClient 의 `context: id ? 'client' : 'system'` 확인 |
| S6 새로고침 후 state 리셋 | onRehydrateStorage 콜백 미작동 | persist 옵션 확인 |

### Step 4 · 자취 박제

- `spec_64 §6 자취` (2026-06-10 15 차)
- `routes/README.md` 자취 1 줄 추가
- 결과보고서 박제 (`docs/reports/d_NavigationContext_type_rename_결과보고서_2026-06-10.md`)

## 4. 위험 + 롤백 방안

| 위험 | 완화 |
|---|---|
| migration 콜백 버그 → 기존 사용자 세션 깨짐 | version 2 + migrate 함수 단위 테스트 작성 |
| zustand persist version 잘못 설정 → 무한 migration | version 명시 + 한 번만 실행 보장 |
| 다른 모듈에서 `'portfolio'` 문자열 비교 잔존 | grep 으로 전수 검색 + 일괄 변환 |

**롤백 방안** : 단일 commit 이라 `git revert` 한 번. migration version 도 1 로 다시 되돌리면 깨끗.

## 5. 작업량 + 합의 사항

| 단계 | 시간 |
|---|---|
| Step 1 migration helper | 10 분 |
| Step 2 rename | 10 분 |
| Step 3 검증 + 수동 시나리오 | 15 분 |
| Step 4 자취 + 결과보고서 | 10 분 |
| **총** | **45 분** |

## 6. 다음 step — 사용자 합의

- 본 계획서 그대로 진행? → "(d) 진행"
- 일부 수정 필요? → 알려주세요
- (d) 지금 진행 X, MVP 후로 미루기? → 다른 후보 진행

## 7. 자취

- **2026-06-10 (계획서)** : 본 문서. 적용 전 사용자 합의 대기.
