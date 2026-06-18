# Session Compact Recovery — 2026-06-15 (ERD 완성·시각화 + normalized tool 피봇 계획 + DB 개명)

> **다음 세션 첫 행동**: ① 본 문서 → ② **[normalized 피봇 계획서](../_claude/plans/normalized_tool_pivot_계획서_2026-06-15.md)**(진행 중 핵심) → ③ [ERD/INDEX.md](../agent_specs/ERD/INDEX.md). 코드 상태: `main e041a00`.
> **작업방식(필독)**: memory `feedback_anti_sycophancy_evidence_labeling`(✓검증/⚠추측·file:line)·`feedback_plan_intent_before_code`·`feedback_no_mixed_codebases`(v1/v2 격리→전환)·`project_erd_new_world_clean_build`·`feedback_no_claude_commit_attribution`.
> 표기: ✓이번 세션 확인 · ⚠주의.

---

## §1 현상황 — 두 스트림

직전 compact([2026-06-14 데이터구조재설계](session_compact_recovery_2026-06-14_데이터구조재설계.md))에서 이어, 이번 세션은 **두 흐름**:

**A. ERD/canonical 세계 완성 + 시각화 (✅ 완료·커밋됨)** — World A를 raw 수준으로 끌어올리고 인터랙티브 HTML로 시각화.
**B. ★ normalized tool production 피봇 계획 (⏳ 계획 단계 — 구현 보류, 오너 확정 대기)** — data_pilot(World A) 레퍼런스로 production normalization을 contract-driven 피봇. **이게 다음 세션 핵심.**

---

## §2 산출물 지도 (✓ 커밋 실측, `3748da0`→`e041a00` 12커밋)

### A 스트림 — ERD/검증 (전부 커밋)
| 커밋 | 내용 |
|---|---|
| `3748da0` | **P1 검증 게이트** — coverage.py(13→18/44 materialized)·dict_gate.py(사전↔raw↔contract diff)·gate.py·verify_outputs WARN. backend/app/data_pilot_project/ |
| `4cf9d39` | raw ERD 추출 충실성 검증(verify_raw_erd) + 타입 오분류 10(금액→date) 정정 + campaign_id 17→18 |
| `a8ec629` | World-B 오염 감사(16파일 적대검증 워크플로) → restart 불필·구조오염 0 + S코드 라벨 청소 17 |
| `a5625f6` | World A 완성도 — 발행 .dbml·description 공란 4·미구현 metric(ctr/cpc/cpm/cvr/tacos) 구현. coverage 13→18·metric 3→8 |
| `bdab40c` | normalized 점검 — meta currency 값변환 연결(거짓라벨 정정) + raw→normalized 변환맵 |
| `e5589e5`·`9581735` | normalized ERD 2종: erd_octorad_normalized_v1.0.dbml(결과) + erd_octorad_raw_normalized_v1.0.dbml(raw 전체컬럼↔canonical 매칭 Ref 40) |
| `02225fc`·`929bca8`·`7b47c92`·`b2e91b9` | **★인터랙티브 흐름 HTML**(erd_octorad_flow.html): 3단(raw 19테이블/normalized measure16·dim15·time2/computed11) · 클릭=연결체인 · hover=desc+값변환+실측값(mer 6.53) · 드래그 · ⓘ메타데이터 · 검색 |
| `e041a00` | **DB 개명** dream_agent/octorad → octormate_system (config+setup) |

생성 도구(gitignore): `docs/_claude/data/erd/` — verify_raw_erd·gen_normalized_erd·gen_erd_html·gen_layer_docs.

### B 스트림 — 계획서 (gitignore, 미커밋 — 계획이라)
**[docs/_claude/plans/normalized_tool_pivot_계획서_2026-06-15.md](../_claude/plans/normalized_tool_pivot_계획서_2026-06-15.md)** (v1~v4). 구조분석(툴92·파이프라인·데이터계층·에이전트·2DB, file:line) + D1~D5 + 마이그레이션 임팩트 + DB 재설계 + 로드맵 P0~P5 + 검증전략.

---

## §3 확정 결정 (오너)

| 결정 | 값 |
|---|---|
| **D1** 피봇 범위 | ✅ measure 16 + dimension 15 + time 2 **전체** canonical translator |
| **D2** production 연결 | 기존 툴 분석 후 부분교체+점진수정 (임팩트: ~8 REPLACE / ~23 MODIFY / ~61 KEEP) |
| **D3** contract 위치 | (권장) docs/agent_specs/ERD → backend 코드 config 이전 — ⚠미최종확인 |
| **D5** 데이터레이어 | ✅ **`normalized` 레이어 신설**(cleaned 아님). Workspace Layer `raw/normalized/computed`. 물리=하이브리드(raw blob + canonical 관계형 테이블) |
| **DB 개명** | ✅ 시스템 DB = **`octormate_system`**(데이터 = `octormate_data` 대칭). .env 이미 octormate_system, 코드 기본값만 정합(e041a00) |
| **DB 리셋** | octormate_system(checkpoint) 보존 / octormate_data raw 보존 + 옛 cleaned/computed 삭제 → ⚠삭제 타이밍 미확정(검증 후 안전삭제 권장) |
| World A 완성 | ✅ measure/dim/time ERD(md+dbml)·description·metric 8/11·HTML 시각화 |

---

## §4 검증된 사실 (✓ 직독/실행)

- **2 Postgres DB**: `octormate_system`(LangGraph checkpoint `checkpoints`/`checkpoint_blobs`/`checkpoint_writes` + 대화메모리) / `octormate_data`(`{client}._workspace` raw·cleaned·computed **JSONB blob**, schema-per-client). ⚠ canonical 관계형 구조 **없음** — 전부 blob.
- **normalization 두 현실**: `ad_cost_helper`(실 clumi 5채널 cost=18,306,923·하드코딩·**load-bearing**: roas_overall·cac_overall·promotion_roas·channel_cac_compare·dashboard1) vs `format_normalizer`(한글 ads.v1·폐기 collector·**dormant**: 테스트+planning catalog만).
- **World A(data_pilot)** = contract+conversion_config 구동 채널 translator+transforms → canonical+lineage. gate 8/8·12/12·coverage 18/44.
- ERD HTML 흐름: raw 567컬럼 중 77 연결(measure40·dim29·time8) + computed nc19. 나머지 회색 = 진짜 미사용(API메타·중첩).

---

## §5 ★ 정직 경고 / 주의 (다음 세션 과신 금지)

1. **B 스트림 = 계획만, 구현 0.** 코드 미작성. "계획 완벽+승인 전 구현 보류"(오너). 다음 세션이 바로 코드 짜면 안 됨.
2. **D2 임팩트 수치(~8/23/61)는 에이전트 근사** — 일부 분류 과함(grade/kst/utm REPLACE 단정). P0 상세설계서 확정.
3. **DB 재설계 = 미착수.** octormate_data는 여전히 blob. 관계형 전환은 P1+.
4. **삭제 타이밍 미확정** — 옛 cleaned/computed를 새 normalized 경로 검증 전 삭제 시 대시보드 공백(캐시 서빙 중).
5. format_normalizer 폐기·지표 23 점진전환·D3 = ⚠**오너 최종 확인 안 받음**("일단 계획 만들고").

---

## §6 남은 일 / 다음 (오너 확정 → P0)

**계획 완성 직전 확인 3건** (계획서 §16·§19):
1. 시스템 DB명 `octormate_system` 수락? (코드 e041a00 반영됨)
2. D3 contract→코드 · D4 format_normalizer 폐기 · 지표 23 점진전환 — 권장대로?
3. 삭제 타이밍 = 검증 후 안전삭제(P4) vs 지금 클린리셋?

**확정 후 → P0 상세설계**: ① 최종 물리 ERD(octormate_data: raw blob + normalized/computed 관계형 DDL) ② Workspace Layer `raw/normalized/computed` 코드변경 ③ tool별 변경표(REPLACE/MODIFY) ④ DB 리셋·재구축 스크립트 → 최종 승인 → **구현(P1~P5)**. 회귀 오라클 = data_pilot gate.

---

## §7 관련 memory
`feedback_anti_sycophancy_evidence_labeling`·`feedback_plan_intent_before_code`·`feedback_no_mixed_codebases`(v1/v2)·`project_erd_new_world_clean_build`(World A 깨끗·World B 참고)·`project_tool_data_agent_separation`·`project_intended_layer_architecture`·`project_data_viz_work_division`(계산=오너영역)·`feedback_no_claude_commit_attribution`.
