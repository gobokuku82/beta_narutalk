# 현재 버전 하드코딩 잔존 감사 v0

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-07-11 |
| 감사 대상 | **현재 버전** = 이 저장소(beta_v0033) 작업 트리 — HEAD `71539bc` + 미커밋 변경(db_design 신규 코드) 포함, `backend/` + `frontend/` |
| 판정 기준 | `docs/legacy_vs_current_comparison_v0.md`(이하 "비교 문서")가 도출한 하드코딩 분류 체계(§3 구세대 진단 22항목 + §6 잔존과제 9건)와 동일 원칙 — "계약=코드, 도메인 선택=YAML/설정", "빈 카탈로그=inert, 주입 시 활성"(빈 골격·주입 스키마 주석·툼스톤은 하드코딩 아님) |
| 분석 방법 | 다중 에이전트 감사: 영역별 파인더 10 + §6 재검증 1 → 원시 발견 141건 → 중복 제거 110건 → **건별 2중 검증(존재확인 + 적대적 반박)** → 누락 비평 → 보완 탐색. 총 에이전트 327개. 결과 **확정 92건 / 기각 63건** (검증 에이전트 오류 1건은 수동 재확인 후 확정에 포함) |
| 관련 문서 | `docs/legacy_vs_current_comparison_v0.md` · `docs/system_analysis_and_base_plan_v1.0.md` · `docs/STATUS.md` |

---

## 0. 질문 해석 — 과거 · 현재 · 미래

사용자 정의에 따른 3세대 구도와 이 감사의 위치:

| 명명 | 실체 | 이 감사에서의 역할 |
|---|---|---|
| **과거** | `docs/_claude/_old/` 스냅샷 (OctorAD 마케팅 시스템) — 현재 트리에 부재 | 하드코딩 분류의 출처(비교 문서 §3) |
| **현재** | **이 저장소(beta_v0033)의 작업 트리** | **감사 대상** |
| **미래** | 현재를 한 번 더 필터링해 만든 별도 프로토타입 | 감사 대상 아님. 단, 비교 문서의 "현행" 서술 일부는 미래 버전에만 구현된 상태를 기술함(§2에서 실증) |

**질문**: "과거↔미래 비교로 파악한 하드코딩 구조가, 현재 버전에도 남아 있는가?"
**답**: **남아 있다.** 그것도 비교 문서가 "해소됐다"(§4.1)고 기록한 코어 지점 다수가 현재 버전에는 미구현 상태로, 구세대(§3.1) 형상 그대로 잔존한다.

## 1. 결론 (TL;DR)

- **확정 92건** (file:line 단위) — 심각도 high 11 / medium 51 / low 30, 분류상 **도메인 잔재 35 / 프레임워크 부채 57**. 논리 이슈로 병합하면 약 60건.
- **최대 발견**: 비교 문서 §4.1이 "현행 일반화 완료"로 기록한 백엔드 코어 5~6곳이 현재 버전에는 **존재하지 않는다** — `scope_params.yaml`·`_SCOPE_BINDINGS`·`tools/shared/display.py`·카탈로그 `routing:` 리더·`MEANINGFUL_QUERY_FIELDS` 전부 파일/grep 0건. 해당 지점은 구세대 §3.1의 #4(결정론 라우팅)·#6(YYYY-MM)·#7(표시 키)·#8(collector 규약)·#9(닫힌 ToolCategory) 형상 그대로다. 즉 **비교 문서의 "현행"은 상당 부분 미래 버전 기준의 서술**이며, 현재 버전의 "코어 일반화 5곳(P1)"은 문서 §5.4의 `✅ 완료`가 아니라 **부분 완료**다(실제 카탈로그 주입이 실재하는 것은 f13a066의 `subject_bound_artifacts`·`domain_headline_metric` 2종).
- §6 잔존과제 9건 재검증: **잔존 7 / 변형 2 / 해소 0**. 특히 #8은 악화 — 문서가 지목한 부트스모크(`test_boot_smoke.py`)가 현재 트리에 없다.
- 문서 이후 추가된 db_design 신규 코드: 구세대형 도메인 하드코딩 유입은 없음. 유일한 구조적 유입은 zod 검증 이원화 확산(`useDbDesign.ts` 6개 API 전부 `as` 캐스팅).
- 그 외 문서 미등재 신규 발견 다수: 죽은 채널/감성 매핑 상수(`CHANNEL_MAP`/`SENTIMENT_MAP`), 버전 4원화, 깨진 wheel 빌드 설정, `USER_ID='demo'` 상수, `errorMessages.ts` 죽은 미러 등.

## 2. 최대 발견 — 비교 문서 "해소 주장" vs 현재 버전 실측

비교 문서 §4.1/§4.2의 전/후 대응표를 현재 코드와 전수 대조한 결과. **✘ = 주장된 메커니즘이 현재 트리에 부재**(모든 부재 판정은 파일 Glob + 전역 grep으로 이중 확인).

| # | 문서의 "현행" 주장 | 현재 버전 실측 | 판정 |
|---|---|---|---|
| 1 | 플래너 단락 라우팅 → 카탈로그 `routing:` 선언 읽기, 미선언=None (`planner.py:690`) | `qa_team/qa_agent/qa_responder`(planner.py:671-673·680), `decision_team/decision_agent/recommender`(:709-711·718) **코드 박제**. `routing` 키를 읽는 코드 backend 전체 0건, `team_catalog.yaml` 주입 스키마에도 없음 | ✘ §3.1-4 그대로 |
| 2 | 스코프 플러그화: `scope_params.yaml`(`params:{}`) + SCOPE_PARAMS 파생 + `_SCOPE_BINDINGS` 전략 registry | 세 가지 모두 부재. `SCOPE_PARAMS = frozenset({"period","period_a","period_b"})` 코드 상수(structured_query.py:186), YYYY-MM 정규식 경계검사(executor.py:120·152-161), 월 산술+MoM 관례(planner.py:259-318), "기간(월)·2026년 4월" 되묻기 문구(responder.py:146-147) | ✘ §3.1-6 그대로 |
| 3 | 표시 키 리졸버 `tools/shared/display.py` + 카탈로그 `display:` 선언 | **display.py 파일 자체 부재**(narrative_keys/insight_keys grep 0건). 표시 키를 responder가 코드로 열거: `report_markdown/answer/recommendation_text`(:153·407-414), `_FILE_ARTIFACTS`(:202-208), `_RENDER_NOISE`(:211-217) — insights 침묵 사고 기전 그대로 | ✘ §3.1-7 그대로 |
| 4 | 요약 선언 디스패치 `display.summary_template` (executor.py:55) | `_generate_summary`(executor.py:41-90)가 구세대 tool 이름 7종 if/elif + 도메인 산출 키(sentiment_distribution·긍정/중립/부정·top_keywords·raw_reviews) 하드코딩 | ✘ §3.1 #7·#8 그대로 |
| 5 | ToolCategory open-vocab — "non-empty만 강제, 관례 밖은 debug 로그 후 수용"(registry.py:87-91) | **정반대**: 닫힌 enum 11종(models/enums.py:19) + 미지 값 즉시 raise(registry.py:83-89, `strict: 알 수 없는 카테고리 = 즉시 raise` 주석) | ✘ §3.1-9 그대로 |
| 6 | layer_inspector 구조 검사 + 확장은 `settings.MEANINGFUL_QUERY_FIELDS` | 해당 설정 grep 0건. `targets.brand` 판독이 COGNITIVE_EMPTY_QUERY fatal 판정에 관여(layer_inspector.py:59·61) — 단 brand∨tasks∨intent 3중 OR라 영향은 국소적 | ✘(주입 경로 부재) |
| 7 | TaskType 도메인 무관 generic 세트 | **확인** — cognitive.yaml의 domain 7종 폐쇄 목록도 실제 제거됨(:56 자유 어휘) | ✔ |
| 8 | `team_catalog.yaml` 빈 골격 + 주입 스키마 | 빈 골격 ✔. 단 코드가 실제로 읽는 주입 키는 `subject_bound_artifacts`·`domain_headline_metric` 2종뿐 — `routing:`·`role:` 주입은 스키마·코드 모두 부재 | △ |
| 9 | SOURCE_REGISTRY 빈 dict 골격 | 빈 골격 ✔ — 단 `repo_root=parents[3]` 버그(§3-H5)로 레지스트리를 주입해도 존재하지 않는 `backend/data/`를 조회해 무력화 | △ |
| 10 | (§4.2) client 필수 게이트 폐지, 미해석 시 generic 모드 전송(actions.ts:35) | actions.ts:58-60이 여전히 `no_client`로 **송신 거부** — 주장된 변경은 어느 브랜치에도 구현된 적 없음 | ✘ |
| 11 | (§4.2) MemoryScope `org`→`workspace` (커밋 d715e4d) | schemas.ts:52는 여전히 `'org'`, 커밋 d715e4d는 git 히스토리에 부재 | ✘ |

> 함의: 위 ✘ 항목들이 미래 버전에 실제 구현돼 있다면, 현재 버전에서의 처방은 재발명이 아니라 **이식(port)** 이다. 비교 문서는 "현행" 표기를 현재/미래 어느 세대 기준인지 명시하도록 정정이 필요하다.

## 3. 심각도 High — 동작 왜곡 또는 새 도메인 온보딩 시 코어 수정 강제 (11건 → 5개 이슈)

### H1. 월-스코프 형상이 코어 4파일을 관통 [도메인 잔재]
- `structured_query.py:186` — `SCOPE_PARAMS = frozenset({"period","period_a","period_b"})` 코드 상수(주입 경로 없음)
- `executor.py:120·152-161` — `_PERIOD_RE = ^\d{4}-(0[1-9]|1[0-2])$`, SCOPE_PARAMS 전 항목에 YYYY-MM(/범위)만 통과, 그 외 전부 SKIPPED
- `planner.py:259-318` — `_prev_month`/`_resolved_month` 월 산술 + `bind_temporal_params`가 "period_a=전월, period_b=당월"(MoM=전월 대비라는 구 리포팅 관례)을 결정론 바인딩. :253의 gap 판정도 SCOPE_PARAMS 결합
- `responder.py:136·146-147` — 되묻기가 어떤 스코프든 "기간(월)" 의미론 + 예시 '2026년 4월'로 고정

**영향**: 일/주/분기/연 단위 기간, YoY 비교, 비시간 스코프(지역/업종/예산)는 schemas+planner+executor(+responder) 동시 수정 없이는 불가. 구세대 "월 단위 마케팅 리포트 체계"(§3.1-6)의 형상이 registry 없이 직접 잔존 — 문서 §6-3의 인정("registry가 월-스코프 형상")보다 실제 결합이 더 강함.

### H2. 결정론 라우팅에 팀/에이전트/툴 이름 박제 [도메인 잔재+부채]
- `planner.py:671-673·680` — factual_lookup → `qa_team/qa_agent/qa_responder`
- `planner.py:709-711·718` — recommendation → `decision_team/decision_agent/recommender`

**영향**: 살아있는 경로다 — cognitive.yaml이 정의/메타 질문에 `factual_lookup`을 도메인 무관하게 emit하고, intent_shim이 RECOMMENDATION을 파생하므로, **빈 카탈로그에서도 해당 쿼리는 존재하지 않는 팀/미구현 tool로 라우팅**된다. 구세대 §3.1-4와 동일 형상("카탈로그에 이 이름이 없으면 실행기 오류").

### H3. 표시·요약 어휘를 카탈로그가 아닌 코드가 소유 [도메인 잔재]
- `responder.py:153·407-414` — 서술 키 `report_markdown/answer/recommendation_text` 폐쇄 열거(어휘 밖 키는 성공해도 화면 침묵 — 문서가 기록한 insights 침묵 사고 기전)
- `responder.py:202-208` `_FILE_ARTIFACTS` / `:211-217` `_RENDER_NOISE` — 파일 키·노이즈 키 코드 사본
- `executor.py:41-90` — tool 이름 7종 if/elif 요약 + `:50` `"collector" in tool_name` 서브스트링 판별 + `:51` 죽은 도메인 키 `raw_reviews`
- **'collector' 서브스트링 규약이 3계층 5개소에 잔존**: executor.py:50 / responder.py:99·318·459 / recovery/manager.py:75 (recovery는 actions.yaml:6의 "감지 기준도 데이터화" 주장과 달리 판별자 자체는 코드)

### H4. ToolCategory 닫힌 enum + 즉시 raise [부채]
- `models/enums.py:19`(11종) + `models/tool.py:41` + `registry.py:83-89`. 새 도메인이 관례 밖 카테고리를 쓰려면 코어 enum 수정 필수. 저장소 자체 결정(open-vocab 전환, 비교 문서 §5.1)과 배치. (완화: 로더가 tool 단위 try/except라 카탈로그 전체 로드가 죽지는 않고 해당 tool만 drop)

### H5. `repo_root = parents[3]` 경로 산술 버그 2건 [부채 — §6-7 등재분 실증]
- `data_layer/data_sources/__init__.py:29` — parents[3]=`backend/`인데 data/는 저장소 루트에 있음(`backend/data` 부재 확인). SOURCE_REGISTRY를 규약대로 주입하는 순간 has()=False → **file 데이터소스 전체가 침묵 무력화**. `setup_data_db.py:49`는 올바르게 루트/data를 계산 — 같은 저장소 안 3자 불일치
- `data_layer/workspace/__init__.py:24` — 동일 버그의 쓰기 판. FileWorkspace가 mkdir로 잘못된 `backend/data/`를 **침묵 생성**해 산출물 트리가 이원화

## 4. 도메인 잔재 — medium/low (구세대 어휘·형상의 잔존)

### 4.1 계약·프롬프트의 커머스 온톨로지 (§6-1 등재 + 코드측 확장)
| 위치 | 내용 |
|---|---|
| `structured_query.py:96-98` | Targets `brand`/`product`/`competitors` 필드 잔존 |
| `llm_manager/prompts/cognitive.yaml:35-37·99` | brand/product/competitors 슬롯 + `missing: ["competitors"]` (라벨만 "주 대상"으로 일반화) |
| `planner.py:643` | `sq.targets.product`를 플래닝 제어 흐름이 직접 소비(현재는 dormant 경로) |
| `cognitive/cognitive_stage.py:73-95` | 클라이언트 프로필 주입 스키마가 마케팅 형상 고정 5필드: `brand_context`·"### 프로모션 코드"·"### 브랜드 특정 은어" — 브랜드/프로모션 개념 없는 도메인은 이 밖의 지식을 주입 못함 |
| `system_graph/layer_inspector.py:59·61·156` | brand 판독 fatal 게이트 + JSONL 요약 brand 키(§3-2의 #6 참조) |

### 4.2 죽은 도메인 상수 — **문서 미등재 신규 발견**
| 위치 | 내용 |
|---|---|
| `tools/shared/helpers.py:17-39` | `CHANNEL_MAP` — 네이버/카카오/메타/쿠팡/올리브영 등 커머스 채널 폐쇄 매핑. grep-zero DoD 폐쇄 목록 어휘가 공용 헬퍼에 잔존, 외부 소비자 0건 |
| `tools/shared/helpers.py:42·98` | `SENTIMENT_MAP` + normalize_sentiment — 리뷰 감성 도메인 어휘, 소비자 0건 |

### 4.3 UI·스타일 (§6-4·5 등재 + 추가)
| 위치 | 내용 |
|---|---|
| `globals.css:71-74·141-144` + `tailwind.config.cjs:96-101` | `--channel-naver/kakao/meta/google` 토큰 8줄 + 유틸리티 클래스 — src 내 소비자 0건인 죽은 도메인 토큰(§6-4 잔존 재확인) |
| `styles/PALETTE.md:55-58` | 위 토큰 HSL 값의 수동 미러 — 이미 드리프트 실증(다크 채널 오버라이드 존재 여부 상충) |
| `components/layout/Sidebar.tsx:23-28` | 제거된 도메인 페이지용 아이콘 14종 import — 주석이 `[marketing-performance]` 등 구 페이지 직지칭 |
| `features/agent/PauseBox.tsx:59` | placeholder 예시 "리뷰 분석" |
| `features/workflow/editing/PropertyPanel.tsx:140·150` | placeholder "예: naver_collector" — 폐쇄 어휘 + 구 collector 명명 규약 |
| `features/navigation/store.ts:26` | 주석의 구 탭 그룹 열거(분석/AI/리뷰/시스템) |

### 4.4 응답 문구·주석 어휘
| 위치 | 내용 |
|---|---|
| `responder.py:146-147·175` | "2026년 4월"(구세대 기준월과 동일) + "채널별 CAC" 마케팅 지표 예시가 사용자 노출 문구에 |
| `data_pg_util.py:102·244` | docstring 예시 `meta_ads_performance.json`, `meta=[campaign_id, …]` |
| `data_layer/data_sources/postgres.py:82` | 삭제된 도메인 tool 2종(kst_timezone_normalizer·ga4_session_aggregator)을 **현재형 필수 consumer로 주장**하는 오도성 docstring |
| `data_layer/workspace/postgres.py:44` | 임계값 근거 주석의 "GA4 traffic" 사고 사례 |

### 4.5 테스트 픽스처 — grep-zero DoD 위반 (테스트 벨트가 클렌징에 뒤처짐)
| 위치 | 내용 |
|---|---|
| `features/agent/actions.test.ts:15-20·34·46-90` | `전체 ROAS`·`2026-04`·`clumi` — 소스(actions.ts)는 이미 중립화됐는데 테스트만 구 어휘 |
| `features/agent/Attachments.test.tsx:8·12`, `store.test.ts:19` | `clumi/outputs/…` 경로 픽스처 |
| `features/agent/SlideView.test.ts:6·13` | "매출·재구매·naver 우위" 마케팅 서사 픽스처 |

## 5. 프레임워크 부채 — medium/low (도메인 무관하나 하드코딩 계열)

### 5.1 이중 진실 소스 (수동 미러 — 다수가 이미 드리프트 실증)
| 이슈 | 위치 | 비고 |
|---|---|---|
| **버전 4원화** | `pyproject.toml:3`(0.1.0) / `config.py:28`(2.0.0) / `main.py:122`·`health.py:28`(2.0.0-alpha) / `.env.example:26`(2.0.0) | 이미 3값으로 발산. settings.APP_VERSION은 소비자 0 |
| 에러 메시지 죽은 미러 | `api/errorMessages.ts` | 진실 소스 경로가 죽은 참조 + 백엔드 12종 중 8종 누락 + 대소문자 미스매치로 매핑 불가 + 소비자 0건 |
| 메모리 스키마 미러 | `api/schemas.ts:53-98` | 소비자 0(광고된 useMemory/useTurns 훅 부재), 백엔드와 enum 이미 드리프트 |
| queryKeys 죽은 규약 | `api/queryKeys.ts` | 소비자 0, 실제 훅은 인라인 키(값도 규약과 불일치) |
| tool 카탈로그 계약 문서 드리프트 | `tools/catalog/_schema.yaml:41·58` | timeout 기본 문서 120 vs 실제 300; version/enum/tags/**enabled**/examples는 로더가 파싱 안 함(enabled:false 침묵 무시), 반대로 storage는 파싱되나 미문서 |
| 확장자→타입 복원 규약 2벌 | `file.py:113-126` vs `postgres.py:293-303` | "1:1" 수기 규약 주석 의존 |
| thread_id 조립 2벌 + 거짓 전제 | `api/thread_id.py:7·20` vs `conversation_manager/manager.py:152` | "UUID라 `_` 안전" 전제가 프론트 `conv_<8hex>` 생성으로 반증(manager.py:7 스스로 자인) |
| todo id·task_type 기본값 각 2벌 | `plan_editor.py:277·197` vs `todo_manager/manager.py:71·78` | NL 경로 'user_added' vs 구조 경로 'custom' |
| 레이어 어휘 3벌 | `workspace/base.py:15` / `workspace/file.py:29-34` / `setup_data_db.py:51` | 단일 소스 파생 없음 — cleanup DROP과 결합 시 위험 |
| 로그 경로 3벌 | `learning_manager/export.py:41-43` vs 각 로거 기본값 | |

### 5.2 죽은 설정 · 주입 경로 부재 ("설정처럼 보이나 바꿔도 무동작" / "주석은 주입, 실제는 코드 상수")
| 이슈 | 위치 | 비고 |
|---|---|---|
| `_TEXT_INTENT_TASKS`·`_SUBJECT_INTENT_MARKERS` | `planner.py:51·55` | §6-2 그대로 — f13a066은 값만 비움, 카탈로그 키 없음 |
| `_INTERPRETATION_TOOLS`·`_COMPUTED_TASKS`·"rows"+startswith | `planner.py:390·396·483` | f13a066 이후에도 남은 G02/G04 계열 코드 상수 — 이름 불일치 시 게이트 침묵 무발동 |
| CORS `["*"]` 리터럴 | `api/main.py:129` | `CORS_ORIGINS` 설정은 소비자 0인 죽은 설정 |
| `DEFAULT_LLM_MODEL/PROVIDER` 소비 0 | `config.py:60-61` | 실효 기본은 `llm_manager/config.py`가 별도 소유 |
| LLMConfig retry/timeout/top_p 미소비 | `llm_manager/config.py:20-27` | §6-7 "retry 미사용" 실증 |
| LAYER_CONFIGS 모델 ID 주입 불가 | `llm_manager/config.py:48·53·59·64` | gpt-5.4-mini/nano 코드 상수 |
| **폐기 Anthropic 모델 + 주입 단절** | `llm_manager/client.py:123` | `claude-3-5-sonnet-20241022` 인라인 + `_generate_anthropic`이 config.model 자체를 안 읽음 → provider=anthropic 즉시 런타임 실패 |
| WS 사용자 식별자 상수 | `frontend/src/api/ws.ts:13` | `USER_ID='demo'` — 전 트래픽·checkpoint·대화 소유권이 단일 pseudo-user로 수렴, ERD의 소유권 모델을 프론트 진입점이 무효화 |
| 기본 언어 'ko' 중복 | `api/ws_agent.py:174·245` | DEFAULT_* 승격 대상 |
| 로거 CWD 상대경로 | `trace_logger.py:48` 외 | settings import만 하고 미사용 |

### 5.3 죽은 라우트·죽은 참조
| 위치 | 내용 |
|---|---|
| `TopBar.tsx:26` | 컨텍스트 토글 '클라이언트' → 폐기된 `/dashboard` navigate (§6-5, 1차 내비게이션이 깨진 상태) |
| `TopBar.tsx:87` | `pathname === '/db'` 영구 false 분기 (§6-5) |
| `Sidebar.tsx:135` | 설정 버튼 → 미등록 `/settings` — §6 미등재 신규 발견 |
| `responder.py:363` | 경로에서 매직 세그먼트 `'data'` 스니핑으로 다운로드 URL 조립 + 대상 `/api/files/download` 라우트가 백엔드에 부재 |
| `data_sources/postgres.py:14` | 적재 규약이 삭제된 `scripts/load_raw_to_data_db.py` 지칭 |
| `frontend/package.json:19` | `test:e2e` — `frontend/e2e` 부재로 실행 즉시 실패(README가 광고 중) |

### 5.4 빌드·배포 리터럴
| 위치 | 내용 |
|---|---|
| `pyproject.toml:39` | `packages = ["test"]` — 존재하지 않는 디렉토리. **빈 wheel이 실제로 빌드됨을 실증**(.venv 설치본에 코드 0파일) |
| `run_server.py:29` | 서빙 포트가 `PORT+1` 산술(8001 직접 지정 불가), 프론트 기대 포트와 주석으로만 결합 |
| `frontend/index.html:10·13` | 폰트 CDN URL 2건(자체 호스팅 P5 부채 자인) — 폐쇄망 배포 시 실패 |
| `setup_data_db.py:50` | EXCLUDE에 구세대 레이아웃 폴더명(pipeline/mock_api/description) 박제 |

### 5.5 로직 부채
- `learning_manager` 3파일 5개소 — `date.replace(day=…)` 월경계 버그의 수동 복제(문서화된 미배선 상태·wiring 선행조건으로 자인됨): trace_logger.py:163-165·240, query_logger.py:146-148·199-201, feedback_collector.py:196-198·229-231
- `conversation_manager/manager.py:53-56` — overall_status 서브스트링 판별에 실존하지 않는 어휘('halt'/'error'/'cancel'/'abort') — enum 미소비 수동 미러
- `recovery/manager.py:135` — 감지 reason은 config 주입인데 payload에는 `"data_insufficient"` 재하드코딩

## 6. 신규 유입 점검 — db_design (비교 문서 이후 추가분)

| 판정 | 내용 |
|---|---|
| **유입 (medium)** | `frontend/src/api/hooks/useDbDesign.ts` — 6개 API 전부 zod 없이 `as` 캐스팅 + BuildReport/QueryResult/IntegrityViolation이 백엔드 응답 shape의 수동 미러 + `maxRows=200`이 백엔드 기본값의 FE 사본. §6-9가 conversations만 지목한 검증 이원화 패턴이 **신규 코드로 확산** |
| 유입 (low) | `backend/api/routes/db_design.py:27` — `_STORE_DIR = parents[3]/var/erd` env/설정 주입 없음 (단 parents[3] 산술 자체는 이 위치에서 정확 — data_layer 버그와 다름) |
| 기각 | 테스트 픽스처의 의원/원장 어휘(구세대 마케팅 아님·프로덕션 미유출), 정수 상한(1000/200/LIMIT 5 — 일반 상수), HR docstring 예시 — 하드코딩 아님 |

**결론**: 신규 코드에 구세대형 도메인 하드코딩 유입은 없음. 다만 "백엔드 스키마의 FE 수동 미러 + as 캐스팅" 패턴이 관성으로 복제되고 있어, 방치하면 구세대 §3.2-2(zod 수동 미러)의 재발 경로가 된다.

## 7. 비교 문서 §6 잔존과제 9건 — 현재 상태 재검증

| # | 항목 | 판정 | 근거 (현재 트리) |
|---|---|---|---|
| 1 | Targets brand/product/competitors + cognitive brand 슬롯 | **잔존** | structured_query.py:96-98, cognitive.yaml:35-37·99 |
| 2 | `_TEXT_INTENT_TASKS`·`_SUBJECT_INTENT_MARKERS` 주입 경로 부재 | **잔존** | planner.py:51·55 — f13a066은 값만 비움, 카탈로그 키 없음 |
| 3 | 스코프 registry 월-형상 | **변형(악화)** | 문서가 기술한 `_SCOPE_FORMATS`/`_SCOPE_BINDINGS`/scope_params.yaml 자체가 부재 — registry 없이 월-스코프가 코드에 직접 잔존(§3-H1) |
| 4 | CSS 채널 토큰 | **잔존** | globals.css:71-74·141-144 + tailwind.config.cjs:96-101 (미커밋 수정에서도 미제거) |
| 5 | TopBar /dashboard·/db | **잔존** | TopBar.tsx:26·87 |
| 6 | client→workspace rename 미실행 | **잔존** | useCurrentClient(clients.ts:43)·clientId(ws.ts 등)·`?client=`(useConversations.ts:41) — 계획된 일괄 rename 대기 상태 그대로 |
| 7 | LLMClient retry 미사용 + 폐기 모델 / repo_root parents[3] | **잔존** | client.py:123, llm_manager/config.py:26-27, data_layer `__init__.py` ×2 (§3-H5) |
| 8 | 테스트 벨트 최소 | **변형(악화)** | 문서가 지목한 `backend/tests/unit/test_boot_smoke.py`가 트리·git 이력에 없음. backend/tests/는 통째 미추적이며 db_design 테스트 1파일뿐 — **부트스모크 소실** |
| 9 | conversations zod 미적용 | **잔존** | useConversations.ts:42·76·107 `as` 캐스팅 (+ useDbDesign으로 확산, §6) |

**해소 0건.** §6은 전부 유효한 백로그다.

## 8. 기각된 주장 63건 — "하드코딩 아님"의 경계 (감사의 반쪽)

적대 검증에서 기각된 대표 계열 — 이후 감사에서 오탐 반복을 막기 위한 기록:

- **빈 골격 = 설계 의도**: tools/prompts/ 디렉토리 부재(주입 시 활성), `_schema.yaml`의 계약 주석, DEGRADE_OPS(안티-할루시 게이트 — tool 주입 시 자동 침묵), planner의 handles_tasks 기본값 등
- **client 어휘 = 도메인 어휘 아님**: client_id/useCurrentClient/`?client=`는 테넌시 계약이며 값은 데이터 기반 — 문제는 rename 미실행(§7-6)이지 하드코딩이 아님
- **env 오버라이드 가능한 기본값**: rest.ts/ws.ts의 `VITE_* ??` 기본값, vite/playwright 설정 파일 내 포트 — 설정 계층 자체
- **프레임워크 자체 계약**: memory scope enum(global/org/user/session — spec 35 정합), data_pg_util의 런타임 워크스페이스 DDL(멀티테넌트 프로비저닝 관용구, 구세대 §3.3과 달리 표시용 파생 캐시로 문서화됨), {label,value,unit} 표시 봉투
- **감사 범위 밖**: `.claude/settings.local.json`(죽은 경로 권한 다수·추적 중 — 위생 정리 대상), `.gitignore` 구세대 주석, 로컬 `.env`의 구세대 키 대량 잔존(미추적)

또한 검증 과정에서 **비교 문서 자체의 서술 오류**가 별도로 확인됐다(§2의 #10·#11): 존재하지 않는 커밋(d715e4d) 인용, 구현된 적 없는 변경(no_client 폐지)의 완료 서술. 문서 정정 대상.

## 9. 권고 우선순위

| 순위 | 작업 | 근거 |
|---|---|---|
| **P0 (버그)** | ① `parents[3]`→`parents[4]` 2건(data_sources·workspace `__init__.py`) ② `client.py:123` 폐기 모델 제거+config.model 소비 ③ `pyproject.toml:39` packages 수정 ④ 부트스모크 복구(§7-8) | 주입 규약을 따르는 순간 침묵 실패하는 지뢰들 |
| **P1 (코어 일반화 — §2의 ✘ 5곳)** | routing 카탈로그화 · 스코프 플러그화 · display 리졸버 · summary 선언 디스패치 · ToolCategory open-vocab (+ layer_inspector 설정화) | "새 도메인 = 카탈로그만 채우면 됨"이 현재 버전에서 성립하려면 필수. **미래 버전에 이미 구현돼 있다면 이식이 최선** |
| **P2 (이중 진실·죽은 설정)** | §5.1~5.3 — 버전 단일화, errorMessages/schemas/queryKeys 정리, collector 규약의 category 기반 전환, CORS/LLM 설정 배선, USER_ID 주입 경로, 죽은 라우트 3건 | 드리프트가 이미 실증된 순서대로 |
| **P3 (어휘 grep-zero 재달성)** | §4 전체 — CHANNEL_MAP/SENTIMENT_MAP 삭제, Targets 어휘 결정(§6-1), CSS 채널 토큰 결정, 테스트 픽스처 중립화, 문구/주석 정리 | 추출 DoD "도메인 마커 grep 0건"의 회복 |
| **P4 (신규 코드 규약)** | useDbDesign zod 스키마화(+useConversations 함께) — "REST 응답은 zod parse" 규약 확정 | §6 확산 차단 |

---

## 10. (2026-07-11 추가) 미래 버전 실측과 이식 방향

미래 버전의 실체가 확인됨: `docs/_claude/futher_v1/` (backend/ + frontend/만 있는 git 미추적 스냅샷). 파일 그룹 16개 병렬 대조 + 병합-안전성 적대 검증 2건으로 실측.

### 10.1 실측 확정

- **futher_v1 = 비교 문서의 "현행"** — 백엔드 96파일/12,071줄로 문서 §2 수치와 정확히 일치. §2 표의 ✘ 항목(routing 카탈로그화·스코프 플러그화·display 리졸버·summary 디스패치·open-vocab 카테고리·MEANINGFUL_QUERY_FIELDS·no_client 폐지·org→workspace) **전부 futher_v1에 실제 구현돼 있음**.
- **병합 안전성 검증 통과**: 현재의 최근 커밋 f13a066(G02/G04 카탈로그 주입)은 미래 planner.py에 완전 포함(1:1 대조). d2846e1(memory_entries)도 미래 setup_checkpointer.py에 DDL 전체 포함 + org→workspace 업그레이드까지 — 현재 고유분은 docstring 진실소스 경로 1줄뿐.
- **미래가 현재의 미커밋 UI 리디자인을 이미 포함**(스냅샷 mtime 2026-07-09) — 디자인 손실 없이 교체 가능.
- 파일 트리 격차: 현재 전용 = db_design 워크벤치 27파일 + storage.py(import 0건 죽은 shim). 미래 전용 = scope_params.yaml · display.py · test_boot_smoke.py 3파일.
- **미래의 역방향 도메인 유입 발견**: portfolio 4파일(WelcomeHero '가려진 경력을 비춰 창업으로 잇다', PersonaCards Operate/Specialist/Foundation, AgentLayerDiagram 창업 4국면)과 TopBar '드림팀' 라벨은 **창업 제품 카피 주입** — 프레임워크-스트립 기준으로는 이식 금지 대상(도메인 주입 지점으로 가야 할 내용).

### 10.2 방향 결론

**현재 저장소(beta_v0033)를 본선으로 유지하고, futher_v1의 개선분을 현재로 선별 이식(back-port)한다.** 근거: (1) futher_v1은 git·루트 인프라(pyproject/run_server/.env)·문서 체계가 없는 부분 스냅샷이라 본선이 될 수 없음, (2) 현재에만 db_design 워크벤치(진행 중 작업)가 있음, (3) 미래 개선분은 파일 단위로 깨끗하게 이식 가능함이 검증됨 — 실질 충돌은 db_design 배선 4곳뿐.

### 10.3 이식 배치 계획 (검증된 파일별 처방)

| 배치 | 내용 | 처방 |
|---|---|---|
| **B1. 백엔드 코어 일반화** (원자 세트 — 상호 import라 반드시 함께) | 신규 복사 3: `schemas/scope_params.yaml`, `tools/shared/display.py`, `tests/unit/test_boot_smoke.py`. 통째 교체 13: structured_query.py, planner.py, team_catalog.yaml, **tools/catalog/_schema.yaml**(open-vocab·display 계약 문서 — 코드와 원자적), executor.py, responder.py, registry.py, models/enums.py·tool.py·__init__.py, layer_inspector.py, helpers.py, prompt_loader.py(+`tool_prompts/README.md` 복사). 삭제 1: `tools/shared/storage.py`(import 0건). 후속 2줄: executor.py docstring 참조 → 10_system_architecture_v1.9.md, **cognitive_stage.py:205 `t.id.value`→`t.id`**(§10.5-C2 크래시 수정) | replace |
| **B2. config/api** | config.py = 미래로 교체(MEANINGFUL_QUERY_FIELDS 신설, 죽은 설정 제거 — 현재 참조 0 확인). main.py = 미래 베이스 + `db_design_router` import/include 2곳 재추가(미래의 제거 주석 폐기, data_db_pool 삭제는 수용). routes/__init__.py = 현재 유지 | merge |
| **B3. checkpointer + org→workspace** | setup_checkpointer.py 미래로 교체 — 실획득 = auth 4테이블(users/auth_sessions/email_verification/password_reset) + workspaces/workspace_members + conversations 인덱스(**pgvector memory_embeddings는 정의만 있고 main():411 주석 처리로 미배선** — 검증 기대값에 넣지 말 것). 후속: docstring 진실소스는 현재 경로(35_DB_SCHEMA_v1.0.md) 유지, **:137 docstring의 stale 'org' 1줄 수정**, **스펙 35 문서의 org 8개소 개정 동반**(안 하면 진실소스가 코드와 모순). `ERD/system_erd_v0.md` 동반 이식은 불가(futher_v1에 docs/ 없음) — 참조 6곳(:135·194·256·298·330·406) 정리로 확정. frontend schemas.ts `org`→`workspace` 반영(런타임 결합 0 확인 — 순서 자유). 로컬 DB memory_entries 0행 실측 — 마이그레이션 불요(방어적 UPDATE 1줄은 선택) | merge |
| **B4. 프론트 게이트 폐지 세트** (타입 유니온 연동 — 함께) | actions.ts, actions.test.ts, CardAsk.tsx, SideChatPanel.tsx 통째 교체(no_client 폐지 → client 옵셔널·generic 모드). 주석 정리 7파일(PauseBox/SlideView/UserBubble/useBubbleProgress/GlobalLayout/hitl store.ts·store.test.ts)도 교체 안전. **선행: 현재 미커밋 리디자인을 먼저 커밋**(기준선 고정) | replace |
| **B5. 선별 체리픽** | Sidebar: /settings 버튼 제거만 채택, **Database 아이콘은 유지**(db-design 탭이 소비 — 미래처럼 지우면 아이콘 침묵 강등). recovery/actions.yaml broaden_period(+3months) 제거 채택. **주석 스크럽 10파일**(명시 열거): ws_agent.py, ws_hitl.py, data_sources/__init__.py·base.py, workspace/__init__.py·base.py, data_pg_util.py, tools/base_tool.py, recovery/manager.py, frontend/src/styles/VOCABULARY.md. **spec-doc 참조 매핑 16파일** = 백엔드 11(connection_manager, error_handler, error_codes, cognitive_stage, planning_stage, response_stage, agent_state, builder, hitl manager·plan_editor, learning decorators) + **프론트 README 5**(api/, workflow/ 3종, routes/ — 현재도 죽은 링크: adr/ 부재, v1.0→v1.2, v1.4→v1.5) — 전부 현재 실존 파일명으로 매핑. **frontend/.env.example 미래판 채택**(run_server_v2 죽은 참조 + localhost→127.0.0.1 결함 수정). 루트 .env.example도 B2와 함께 정리(DATABASE_URL·TITLE_* 3줄 삭제, CORS_ORIGINS·MEANINGFUL_QUERY_FIELDS 항목 추가) | cherry-pick |
| **B6. 이식 금지** | portfolio 4파일(**WelcomeHero, PersonaCards, AgentLayerDiagram, PortfolioPage** — 창업 카피, B5 스크럽으로 오분류 금지)·TopBar '드림팀' 라벨, router.tsx·navigation store의 db-design 삭제분, package.json xlsx 제거분 | keep current |

**전역 선행조건**(B4 전이 아니라 **B1 전**): 미커밋 48파일(UI 리디자인) + 미추적(backend/tests/, backend/app/db_design/, frontend db_design 신규 등)을 **기준선 커밋으로 먼저 고정**하고, 각 배치 커밋은 경로 명시 `git add`로 제한(더러운 트리 위에서 배치를 만들면 WIP가 휩쓸리고 검증 실패의 원인 귀속이 불가능해짐). 각 배치 커밋 메시지에 이식 소스(`docs/_claude/futher_v1` — gitignore 대상이라 저장소에 남지 않음) 명시.

각 배치 후 검증: `pytest`(부트스모크 — B1이 신설; 현재 트리에서도 통과함을 실측 확인) + `pnpm vitest run`(watch 아닌 run 모드 명시) + `tsc`/build. 배치 간 강한 순서 의존 없음이 검증됨(B1↔B2는 getattr 폴백, B3·B4 독립 — B4는 현재 백엔드가 이미 client 부재 시 generic 모드를 지원해 B1 없이도 안전).

### 10.4 이식 후에도 남는 부채 (미래도 미해소 — 별도 백로그)

이식과 무관하게 현재에서 직접 고쳐야 하는 것들: **cognitive_stage.py:205 `t.id.value` AttributeError(§10.5-C2 — P0급, B1 후속으로 수정)**, `parents[3]` 버그 2건, `claude-3-5-sonnet-20241022` 폐기 모델(+config.model 미참조), retry/timeout 미소비, `USER_ID='demo'`, 채널 CSS 토큰, useConversations/useDbDesign zod 이원화, learning_manager 월경계 버그 5개소, CDN 폰트, `_RENDER_NOISE`, `_download_url` 'data' 스니핑, `_TEXT_INTENT_TASKS`/`_SUBJECT_INTENT_MARKERS` 주입 경로 부재, `_COMPUTED_TASKS`·"rows"+startswith, Targets brand/product/competitors, cognitive_stage 프로필 스키마, actions.test 픽스처(ROAS/clumi)·PauseBox '리뷰 분석', TopBar /dashboard·/db 죽은 라우트, 버전 이중 진실(main.py 2.0.0-alpha), DEFAULT_LLM_MODEL 죽은 설정, `_schema.yaml` timeout 120vs300·ghost 필드. 그리고 루트 파일 결함(pyproject packages=["test"], run_server PORT+1)은 미래 스냅샷 범위 밖이므로 당연히 현재에서 수정.

## 10.5 (2026-07-13 추가) 이식 계획 적대 검토 결과

관점별 검토자 7(B1 import 폐포 / 배치 완전성 / B3 결합 / B4 프론트 폐포 / B2 병합 / 동작 변화 / git 절차)로 계획을 재검증. **blocker 0건** — 계획 골격 유지. 정정분은 §10.3에 반영 완료(위 표가 최신). 핵심 실증과 신규 발견:

- **B1 원자성 실증**: B1 15+1파일 교체를 스크래치 사본에 실제 적용 → 전 모듈 import 0실패, 부트스모크 2 passed. 사라지는 심볼 전수(grep)의 외부 소비자 0건, execution_stage.py는 양쪽 byte-identical이고 `_generate_summary` 이름도 미래에 생존 — 개명 파손 없음.
- **C2 신규 크래시 발견 (감사 92건에도 없던 P0급)**: `cognitive_stage.py:205`의 `tasks=[t.id.value for t in sq.tasks]` — 프레임 스트립 후 Task.id는 str이라 **tasks가 비어있지 않은 모든 쿼리가 cognitive 단계에서 AttributeError로 즉사**(pydantic 실측 재현). 현재·미래 공히 존재, 어느 배치도 미수정 → B1 후속 1토큰 수정(`t.id`)으로 등재. 이 크래시 때문에 "현재는 qa_team으로 라우팅된다"는 §3-H2의 런타임 시나리오도 실제로는 도달 전에 죽는다.
- **동작 변화 판정 (5개 시나리오 코드 추적 + 시뮬레이션)**: 현재 tool 카탈로그도 비어 있어(registry count=0 실측) 스코프 강제·되묻기·tool별 요약·recovery 메뉴는 **오늘도 도달 불가** — B1 후 소멸해도 체감 회귀 없음(전부 중립~개선). cognitive 게이트는 "강화"가 아니라 실질 **완화**(모호 쿼리 fatal 해소). 유일한 예고 사항: **도메인 주입 시 scope_params.yaml을 안 채우면 기간 되묻기 UX가 복원되지 않음** — 도메인 주입 체크리스트에 "스코프 되묻기는 scope_params.yaml 선언 필수" 명시.
- **정정 반영 목록**: `_schema.yaml` B1 편입(4개 검토자 공통 — 계약 문서가 코드와 원자적), B3의 pgvector 서술 오류·:137 stale org·스펙 35 개정·ERD 참조 6곳, B5 스크럽 10파일 열거·spec-doc 16파일 확장·frontend/.env.example 편입, 루트 .env.example 정리, B6에 PortfolioPage 명시, 전역 선행 커밋 승격, `vitest run` 명시.
- **비정정 확인 사항**: 라인엔딩은 우려와 달리 무해(미래 파일 대부분 CRLF + autocrlf=true — 전량 diff 발생 안 함). main.py diff에는 계획 미기재 4번째 변경(CORS `["*"]`→`settings.CORS_ORIGINS`)이 있으나 미래 config 기본값이 `["*"]`라 동작 동일 — 되돌리지 말 것. B4의 hitl/store.test.ts는 주석-전용이 아니라 코드 1줄(옵셔널 체이닝) 포함 — 무해. 선재 부채 신규 등재: frontend MemoryTypeSchema 9종 vs DDL memory_type_chk 8종 어휘 불일치(교집합 4종) — MemoryManager 배선 시 CHECK 위반 예정, B3가 두 파일을 여는 적기.

## 10.6 (2026-07-13 추가) 이식 실행 기록 — 완료

§10.3 계획(§10.5 정정 반영)을 전량 실행. 커밋 체인:

| 커밋 | 내용 |
|---|---|
| `70de0bc` | 기준선: UI 리디자인 + db_design 워크벤치 WIP 고정 (66파일) |
| `01859e2` | docs: 비교/감사 문서 등재 |
| `c0ecbb1` | **B1**: 코어 일반화 — 신규 4(scope_params.yaml·display.py·부트스모크·tool_prompts/README) + 교체 13 + storage.py 삭제 + 후속 2(executor 참조 1줄, cognitive_stage.py:205 크래시 수정) |
| `8d0e88b` | **B2**: config.py 교체(MEANINGFUL_QUERY_FIELDS 신설·죽은 설정 제거) + main.py 병합(db_design 라우터 보존, data_db_pool 삭제, CORS 설정 배선) + .env.example 정리 |
| `4df62a5` | **B3**: setup_checkpointer(auth 4테이블+workspaces+conversations, scope org→workspace) + schemas.ts workspace + 스펙 35 org 8개소 개정 + ERD 죽은 경로 참조 정리 |
| `ba43387` | **B4**: no_client 폐지 4파일 연동 + 주석 정리 7파일 + Sidebar /settings 제거(B5 앞당김 — tsc TS2322 차단 해소) |
| `29daf5d` | **B5**: 주석 스크럽 10파일 + recovery broaden_period 제거 + 죽은 spec 참조 매핑(백엔드 5 실수정 + 프론트 README 4 — 나머지 11파일은 현재 참조가 이미 실존 문서라 유지) + frontend/.env.example + 스펙 11 유령 설정 표기 |

**최종 검증**: pytest 6 passed(부트스모크 신설 포함) · vitest run 144 passed(17 files) · tsc -b + vite build GREEN · `qa_team/decision_team/_PERIOD_RE/CHANNEL_MAP` grep = 제거 툼스톤 1건 외 0 · 죽은 spec 참조 grep 0건.

**이로써 해소된 감사 항목**: §3의 H1(월-스코프)~H4(닫힌 enum) 전부 + §2 표의 ✘ 백엔드 5곳 + #10(no_client)·#11(org→workspace) + CHANNEL_MAP/SENTIMENT_MAP + Sidebar /settings + CORS 죽은 설정 + broaden_period + §10.5-C2 크래시. **미해소 잔존(§10.4 백로그 유효분)**: H5 parents[3] ×2, 폐기 모델 claude-3-5, USER_ID='demo', retry 미소비, 채널 CSS 토큰, zod 이원화(useConversations/useDbDesign), 월경계 버그, CDN 폰트, _RENDER_NOISE, 'data' 스니핑, _TEXT_INTENT_TASKS 주입 경로, _COMPUTED_TASKS·rows+startswith, Targets 어휘, 테스트 픽스처(ROAS/clumi), TopBar /dashboard·/db, 버전 이중 진실, pyproject packages, PORT+1, memory type 어휘 불일치(9종 vs 8종).

DB 반영 주의: setup_checkpointer.py는 코드만 이식됨 — 신규 테이블(auth/workspaces/conversations)과 scope CHECK 개명은 **스크립트를 수동 실행해야 DB에 적용**된다(memory_entries 로컬 0행 확인, 멱등).

## 부록 — 확정 발견 전수 목록 (92건)

아래 표는 검증(존재확인+반박)을 통과한 file:line 단위 원자료다. 본문은 이를 논리 이슈로 병합해 서술했다.

| # | 위치 | 심각도 | 분류 | 요지 |
|---|---|---|---|---|
| 1 | `backend/app/data_layer/data_sources/__init__.py:29` | high | 부채 | repo_root 경로 산술 버그 (문서 §6-7 인정 결함, 코드로 재확인). parents[3] = backend/ 인데 data/는 저장소 루트(beta_v0033/data)에 있음 — bac… |
| 2 | `backend/app/dream_agent/execution/executor.py:120` | high | 도메인 잔재 | 실행 경계에 YYYY-MM 월 형식 정규식이 그대로 잔존 — 구세대 진단 §3.1-6에서 지목한 것과 동일 형상. _param_boundary_issue(:152-161)가 SCOPE_PARAMS … |
| 3 | `backend/app/dream_agent/models/enums.py:19` | high | 부채 | ToolCategory가 닫힌 enum(11종) + 미지 값 즉시 raise 형상 그대로 잔존. ToolSpec.category 타입이 이 enum(models/tool.py:41)이고, tools… |
| 4 | `backend/app/dream_agent/planning/planner.py:259` | high | 도메인 잔재 | 월 산술(_prev_month 259-267행, _resolved_month 의 YYYY-MM 파싱 270-288행)과 bind_temporal_params 의 'period'/'period_a'/… |
| 5 | `backend/app/dream_agent/planning/planner.py:260` | high | 도메인 잔재 | 코어 플래닝에 월 산술이 하드코딩: _prev_month(:259-267) 월 감산, _resolved_month(:270-288) YYYY-MM 파싱·정규화, bind_temporal_params… |
| 6 | `backend/app/dream_agent/planning/planner.py:267` | high | 도메인 잔재 | _prev_month(259-267행)·_resolved_month(270-288행)가 YYYY-MM 강제 파싱·zero-pad 정규화·전월 산술을 planner 코어에 인라인 구현. 비교문서 §4… |
| 7 | `backend/app/dream_agent/planning/planner.py:671` | high | 도메인 잔재 | QA short-circuit(_build_qa_plan, factual_lookup 트리거)이 team="qa_team"/agent="qa_agent"/tool="qa_responder"(671-… |
| 8 | `backend/app/dream_agent/planning/planner.py:709` | high | 부채 | recommendation short-circuit(_build_recommendation_plan)이 team="decision_team"/agent="decision_agent"/tool="re… |
| 9 | `backend/app/dream_agent/response/responder.py:153` | high | 도메인 잔재 | 표시 산출 키 하드코딩 열거가 구세대 §3.1#7(구 responder.py:155)과 사실상 동일 형태로 잔존 — build_display_payload에도 반복(407 summary, 412 r… |
| 10 | `backend/app/dream_agent/response/responder.py:412` | high | 도메인 잔재 | 표시 산출 키(report_markdown/answer/recommendation_text, 412-414행)를 코드에 하드코딩 열거 — 어휘 밖 키는 성공해도 침묵(구세대 §3.1-7 사고 패턴)… |
| 11 | `backend/app/dream_agent/schemas/structured_query.py:186` | high | 도메인 잔재 | 스코프 파라미터 레지스트리가 코드 상수(frozenset)로 하드코딩. 비교 문서 §4.1은 'scope_params.yaml:28 (params: {}) + structured_query.py:2… |
| 12 | `.env.example:26` | medium | 부채 | Third (and conflicting) copy of version truth: backend/app/core/config.py:28 has APP_VERSION: str = "2.0.0", w… |
| 13 | `backend/api/main.py:122` | medium | 부채 | 버전 문자열 이중 진실: settings.APP_VERSION("2.0.0", env 오버라이드 가능)이 있는데 main.py:122와 health.py:28("version": "2.0.0-alp… |
| 14 | `backend/api/main.py:129` | medium | 부채 | CORS 오리진을 코드에 ["*"] 리터럴로 하드코딩. config.py:87에 CORS_ORIGINS 설정(env 오버라이드 가능)이 존재하지만 어디에서도 주입되지 않는 죽은 설정 — "설정은 있… |
| 15 | `backend/api/thread_id.py:7` | medium | 부채 | '두 ID 모두 UUID v4라 _ 구분자 안전' 전제가 거짓: 프론트 session/store.ts:19가 `${prefix}_${uuid.slice(0,8)}`로 conv_<8hex> 형식 ID… |
| 16 | `backend/api/ws_agent.py:174` | medium | 부채 | 기본 언어 "ko" 리터럴이 API 경계 2곳(:174, :245)에 중복 하드코딩 — env/설정 오버라이드 경로 없음. 도메인-무관 프레임워크 선언과 달리 한국어 배포 전제가 코드 기본값으로 박… |
| 17 | `backend/app/core/config.py:61` | medium | 부채 | settings.DEFAULT_LLM_MODEL / DEFAULT_LLM_PROVIDER(60행)는 소비처 0건(backend 전체 grep — 정의부 외 참조 없음). 실효 기본은 llm_mana… |
| 18 | `backend/app/data_layer/data_sources/postgres.py:293` | medium | 부채 | 확장자→타입 복원 규약(.csv→DataFrame/.json→dict\|list/.jsonl→list/.sql→str)이 FileDataSource.get(file.py:113-126)과 Postgr… |
| 19 | `backend/app/data_layer/workspace/__init__.py:24` | medium | 부채 | 위와 동일한 parents[3] 버그의 workspace 판. 더 나쁜 점: FileWorkspace._dir(file.py:42)이 mkdir(parents=True, exist_ok=True)를… |
| 20 | `backend/app/dream_agent/cognitive/cognitive_stage.py:79` | medium | 도메인 잔재 | _build_client_block(73-95행)이 클라이언트 프로필 주입 스키마를 마케팅 형상 필드명으로 코드에 하드코딩: brand_context(79행)·promotions '### 프로모션 … |
| 21 | `backend/app/dream_agent/execution/executor.py:50` | medium | 도메인 잔재 | tool 이름 서브스트링 'collector'가 타입 판별 역할(수집 tool 여부) 수행 + 바로 아래 줄(51)에서 도메인 산출 키 raw_reviews를 하드코딩 참조. 구세대 §3.1#8 규… |
| 22 | `backend/app/dream_agent/execution/executor.py:60` | medium | 도메인 잔재 | _generate_summary(41-90)가 tool 이름별 if/elif 요약 템플릿 체인 유지: text_preprocessor/sentiment_analyzer/keyword_extracto… |
| 23 | `backend/app/dream_agent/llm_manager/client.py:123` | medium | 부채 | Anthropic 경로의 모델 ID가 인라인 리터럴로 박혀 있고(폐기 세대 claude-3-5-sonnet-20241022), _generate_anthropic이 self.config.model을… |
| 24 | `backend/app/dream_agent/llm_manager/config.py:26` | medium | 부채 | LLMConfig가 max_retries/retry_delay_sec(27행)/timeout_sec(23행)/top_p(20행)를 선언하지만 client.py 어디에서도 소비하지 않음(재시도 루프·… |
| 25 | `backend/app/dream_agent/llm_manager/config.py:48` | medium | 부채 | LAYER_CONFIGS 4개 레이어의 모델 ID(gpt-5.4-mini ×3: 48/53/59행, gpt-5.4-nano: 64행)가 env/설정 오버라이드 경로 없는 코드 상수. settings… |
| 26 | `backend/app/dream_agent/planning/planner.py:51` | medium | 부채 | 주석은 '설정-주입(도메인 등록)'이라 하나 실제로는 모듈 레벨 코드 상수이며 카탈로그/설정에서 읽는 주입 경로가 전무(f13a066은 값만 비웠고 subject_bound_artifacts와 달리… |
| 27 | `backend/app/dream_agent/planning/planner.py:55` | medium | 부채 | 구세대 한국어 도메인 마커 튜플(리뷰/후기/평점/댓글)은 f13a066에서 제거됐으나, 대체물이 '설정-주입' 주석의 빈 코드 tuple이라 주입 경로 부재는 동일. _has_text_intent(… |
| 28 | `backend/app/dream_agent/planning/planner.py:309` | medium | 부채 | bind_temporal_params가 스코프 param 이름 리터럴 "period_a"/"period_b"/"period"(309·310·313·317행)와 'period_a=전월, period_… |
| 29 | `backend/app/dream_agent/planning/planner.py:390` | medium | 부채 | G04(ensure_interpretation_fed) 게이트가 해석 tool을 카탈로그 role 선언이 아닌 코드 상수의 정확한 이름 3종으로 식별. f13a066이 headline metric은… |
| 30 | `backend/app/dream_agent/planning/planner.py:396` | medium | 부채 | G04의 '계산된 산출' 판별이 코드 상수의 닫힌 task_type 3종. f13a066이 마케팅 task(sentiment_analysis 등)를 generic으로 바꿨으나 여전히 코드 상수 — … |
| 31 | `backend/app/dream_agent/planning/planner.py:483` | medium | 부채 | enforce_breakdown_dimension이 (a) 매직 artifact 리터럴 "rows"를 '차원분해 tool' 판별 신호로, (b) tool 이름이 쿼리 dimension 토큰으로 시작… |
| 32 | `backend/app/dream_agent/response/responder.py:99` | medium | 부채 | tool 이름 서브스트링 'collector'가 인프라/분석 판별 규약으로 3곳에서 반복(99 부분성공 판정, 318 skipped 고지 제외, 459 '완료 둔갑 금지' 게이트) — docstri… |
| 33 | `backend/app/dream_agent/response/responder.py:146` | medium | 도메인 잔재 | 스코프 미바인딩 되묻기(build_missing_period_payload)가 '기간(월)' 의미론과 예시 날짜 '2026년 4월'을 코드에 하드코딩(146-147) — 스코프 param이 선언 구… |
| 34 | `backend/app/dream_agent/response/responder.py:202` | medium | 부채 | 파일 산출 artifact 키→kind 매핑(pdf_file_path/excel_file_path/pptx_file_path/designed_pptx_path/word_file_path, 202-2… |
| 35 | `backend/app/dream_agent/response/responder.py:211` | medium | 부채 | metric 렌더 제외 키 목록(count/file_no/source_id/word_count/report_markdown/summary/schema_version/op/field 등, 211-21… |
| 36 | `backend/app/dream_agent/response/responder.py:363` | medium | 부채 | _download_url이 산출물 경로에서 매직 디렉토리명 'data' 세그먼트를 스니핑해 다운로드 URL(/api/files/download?p=)을 조립 — 워크스페이스 저장 루트 이름이 설정 … |
| 37 | `backend/app/dream_agent/system_graph/layer_inspector.py:59` | medium | 도메인 잔재 | 구 도메인 어휘 'brand'가 '의미 있는 쿼리' 판정 제어 흐름을 담당 — targets.brand 유무가 COGNITIVE_EMPTY_QUERY fatal 판정을 좌우(:61)하고, 요약 함수… |
| 38 | `backend/app/dream_agent/tools/catalog/_schema.yaml:41` | medium | 부채 | 스키마는 timeout_sec 기본값을 120초로 문서화하나 실제 로더 기본값은 300초(registry.py:120 data.get("timeout_sec", 300), ToolSpec.timeo… |
| 39 | `backend/app/dream_agent/tools/catalog/_schema.yaml:58` | medium | 부채 | 스키마가 계약으로 문서화한 필드 중 version(:17), parameters[].enum(:37), tags(:57), enabled(:58), examples(:62-65)를 registry.… |
| 40 | `backend/app/dream_agent/tools/registry.py:84` | medium | 부채 | 카탈로그 category를 닫힌 ToolCategory enum으로 파싱하고 미지 값이면 즉시 raise(86-89행 'Unknown category ... Valid = [...]') — 구세대 … |
| 41 | `backend/app/dream_agent/tools/registry.py:87` | medium | 부채 | ToolCategory 닫힌 enum + 미지 카테고리 즉시 raise(83-89행, 구세대 §3.1-9 패턴) — 새 도메인 카테고리 등록이 코어 enums.py 수정 없이는 불가. 문서 §4.1… |
| 42 | `backend/app/dream_agent/workflow_managers/conversation_manager/manager.py:152` | medium | 부채 | Re-implements the thread_id composition convention inline instead of using the canonical builder backend/api/t… |
| 43 | `backend/app/dream_agent/workflow_managers/hitl_manager/plan_editor.py:197` | medium | 부채 | Two divergent hardcoded defaults for the same concept (user-added todo classification label): the NL edit path… |
| 44 | `backend/app/dream_agent/workflow_managers/hitl_manager/plan_editor.py:277` | medium | 부채 | Todo-id format 'todo_%03d' is generated in two independent implementations with different collision strategies… |
| 45 | `backend/app/dream_agent/workflow_managers/learning_manager/export.py:41` | medium | 부채 | LearningDataExporter re-declares all three logger directory literals (lines 41-43: logs/traces, logs/queries, … |
| 46 | `backend/app/dream_agent/workflow_managers/learning_manager/feedback_collector.py:197` | medium | 부채 | Month-boundary bug in the 7-day feedback lookback (get_session_feedback, lines 196-198; duplicated in get_aver… |
| 47 | `backend/app/dream_agent/workflow_managers/learning_manager/trace_logger.py:48` | medium | 부채 | CWD-relative output directory literal with no config/env injection: the singleton get_trace_logger() always co… |
| 48 | `backend/app/dream_agent/workflow_managers/learning_manager/trace_logger.py:240` | medium | 부채 | Broken month-boundary date arithmetic hardcoded into cleanup_old_files: with default days=30, cutoff.day > 30 … |
| 49 | `backend/app/dream_agent/workflow_managers/recovery/actions.yaml:9` | medium | 부채 | Config comment codifies the collector-substring convention as the meaning of no_other_output, but only the boo… |
| 50 | `backend/app/dream_agent/workflow_managers/recovery/manager.py:75` | medium | 부채 | Third live copy of the 'collector' substring convention: tool-name string matching acts as the type discrimina… |
| 51 | `backend/scripts/setup_data_db.py:51` | medium | 부채 | 레이어 어휘(raw/normalized/computed/blended)가 4곳에 독립 상수로 미러: workspace/base.py:15 Layer Literal, workspace/file.py:… |
| 52 | `frontend/src/api/errorMessages.ts:9` | medium | 부채 | 백엔드 error 카탈로그의 수동 미러(기준 10)가 실제로 드리프트됨: (a) 헤더(line 5)가 가리키는 진실 소스 'backend/api/error_codes.py'는 존재하지 않음 — 20… |
| 53 | `frontend/src/api/hooks/useConversations.ts:42` | medium | 부채 | conversations 계열 REST 3개 응답 전부 zod 미적용 `as` 캐스팅: line 42 as ConversationList, line 76 as ConversationTurns, li… |
| 54 | `frontend/src/api/hooks/useDbDesign.ts:13` | medium | 부채 | 신규 코드(미커밋 변경 포함, db-design 워크벤치)가 zod 검증 없이 `as` 캐스팅만으로 6개 API 전부 처리: line 13/20 as ErdDesign, line 24 as { na… |
| 55 | `frontend/src/api/queryKeys.ts:6` | medium | 부채 | Query Key 규약 모듈의 소비자가 frontend/src에 0건(README 예시 제외) — 실제 훅은 인라인 리터럴 키를 사용하며 규약과 값도 다름: useConversations.ts:37… |
| 56 | `frontend/src/api/schemas.ts:65` | medium | 부채 | MemoryEntrySchema·MemoryTypeSchema(9종 닫힌 enum)·WorkflowTemplateContentSchema·ParamSlotSchema 블록의 소비자가 0건 — REA… |
| 57 | `frontend/src/api/ws.ts:13` | medium | 부채 | 양 WS 채널(/ws/agent, /ws/hitl)의 user_id가 코드 상수 'demo'로 고정. 주석은 'Sprint 16+ 로그인 도입 시 useSession에서 주입'이라 하나 현재 주입 … |
| 58 | `frontend/src/components/layout/Sidebar.tsx:135` | medium | 부채 | Sidebar 하단 '설정' 버튼이 존재하지 않는 '/settings' 라우트로 navigate (router.tsx 에 미등록). 문서 §6 에 없는 미등재 죽은 라우트 — TopBar '/das… |
| 59 | `frontend/src/components/layout/TopBar.tsx:26` | medium | 부채 | 컨텍스트 토글의 '클라이언트' 버튼이 폐기된 '/dashboard' 라우트로 navigate. router.tsx 에는 /, /portfolio, /workflow, /conversations, /… |
| 60 | `frontend/src/styles/PALETTE.md:55` | medium | 도메인 잔재 | src 내 팔레트 문서가 채널 토큰 4종(55-58행: 네이버 녹/kakao 노랑/메타 파랑/구글 빨강)의 HSL 값을 수동 복제 — globals.css 와의 이중 진실 소스(판정 기준 10)이자… |
| 61 | `pyproject.toml:39` | medium | 부채 | hatchling wheel 타깃이 존재하지 않는 디렉토리 'test'를 가리킴 — 저장소 루트에는 backend/와 tests/만 존재 (test/ 부재 직접 확인). `uv build`/`pip… |
| 62 | `run_server.py:29` | medium | 부채 | 실제 서빙 포트가 env로 직접 지정 불가한 'PORT+1' 산술로 코드에 박힘. PORT=8000이면 8001로 뜨는 규약이 프론트 기본 연결(127.0.0.1:8001)과 주석으로만 결합 — P… |
| 63 | `backend/api/routes/db_design.py:27` | low | 부채 | Persistence root for ERD designs and built SQLite DBs is a module-level literal (repo_root/var/erd) computed w… |
| 64 | `backend/app/data_layer/data_sources/postgres.py:14` | low | 부채 | raw 적재 경로 규약으로 명시된 scripts/load_raw_to_data_db.py가 존재하지 않음 (backend/scripts/ = __init__, setup_checkpointer, s… |
| 65 | `backend/app/data_layer/data_sources/postgres.py:82` | low | 도메인 잔재 | 도메인 마커 ga4 + 프레임 추출 때 삭제된 마케팅 도메인 tool 2종(kst_timezone_normalizer, ga4_session_aggregator)을 '현재 필수 consumer'로 … |
| 66 | `backend/app/data_layer/workspace/postgres.py:44` | low | 도메인 잔재 | STREAM_ROUTE_THRESHOLD 상수의 근거 설명에 구 도메인 마커 'GA4 traffic' 잔존. 제거 툼스톤이 아니라 현행 임계값의 정당화 주석이므로 면제 대상 아님 — 사고 사례를 도… |
| 67 | `backend/app/data_pg_util.py:102` | low | 도메인 잔재 | typed_table_name docstring 예시가 구세대 SOURCE_REGISTRY의 마케팅 파일명(meta_ads_performance.json)을 그대로 사용 — §3.3이 진단한 '파일… |
| 68 | `backend/app/data_pg_util.py:244` | low | 도메인 잔재 | write_relational_table의 파라미터 규약 설명이 마케팅 도메인 예시(meta 광고, campaign_id)로 작성됨 — 도메인 마커 폐쇄 목록(meta/campaign) 잔존. 커밋… |
| 69 | `backend/app/dream_agent/llm_manager/prompts/cognitive.yaml:35` | low | 도메인 잔재 | targets 스키마의 brand(35행)/product(36행)/competitors(37행) 슬롯 + missing 규칙의 ["competitors"](99행)가 구 도메인 계약 어휘로 잔존 —… |
| 70 | `backend/app/dream_agent/planning/planner.py:643` | low | 도메인 잔재 | planner 제어 흐름(_has_text_intent)이 구세대 커머스 계약 어휘 필드 Targets.product를 직접 소비. 스키마 필드 자체는 §6 #1 등재(brand/product/co… |
| 71 | `backend/app/dream_agent/response/responder.py:175` | low | 도메인 잔재 | 사용자 노출 next_action 문구에 마케팅 지표 어휘 '채널별 CAC'(고객획득비용)와 특정 기간 리터럴 '2026년 4월'이 하드코딩 — 도메인-무관 프레임워크의 응답층 코드에 마케팅 예시가… |
| 72 | `backend/app/dream_agent/schemas/structured_query.py:96` | low | 도메인 잔재 | 코어 계약 Targets가 구 마케팅 형상 필드(brand :96 / product :97 / competitors :98)를 유지 — '브랜드·제품·경쟁사'라는 커머스 온톨로지가 도메인-무관이어야… |
| 73 | `backend/app/dream_agent/tools/shared/helpers.py:17` | low | 도메인 잔재 | 커머스/광고 채널 폐쇄 매핑(네이버→naver, 카카오→kakao, 메타/페이스북/인스타→meta, 구글, 유튜브, 쿠팡→coupang, 올리브영→oliveyoung, 17-39행)이 프레임워크 공… |
| 74 | `backend/app/dream_agent/tools/shared/helpers.py:42` | low | 도메인 잔재 | 리뷰 감성 라벨 매핑(긍정/중립/부정→positive/neutral/negative)과 normalize_sentiment(98)가 공용 헬퍼에 잔존 — 구세대 리뷰/평점 분석 도메인의 어휘. 감성… |
| 75 | `backend/app/dream_agent/workflow_managers/conversation_manager/manager.py:53` | low | 부채 | Substring matching against overall_status plays the role of a status discriminator, mirroring a vocabulary tha… |
| 76 | `backend/app/dream_agent/workflow_managers/learning_manager/query_logger.py:147` | low | 부채 | Same date.replace(day=...) month-boundary arithmetic copied a third time (get_popular_queries lines 146-148, g… |
| 77 | `backend/app/dream_agent/workflow_managers/recovery/manager.py:135` | low | 부채 | detect_recovery hardcodes reason 'data_insufficient' into the interrupt payload context even though the detect… |
| 78 | `backend/scripts/setup_data_db.py:50` | low | 부채 | data/ 하위에서 client 스키마 후보를 고르는 규칙이 구세대 데이터 폴더 레이아웃 지식(pipeline·mock_api·description — mock_api는 구 mock 수집기 잔재 어… |
| 79 | `frontend/index.html:10` | low | 부채 | 폰트를 외부 CDN URL 리터럴 2건(10행 jsdelivr Pretendard, 13행 fonts.googleapis.com JetBrains Mono)에 의존 — 8-9행 주석 스스로 '자체 … |
| 80 | `frontend/package.json:19` | low | 부채 | Script consumer of the dead playwright config — invoking it fails because frontend/e2e does not exist. Part of… |
| 81 | `frontend/src/components/layout/Sidebar.tsx:27` | low | 도메인 잔재 | ICON_MAP 이 제거된 도메인 페이지용 아이콘 14종을 계속 import/등록 — 주석 마커가 구 도메인 페이지를 직지칭([marketing-performance]=27행, [monthly]=2… |
| 82 | `frontend/src/components/layout/TopBar.tsx:87` | low | 부채 | 폐기된 '/db'(Data DB 콘솔) 라우트 pathname 체크 잔존 — router 에 /db 가 없어 조건이 영구 false 인 죽은 분기. 문서 §6 #5 등재 항목 재확인. |
| 83 | `frontend/src/features/agent/Attachments.test.tsx:8` | low | 도메인 잔재 | 첨부 칩 테스트 픽스처 URL 에 구 클라이언트 식별자 'clumi' 경로 잔존(12행 기대값에도 동일) — 구세대 특정 고객 데이터 경로가 테스트에 박제. |
| 84 | `frontend/src/features/agent/PauseBox.tsx:59` | low | 도메인 잔재 | todo NL 편집 placeholder 예시에 구세대 마케팅 어휘 '리뷰 분석' 잔존 — 구 planner 의 리뷰 마커 튜플('리뷰','후기','평점')과 같은 계열 어휘가 중립 UI 예시로 유… |
| 85 | `frontend/src/features/agent/SlideView.test.ts:6` | low | 도메인 잔재 | 슬라이드 파서 테스트 픽스처가 마케팅 서사(월 보고서·매출·재구매·채널·naver)로 고정 — 폐쇄 목록 어휘 'naver' 포함(13행 기대값에도 'naver 우위'). |
| 86 | `frontend/src/features/agent/actions.test.ts:16` | low | 도메인 잔재 | askAgent seam 테스트 픽스처가 마케팅 도메인 어휘로 고정: '전체 ROAS'(16행), period '2026-04'(18행), 기대값 '[전체 ROAS 0.30× · 2026-04]'(… |
| 87 | `frontend/src/features/agent/actions.test.ts:52` | low | 도메인 잔재 | API 계층(sendQuery @/api/ws)의 계약을 검증하는 테스트에 구세대 도메인 마커가 잔존: line 15-20 CTX = { metric: '전체 ROAS', period: '2026-… |
| 88 | `frontend/src/features/agent/store.test.ts:19` | low | 도메인 잔재 | agent store 테스트 픽스처에도 'clumi/outputs' 클라이언트 경로 리터럴 잔존 — Attachments.test 와 동일 계열. |
| 89 | `frontend/src/features/navigation/store.ts:26` | low | 도메인 잔재 | NavigationTab.group 필드 주석이 구세대 도메인 탭 그룹 목록(분석/AI/리뷰/시스템)을 열거 — '리뷰' 는 도메인 마커 폐쇄 목록 어휘. 현행 SYSTEM_TABS/CLIENT_T… |
| 90 | `frontend/src/features/workflow/editing/PropertyPanel.tsx:150` | low | 도메인 잔재 | todo 편집 패널의 tool 입력 placeholder 에 구 마케팅 도메인 어휘 'naver' + 구세대 collector 명명 규약이 예시로 박힘(140행 '예: analyst, collect… |
| 91 | `frontend/src/styles/globals.css:71` | low | 도메인 잔재 | 구 마케팅 광고 채널 4종(naver/kakao/meta/google) 색 토큰이 전역 디자인 토큰에 잔존 (라이트 71-74행 + 다크 테마 141-144행 총 8줄). frontend/src 전… |
| 92 | `frontend/tailwind.config.cjs:97` | low | 도메인 잔재 | Tailwind 색상 확장에 channel.naver/kakao/meta/google 4종(96-101행)이 유틸리티 클래스(bg-channel-naver 등)로 노출, 직전 95행 주석 '// 매… |
