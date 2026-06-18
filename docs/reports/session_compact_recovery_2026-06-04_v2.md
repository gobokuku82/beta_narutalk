# Session Compact Recovery v2 — PMAL B1 구현 (2026-06-04 오후)

> v1(`session_compact_recovery_2026-06-04.md`, 오전)은 F2 *진단* 시점. 본 **v2 = F2 해결 + PMAL B1 (W1~W3) 구현 완료** 시점. **다음 세션 1순위 읽기.**
> **한 줄**: 시작점 불일치(쪽지=cognitive 출력에 *주제 칸*이 없어 planning이 추측)를 PMAL `intent`로 고쳐 **F2 구조적 해결 + end-to-end 작동**. 남은 핵심 = 조합형 분석(diagnose=M3)은 다음 phase.

---

## §1 이번 세션 9 커밋
| 커밋 | 내용 |
|---|---|
| `9a2371a` | F2 subject-coherence 게이트 (리뷰-데이터 누출 차단) |
| `495d98e` | F2 게이트 보강 — 결정론 post-filter + 단위테스트 11 |
| `32d8241` | Phase A — cognitive 회사-무관 + `clients/{client}.yaml` 주입 (신규 회사 = yaml 1장) |
| `7151cb7` | Q1 provenance — client 프로필 fail-fast (silent fallback 제거) |
| `646c56e` | A4-lite — planning/cognitive 블루밍 잔재 이름 중립화 |
| `fe504d5` | **spec 37** agent_specs/37_agent_language_pmal — PMAL 계약 (committed) |
| `16ca4f5` | **W1** Intent 스키마 (쪽지의 주제 칸) — TDD 7 |
| `504e502` | **W2** intent→tasks shim (순수함수) — TDD 8 |
| `35da041` | **W3** cognitive intent emit + shim 연결 — **F2 구조적 해결** |
| `8d098e1` | agent_pool by-name tool 해석 fallback (planning agent 오추측 robust) |

## §2 현 상태 — B1 작동 (검증됨)
- cognitive가 `intent{operation × domain(SET) × metric(open) × dimensions}` 방출. **주제(domain)가 쪽지 1급 칸.**
- **F2 구조적 해결**: "왜 매출?" → `operation=diagnose·domain=[revenue]` → shim 빈 tasks → 정직 (게이트 사후패치 *아님*, 쪽지의 domain이 구조로 잡음 = criteria §4.1 목표).
- 일반화 **10/10** (anti-tautological, `_scratch/agent_generalization_test.py`). end-to-end 실행 **실패 0**.
- 실제 응답 (`_scratch/response_check.py`): 매출 **119,539,660원** / ROAS **6.53** / 리뷰 **긍정 58.3%** — 코어 데이터분석 end-to-end 작동.
- `intent_shim.py`: domain∋reviews→sentiment(최우선) / diagnose·forecast·attribute→[](F2 재유발 방지·degrade는 planning) / 그 외→metric_calculation.

## §3 B1 닫기 전 미해결 (작음, 1개)
- **diagnose 응답이 거짓 이유를 말함**: "데이터(orders 매출)가 제공되지 않아"(거짓 — 매출 119M 잘 계산됨) + 내부용어("execution_summary") 누출. 진짜 이유는 "**인과 분석 기능 미구현**, 매출 추이는 보여줄 수 있음". → 빈-plan→response 경로의 정직 fix (M3 빌드 아님, 한 줄 정직 교정).

## §4 핵심 결정/기준 (박제)
- **`docs/_claude/4layer_system/criteria_map_260604_v1.md`** (기준 지도): core 4 (C1 쪽지3원칙 NL-free·도메인complete·카탈로그free / C2 작동우선 / C3 정직degrade / C4 provenance) + layer 기준(시작-과정-결과-됐다/안됐다). component 세부 기준은 *흔들릴 때만*.
- **검증 ≠ 품질** (사용자 정정): 작동·품질 먼저, 검증은 보조(필요시). 땜질로 품질 대체 금지. B1(작동)/B2(검증) 단계.
- **`pmal_b_baseline_260604_v1.md` / `pmal_b_impl_260604_v1.md`** (기준/구현 계획서, 검증 통과·정제, _claude). 구 cognitive_subplan/planning_subplan 대체.
- **시작점 불일치 진단** (감사 `wf_e16672b0`, 적대검증 HIGH 4 통과): SQ v0에 WHAT(주제) 1급 칸 없음 + source축(charter 위반) + (metric,dim)→tool lookup 부재 + 인과 tool 부재. PMAL이 이를 고침.

## §5 다음 (우선순위)
1. **B1 닫기**: §3 diagnose 응답 정직 fix (거짓 이유 → 진짜 이유). 작음. TDD.
2. **(연기) W4 source 제거 → B2**: F2 풀려서 안 급함. #1 지뢰 = "source 그냥 빼면 역F2(전 쿼리 리뷰)" → collector 재배선과 atomic 必.
3. **★ 조합형 분석 (diagnose = M3 skeleton+fill) = 다음 phase 중심** (compose 3-mode 분석 `wf_ec7ef3ef`):
   - 사용자 3-mode(scratch/정의workflow/skeleton+fill) = "조립"축만 봄. **진짜 난제 = 종합(델타→서사) + 정직성(상관≠인과)** — 3-mode 밖.
   - M3(skeleton+fill)이 답 (검증 holds). 3 mode = 배타 아닌 진행단계(ADR-023 5주체: M1 Agent→M3 Maker-Agent→M2 Pipeline).
   - 단: (a) (metric,dim)→tool lookup(Phase B, 현재 0) 선결 (b) **진짜 인과 불가 — 델타분해(상관)+정직 고지뿐** (c) factor-map 도메인지식 출처 미해결([[project_no_user_domain_assumption]] 충돌) (d) **ADR-024 skill 게이트** — M3 1차는 "planning 내부 결정적 골격"으로 한정(skill 저장/자동화 X). 별도 설계+검증-재검증 必.
4. **(preview) HITL clarification**: 모호하면 되묻기 = 미배선 (cognitive 모호 감지하나 interrupt 루프 없음). plan_review HITL은 있음(`require_review=True` → tool 조합 검수). 추후 (사용자 "예고편").

## §6 사용자 컨텍스트
- 초보자·비전공자. "작동하는 에이전트" 우선. **단일 전문가 권장** 원함(옵션 나열 X).
- **동어반복 검증 거부** — 안 가르친 표현(일반화)으로 판정. **TDD RED→GREEN** 선호 (구현 전 테스트 OK).
- **무조건 동의 금지, 객관 평가 요구.** 검증-재검증(독립 에이전트/workflow) 고집 — 매번 구현-파괴 버그 잡음.
- 깊이 못 따라가면 말함 → 속도↓·쉬운 설명. **계획서/검증만 쌓지 말 것** (구현·작동 우선).
- 메모리 박제 자제(docs로). bypassPermissions 전역.

## §7 한 문장 재개
> PMAL B1(W1~W3)로 **F2 구조적 해결 + end-to-end 작동**(매출 119M·ROAS 6.53·리뷰 58% 실측). 다음 = ① **B1 닫기**(diagnose 응답 거짓이유→진짜이유, 작은 정직 fix) ② **조합형 분석(diagnose=M3 skeleton+fill)을 다음 phase로 설계**(Phase B (metric,dim)→tool lookup 선결 + ADR-024 게이트, 진짜 인과는 불가·정직 고지만). 사용자=초보·작동우선·동어반복거부·객관평가요구·TDD·검증과잉금지.
