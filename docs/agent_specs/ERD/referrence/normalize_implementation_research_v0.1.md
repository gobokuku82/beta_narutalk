# raw → canonical 표준화 구현 방법 리서치 종합 — normalize_implementation_research

> **v0.1 — 외부 4각도 웹조사 + 현 코드 진단 종합. 구현 아키텍처 선택지(ⓐ~ⓔ) 비교·권장.**
>
> 입력:
> - 충돌 레지스터·cluster: [`normalize_synonym_classification_v0.1.md`](./normalize_synonym_classification_v0.1.md) (§3 C-1~C-7, §2 A1~T11)
> - 4각도 조사 결과 JSON: `docs/_claude/data/erd/_wf_res_textbook.json` · `_wf_res_trend.json` · `_wf_res_ax.json` · `_wf_res_arch.json`
> - 현 코드 직독: `backend/app/dream_agent/tools/normalization/format_normalizer.py` · `tools/shared/ad_cost_helper.py` · `tools/metrics/ad_cost_total.py`
>
> **이 문서는 구현 방법 비교·권장이다. 명명(canonical name) 결정은 분류 문서 §4 오너 결정 대기.**

---

## ① 문제 재정의 — 벤더 raw → canonical, 우리 충돌

**문제:** 의미는 같으나 채널(Meta / Naver SA / Naver GFA(ADVoost) / Kakao / GA4 / Cafe24 / 내부 마스터)마다 **이름·타입·단위·포맷·grain·ID공간**이 다른 raw 광고/마케팅 데이터를 1개 표준(canonical) 문서/스키마로 통합한다.

**충돌 5종 (분류 문서 §3 요약):**

| 충돌 종류 | 대표 사례 | 미처리 시 (분류 §3) |
|---|---|---|
| **단위 — 배수 vs %** (C1) | ROAS: Meta `purchase_roas`=배수(2.21) vs naver `ror`·advoost `roas`=%(512/928) | 100배 오류 보장. advoost `roas`(%)↔Meta `roas`(배수) 동명 함정 |
| **단위 — 통화 KRW/USD** (C2) | GA4 `purchase_revenue`(KRW)↔`purchase_revenue_in_usd` 나란히 / Meta `account_currency` 별도 | ~1300배 통화혼합 |
| **타입/단위 — us↔sec, str↔int** (C3) | GA4 `event_timestamp`=μs(16자리) vs `event_time_unix`=초(10자리); Meta/advoost/GA4 수치=string | ×1e6 누락 시 5만년 오차 / 합산·정렬 오류 |
| **포맷 — 날짜·TZ** (C4) | naver `statDt`·GA4 `event_date`=YYYYMMDD vs Meta=YYYY-MM-DD; GA4=UTC vs 나머지 KST | 파싱 분기·±1일 silent misalign |
| **ID 공간 — join 불가** (C5) | campaign_id: Meta 17자리 / naver `cmp-` / advoost `GFA` / kakao `CMP_KKO` / CRM int | cross-channel 직접 join 전부 미스매치 |
| **의미함정 — 이름↔의미 반대** (C6, 최우선) | naver SA `salesAmt`=**매출 아닌 광고비** / `convAmt`=매출 (헷갈림 쌍) | 비용↔매출 뒤섞임 → ROAS 뒤집힘. 영구 오염 1순위 |
| **중첩 배열** (C6.2) | Meta `actions[]`/`action_values[]`/`purchase_roas[]`=`[{action_type,value}]` | `action_type='omni_purchase'` 필터 없이 추출 시 silent-0 |
| **grain** (C7) | Meta/naver=일×캠페인 vs kakao/talktalk summary=캠페인 누계 vs interest=월별 | 단순 합산 전 grain 정렬 필요 |

**현 구현 진단 (코드 직독):**
- `format_normalizer.py` — 단일 함수 ⓐ. `ADS_FIELD_ALIASES` 한 dict에 **매칭(이름 대응)** + 인라인 **매핑(micros÷1e6·int/float 캐스팅)**이 섞임. 채널 식별은 시그니처 휴리스틱. `produces` 키가 **폐기된 5 collector**(작업 ⑫) 기준 → 사실상 미배선. 5개 평탄 alias라 actions[] 중첩·배수vs%·통화 충돌은 담지 못함.
- `ad_cost_helper.py` — 채널별 `extract_*_cost` 함수 + `CHANNELS` 레지스터. 부분적 per-source-translator이나 **cost 1개 지표만**·col_hint 하드코딩·계약 부재. `ad_cost_total.py`가 이를 호출(SUM 하드코딩 formula). = 산발 하드코딩 매핑.
- **진단 핵심:** 교과서가 분리하라는 **매칭(format_normalizer)과 매핑(ad_cost_helper)이 따로 떠돌고**, 둘 다 계약(contract)이 없어 silent 오류를 막지 못한다.

---

## ② 외부 레퍼런스 4각도 요약표

> 모든 행에 출처 URL. maturity = 출처 자체 표기.

### 2-A. 교과적 / 정통 데이터 통합 (textbook)

| 방법/도구 | 무엇 | 우리 적용성 | 출처 URL | maturity |
|---|---|---|---|---|
| Schema Matching vs Mapping | 매칭(어느 raw=어느 canonical 개념) ≠ 매핑(어떻게 변환). 충돌 4계층(syntactic/structural/model/semantic) | **우리 문제 정의 그 자체.** 한 함수에 매칭·매핑 섞지 말 것 = 현 코드 병폐 진단 | https://en.wikipedia.org/wiki/Schema_matching | 교과정설 |
| Mediated Schema + GAV/LAV/GLAV | canonical=단일 질의 인터페이스. GAV=질의 쉽고 소스추가 어려움 / LAV=소스 자율추가, 질의 NP | 소스추가 용이성=가치 → **LAV 정신(채널이 canonical 위 자기 view 선언)** + ETL materialize로 LAV 지수비용 회피 | https://www.geeksforgeeks.org/dbms/local-as-view-lav/ | 교과정설 |
| **Canonical Data Model (Hohpe & Woolf, EIP)** | canonical 1 + 소스별 Message Translator N. N×N→N. 6소스 30→12 | **오너 선택지 직접 답.** ⓒ(채널 툴 병렬→1문서) 청사진. ⓐ는 indirection 위반. 5채널=비용회수(>3) | https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html | 업계표준 |
| MDM: Standardization + Entity Resolution | parsing→standardization→matching/ER→consolidation(golden). 표준화가 매칭 '이전' | ID join불가=ER 영역이나 부분. **순서 교훈: 표준화(단위/타입/포맷)가 join보다 먼저.** cleaned=표준화, computed=consolidation | https://www.sciencedirect.com/topics/computer-science/master-data-management | 업계표준 |
| Semantic / Metrics Layer (dbt MetricFlow) | 메트릭을 YAML 중앙정의. measure(원자)/metric(ratio·derived) 분리 | **ROAS=revenue/spend는 canonical 1곳(computed).** 채널은 원자 measure(spend,revenue)만 → 배수vs%·actions[] 함정이 측정/파생 분리로 소멸. MVP+ 권장 | https://docs.getdbt.com/docs/build/about-metricflow | 업계표준 |
| Unit/Currency Conversion + Kimball | 단위/통화 변환은 전용 conversion table(rate+effective date). 차원 정합 | 변환을 인라인 아닌 **conversion config 외부화**(환율은 시변). 배수↔%는 canonical 한 표현 고정·표시단 변환 | https://en.wikipedia.org/wiki/Dimension_(data_warehouse) | 교과정설 |

### 2-B. 모던 데이터스택 트렌드 (trend)

| 방법/도구 | 무엇 | 우리 적용성 | 출처 URL | maturity |
|---|---|---|---|---|
| dbt staging layer | 소스당 1:1 얇은 모델. rename/cast/단위변환만, JOIN·집계 금지(grain 보존) | **{client}/raw→cleaned = staging.** format_normalizer를 채널별 작은 변환기로 쪼개라. join/계산은 computed로 | https://docs.getdbt.com/best-practices/how-we-structure/2-staging | 교과정설 |
| **Config-driven mapping (Truto)** | canonical schema + per-integration 선언적 매핑(JSONata) + generic engine. Canonical ID + crosswalk | **오너 선택지 가장 직접.** 변환기=코드 아닌 config. ID는 canonical_id 발급+source id crosswalk(join불가 해결) | https://truto.one/blog/what-is-the-best-way-to-normalize-data-models-across-different-crms | 업계표준 |
| Semantic Layer + OSI (2025) | 메트릭 1회 정의→어디서나 소비. OSI=dbt+Snowflake+Salesforce 벤더중립 YAML 표준 | (A)구문 정규화=cleaned / (B)지표 의미=computed 분리. agent들이 동일 metric 정의 참조 시 일관성↑ | https://promethium.ai/guides/top-10-semantic-layer-tools-2026-definitive-comparison/ | 업계표준 + OSI 신생 |
| **Data Contracts + Schema Registry** | schema+semantic def+quality rules+SLA+versioning. 필드 의미 명문화 | **의미함정 해결 정설.** canonical을 코드 아닌 별도 contract(YAML/JSON)로, `salesAmt='이것은 비용'` 박제. CI 검증. JSONB+schema_version 원칙 정합 | https://datadef.io/guides/en/data-contracts | 업계표준 |
| LLM schema matching (function calling) | LLM이 raw 컬럼→canonical 매핑 추론. JSON schema 강제 출력으로 환각↓ | **'LLM-heavy 초기' 정합.** 신규 채널 매핑 초안 LLM 생성→검증→config 박제. 런타임 변환은 결정적. 의미함정 LLM 단독 금지 | https://scrapingant.com/blog/llm-powered-data-normalization-cleaning-scraped-data | 신생/실험 |

### 2-C. AX / LLM-에이전트 방식 (ax)

| 방법/도구 | 무엇 | 우리 적용성 | 출처 URL | maturity |
|---|---|---|---|---|
| Canonical Data Model (hub-and-spoke) | N×M→N+M. <3소스면 오버헤드. 'lowest-common-denominator' 함정 경고 | 5소스=손익분기 넘김. **canonical=교집합이 아닌 union+optional**(actions[] 고유필드 JSONB 보존) | https://datadriven.io/data-modeling/canonical-data-model | 교과정설 |
| **Declarative Data Contract (Confluent)** | schema+domain rules(CEL)+migration rules(JSONata rename)+metadata. 버전드 선언 | **가장 운영현실적 청사진.** 벤더당 1 선언 파일. 단위변환=migration rule, 의미함정=metadata+품질룰, schema_version=migration | https://docs.confluent.io/platform/current/schema-registry/fundamentals/data-contracts.html | 업계표준 |
| LLMatch (arXiv 2025) | LLM 스키마매칭 Rollup/Drilldown 2단계. 컬럼명만으로 매핑 | 신규 벤더 온보딩 매핑 초안 부트스트랩. 의미함정은 인간검토+계약 박제. '1회 LLM, 런타임 결정적' | https://arxiv.org/pdf/2507.10897 | 신생 |
| DocETL (VLDB 2025) | 선언적 YAML + LLM operator(map/reduce/resolve/gather). agentic optimizer가 LLM→코드 치환 | **'연산자 선언 조합→1문서'.** resolve=ID join불가, gather=actions[] 중첩 펼침. LangGraph 노드=operator 대응 | https://github.com/ucbepic/docetl | 신생 |
| LLM Entity Resolution (SIGMOD/COLING 2025) | 두 레코드 동일 엔티티 판정. blocking+RAG 비용절감 | campaign/계정 ID join불가=ER. blocking+결정적 검증 병행 필수(수치 hallucination=오염) | https://aclanthology.org/2025.coling-main.8/ | 신생 |
| Agentic ETL (self-healing) | LLM이 새 소스 매핑 자동생성·드리프트 교정 | 신규 벤더 온보딩 보조. maturity 낮음. **런타임 즉흥 매핑 위험 → author=LLM, run=contract 분리** | https://airbyte.com/agentic-data/etl-for-ai | 실험 |

### 2-D. 구현 아키텍처 패턴 (arch)

| 방법/도구 | 무엇 | 우리 적용성 | 출처 URL | maturity |
|---|---|---|---|---|
| **CDM + per-source Translator/Adapter** | 소스당 어댑터 1. N²→N. 6소스 직접 30 vs canonical 12 | ad_cost_helper 산발=N² 안티패턴 증상. ⓐ 아닌 **채널별 변환기 N + canonical 계약** | https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html | 교과정설 |
| dbt staging (1:1, 멱등) | rename/cast/단위환산만. JOIN/집계 금지. view materialize | cleaned=staging(채널별 1:1, 멱등), computed=합성. ROAS·KRW/USD 정규화=cleaned | https://docs.getdbt.com/best-practices/how-we-structure/2-staging | 업계표준 |
| Unified API (Airbyte/Singer) | 소스별 connector가 provider↔unified schema 매핑. raw/normalized 분리 | FB/TikTok 광고 정규화 바로 그 사례. raw 보존+normalized 별도 = 우리 raw/cleaned 정당화 | https://airbyte.com/agentic-data/unified-api | 업계표준 |
| **Declarative field mapping (YAML)** | 변환을 명령형 코드 아닌 선언적 템플릿(source·target·expression) | format_normalizer dict alias가 맹아(미배선). **외부화하면 새 채널=설정만.** 의미함정·중첩은 code escape hatch | https://github.com/snatalenko/declarative-mapper | 업계표준 |
| **Fan-Out/Fan-In (≈Map-Reduce)** | 독립 서브태스크 병렬(fan-out)→1개 reduce(fan-in). key shuffle 적으면 적합 | **ⓒ 오케스트레이션 이론.** 채널 5=fan-out, canonical 합성=fan-in/reduce. LangGraph 자연 표현 → ⓑ+ⓒ 동시 지지 | https://theburningmonk.com/2024/07/do-you-know-your-fan-out-fan-in-from-map-reduce/ | 교과정설 |
| CDM Anti-pattern + DDD ACL | 거대 단일 canonical=god-schema 안티패턴. 대안=bounded context + ACL, 최소 교집합만 공통화 | **ⓐ 직접 반례 + 가드레일.** canonical=최소 합의 계약(공유 핵심지표 mandatory)+채널 고유필드 옵셔널. 각 어댑터=ACL(salesAmt 함정 차단) | https://teivah.medium.com/why-is-a-canonical-data-model-an-anti-pattern-441b5c4cbff8 | 업계표준 |

**출처 총 = 23개 고유 URL** (교과 6 + 트렌드 5 + AX 7 + 아키텍처 6, EIP CDM은 교과·아키텍처 양 각도에 등장 = 중복 1건 제외 시 고유 22).

---

## ③ ★ 아키텍처 비교표 (ⓐ~ⓔ)

> 우리 충돌 처리 적합도: 단위(C1·C2·C3) / ID공간(C5) / grain(C7) / 중첩배열(C6.2) + 의미함정(C6) 각각 ◎좋음 ○가능 △부족 ✗못함. POC 비용 = 5채널·90 tool·LangGraph 환경 기준.

| 선택지 | 무엇 | 장점 | 단점 | 단위 | ID공간 | grain | 중첩 | 의미함정 | POC 비용 |
|---|---|---|---|---|---|---|---|---|---|
| **ⓐ 단일함수** (현 format_normalizer) | 한 함수에 5채널 alias dict + 인라인 변환 | 추가 코드 0(이미 존재). 한 곳에서 봄 | indirection 위반·N² 하드코딩화·god-schema·매칭/매핑 혼재. **모든 4각도가 반대** | △ 인라인뿐 | ✗ | ✗ | ✗ 평탄 가정 | ✗ silent 깨짐 | 0 (그러나 충돌 미해결 = 부채) |
| **ⓑ 복합함수/그래프 (LangGraph)** | 변환을 노드 그래프로(전처리→매칭→매핑→reduce) | join·집계·파생(ROAS) 다운스트림에 맞음. 오케스트레이션 명시 | 정규화 자체엔 과함(정규화는 1:1 grain 보존이어야). 노드=코드면 여전히 하드코딩 | ○ | ○ reduce 노드 | ◎ reduce에서 정렬 | ○ 노드 분해 | △ 노드가 코드면 미흡 | 중 (그래프 골격) |
| **ⓒ 병렬 툴 → reducer 1문서** | 채널별 translator N개 병렬(fan-out) → 단일 merge 노드(fan-in) | CDM 정설. N²→N. 신규 채널=어댑터 1개. raw/cleaned 분리 정당 | merge 노드에 ID·grain·단위 충돌 해소 집중(설계 필요). 변환기가 코드면 ⓐ 분산판 | ○ 어댑터별 | ◎ merge 집중 해소 | ◎ merge 정렬 | ◎ 어댑터가 펼침 | ○ 어댑터=ACL | 중 |
| **ⓓ 선언적 매핑 (config/YAML)** | canonical contract(별도 아티팩트) + 채널별 선언 매핑 + 공통 engine | 신규 채널=config만(코드 불변). 의미함정 명문화. CI 검증. convention-우선 정합 | 순수 선언으론 actions[] 중첩·복잡변환 부족 → code escape hatch 필요. engine 1회 구축 비용 | ◎ 변환룰 외부화 | ○ crosswalk 선언 | ○ grain 메타 선언 | △ escape hatch 의존 | ◎ contract metadata | 중-고 (engine+contract) |
| **★ⓔ 하이브리드** (ⓒ 골격 + ⓓ 계약 + ⓑ 그래프 + 핵심부 LLM author) | canonical contract(ⓓ) ← 채널별 선언 translator(ⓒ, 병렬) ← LangGraph fan-out/in(ⓑ) ← 신규채널 매핑은 LLM 초안→검증 박제 | 4각도 수렴점. 충돌 5종 각 적소 처리. 측정/파생 분리(computed에 ROAS) | 초기 설계 비용 최대. engine+contract+그래프 동시. 과설계 위험(POC) | ◎ | ◎ | ◎ | ◎ | ◎ | 고 (단 단계 도입 가능) |

**핵심 판정:**
- **ⓐ 단일함수 = 4각도 만장일치 기각.** 교과(indirection 위반)·트렌드(staging 반패턴)·AX(계약 부재 증상)·아키텍처(N²·god-schema)가 전부 반대. 단위·의미함정·ID·grain·중첩을 한 dict가 동시에 못 담음.
- **ⓒ + ⓓ가 합쳐진 ⓔ = 모든 각도의 수렴 권장.** "채널별 얇은 translator(ⓒ, 병렬) + 그들이 만족시킬 별도 canonical 계약(ⓓ) + LangGraph fan-out/in(ⓑ)" = config-driven canonical pipeline.

---

## ④ 권장안 + 근거

### 권장 아키텍처 (단일 전문가 의견)

> **채널별 얇은 declarative translator N개(ⓒ, fan-out 병렬)가 별도 canonical data contract(ⓓ, YAML 아티팩트)를 만족시키며 cleaned를 채워 넣고, 단일 reduce 노드(ⓑ LangGraph fan-in)가 ID·grain 충돌을 해소해 canonical 1문서로 합성하며, ROAS 같은 파생 메트릭은 cleaned가 아닌 computed(metrics layer)에 단일 정의한다 = 선택지 ⓔ 하이브리드(ⓒ 골격 + ⓓ 계약 중심 + ⓑ 그래프 실행).**

핵심 분리:
1. **매칭 vs 매핑 분리** — 이름 대응(어느 raw=어느 canonical)은 contract의 alias 선언, 변환(단위/통화/타입)은 conversion config로 외부화. 현 코드는 이 둘이 섞여(format_normalizer dict + ad_cost_helper 하드코딩) 떠도는 게 병폐.
2. **측정(measure) vs 파생(metric) 분리** — 채널은 원자값(spend, revenue, impressions)만 cleaned에 올리고, ROAS=revenue/spend는 computed 한 곳에만. → 배수vs%·actions[] 중첩·통화 함정이 측정/파생 분리로 소멸.
3. **author(LLM) vs run(결정적) 분리** — 신규 채널 매핑 초안만 LLM(function calling + canonical schema 강제), 검증 후 config 박제. 런타임은 결정적 engine. 광고 수치 hallucination=오염이라 런타임 LLM 변환 금지.

### 근거 (교과 정설 + 트렌드 + AX 수렴점)

1. **CDM 정량 근거 (교과+아키텍처 수렴):** 소스별 translator N개 + canonical 1이 N×N 점대점을 N으로 감소(6소스 30→12). 5채널은 비용회수 구간(>3소스). 현 `ad_cost_helper`의 채널별 하드코딩 = N² 안티패턴 증상. [EIP CDM](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html) · [datadriven.io](https://datadriven.io/data-modeling/canonical-data-model)
2. **계약(contract)이 의미함정 유일 해법 (트렌드+AX 수렴):** `salesAmt=비용` 같은 함정은 schema 매칭만으론 안 풀리고 contract의 명시 semantic 정의(metadata)로만 차단. LLM 추측 금지. canonical을 코드 아닌 별도 버전드 아티팩트로. [datadef Data Contracts](https://datadef.io/guides/en/data-contracts) · [Confluent](https://docs.confluent.io/platform/current/schema-registry/fundamentals/data-contracts.html)
3. **정규화=1:1 grain 보존, 합치기·파생은 별도 레이어 (트렌드+아키텍처 수렴):** dbt staging는 rename/cast/단위변환만, JOIN/집계 금지 → cleaned. 채널 union·ROAS 계산 = computed(metrics layer 단일 정의). Fan-Out(채널 병렬)/Fan-In(단일 reduce가 ID·grain 해소)이 LangGraph로 자연 표현. [dbt staging](https://docs.getdbt.com/best-practices/how-we-structure/2-staging) · [MetricFlow](https://docs.getdbt.com/docs/build/about-metricflow) · [Fan-Out/Fan-In](https://theburningmonk.com/2024/07/do-you-know-your-fan-out-fan-in-from-map-reduce/)

### 반대 증거 (1줄)

**CDM god-schema 안티패턴:** canonical을 5벤더 필드 superset으로 부풀리면 optional 투성이·전체 강결합·진화 마비 → mandatory는 공유 핵심지표 최소로, 채널 고유필드(actions[])는 옵셔널/namespace 격리 + JSONB 보존(MEMORY JSONB+Optional+append-only 정합). [CDM anti-pattern](https://teivah.medium.com/why-is-a-canonical-data-model-an-anti-pattern-441b5c4cbff8)

---

## ⑤ 우리 시스템 매핑

> 현 코드 → 권장 구조. 파일 경로는 실재(직독 확인).

### format_normalizer 단일함수 → 무엇으로

| 현재 (`tools/normalization/format_normalizer.py`) | 권장 | 근거 |
|---|---|---|
| 단일 `ADS_FIELD_ALIASES` dict (매칭+매핑 혼재) | **채널별 declarative contract 파일** (canonical alias = 매칭) + **conversion config** (단위/통화/타입 = 매핑) 분리 외부화 | Schema Matching vs Mapping; declarative-mapper |
| 인라인 micros÷1e6·int/float 캐스팅 (`_map_ads`) | conversion config의 변환룰로 외부화 (환율=rate+effective date) | Kimball conversion table; Confluent migration rules |
| 시그니처 휴리스틱 채널 식별 (`_detect_ads_channel`) | 채널별 translator가 자기 소스만 담당(1:1) → 식별 불요 (dbt staging 1소스 1모델) | dbt staging |
| 폐기 collector `produces` 키 (미배선) | 신 collector가 contract 충족하도록 CI 검증 (Status 마커 정합) | Data Contracts CI |
| 5개 평탄 alias (actions[] 중첩 못 담음) | contract에 중첩 경로 선언 + escape hatch(`actions[].action_type=omni_purchase` 필터) | DocETL gather/extract; C6.2 |

### ad_cost_helper 산발 하드코딩 → 무엇으로

| 현재 (`tools/shared/ad_cost_helper.py`) | 권장 |
|---|---|
| 채널별 `extract_*_cost` 함수 + `CHANNELS` 레지스터 (cost만, col_hint 하드코딩) | 단일 지표 하드코딩 흡수 → **contract의 spend alias + conversion 룰**로 일반화. `aggregate_ad_cost`의 SUM = computed metrics layer로 이동 |
| `salesAmt`/`total_cost_krw` 채널별 분기 | contract에 `salesAmt → ad_cost(KRW), semantic='이것은 비용'` 박제 (C6.1 함정 차단) |

### DataSource / cleaned / computed 레이어 어디에

```
{client}/raw          ← 채널별 raw 보존 (Airbyte raw/normalized 분리 정당화)
   │  fan-out: 채널별 declarative translator N개 (병렬, 1:1, 멱등)
   │           = rename·cast·단위정규화(배수↔배수, KRW 통일)·중첩 펼침. JOIN/집계 금지
   ▼
{client}/cleaned      ← canonical contract 충족 (= dbt staging / MDM standardization)
   │  fan-in: 단일 reduce 노드 (LangGraph) — ID공간 crosswalk·grain 정렬·중복 해소
   │  파생: ROAS=revenue/spend 등 metric 단일 정의 (measure vs metric 분리)
   ▼
{client}/computed     ← consolidation + metrics layer (ROAS·CAC·전환율 1곳 정의)
{client}/description  ← canonical data contract 아티팩트(YAML/JSON) 박제 위치 후보
```

레이어 사상: raw→(채널 translator 병렬)→cleaned[canonical contract] → (reduce + metric)→computed[지표 1정의]. MEMORY [tool/data/agent 분리]·[data 폴더 구조]·[convention 우선] 정합.

### {client} 확장 (convention 우선)

- 신규 client/채널 = **폴더 + contract 파일 1개 추가**, engine·reduce 노드 코드 불변. (MEMORY [data 폴더 구조: 신 client = 폴더만 추가] 정합)
- 신규 채널 매핑 초안 = LLM author(LLMatch식) → 오너/검증 confirm → contract 박제. (MEMORY [LLM-heavy 초기: 페어 누적→규칙 추출] 정합)

---

## ⑥ 다음 단계

1. **명명 확정 (선결, 분류 §4 오너 결정):** A1~T11 cluster의 canonical 명·단위(ROAS=배수 통일 권장)·grain·매핑정책. 이름만으로 충돌 안 풀림 — 단위·의미함정 매핑 동반 결정.
2. **canonical data contract 스키마 박제:** 별도 YAML/JSON 아티팩트. 필드당 {canonical명, 타입, 단위, semantic 정의(salesAmt='비용'), enum, source alias, 중첩경로, grain}. 위치 = `{client}/description/` 또는 `docs/agent_specs/ERD/` 후보. (Confluent 4요소: schema+rules+migration+metadata)
3. **conversion config 외부화:** 통화(rate+effective date)·배수↔% (÷100 채널별)·타입 캐스팅·날짜/TZ(UTC→KST)·μs↔sec 변환룰. C1~C4 처방.
4. **채널별 translator 시범 1개 (PILOT):** format_normalizer를 한 채널(예 Meta)부터 contract 충족 translator로 쪼개 cleaned 배선. ⓐ→ⓒ 전환의 첫 슬라이스. (MEMORY [v1/v2 섞임 금지: 점진 추가 후 전환 sprint])
5. **reduce 노드 + ID crosswalk 설계:** campaign_id 채널 namespace prefix 보존 + campaign_name/utm_campaign 매핑테이블(C5 join불가 해소). LangGraph fan-in.
6. **computed metrics layer 단일 정의:** ROAS=revenue/spend·CAC·전환율을 한 곳에. `ad_cost_total`의 SUM·`roas_overall` 등 흡수.
7. **LLM author 파이프라인 (MVP+):** 신규 채널 매핑 초안 생성(function calling + canonical schema 강제) → 검증 → config 박제. ER(campaign 동일성)은 blocking+결정적 검증 병행.

> 비용 가드: ⓔ 전부를 한 번에 만들지 말 것. **순서 = ① 명명 → ② contract 1개 → ④ 채널 1개 PILOT translator → ⑤⑥ reduce·computed**. 각 슬라이스 검증·커밋. (MEMORY [한 턴 ONE 변경→검증→커밋])
