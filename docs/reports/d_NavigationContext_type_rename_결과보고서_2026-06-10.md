# (d) NavigationContext type 'portfolio' → 'system' rename — 결과보고서 (2026-06-10)

> 계획서: `docs/reports/d_NavigationContext_type_rename_계획서_2026-06-10.md`
> 결정: 사용자 = R1 (순수 rename + 사용자 1클릭 또는 localStorage 수동 reset). migration helper 제외 (legacy 호환 코드 누적 회피, `feedback_no_mixed_codebases` 정합).

## 1. 변경 요약

| 영역 | 변경 |
|---|---|
| `features/navigation/store.ts` | type `'portfolio' \| 'client'` → `'system' \| 'client'`. context literal × 4 (initial · setContext 분기 · setClient 분기 · onRehydrateStorage 분기) |
| `components/layout/TopBar.tsx` | CONTEXTS 배열 `value: 'portfolio'` → `'system'`. 코멘트 갱신 |
| 백엔드 | **0** (grep 결과 0건 — 백엔드 무관) |

**의도된 잔존**:
- tab id `'portfolio'` (`store.ts:35,80`) — `/portfolio` 라우트 매칭 페이지 id. context type 과 별개.
- docstring 자취 (`store.ts:13~15`) — 의도된 박제.

## 2. 검증

### 2.1 자동 검증

| # | 검증 | 결과 |
|---|---|---|
| A1 | TypeScript 컴파일 (변경 모듈) | ✅ navigation/store + TopBar 관련 에러 0건 |
| A2 | `pnpm audit:tabs` | ✅ 통과 (Sidebar/Router 정합) |
| A3 | grep `'portfolio'` (context 비교) | ✅ 0건 잔존 |

**외부 영역 잔존 실패** (이전 세션 사용자 명시 = 다른 곳 작업):
- `pnpm audit:tokens` FAIL — `ConversationsPage.tsx:154` `gap-1.5` (외부)
- `pnpm tsc` 3건 — `ConversationsPage.tsx:176,190,192` TS18048 (외부)

→ (d) 영향 0. 외부 영역 별도 작업 분리.

### 2.2 사용자 수동 검증 (남은 단계)

| # | 시나리오 | 액션 | 기대 |
|---|---|---|---|
| **M1** | 신규 사용자 | localStorage `navigation` key 비우고 `pnpm dev` | `state.context = 'system'`, SYSTEM_TABS 6 표시, TopBar "시스템" 활성 |
| **M2** | 기존 localStorage `'portfolio'` 잔존 (본인) | F12 → Console → `localStorage.removeItem('navigation')` → F5 | M1 과 동일 |
| **M3** | TopBar "클라이언트" 클릭 | — | `state.context = 'client'`, CLIENT_TABS 8 표시, `/dashboard` 이동 |
| **M4** | TopBar "시스템" 클릭 (역방향) | — | SYSTEM_TABS 6 표시, `/portfolio` 이동 |
| **M5** | 새로고침 (F5) | — | localStorage 상태 그대로 복원 |

→ 사용자 액션 = M2 한 번만 수행.

## 3. 위험 + 롤백

| 위험 | 완화 |
|---|---|
| 기존 사용자 localStorage 옛 `'portfolio'` 잔존 → 첫 진입 Sidebar mismatch | 1클릭 또는 `localStorage.removeItem('navigation')` 즉시 복구. 본인 1명. |
| 다른 모듈 `'portfolio'` 문자열 비교 잔존 | grep 으로 전수 확인 완료. context 비교 0건. |

**롤백 방안**: 단일 commit `git revert` 한 번.

## 4. 자취

- **2026-06-10**: 본 결과보고서. R1 적용 완료. M2 사용자 액션 대기.
