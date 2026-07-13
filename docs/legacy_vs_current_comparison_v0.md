# 구세대 ↔ 현행 코드베이스 비교 분석 v0

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-07-10 |
| 비교 대상 | **구세대** = `docs/_claude/_old/` (git 미추적 스냅샷 — `.gitignore:175` `docs/_claude/`) ↔ **현행** = `backend/` + `frontend/` |
| 목적 | 데이터 계층/ERD 설계 없이 에이전트부터 개발해 생긴 구세대의 하드코딩·강제 로직을 진단하고, 현행 클렌징이 각 결합점을 어떻게 일반화했는지 전/후 대응으로 기록 |
| 분석 방법 | 주요 주장은 구세대 스냅샷·현행 코드의 file:line 을 직접 대조해 확정 |
| 관련 문서 | `docs/system_analysis_and_base_plan_v1.0.md` (Phase 0~5 마스터 계획) · `docs/STATUS.md` (진행 장부) · `.claude/refactor_plan_detailed.md` (추출 런북) · `docs/agent_specs/ERD/` (ERD 전용 폴더) |

---

## 1. 요약 (TL;DR)

구세대는 **"OctorAD" — 한국 화장품/뷰티 D2C 브랜드(클라이언트 clumi)의 마케팅 분석 시스템**이었다. 4-Layer(cognitive→planning→execution→response) 에이전트 프레임 자체는 갖췄으나, ERD/데이터 계층 설계가 선행되지 않은 채 에이전트부터 개발되어 마케팅 도메인 어휘가 코어 전 층에 하드코딩됐다 — 코어 계약 스키마의 작업/소스 enum, 플래너의 결정론 라우팅과 한국어 리뷰 마커, 실행 경계의 YYYY-MM 정규식, 응답기의 표시 키, LLM 프롬프트의 뷰티 브랜드 페르소나까지. 데이터는 설계된 스키마 없이 **런타임 DDL로 임의 생성한 jsonb kv 테이블 + 파일명 하드코딩 레지스트리**로 다뤄졌고, 하드코딩은 `HARDCODE-OK` 주석 제도로 표식만 붙인 채 잔존했다.

현행은 이를 두 단계로 클렌징했다: **프레임워크 추출(2026-06-19)** — 최대-삭제/최소-골격, 도메인 마커 grep-zero DoD. **기본구조 전환(2026-07-02~)** — 잔존한 강제 코어 수정 지점 5곳을 "빈 카탈로그=inert, 카탈로그 주입 시 활성" 원칙으로 일반화(코어 diff 0 검증), db_design 구도메인 완전 삭제, DB 스택 확정과 시스템 ERD 설계. 결과: **코어 계약=코드, 도메인 선택=YAML/설정 데이터** — 새 도메인은 주입 지점(카탈로그·프롬프트·스코프·소스 레지스트리)을 채우고 Tool 구현체를 등록하면 코어 수정 0으로 온보딩된다. ERD는 구세대에서 "도메인 부산물"(추출 시 23파일 전체 DELETE)이었으나, 현행에서는 "DB 설계는 모든 소프트웨어의 핵심" 헌장 아래 **구현을 선행하는 설계 문서**로 지위가 역전됐다.

## 2. 정량 비교

| 항목 | 구세대 (`docs/_claude/_old`) | 현행 | 변화 |
|---|---|---|---|
| 백엔드 .py | 489파일 / 55,909줄 † | 96파일 / 12,071줄 | **-78%** |
| — 그중 앱 코드(app+api) | 253파일 / 24,046줄 | 91파일 / 11,488줄 | -52% |
| — 테스트 | 165파일 / 20,822줄 (스프린트 단위, 도메인 종속) | 1파일 / 20줄 (부트스모크) | 특성화 벨트 재구축 대상 |
| 프론트 .ts/.tsx | 153파일 / 23,234줄 | 88파일 / 8,176줄 | **-65%** |
| 프론트 features | 25종 | 8종 (agent·execution·hitl·session·navigation·conversations·workflow·portfolio) | 도메인 화면 17종 제거 |
| 프론트 라우트 | 19개 (도메인 전용 9개) | 4개 (`/` `/portfolio` `/workflow` `/conversations`) | -15 |
| team_catalog.yaml | 797줄 (analysis_team 7 agent + qa_team + decision_team) | `teams: {}` 빈 골격 + 주입 스키마 주석 | 도메인 주입 지점화 |
| tools/catalog YAML | 94개 (collection 22종·metrics 37종… 전부 마케팅) | `_schema.yaml` 1개 | 도메인 주입 지점화 |
| LLM tool 프롬프트 | 6종 (전부 마케팅 페르소나, 그중 5종 "화장품/뷰티 브랜드" 명시) | 0 (`tool_prompts/` README 규약만) | 도메인 주입 지점화 |
| 파이프라인 flows YAML | 52개 (대시보드 위젯 1개 = 파이프라인 1개) | 0 (구조 자체 폐기) | — |
| zustand 스토어 | 9종 | 7종 (WS 메시지 fanout 3종: agent·execution·hitl — session 은 연결상태만 수신) | 관찰 fanout 제거 |
| WS zod 유니언 | 13종 | 13종 (계약 승계, memory scope `org`→`workspace`) | 프레임 자산 승계 |

† 구세대 백엔드 .py 는 `backend/_scratch/`(27파일 / 7,188줄, 폐기 작업물) 제외값. 스냅샷 전체는 516파일 / 63,097줄.

## 3. 구세대 진단 — 하드코딩·강제 로직의 실체

### 3.1 백엔드: 도메인이 4-Layer 전 층을 관통

전부 구세대 스냅샷(`docs/_claude/_old/backend/`) 기준 file:line.

| # | 층 | 증거 (구세대 file:line) | 내용 |
|---|---|---|---|
| 1 | 계약 스키마 | `app/dream_agent/schemas/structured_query.py:29,32,49` | TaskType 닫힌 enum에 `sentiment_analysis`·`competitor_comparison`·`budget_optimization` 등 마케팅 작업 어휘. 새 도메인 작업 추가 = 코어 스키마 수정 |
| 2 | 계약 스키마 | `app/dream_agent/schemas/structured_query.py:87-107,125-127` | Source 닫힌 enum에 naver/coupang/oliveyoung/meta/kakao/ga4 등 커머스·광고 채널, Targets에 `brand`/`competitors` 필드 — 코어 계약 = 마케팅 계약 |
| 3 | cognitive | `app/dream_agent/llm_manager/prompts/cognitive.yaml:92-93` | 공용 프롬프트가 domain 어휘를 마케팅 7종(revenue\|ad_performance\|customers\|channel\|conversion\|promotion\|reviews)으로 폐쇄 |
| 4 | planning | `app/dream_agent/planning/planner.py:759,799` | 결정론 라우팅에 팀/에이전트/툴 이름 하드코딩 — 질의응답→`qa_team/qa_agent/qa_responder`, 추천→`decision_team/decision_agent/recommender`. 카탈로그에 이 이름이 없으면 실행기 RuntimeError |
| 5 | planning | `app/dream_agent/planning/planner.py:55,68,386` | 한국어 리뷰 마커 튜플(`"리뷰","후기","평점","댓글"`)이 플래닝 제어 흐름을 결정, tool 이름 문자열(`review*`/`*sentiment*`)이 타입 시스템 역할, 도메인→대표 metric dict(`revenue→revenue_total`)에 `HARDCODE-OK(도메인지식)` 주석 |
| 6 | execution | `app/dream_agent/execution/executor.py:120` | `_PERIOD_RE = ^\d{4}-(0[1-9]\|1[0-2])$` — 월 단위 마케팅 리포트 체계가 실행 경계 정규식으로 강제 |
| 7 | response | `app/dream_agent/response/responder.py:155,421` | 표시 산출 키(`report_markdown`/`answer`/`recommendation_text`)를 하드코딩 열거 — 어휘 밖 키는 성공해도 화면에 안 나옴(실제 `insights` 키 침묵 사고 후 `_render_insights`를 덧댄 이력이 290-294행 docstring에 기록) |
| 8 | response | `app/dream_agent/response/responder.py:101` | `"collector" not in r.tool` — tool 이름 서브스트링이 인프라/표시 판별 규약 |
| 9 | tools | `app/dream_agent/tools/registry.py:84-87` | ToolCategory 닫힌 enum + 미지 카테고리 즉시 raise — 새 도메인 카테고리 등록 자체가 불가 |
| 10 | 프롬프트 | `app/dream_agent/tools/prompts/qa_responder.yaml:4` 외 | LLM tool 프롬프트 6종 전부 마케팅 페르소나("한국 화장품/뷰티 브랜드의 마케팅 분석…" 5종 + 마케팅 요약 1종) |
| 11 | API 역결합 | `api_v2/routes/dashboard1.py:20` | 873줄 마케팅 KPI 라우트가 도메인 tool 클래스 20여 개를 API 계층에서 직접 import. 파일 헤더에 "routes/clumi.py → routes/dashboard1.py (path 가 회사 이름 박힘 정정)" 개명 이력 자인 |

부수 구조: `app/pipelines/flows/` 52개 YAML = 대시보드 위젯 1개당 파이프라인 1개. `_domains/`(26파일 5,649줄)는 코어 import 0건의 "참조 코드 라이브러리" — 등록 메커니즘 없는 복사-붙여넣기 온보딩이며, google_trend_analysis 는 pytrends 시드키워드(Beauty&Fitness)·스케줄러가 하드코딩된 독립 스크립트에 실행 산출물(json/txt)까지 저장소에 포함돼 있었다.

### 3.2 프론트엔드: 데이터 계층 지식의 UI 정적 복제

| # | 증거 (구세대 file:line) | 내용 |
|---|---|---|
| 1 | `src/features/data_model/flowData.ts:1` | 백엔드 스크립트가 자동 생성한 도메인 ERD **6,367줄**(구 프론트 전체의 27%)을 프론트 소스에 복제 — ERD 진실 소스가 프론트/백엔드로 이원화 |
| 2 | `src/features/monthly/types.ts:2` | 백엔드 Pydantic 20모델(KPI 9·MoM 4·Segment 7)을 zod로 1:1 수동 미러 — "backend 모델 변경 시 본 파일도 함께 update" 수기 규약 의존 |
| 3 | `src/features/monthly/KpiGrid.tsx:44` | KPI 산출 방법론을 SQL 조각(`SUM(orders.payment_amount) WHERE order_status != C40…`)까지 UI 상수로 하드코딩 — DB 스키마 변경이 곧바로 프론트 텍스트 수정을 요구 |
| 4 | `src/api/hooks/useMonthlyData.ts:52` | `DEFAULT_CLIENT = 'clumi'` 하드코딩 + `/api/dashboard1/*` 20 엔드포인트 URL 리터럴 직결 |
| 5 | `src/features/monthly/periods.ts:8` | 분석 기간 `'2026-04'` 리터럴 고정 (+ dashboard/trend/channel/cost/creative 5개 페이지 `const PERIOD = '2026-04'`), 기간 선택 UI 없음 |
| 6 | `src/features/marketing-performance/types.ts:77` | 광고 채널 5종(meta/naver_sa/advoost/kakao/talktalk) 라벨·차트색 상수 — 채널 추가·교체 = 코드 수정 |
| 7 | `src/styles/globals.css:56-59` | 전역 디자인 토큰에 `--channel-naver/--channel-kakao/--channel-meta/--channel-google` — 스타일 계층까지 도메인 침투 |
| 8 | `src/features/dashboard/DashboardPage.tsx:60` | 마케팅 퍼널 축(노출수→클릭수→전환수→전환매출, CTR/CVR/객단가)을 코드로 조립 — 화면 구조 자체가 광고 퍼널 전제 |
| 9 | `src/features/workflow/ToolPalette.tsx:2,19` | "90 tool 카탈로그 검색·필터·표시", GROUP_ORDER 8 카테고리 박제 |
| 10 | `src/api/hooks/useTrendOverview.ts:30` 외 | overview 훅 5종은 zod 검증 없이 `as` 캐스팅만 — monthly 20훅(zod parse)과 응답 검증 기준 이원화 |
| 11 | `src/features/agent/actions.ts:40` 주석·예시 | 카드→에이전트 심(seam)의 예시가 마케팅 지표(`[전체 ROAS 0.30× · 2026-04]`) — 중립이어야 할 대화 프로토콜에 도메인 용어 유입 |

### 3.3 근본 원인 — 데이터 계층/ERD 후행의 대가

구세대 코드가 스스로 남긴 자인 기록이 가장 강한 증거다.

- **스키마의 진실 소스가 실행 코드**: `app/data_pg_util.py:76-85`가 `{client}._workspace(layer, key, payload jsonb, meta jsonb)` kv 테이블을 `CREATE TABLE IF NOT EXISTS`로 런타임 생성, 클라이언트 스키마도 즉석 `CREATE SCHEMA`. typed 테이블은 값에서 타입을 추론해 DROP+CREATE하는 표시용 부산물.
- **데이터 카탈로그가 파이썬 dict**: `app/data_sources/file.py`의 SOURCE_REGISTRY가 source_id→클라이언트 데이터 파일명(meta_ads_performance.json, orders.csv…)을 코드 상수로 하드코딩.
- **계약 문서를 코드가 역참조**: `app/dream_agent/tools/shared/semantic_contract.py:23-24`가 `parents[5]/docs/agent_specs/ERD/octorad_canonical_contract_v0.1.yaml`을 런타임 read — 모듈 docstring 스스로 이 contract가 "런타임 read 0건 죽은 문서"였고 단위·함정 정의가 3곳(COL_DESC·canonical_translator·clumi.yaml)에 손복제됐었다고 자인.
- **차원 매핑의 사후 외부화**: `app/data_pilot_project/dimension_maps.yaml` 헤더가 "production 하드코딩 dict를 config로 외부화한 프로토타입"(채널그룹·회원등급·UTM 매핑이 원래 normalizer 코드에 박혀 있었음)을 명시.
- **정합성 기준이 스키마 계약이 아니라 상수 재현**: data_pilot_project의 검증 기준 = 특정 클라이언트 특정 월(2026-04)의 정답값(ad_cost 합 18,306,923원, mer 6.53) 재현.
- **ERD의 지위 = 도메인 부산물**: 프레임워크 추출 시 구 ERD 폴더 23파일이 "octorad raw/canonical"로 전체 DELETE 판정(`.claude/folder_decision_map.md:150`) — 시스템 차원의 DB 설계 문서는 별도로 존재하지 않았다.

## 4. 현행 구조 — 전/후 대응

### 4.1 백엔드 일반화 대응표 (전 항목 현행 코드 대조 확인)

핵심 패턴: **계약=코드, 선택=데이터(YAML/설정)**. 미선언 = dormant/inert, 주입 시 활성.

| 구세대 하드코딩 | 현행 일반화 (file:line) | 메커니즘 |
|---|---|---|
| 플래너 단락 라우팅 (qa_team/recommender 이름 박제) | `backend/app/dream_agent/planning/planner.py:690` | 카탈로그 `routing:` 선언 읽기. 미선언 → None → 3-stage LLM 경로 |
| 팀/에이전트/툴 정의 797줄 | `backend/app/dream_agent/planning/catalog/team_catalog.yaml:54` | `teams: {}` 빈 골격 + routing·subject_bound_artifacts·domain_headline_metric·role 주입 스키마를 주석으로 규정 |
| TaskType 마케팅 enum | `backend/app/dream_agent/schemas/structured_query.py:23` | 도메인 무관 generic 세트, Task.id는 자유 문자열 |
| YYYY-MM 정규식·월 산술·되묻기 4파일 관통 | `backend/app/dream_agent/schemas/scope_params.yaml:28` (`params: {}`) + `structured_query.py:222` (SCOPE_PARAMS 파생) + `planner.py:328` (`_SCOPE_BINDINGS` 전략 registry) | 스코프 파라미터 플러그화 — 공집합 = 프레임 완전 inert. executor 경계검사·planner gap 판정·responder 되묻기가 전부 선언 구동 |
| 표시 산출 키·`collector` 이름 규약 | `backend/app/dream_agent/tools/shared/display.py:18` + `response/responder.py:241` | tool 카탈로그 `display:` 선언(narrative_keys/insight_keys/table_key/attachment/infra) 리졸버. 미선언 tool = `_EMPTY`(inert). 리졸버를 tool 레이어에 둬 의존 하향 불변식 유지 |
| tool 이름별 if/elif 요약 | `backend/app/dream_agent/execution/executor.py:55` | `display.summary_template` 선언 디스패치, 미선언 = 일반 "완료" |
| ToolCategory 닫힌 enum + raise | `backend/app/dream_agent/tools/registry.py:87-91` | open-vocab — non-empty만 강제, 관례 밖 카테고리는 debug 로그 후 수용 |
| layer_inspector의 brand/intent.domain 판독 | `backend/app/dream_agent/system_graph/layer_inspector.py:87` | 구조적 유효성(tasks 또는 intent 존재)만 검사, 확장은 `settings.MEANINGFUL_QUERY_FIELDS` 설정으로만 |
| SOURCE_REGISTRY 파일명 하드코딩 | `backend/app/data_layer/data_sources/file.py:46` | 빈 dict 골격 — 미등록 source_id는 DataSourceNotFound(빈-프레임 정상 동작) |
| 마케팅 페르소나 프롬프트 6종 | `backend/app/dream_agent/tools/tool_prompts/` | README 규약만(파일명=tool명) — LLM tool 프롬프트를 카탈로그 계약과 분리해 도메인이 주입 |

데이터 계층은 `app/data_layer/`로 재편: DataSource(입력)/WorkspaceBackend(출력) 이중 추상 + pushdown v1 계약(File/Postgres 같은답), `DATA_BACKEND` 단일 토글로 lifespan에서 싱글턴 교체 한 번에 File↔Postgres 스왑(`backend/api/main.py:69`, 실패 시 file 유지 = honest degrade), DB는 dreamagent_system(체크포인트·memory) + dreamagent_data(schema-per-client) 2원화.

### 4.2 프론트엔드 대응표

| 구세대 | 현행 (file:line) | 비고 |
|---|---|---|
| 라우트 19 (도메인 9) | 4개 — `frontend/src/routes/router.tsx:5` 툼스톤 "도메인 분석 페이지 + 부가 콘솔/리포트/설정 페이지는 프레임 추출 시 제거" | features 25→8종 |
| flowData.ts 6,367줄 ERD 복제 | 제거 — ERD는 `docs/agent_specs/ERD/` 전용 폴더로 이관 | db-design 잔재도 툼스톤 3곳(router.tsx:17, navigation/store.ts:34, Sidebar.tsx:48)만 |
| client 필수 게이트 (`no_client` 거부) | `frontend/src/features/agent/actions.ts:35` — 사유 폐지, client 미해석 시 generic 모드 전송 | 도메인 데이터 없이도 에이전트 사용 가능 |
| ToolPalette 90 tool·8 카테고리 | `frontend/src/features/workflow/ToolPalette.tsx:4` — 빈 placeholder "도메인 도구는 런타임에 등록" | |
| WS 메시지 fanout 4스토어 (agent·execution·hitl·obsEventLog) | `frontend/src/api/hooks/useWebSocket.ts:22-26` — 관찰 스토어 제거로 3스토어(agent·execution·hitl)로 축소 | "소비자 없는 신호 금지" 헌법 부합 |
| localStorage `octormate.*` | `frontend/src/features/session/store.ts:14` — `dreamagent.*` | 구 제품 식별자 제거 |
| MemoryScope `org` | `frontend/src/api/schemas.ts:52` — `workspace` (커밋 d715e4d) | 회원가입형 DB 설계와 enum 정합 |
| WS zod 유니언 13종 + safeParse 게이트 | `frontend/src/api/ws.ts:36` — 동일 계약 승계 | 구세대의 프레임 자산을 그대로 계승한 대표 사례 |

HITL 스택(PlanReviewModal·pause/resume·todo 편집·DAG 재계산)과 세션 연속성 3중 체계(부팅 정적 복원 + `/state` 스냅샷 rehydrate + 순단 resume_query)도 구세대에서 승계·강화된 프레임 자산이다.

### 4.3 데이터 계층의 위상 역전

| | 구세대 | 현행 |
|---|---|---|
| ERD 지위 | 도메인 부산물 (추출 시 23파일 전체 DELETE) | **구현 선행 설계 문서** — `docs/agent_specs/ERD/` 전용 폴더 헌장 "DB 설계는 모든 소프트웨어의 핵심" (`ERD/README.md:3`) |
| 스키마 생성 | 코드가 런타임 DDL로 즉석 생성 | `system_erd_v0.md`(434줄) 설계 → `setup_checkpointer.py`/`setup_data_db.py` 구현 → 구현 후 진실 소스는 코드로 복귀하는 위상 규약 |
| 설계 검증 | 정답값 상수 재현 | 4관점 적대 리뷰(2026-07-05)로 구현 전 치명결함 2건 교정 — conversations.id UUID→TEXT(코드가 먼저 굳힌 `conv_<8hex>` 포맷과의 충돌), 교차사용자 대화주입 차단 소유권 모델 |
| 벡터/그래프 | (없음 — FAISS 검토 흔적) | PostgreSQL×2 + pgvector 확정, Neo4j·Qdrant는 "Postgres=진실 소스, 파생 저장소, 단계 도입" — 어댑터 뒤에 둬 코어 수정 0 |

코드-선행이 설계를 역구속한 실례가 ERD 문서에 박제돼 있다: 프론트가 이미 `conv_<8hex>` 형식으로 대화 ID를 직렬화·축적해 와서, ERD가 UUID 컬럼을 선언하면 기존 데이터 백필이 실패한다 — 설계가 코드를 따라가야 했던 역전(`system_erd_v0.md` §0.1). 새 도메인이 무문서로 자라는 것을 막는 조항(INDEX 70번대 도메인 밴드 — "구 db_design 도메인이 무문서로 산 전철 방지")도 같은 교훈의 제도화다.

## 5. 전환 방법론 — 어떻게 클렌징했나

### 5.1 프레임워크 추출 (2026-06-19)

근거: `.claude/refactor_plan.md` · `refactor_plan_detailed.md` · `folder_decision_map.md`

- 방침 = **"뼈대만 남기고 필요없는 파일은 최대한 삭제. 단, 부트-경로를 깨지 않으며 데이터/도구 레이어의 추상 골격은 보존"** (`refactor_plan.md:5`)
- 부트-경로 import 폐포 추적으로 살아있는 골격 확정 → KEEP / EMPTY-EDIT / DELETE 3분류. 판정표(`folder_decision_map.md`)를 폴더 단위로 점검·승인 후 실행
- 실행 규율: 수정-전-삭제(import 폭탄 방지), 의존성 역순 Phase 진행(leaf→키스톤), 매 단계 **DB 없는 부트스모크 1줄**(`import api.main; build_graph(None)`)로 그린 유지
- DoD = **도메인 마커(roas/campaign/clumi/octorad…) grep 0건(문서 예시 제외)** (`refactor_plan_detailed.md:189`) — "구세대 흔적 0"을 기계 검증 가능하게 계량화
- enum류는 open-vocabulary 런타임 주입 전략으로 전환 결정

### 5.2 기본구조 전환 (2026-07-02 ~ 진행중)

근거: `docs/system_analysis_and_base_plan_v1.0.md` · `docs/STATUS.md`

1. **시스템 분석 (07-02)** — 서브시스템 딥리더 5 → 평가자 3 → 완전성 비평 1의 병렬 분석(계획서 메타)으로 "새 도메인 = 카탈로그만 채우면 됨"이 아직 거짓임을 증명: 강제 코어 수정 지점 5곳(플래너 단락 라우팅·기간 스코프·표시 어휘·ToolCategory·layer_inspector — 계획서 §4.2) + 리스크 8건 진단 → Phase 0~5 마스터 계획 수립
2. **워크스페이스 개념 확정 (07-02)** — 구 `client`를 재정의: 회사 테넌트가 아니라 "사용자가 고르는 컨텍스트". 공식 구조 = 사용자 1:N workspace, workspace = {데이터 스코프(schema-per-workspace) + 에이전트 지식(prompts/clients→workspaces) + 대시보드 조합(dashboard_spec)}. 테넌트 기계(clients.ts·드롭다운 등)는 휴면 존치 = 재연결 지점. 이 결정이 이후 DB 스택·시스템 ERD·client→workspace rename 의 전제 (STATUS 2026-07-02 결정 기록)
3. **문서 재베이스라인 (07-02)** — agent_specs v1 세대 31개 → v0 세대 26개 재작성/이관(v1 은 `docs/_archive/agent_specs_v1/` 보존), 70번대 도메인 밴드 신설("구 db_design 도메인이 무문서로 산 전철 방지"), **ERD 전용 폴더 신설**("DB 설계는 모든 소프트웨어의 핵심" 헌장). "진실 소스는 코드" 거버넌스를 문서 체계에 적용
4. **코어 일반화 5곳 (07-02)** — "빈 카탈로그=inert, 주입 시 활성" 원칙으로 §4.1의 대응표 구현. 검증은 양방향: 빈 카탈로그 회귀 GREEN + 카탈로그/설정 주입만으로 전 결합점 활성(**코어 diff 0**)
5. **안전망 (07-02~03)** — 채팅 데드락 해제(존재하지 않는 admin API에 입력을 게이트하던 프론트 수정), tsc 빌드 2건 수정, git 연결 + 검증 벨트 GREEN 후 기초 커밋
6. **db_design 구도메인 제거 (07-03)** — 부분 보존안 기각, "죽은 코드 즉시 폐기" 헌법에 따른 완전 삭제. 테스트 공백은 부트스모크의 pytest 승격으로 방지. grep-zero(툼스톤 제외) + pytest 2/2 + vitest 72/72 + build GREEN
7. **DB 스택 확정 (07-03~05)** — PostgreSQL×2 + pgvector 확정(FAISS 폐기) + Neo4j/Qdrant 파생·단계 도입
8. **시스템 ERD 설계 (07-05)** — `system_erd_v0.md` 신설, 적대 리뷰로 치명결함 2건 선제 교정. 현재 DB 스키마 구현 진행중 (순서: DB스키마→문서동기→rename→auth)

### 5.3 전환을 지배한 원칙 (문서 명문화분)

- **진실 소스는 코드** — 문서와 다르면 코드가 맞고 문서를 고친다
- **아키텍처 헌법 정직 불변식 I1~I5** (문서 19) — 성공 위조 금지, honest-degrade, 소비자 없는 신호 금지. mock/stub 실행 경로 폐지 — 미구현은 시끄럽게 실패
- **의존 방향 `api→agent→tool→data` 하향만** (문서 16, grep 0건 불변식)
- **죽은 코드 즉시 폐기** + 제거 시 `(날짜) X 제거 — 사유` 툼스톤
- **빈 카탈로그 = inert, 주입 시 활성** — 도메인 온보딩 = 카탈로그 주입, 코어 수정 0
- 1회성 추출 절차(부트스모크·grep-zero·수정-전-삭제)는 `40_domain_swap_runbook_v0` §4 검증 게이트 G-A~G-E로 일반화 승격

### 5.4 Phase 0~5 현재 상태 (STATUS 대조, 2026-07-10 기준)

| Phase | 내용 | 상태 |
|---|---|---|
| P0 | 안전망 (git·빌드·데드락·특성화 테스트 벨트) | ✅ 부분 완료 — git·빌드·데드락 완료 / P0-3 특성화 테스트 벨트 미구축(§6-8) |
| P1 | 코어 일반화 5곳 | ✅ 완료 — 단 P1-6(LLMClient·repo_root) 부채 잔존 |
| P2 | db_design 제거 | ✅ 완료 |
| P3 | 대시보드 기본구조 | ⬜ 미착수 |
| P4 | 창업 도메인 명세·주입 | ⬜ 미착수 (저장소 내 정의 0건, Q1~Q3 결정 선행) |
| P5 | 운영 기반 (auth·memory·DB) | 🔄 부분 — 시스템 ERD 설계 완료, DB 스키마 구현 진행중 |

## 6. 잔존 과제 — 현행에 남은 구세대 흔적과 부채

전/후 비교에서 드러난, 아직 클렌징이 끝나지 않은 지점. (계획서·STATUS 등재분 포함)

| # | 잔존물 | 위치 | 성격 |
|---|---|---|---|
| 1 | Targets의 `brand`/`product`/`competitors` 필드명 + cognitive 프롬프트의 brand 슬롯(라벨만 "주 대상"으로 일반화) | `backend/app/dream_agent/schemas/structured_query.py:100` 부근 | 구세대 어휘 유산 — 동작엔 무해하나 계약 어휘가 구 도메인 형상 |
| 2 | `_TEXT_INTENT_TASKS`(빈 set)·`_SUBJECT_INTENT_MARKERS`(빈 tuple) — 주석은 "설정-주입"이나 실제로는 코드 상수라 도메인이 채우려면 코어 수정 필요 | `backend/app/dream_agent/planning/planner.py:51,55` | 일반화 미완(주입 경로 부재) |
| 3 | `_SCOPE_FORMATS`에 year_month 1종, `_SCOPE_BINDINGS`에 월 산술 2종만 — 스코프 registry가 아직 구 월-스코프 형상 | `backend/app/dream_agent/schemas/structured_query.py:227` 부근, `planner.py:328` | 새 도메인 스코프(지역/업종/예산 등)는 registry 확장 필요 |
| 4 | 전역 CSS의 `--channel-naver/--channel-kakao/--channel-meta/--channel-google` 토큰이 현행에도 잔존 | `frontend/src/styles/globals.css:71-74,141-144` + `tailwind.config.cjs:97-100` | 구 도메인 색 토큰 — 소비자 확인 후 정리 대상 |
| 5 | TopBar 컨텍스트 토글이 폐기된 `/dashboard`로 navigate + `pathname === '/db'` 체크 | `frontend/src/components/layout/TopBar.tsx:26,87` | 죽은 라우트 참조 |
| 6 | client→workspace rename 미실행 (clientId·useCurrentClient·`?client=` 쿼리 등) | 프론트·백엔드 전반 | DB 스키마 구현과 일괄 예정 — rename 은 2축: 축A identity(client_id→workspace_id UUID, grep-zero DoD) + 축B 물리 schema_name(`ensure_schema` 인자는 UUID 아닌 schema_name, checkpoint 하위호환 분기 포함, `system_erd_v0.md` §5) |
| 7 | LLMClient retry 미사용 + Anthropic 폐기 모델 하드코딩 / data_layer `repo_root=parents[3]` 버그 | `backend/app/dream_agent/llm_manager/client.py` / `backend/app/data_layer/*/__init__.py` | 계획서 P1-6 인정 결함 |
| 8 | 테스트 벨트 최소 상태 — 백엔드 pytest 부트스모크 1파일 | `backend/tests/unit/test_boot_smoke.py` | 특성화 테스트 벨트(계획서 R4) 확충 대상 |
| 9 | conversations 계열 REST 응답이 zod 미적용(`as` 캐스팅) — clients.ts만 zod 검증 | `frontend/src/api/hooks/useConversations.ts` | 구세대 검증 이원화의 축소판 잔존 |

## 7. 결론

구세대의 문제는 "에이전트 프레임이 나빴다"가 아니라 **설계 순서의 역전** — 데이터 계층/ERD 없이 에이전트를 먼저 만들자, 도메인 지식이 갈 곳(카탈로그·스키마·설정)이 없어 코어 코드에 직접 박혔고, 데이터 정합성은 스키마 계약 대신 정답값 상수 재현으로 지탱됐다. 현행 클렌징은 그 역전을 두 방향에서 교정했다: (1) 도메인 지식의 자리를 먼저 만들고(카탈로그·프롬프트·스코프·소스 레지스트리 등 주입 지점, 빈 골격=inert) 코어를 비웠으며, (2) ERD를 도메인 부산물에서 구현 선행 설계로 승격시켰다. 남은 것은 §6의 잔존물 정리와, 이 프레임 위에 첫 도메인(창업 도우미)을 "코어 수정 0"으로 주입해 일반화가 실전 검증되는 일이다.
