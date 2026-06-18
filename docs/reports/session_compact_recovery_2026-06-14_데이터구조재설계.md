# Session Compact Recovery — 2026-06-14 (데이터 구조 재설계 — raw→canonical 파이프라인)

> **다음 세션 첫 행동**: ① 본 문서 → ② [ERD/INDEX.md](../agent_specs/ERD/INDEX.md)(폴더 진입점·과설계 점검·로드맵·방법론) → ③ §6 다음에서 오너 선택.
> **작업 방식(필독)**: memory `feedback_anti_sycophancy_evidence_labeling` 자동 로드 — ✓검증/⚠추측 분리·근거 file:line. 코드 상태: main `6317322`, 검증 8/8·12/12 PASS(단 §5 경고).
> 표기: ✓이번 세션 코드/실행 확인 · ⚠미검증/주의.

---

## §1 현상황 — 이 스트림이 무엇이고 어디까지

직전 compact([session_compact_recovery_2026-06-13_데이터전달재설계](session_compact_recovery_2026-06-13_데이터전달재설계.md))는 "데이터 *전달* 재설계"였고, 이번 세션은 오너 지시로 **"데이터 *구조* 재설계"**(raw 데이터 → 표준 canonical 데이터)로 전환·집중했다.

**한 흐름 (전부 완료, 커밋됨)**:
```
raw ERD → 메타데이터(712컬럼) → 동의어분류 → 구현리서치 → 업계리서치(07)
  → 명명 confirm → canonical contract(SPEC) + conversion config
  → data_pilot(코드: raw→cleaned→computed) → materialize → 3-레이어 ERD/메타/desc + registry + crosswalk
  → 산출물 검증(독립 12/12 + 적대 4렌즈 28건) → P0 역반영 → 재검증
```
= **설계→코드→materialize→검증→수정 한 사이클 완주.** 전부 `docs/agent_specs/ERD/` + `backend/app/data_pilot_project/`.

---

## §2 산출물 지도 (✓ 실측 — 파일·커밋 존재 확인)

**ERD 폴더 = `docs/agent_specs/ERD/` (진입점 [INDEX.md](../agent_specs/ERD/INDEX.md))**:
| 파일 | 무엇 | 커밋 |
|---|---|---|
| erd_octorad_raw_v1.0.{md,dbml} | raw ERD 30파일/34테이블 (실파일 직독) | d3eb98d |
| octorad_raw_metadata_v0.1.{md,yaml} | raw 메타+desc 712컬럼(source/confidence) | e2149f3 |
| octorad_canonical_contract_v0.1.{yaml,md} | ★normalized/computed SPEC (16 measures·11 metrics·15 dim·2 time) | efd67e8·6aa3667 |
| octorad_conversion_config_v0.1.yaml | 값변환 규칙집(transform·환율·채널 quirk) | 766ad3f |
| normalize_canonical_naming_v0.1.md | canonical 명명(영문 snake·§1.5 이름+값 한쌍) | 5aa3c72·e2d6720 |
| erd_octorad_canonical_layers_v0.1.md | normalized/computed ERD/메타/desc (SPEC에서 생성) | 029ac48·6aa3667 |
| octorad_metric_registry_v0.1.md | 지표 registry(ROAS 일가족 단일권위) | 029ac48 |
| octorad_campaign_crosswalk_v0.1.md | campaign_id 채널 매핑(C5) | 029ac48 |
| octorad_pilot_verification_v0.1.md | ★산출물 적대검증 리포트(28 finding) | 6aa3667 |
| referrence/06,07 + classification + research | 검증·업계·동의어·구현 리서치(입력) | 3625722~ |

**PILOT = `backend/app/data_pilot_project/` (격리, 기존 tools 미수정)**:
- `transforms.py`(값변환)·`pipeline.py`(채널 translator)·`compute.py`(파생·MER)·`crosswalk.py`·`materialize.py`·`verify_outputs.py`·`run_pilot.py`. 커밋 4d3a807·029ac48·8ffdfdc·6aa3667.
- 실행: `python backend/app/data_pilot_project/run_pilot.py` (8/8) · `verify_outputs.py` (12/12).
- materialize 산출 = `data/clumi/_canonical/{cleaned,computed,crosswalk}/` (✓ 실재, **gitignore=local**).

**재생성 스크립트** = `docs/_claude/data/erd/` (gitignore): extract_raw_schema·gen_dbml_draft·assemble_erd·gen_layer_docs·assemble_metadata.

---

## §3 확정 결정 (오너 confirm — "전부 권장대로")

| 결정 | 값 |
|---|---|
| 언어 | **영문 snake_case** + 단위접미사(`_krw`/`_pct`/`_x`/`_count`) |
| 값 표현 | **정규화값 + 원본 lineage 보존**(신뢰) + 파생 **computed 재계산** + **MER** |
| measure vs metric | spend·revenue·count=cleaned / roas·mer·cvr=computed |
| 분리 | `member_id`↔`anon_client_id` · `membership_grade`↔`rfm_tier` · **광고↔메시징(C6.3)** |
| 보류 | M2·M5·M7·M8 (Kakao 대행사 doc 블로커) |
| ★ 레이어 본질(§2 정정) | 데이터분석 에이전트라 **normalized/computed = 1급 서빙 레이어**(사전계산·저장, 에이전트가 추출). lineage=신뢰 기전. 3 레이어 다 ERD/메타/desc. 단 **SPEC 손수 + 레이어 문서 생성**, 순서=설계→materialize→문서화 |

---

## §4 검증된 사실 (✓ pilot 실행 + 독립 재계산)

- **MER = total_order_revenue / total_marketing_cost = 119,539,660 / 18,306,923 = 6.53** = methodology **S004 전사 ROAS**. → 오너의 "**18.3M 분모**" 정체 = MER/blended ROAS 확정.
- ad_cost 18,306,923(S003=ad 18,235,453 + msg 71,470) · orders 매출 119,539,660(S001). 채널별 전부 일치.
- **채널 roas 과대**(meta 1.91·naver 2.74·advoost 6.5) vs **blended mer 6.53 신뢰** — 07 업계 MER 우위 실증.
- ★ PILOT이 적발한 drift: `naver statDt`=ISO `2026-04-01`(사전/SPEC yyyymmdd 오기) → 정정. `meta campaign_id`=18자리(사전·contract 17 오기) → 정정.
- grain 이중계상 가드: meta `by_age`/`instagram_inapp`=performance breakdown(spend 동일) → performance만 합산(정답).

---

## §5 ★ 정직 경고 (반동조 — 다음 세션이 과신하면 안 됨)

검증 리포트([octorad_pilot_verification_v0.1](../agent_specs/ERD/octorad_pilot_verification_v0.1.md))의 핵심 판정:

> **"8/8·12/12 PASS는 *코드가 옳아서*가 아니라 mock의 우연한 단순성(단일월·전부 KRW·VT=0·omni중복0·name교차0) 덕. 실데이터(USD·다월·VT>0·다중 attribution)면 침묵하며 틀린다(silently wrong)."**

- **커버리지**: contract 42필드 중 **~7개만 materialize**. verify 12개가 전부 동일 ~6 measure/2 metric 대상 → 미구현 ~35필드 위에서 vacuously green. "N/42 materialized" 정직 표기 필요(P1).
- **crosswalk**: cross-channel 그룹 = **0%**(C5 미해결, 이름으로도 자동연결 안 됨 — 의도적 매핑 필요). 검증 미반영.
- **데이터사전(`clumi_data_dictionary.csv`)**: raw와 다중 drift(ccnt 역전·campaign_id 17·statDt·orders/customers 컬럼). **결정론 값검증이 절대 못 잡는 종류** → 사전을 raw에서 자동생성 + 사전↔contract 자동 diff 게이트 필요(P0/P1). 사전 계산내용 수정은 memory `project_data_viz_work_division`상 **오너 영역**.
- P0 역반영 완료(C6.3 분리·order_revenue 등재·campaign_id 18·GA4 native KRW)는 ✓ 재검증됨. 단 위 잔여는 미해결.

---

## §6 남은 일 / 다음 (오너 선택)

검증 리포트 §5 우선순위:
| P | 항목 |
|---|---|
| **P1** | coverage.json 매니페스트(42필드 status·not_attempted FAIL) + 배지 "N/42 materialized, M tested" |
| **P1** | crosswalk cross_channel==0 시 WARN + UTM/code 매핑 전략 |
| **P1** | 사전 raw 자동생성 + 사전↔contract 자동 diff 게이트 (⚠사전 계산내용=오너 영역) |
| P2 | GA4 native KRW 전환·매출 3소스 reconciliation note·vt_conversion 등 미구현 metric |
| P3 | 비4월·USD·VT>0·multi-omni mock으로 분기 회귀 |

**다음 갈림길**:
- ⓐ **잔여 P1~P3 보강** (검증 견고화 — coverage 정직 표기·사전 게이트). *권장: tools 전환 전에 P1 먼저.*
- ⓑ **tools 전환** — pilot 레퍼런스로 `tools/normalization/`(format_normalizer 폐기예정·ad_cost_helper 산발) → 채널 translator+config. 기존 격리 후 정리(memory `feedback_no_mixed_codebases`).
- ⓒ 다른 영역.

> 직전 턴 오너가 "a"(ⓐ 잔여 보강) 입력 후 compact로 전환 — 재개 시 ⓐ 의향 재확인.

## §7 관련 memory
`feedback_anti_sycophancy_evidence_labeling`(반동조) · `project_data_analyst_4_layers`(시스템 정체성) · `feedback_no_claude_commit_attribution`(커밋 표기 금지) · `project_extension_ease_priority`(과설계 가드) · `feedback_no_mixed_codebases`(v1/v2 전환) · `project_data_viz_work_division`(계산=오너 영역).
