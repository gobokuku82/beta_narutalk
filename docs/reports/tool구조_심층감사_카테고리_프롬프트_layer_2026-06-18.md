# tool 구조 심층 감사 — 카테고리·툴 / 프롬프트 설계 / tool·data layer 구분 (2026-06-18)

> 워크플로 `wiclg6dps`(3트랙 병렬 + 적대 synthesis, file:line 실측). 오너 지시: "카테고리/툴/프롬프트 설계 제대로 됐나 + tool/data layer 구분 잘 됐나". 선행 = [A-4 대조표]·[A-7 보고서](A-7_tool구조점검_게이트감사_2026-06-18.md)·[컨텍스트엔지 보고서](컨텍스트엔지니어링_게이트인과재귀속_2026-06-18.md). 상위 [고도화 계획서](../_claude/plans/gate최소화_컨텍스트엔지니어링_고도화_계획서_2026-06-18.md).

## §0 ★ 종합 답 — "골격은 됐고, 의미 흐름은 안 됐다" (2층위)
1. **골격·경계 설계 = 의도대로 ✅.** tool/data/agent 분리 핵심(tool=순수기능·`self.fetch`만·raw 직독 금지)이 **92 tool 위반 0건**. collection/rendering/report/qa·canonical_translator = 모범. 프롬프트 콘텐츠/로직 분리(spec16 §1)도 깨끗(11종 전부 yaml 외부화). **북극성 아키텍처가 코드에 살아있음.**
2. **"의미가 흐르게" 설계 = No ❌ — 이게 할루시 뿌리.** 세 트랙이 **같은 병목**을 가리킴: 데이터 의미(단위·정의·함정라벨)가 cognitive에서 출발해 **execution 해석 단계 직전에서 끊김.** 트랙 충돌 0건 — 상호 강화하는 한 진단.

## §1 트랙1 — 카테고리·툴 설계 (refine, 재구축 ✗)
| verdict | 카테고리 |
|---|---|
| **solid** | collection(22, naming·produces 2-key 100% 일관·self.fetch 준수)·rendering(3)·report(2)·qa(1)·canonical_translator(contract-driven 모범) |
| **problematic** | **metrics(35=38%)**: 3결 혼재(순수KPI / 정제위장4 `clumi_methodology:cleaning` 자인 / 카운트 패스스루) · produces 3패턴 혼재 → 계약 예측 불가. **analysis(12)**: 3결(LLM추론·ML텍스트·대시보드 mock카드) + 중복(review_sentiment↔sentiment_analyzer·ai_recommendation↔recommender) · mock카드 6종 consumes/params 미선언 |
| **needs_refine** | cleaning(정제 3카테고리 파편화)·normalization(통합엔진+단일매퍼 추상화레벨 불일치)·preprocessing(1-tool)·comparison(grade_timeseries 오분류)·decision(엔진중복) |
- **공통 갭**: `consumes` 계약이 **per-tool catalog yaml에 0건**(team_catalog에만 8건) → I/O 계약이 두 파일로 분열, 데이터흐름을 catalog 단독 검증 불가.

## §2 트랙2 — ★프롬프트 설계 (execution 해석 LLM 5종 = blocker)
| 품질 | 프롬프트 |
|---|---|
| solid | cognitive.yaml(CLIENT PROFILE 풀 주입 모범)·planning_stage1·qa_responder(glossary 받는 유일 execution tool) |
| thin | planning_stage2/3 (stale 안내 + SSOT 복제) |
| **problematic/blocker** | **insight_extractor·diagnoser·forecaster·report_writer·summary_generator** — system_prompt 한 줄 "전문가" + `json.dumps(키:값)` 벌거벗은 숫자 + few-shot 0 |

**구조적 갭 (systemic):**
1. ★★ **데이터 계약(의미) 비대칭 = 깔때기**: 컨텍스트 주입이 cognitive(풀)→qa(glossary)→**[단절]**→execution 5종(0). 숫자 *뽑는* 단계는 의미 알고, *해석*하는 단계는 모름.
2. **의미 자산 다 있는데 배선만 없음** (저비용): clumi.yaml glossary(단위·실측값)·`_COL_DESC` 40+칼럼(원/%/배수)·`_lineage` 함정라벨(salesAmt=비용).
3. **자기파괴적 입력 정제**: collect_inputs가 `_`-prefix 키 일괄 strip → metric tool의 `_meta`(formula·단위)도 같이 버림(insight_extractor.py:60).
4. **stale 모순**: stage2/3 본문은 "광고지표=canonical 내부소비, 별도 정규화 agent 불요(A-5)"인데 **few-shot 예시는 여전히 channel_normalizing_agent 체인 포함** (A-5.3 prompt 수정의 미완 — 본 감사가 적발).
5. **SSOT 약화**: stage3가 metrics 35 KPI 매핑·collector source 분기를 본문에 복제 → catalog produces/consumes가 진실이어야 할 매핑을 프롬프트가 중복.
6. **few-shot 비대칭**: execution 5종 few-shot 0 → 출력 형식·evidence 단위명기를 모델 자율에 의존.

## §3 트랙3 — tool/data layer 구분 (mostly_clean)
- **INPUT 평면 = CLEAN ✅**: 92 tool raw 직독 위반 **0**. 전부 `base_tool.fetch(source_id,context)→self.ds.get` + DataSource pushdown(stream_jsonl/query_iter/aggregate). ★ **A-4의 kst_timezone_normalizer 'raw_direct 위반'은 STALE 정정** — 현 코드 `self.ds.stream_jsonl`. External collector `pd.read_csv`는 인가된 예외(mock_api 파싱).
- **SCHEMA 평면 = CLEAN ✅**: I/O 전부 dict, 내부메타 `_`컨벤션 일관(executor `_` 키 주입 제외·Pydantic extra='ignore').
- **DEPENDENCY 평면 = MOSTLY_CLEAN ⚠**: tool간 의존이 catalog 밖 `get_registry().get().execute()` 직접 인스턴스화 다수(mom_revenue→revenue_total 등) — 숨은 의존.
- **OUTPUT 평면 = LEAKY ❌** (A-6 재확인): `_storage`{layer,key}를 ~35 tool이 선언하나 **읽어 영속하는 소비자 코드 0**(장식성) · rendering이 workspace 우회 디스크 직접 기록 · canonical_translator.persist_* production 호출자 0(테스트만) · dashboard1 route 패턴 혼재(A-5.3 부분정리 잔존).

## §4 ★ 수렴 + 우선 수정
세 트랙이 한 지점: **"의미 자산은 다 있는데 execution 단계에 배선만 없다."** → 프롬프트 설계 갭 = **컨텍스트엔지(S1~S3) 수정의 직접·일차 대상**(추론 아닌 동일 사물의 세 각도). 게이트 최소화 계획과도 정합(새 게이트 0, 의미 배선).

| 우선 | 수정 | 영향·난이도 |
|---|---|---|
| **1 최우선** | execution 5 tool 의미 컨텍스트 배선 (= S1~S3, qa `_load_glossary` 일반화) | 大·小 |
| 2 | `_schema.yaml` taxonomy 봉합 8→10~11(decision/qa/rendering 등재) — 문서, 코드 0 | 中·小 |
| 3 | `consumes`를 per-tool catalog yaml로 일원화 ⚠ catalog_code_drift 주의(실측 대조 필수) | 中·中 |
| 4 | 오분류 회수(정제룰→cleaning·grade_timeseries→metrics·review_normalizer→text) + produces 키 컨벤션 | 中·中 |
| 5 보류 | 중복엔진(ai_recommendation/recommender) 출력키 통일(삭제는 오너 결정) · output persist 계약(DB 재구축 시점) | — |

## §5 적대 점검 flags
- 세 트랙 verdict 모순 **0** — 상호 강화(동일 병목의 세 각도).
- ⚠ **과소진단**: 중복엔진을 'A-7 KEEP 패턴'으로 관대히 봄 — 출력키조차 다름(recommendations/count vs rows/count)은 계약 문제. 출력키 통일은 필요.
- ⚠ **catalog_code_drift 주의**: consumes 끌어올릴 때 team_catalog 8건이 코드 실호출키와 일치 보장 없음 — grep 단정 금지, 실측 대조.
- ✅ **과대진단 경계 확인**: kst STALE 정정·External collector 인가예외 — input 위반 0 정확.

## §6 다음
**S1~S3(execution LLM 의미 배선)이 삼중 검증된 최우선** (컨텍스트엔지 감사·게이트 재귀속·본 구조감사 전부 #1로 수렴). 파일럿 검증 후 착수. 병행 저위험: `_schema` 봉합·stale few-shot 정정(A-5.3 미완). consumes 일원화는 catalog_code_drift 실측 대조 후.
