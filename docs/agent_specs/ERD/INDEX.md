# ERD/ — 데이터 구조 재설계 폴더 INDEX

> **raw → normalized → computed 데이터 구조 재설계의 단일 진입점.** 현재 문서 + 과설계 점검 + 앞으로 만들 문서 + normalized 방법론.
> 상위: [agent_specs INDEX 30대](../INDEX.md). 재생성 스크립트·중간산출 = `docs/_claude/data/erd/`(gitignored).

---

## §1 현재 문서 (읽는 순서)

| # | 문서 | 무엇 | 상태 |
|---|---|---|---|
| 1 | [erd_octorad_raw_v1.0.md](erd_octorad_raw_v1.0.md) (+`.dbml`) | **raw ERD** — 30파일/34테이블/11도메인, 테이블·컬럼·관계(확정 Ref 17·추정 7). *구조* | ✅ |
| 2 | [octorad_raw_metadata_v0.1.md](octorad_raw_metadata_v0.1.md) (+`.yaml`) | **raw 메타데이터+description** — 712컬럼, 벤더·API·grain·PII + 설명(source/confidence). *의미* | ✅ |
| 2b | [normalize_canonical_naming_v0.1.md](normalize_canonical_naming_v0.1.md) | **canonical 명명** — A/M/I/T cluster별 영문 canonical 이름·단위·변환룰. §1.5 이름+값 한쌍 | ✅ confirm |
| 2c | [octorad_canonical_contract_v0.1.yaml](octorad_canonical_contract_v0.1.yaml) (+[.md](octorad_canonical_contract_v0.1.md)) | **★ canonical data contract** — normalized/computed SPEC **44 필드**(measures 16·metrics 11·dims 15·time 2). 채널 translator·lineage·MER·거버넌스 governing. raw 메타의 진화형 | ✅ v0.1 |
| 2d | [octorad_conversion_config_v0.1.yaml](octorad_conversion_config_v0.1.yaml) | **conversion config** — 값 변환 규칙집(transform primitive 10·환율 effective date·채널 quirk 바인딩 5). contract의 *값변환* 짝(matching=contract / mapping=여기) | ✅ v0.1 |
| 2e | [erd_octorad_canonical_layers_v0.1.md](erd_octorad_canonical_layers_v0.1.md) (+[.dbml](erd_octorad_canonical_layers_v0.1.dbml)) | **normalized·computed ERD/메타/desc(통합)** — SPEC+materialized에서 *생성*. cleaned 16 measures·computed 11 metrics(8 materialized·3 blocked) + 실측값(mer 6.53)·lineage + raw→normalized 변환맵(칼럼명+값변환) | ✅ 생성 |
| 2e' | [erd_octorad_normalized_v1.0.dbml](erd_octorad_normalized_v1.0.dbml) | **normalized 결과 ERD** — normalized_measures 단일 wide(채널×period, 16 measures + lineage). contract에서 생성 | ✅ 생성 |
| 2e'' | [erd_octorad_raw_normalized_v1.0.dbml](erd_octorad_raw_normalized_v1.0.dbml) | **raw↔normalized 연결 ERD** — 기존 raw 8 소스테이블(**전체 컬럼**) + normalized + **Ref 40(매칭 컬럼만 canonical 연결)**. salesAmt·spend·cost→ad_cost_krw 등 *이름 매칭* 시각화 | ✅ 생성 |
| 🌐 | [erd_octorad_flow.html](erd_octorad_flow.html) | **★ 인터랙티브 흐름 ERD** — raw 19테이블(567컬럼) / normalized(measure 16·**dim 15·time 2**) / computed 11 / **★목표(target) 4박스(KPI 레인, ◎컬럼 23)**. raw ●measure◆dim◇time 정규화 + **점선엣지=실적↔목표 대조**(tg 13·gap 4). daily_performance=레거시 표시. 칼럼 **클릭**=연결체인 · **hover**=desc · **드래그** · **ⓘ**=메타데이터 · **▾**=접기 · **검색**. 자가완결 HTML | ✅ 생성 |
| 🌐 | [erd_octorad_pivot_migration.html](erd_octorad_pivot_migration.html) | **★ 피봇 변환 시각화** — 기준(현재) 카테고리/툴 → 신규 카테고리/툴 표. 데이터 정합 진단(실적 canonical 18.3M / 목표 = 기존 4파일 / 레거시 mock daily_performance → 폐기) · 툴 변환 22행(REPLACE 5+shared·MODIFY 10·KEEP 77·NEW 1 canonical_translator) · 데이터레이어(cleaned→normalized 관계형) · 검증배지(교차세계 measures 10+dim 4). **제안(미구현)** | ✅ 생성 |
| 2f | [octorad_metric_registry_v0.1.md](octorad_metric_registry_v0.1.md) | **지표 registry** — computed 지표 단일정의. ★ROAS 일가족(mer/channel/blended) grain별 신뢰 단일화 = '3값 모순' 해소 | ✅ v0.1 |
| 2g | [octorad_campaign_crosswalk_v0.1.md](octorad_campaign_crosswalk_v0.1.md) | **campaign_crosswalk(C5)** — 채널 ID 네임스페이스 매핑. ★실측: cross-channel 0(이름도 자동연결 X → 의도적 매핑 필요) | ✅ v0.1 |
| 🔧 | `backend/app/data_pilot_project/` (코드) | **PILOT 참조구현** — raw→cleaned→computed (격리, tools 미수정). SPEC 8/8·독립 12/12 검증. materialize→`data/clumi/_canonical/` | ✅ |
| 🔍 | [octorad_pilot_verification_v0.1.md](octorad_pilot_verification_v0.1.md) | **산출물 적대검증 리포트** — 4렌즈 28 finding·4클러스터. ★"8/8 PASS=mock 우연, 실데이터면 침묵하며 틀림" 정직평가. P0 역반영 완료(C6.3·order_revenue·campaign_id·GA4) | ✅ |
| 🛡 | `data_pilot_project/{coverage,dict_gate,gate}.py` (코드) | **★P1 거버넌스 게이트** — ① coverage 매니페스트(**배지 13/44 materialized·7 tested·4 blocked·31 not_attempted**, vacuously-green 가시화) ② crosswalk **WARN**(cross_channel=0 '연결됨' 착시 경고) ③ 사전↔raw↔contract diff(**CRITICAL 0**·DRIFT 18=사전 owner영역 보고). `gate.py`=4단 통합 OVERALL ✅ | ✅ P1 |
| 3 | [normalize_synonym_classification_v0.1.md](referrence/normalize_synonym_classification_v0.1.md) | **채널 동의어 분류** — 49 cluster + 충돌 레지스터(단위/ID공간/grain/의미함정) + 명명대기 + 실측해소 | ✅ |
| 4 | [normalize_implementation_research_v0.1.md](referrence/normalize_implementation_research_v0.1.md) | **구현 아키텍처 리서치** — 외부 4각도 출처22 → ⓔ 하이브리드(채널별 translator + canonical contract + LangGraph fan-out/in) | ✅ |
| 5 | [referrence/06_erd_and_verification.md](referrence/06_erd_and_verification.md) | **외부 검증 + 명명 작업시트** — 공식 doc(Naver Java Stat.java·Meta v25) 10 PASS/2 PARTIAL + canonical name 시트 (입력 참고) | 참고 |
| 6 | [referrence/07_industry_raw_to_standard.md](referrence/07_industry_raw_to_standard.md) | **업계 실무 외부 리서치** — 퍼포먼스마케팅 회사(Funnel·Improvado·Northbeam)의 raw→표준 변환. MCDM·mapping table·siloed+unified·★MER/blended ROAS. 우리 설계 8/8 검증 + MER 보강 | 참고 |

> 읽는 순서 = 구조(1) → 의미(2) → 통합후보(3) → 구현법(4) → 검증·명명입력(5). **본 산출물 = 1·2 (`ERD/` 루트), 참고·입력 = 3·4·5 (`referrence/`).**

---

## §2 ★ 과설계 점검 (정정 2026-06-14 — 오너 중요시사점)

> ⚠ **정정**: 데이터분석 에이전트라 **normalized/computed = precompute-and-serve 1급 데이터 레이어**(사전계산·저장돼 에이전트가 거기서 추출). + **raw→norm→computed lineage를 *보여줘* 신뢰성 부여**(raw만 써도 되지만 과정 노출). → **3 레이어 각각 ERD+metadata+desc 정당.** 아래 '9칸→3'은 *현재 thin 상태*만 본 ⚠과교정 — 표의 '설계 vs 추출' 구분은 유효하나 결론('문서화 불필요')이 틀림. **정정 결론 = §2 하단.**

오너 매트릭스 = {ERD · 메타데이터 · description} × {raw · normalized · computed · 그외} = **최대 9~12 문서**. **그러나 그대로 만들면 과설계입니다.** 이유:

| 레이어 | 데이터 성격 | ERD/메타/desc 따로? |
|---|---|---|
| **raw** | *추출*됨 — 실제 벤더 소스 테이블(34) | ✅ **3개 정당** (이미 완료). raw는 진짜 관계형 테이블이라 ERD·메타·desc가 의미 있음 |
| **normalized** | *설계*됨 — 테이블로 materialize 안 됨(translator/매핑임. [§2-B 분류](referrence/normalize_synonym_classification_v0.1.md) 확인) | ❌ **3개 = 과설계.** ERD·메타·desc가 *같은 것* = **canonical data contract 1개**(schema+의미+단위 통합, 리서치 ⓓ) |
| **computed** | *파생*됨 — 지표 산출(ROAS=rev/spend, scalar·dict). 관계형 아님 | ❌ **ERD 부적합.** **지표 registry 1개**(파생식·단위·grain 정의)로 갈음 |
| **그 외** | 지원 아티팩트 | conversion config·campaign crosswalk·명명 worksheet |

**정정 결론: 3 레이어 × (ERD+metadata+desc) + ★lineage + SPEC 2개.**
- **raw** (ERD+메타+desc) = ✅ 완료 (추출됨, provenance 뿌리)
- **normalized** = SPEC(**canonical data contract**) + 그 SPEC이 *생성*하는 normalized ERD/metadata/desc (materialize 후). **에이전트 서빙·추출 대상**
- **computed** = SPEC(**지표 registry**) + 생성되는 computed 문서. **에이전트 서빙·추출 대상**
- **★lineage** (raw→norm→computed provenance) = 신뢰 기전 (신규 필수)

> **왜 과설계가 아닌가**: 데이터분석 에이전트는 normalized/computed를 *사전계산·저장*해 서빙 → raw처럼 추출 대상이라 문서화 필요. 단 효율 가드: ① **SPEC(contract/registry) 손수작성 + 레이어 문서는 *생성*** (raw ERD를 raw파일에서 생성했듯) — 9개 손수작성은 여전히 과설계. ② **순서**: 설계→깨끗이 materialize→문서화 (현 cleaned/computed=grab-bag이라 정돈 먼저). (memory `project_extension_ease_priority`)

---

## §3 앞으로 만들 문서 (로드맵)

| 우선 | 산출물 | 레이어 | 무엇 | 선행 |
|---|---|---|---|---|
| ~~1~~ ✅ | **canonical data contract** (YAML+md) | normalized | concept별 canonical 명·단위·grain + 채널 alias·변환룰 + 의미 + MER. **v0.1 작성됨**(`octorad_canonical_contract_v0.1`) | ✅ 완료 |
| **2** | **지표 registry** | computed | ROAS·CAC·전환율 등 파생식 *단일 정의*(measure vs metric 분리). ROAS=배수 통일 | 명명 + 분모 18.3M(결정됨) |
| ~~3~~ ✅ | **conversion config** | 그 외 | 통화(rate+effective date)·배수↔%(÷100)·날짜 KST·μs→datetime·int캐스팅 외부화. **v0.1**(`octorad_conversion_config_v0.1`) | ✅ 완료 |
| 4 | **campaign_id crosswalk** | 그 외 | 채널별 ID 네임스페이스 → name/UTM 매핑테이블(C5 join불가 해소) | — |
| ★ | **lineage / provenance** | 횡단 | raw→normalized→computed 변환 계보 — 에이전트가 신뢰 위해 "이 computed 값이 어느 raw·변환서 왔나" 표시 | 레이어 materialize |
| — | normalized·computed **ERD+metadata+desc** | norm·computed | SPEC(contract/registry)에서 *생성* (손수작성 X). 에이전트 서빙층 문서화 | materialize 후 |
| 5 | (선택) DataSource/Workspace as-built spec | 그 외 | ADR-020/022/031 통합(데이터레이어 계약) | — |

> 정정(§2): normalized/computed도 ERD/metadata/desc 가짐(에이전트 서빙층) — 단 **SPEC(contract/registry)에서 *생성*** + **lineage(raw→norm→computed)** 추가. **손수작성은 SPEC 2개**; 레이어 문서는 raw처럼 스크립트 생성. materialize 정돈이 선행.

**광의 데이터엔지니어링 문서**(시스템설계지도 §1-B 연계): 위 1·2가 곧 "단일 권위 registry" 본진. 데이터사전↔raw drift 정정(별건 todo)도 raw metadata에 반영됨.

---

## §4 normalized 방법론 — 컬럼은 어떻게, 숫자는 어떻게

> 리서치 ⓔ + 06 검증을 운영 규칙으로. **핵심 = 매칭(이름)과 매핑(변환) 분리, 측정과 파생 분리.**

### 컬럼 (이름) — "어떤 식으로"
1. **concept당 canonical 이름 1개** — 06 §5 시트 기준 (예: `ad_cost_krw`·`conversion_count`·`conversion_revenue_krw`·`impressions`·`clicks`). 명명 = 오너 결정.
2. **채널별 translator가 alias 선언** — `Naver: salesAmt → ad_cost_krw (semantic='비용')`, `Meta: data[].spend → ad_cost_krw`. 코드 분기 아닌 **선언적 매핑(config)**.
3. **매칭 ≠ 매핑** — 이름 대응(alias)은 contract에, 값 변환(단위/통화)은 conversion config에 분리.
4. **고유 필드는 옵셔널/JSONB** — Meta `actions[]` 같은 채널 고유 구조는 강제 공통화 X(god-schema 회피), namespace 보존.

### 숫자 (값) — "어떤 식으로"
| 충돌 | canonical 규칙 (06 검증 기반) |
|---|---|
| ROAS 배수 vs %(100배) | **canonical = 배수(×)**. Naver `ror`·advoost `roas` **÷100**. Meta 그대로 |
| ROI ≠ ROAS | 별 canonical(`msg_roi_pct`). `ROI%=(ROAS−1)×100`(06 P-07) |
| 통화 KRW/USD | KRW 통일. Meta `account_currency` 확인 후 환산(rate+effective date). USD 병기 분리 |
| 전환 추출 | Meta `actions[]`에서 **`action_type='omni_purchase'` 필터**(평탄키 가정=silent-0) |
| salesAmt 함정 | `salesAmt → ad_cost_krw`(비용), `convAmt → conversion_revenue_krw`(매출) — 절대 혼동 금지 |
| 날짜/TZ | KST `YYYY-MM-DD` 통일. GA4 UTC→KST, naver `statDt` int→date |
| 타임스탬프 | KST datetime(ISO). GA4 μs ÷1e6, `event_time_unix` 자릿수 확인 |
| 타입 | string 수치(Meta/advoost) → numeric 캐스팅 일관화 |
| 측정 vs 파생 | 채널은 원자값(spend·revenue·count)만 cleaned에. **ROAS=rev/spend는 computed 1곳**(파생을 채널이 만들지 않음) |

### 정규화 ⚠ 보류 (06 PARTIAL — 외부 블로커)
- 메시징 `open_rate`/`click_rate` **분모**(대상/송달/시도) 미확정 → Kakao 공식 doc(대행사 계약) 필요. **그 전까지 채널 간 율 비교·통합 금지** (분류 M5/M7/M8).
- `success_count`(요청수락) vs `delivered_count`(단말도달) 단계 정의 미확정.

---

## §5 다음 행동

1. **명명 착수** — 분류 §4 + 06 §5 작업시트로 canonical 이름 확정(ROAS=배수·CTR=inline_link_click_ctr·campaign_id prefix 등 06 권고 반영). M5/M7은 Kakao 블로커라 보류.
2. → **canonical data contract** 1개 작성(§3-1). 그 후 **지표 registry**(§3-2).
3. **과설계 가드**: normalized/computed의 별도 ERD·메타 문서 만들지 말 것. contract·registry가 흡수.

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-14 | v1 — ERD/ 폴더 INDEX 신설. 현재 5문서 + ★과설계 점검(9칸→3산출물) + 로드맵(canonical contract·지표 registry·conversion config·crosswalk) + normalized 방법론(컬럼/숫자 규칙, 06 검증 반영). |
