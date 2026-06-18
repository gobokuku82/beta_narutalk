# 17. Functions → Agents → Tools → Data → I/O — 종단 매핑

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 아키텍처 (10대) |
| 진행상태 | Active |
| 버전 | **v1.0** |
| 최종 수정일 | 2026-05-18 |
| 독자 | "기능 1개가 어디서 시작해 어디서 끝나는가" 한 흐름으로 보고 싶은 사람 |
| 자매 문서 | [14 System Agent Overview](14_system_agent_overview_v1.0.md) (Layer 관점) · [15 End-to-End Flow](15_end_to_end_flow_v1.0.md) (시간 축) · **본 문서 (계층 종단 축)** |

---

## 0. 본 문서의 역할

> **5단계 종단 매핑** — 마케터 기능 → 에이전트 → 툴 → 데이터 → I/O 메커니즘 한 페이지.

다른 spec 은 한 단계만 다룸:
- 14 = Layer 책임 (Cognitive/Planning/Execution/Response)
- 15 = 시간축 sequence (query → 응답)
- 30 = Pydantic 데이터 모델
- 31/32 = Tool 카탈로그 / 구현 현황

→ **본 문서는 5단계가 한 흐름으로 흐른다**. 신규 Tool 작성자가 진입점으로 사용.

### 진실 소스 / 참조 흐름

| 단계 | 진실 소스 (참조) |
|---|---|
| ① 기능 | [`docs/_claude/referrence/agent_design/`](../../docs/_claude/referrence/agent_design/) (비전) + [08 화면_채팅_연결흐름](../../docs/_claude/referrence/agent_design/08_화면_채팅_연결흐름.md) (11 매트릭스) |
| ② 기능 → 에이전트 | [agent_design README](../../docs/_claude/referrence/agent_design/README.md) + [tool/TOBE_MVP/02_agent_cards](../../docs/_claude/tool/TOBE_MVP/02_agent_cards.md) |
| ③ 에이전트 → 툴 | [31 Execution Agent Function List](31_execution_agent_function_list_v0.6.md) + [32 Execution Agent Tools](32_execution_agent_tools_v1.0.md) |
| ④ 툴 → 데이터 | [tool/TOBE_MVP/01_tool_data_matrix](../../docs/_claude/tool/TOBE_MVP/01_tool_data_matrix.md) + [data/description/mock/SCHEMA](../../data/description/mock/SCHEMA.md) |
| ⑤ I/O 메커니즘 | 코드 — [base_tool.py](../../backend/app/dream_agent/tools/base_tool.py) + [executor.py](../../backend/app/dream_agent/execution/executor.py) + [shared/helpers.py](../../backend/app/dream_agent/tools/shared/helpers.py) |

---

## 1. ① 마케터 기능 카탈로그 (POC 24)

> 진실 소스: [agent_design §08 11 매트릭스](../../docs/_claude/referrence/agent_design/08_화면_채팅_연결흐름.md) + [agent_design §04 POC 9 모듈](../../docs/_claude/referrence/agent_design/04_분석_에이전트.md) + [agent_design §05~§07 콘텐츠 4](../../docs/_claude/referrence/agent_design/) 흡수.

### 1.1 화면 트리거 (11개)

| ID | 화면 | 버튼/트리거 | 한 줄 |
|---|---|---|---|
| F-D1 | 대시보드 | "상세 분석 보기 →" | KPI 이상 알림 → 원인 분석 진입 |
| F-D2 | 대시보드 | HITL 승인 클릭 | 월간 리포트 발송 승인 |
| F-R1 | ROAS분석 | "원인 상세 보기" | 날짜/매체별 ROAS 하락 원인 |
| F-C1 | 소재분석 | "AI 소재 생성 시작" | 대체 소재 자동 생성 |
| F-C2 | 소재분석 | "A/B 테스트 시작" | A/B 설계 가이드 |
| F-O1 | 비용최적화 | "무전환 키워드 중지" | 영향 분석 + 승인 후 중지 |
| F-O2 | 비용최적화 | "AI 예산 재배분" | 시뮬레이션 + 승인 |
| F-RP1 | 리포트 | "리포트 생성" | 분석 종합 → PDF |
| F-CH1 | 채팅 직접 | "소재 만들어줘" | 이미지 생성 대화 |
| F-CH2 | 채팅 직접 | "스토리보드 만들어줘" | 영상 스토리보드 |
| F-CH3 | 채팅 직접 | "리포트 만들어줘" | 리포트 종합 |

### 1.2 자동 트리거 분석 (POC 9 모듈)

| ID | 모듈 | 트리거 | 한 줄 |
|---|---|---|---|
| F-A01 | KPI 이상 감지 | 매일 자동 | CPA +30/+100% 임계 |
| F-A02 | KPI 달성률 예측 | 매일 자동 | 선형 외삽 |
| F-A03 | ROAS 원인 분석 | 인사이트 박스 / 요청 | 규칙 트리 (Freq→올영세일→예산→픽셀) |
| F-A04 | 소재 피로도 감지 | 매일 자동 | Freq≥3.5 + CTR 하락 |
| F-A05 | A/B 테스트 판정 | 요청 / 50건 도달 | proportion_ztest |
| F-A06 | 무전환 키워드 감지 | 매일 자동 | 클릭≥100 ∧ 전환=0 |
| F-A07 | 감성 분석 | 일 1회 (리뷰 수집 후) | ML 분류 (POC: 규칙) |
| F-A08 | 검색량 급등 감지 | 일 1회 | DataLab +20% |
| F-A09 | AI 리포트 스토리 | 요청 | LLM 3단계 스토리 |

### 1.3 콘텐츠 생성 (4개)

| ID | 기능 | 한 줄 |
|---|---|---|
| F-G1 | 광고 이미지 생성 | DALL-E 3, 3 시안 + 5축 채점 |
| F-G2 | 스토리보드 | 4 씬 (Hook-Value-Result-CTA) |
| F-G3 | PDF 출력물 | 4 종 (성과/제안서/스토리보드/내부) |
| F-G4 | 슬로건·카피 | LLM 생성 + 평가 |

→ **총 24 기능** (11 + 9 + 4). MVP 진입 = 이 24 모두 mock 으로 동작.

---

## 2. ② 기능 → 에이전트 매핑

> 진실 소스: [tool/TOBE_MVP/02_agent_cards](../../docs/_claude/tool/TOBE_MVP/02_agent_cards.md) + [agent_design/01_채팅_허브](../../docs/_claude/referrence/agent_design/01_에이전트_채팅_허브.md).

### 2.1 호출 매트릭스

| 기능 ID | 호출 에이전트 | HITL 카테고리 |
|---|---|---|
| F-D1 / F-R1 / F-A01~A04, A06~A08 | **analysis** | 조회·자동 |
| F-D2 / F-O1 / F-O2 / F-C2 | analysis | 실행 전 승인 |
| F-A05 | analysis | 실행 전 |
| F-A09 / F-RP1 / F-CH3 | analysis + **report_text** + **report_ppt** | 생성 후 |
| F-C1 / F-G1 / F-CH1 | **image** | 생성 후 |
| F-G2 / F-CH2 | **storyboard** (image + report_ppt 호출) | 생성 후 |
| F-G3 | **report_ppt** | 생성 후 / 외부 발송 |
| F-G4 | image (슬로건 = image 의 부 기능) | 생성 후 |

> HITL 4 카테고리 = 조회·자동 / 생성 후 / 실행 전 / 외부 발송. 상세 = [tool/TOBE_MVP/02 §7](../../docs/_claude/tool/TOBE_MVP/02_agent_cards.md).

### 2.2 9 에이전트 (D9 결정 — 전처리 2분리 + D13 결정 — 레포팅 2갈래)

```
① chat_hub_agent              ← 마케터 진입점 (NL + 11 화면 버튼)
② collection_agent             ← 매체별 raw 데이터 적재
③a text_preprocessing_agent    ← 자연어 정제 (8 단계)
③b channel_normalizing_agent   ← 광고성과 4채널 통합
④ analysis_agent               ← 9 분석 모듈
⑤ image_agent                  ← 이미지 + 5축 채점
⑥ storyboard_agent             ← 영상 4 씬 스토리보드
⑦ report_text_agent            ← 보고서 텍스트 (markdown / LLM 스토리)
⑧ report_ppt_agent             ← PPT/PDF/Excel 출력물
```

> 9 에이전트 = 사용자 D9 (전처리 2분리) + D13 (레포팅 2갈래) 결정 반영. 카운트 변화 이력 = [tool/TOBE_MVP/03 Drift D14](../../docs/_claude/tool/TOBE_MVP/03_drift_report.md).

---

## 3. ③ 에이전트 → 툴 분해

> 진실 소스: [31 Tool 요구사항](31_execution_agent_function_list_v0.6.md) + [32 Tool 현황](32_execution_agent_tools_v1.0.md).

### 3.1 에이전트별 툴 수 (POC + MVP)

| 에이전트 | 툴 수 (요구) | 구현 완료 | 비고 |
|---|---:|---:|---|
| ① chat_hub | (Cognitive Stage 로직, 별도 툴 아님) | ✅ 기본 | 11 매트릭스 prompt 강화 (Phase 5) |
| ② collection | 7~8 (매체별 4 + datalab + review + external + brief 옵션) | ✅ 1 (naver) | D2 결정 — review 와 광고성과 분리 |
| ③a text_preprocessing | 8 (단계별) | ✅ 1 (통합) | MVP 시 단계 분리 |
| ③b channel_normalizing | 5 | ✅ 1 (format) + 🟡 4 | MVP 시 4 채널 매핑 룰 흡수 |
| ④ analysis | 10+ (POC-01~09 + 공유 3) | ✅ 3 + △ 1 + 🟡 6 + 🔴 1 | DataLab 의존 1건 (POC-08) blocked |
| ⑤ image | 6 (RAG + 생성 + 5축 + 리사이즈 등) | 🟡 0 | brand_guideline RAG 선결 (D8) |
| ⑥ storyboard | 3 | 🟡 0 | image + report_ppt 의존 |
| ⑦ report_text | 3 (synthesizer + writer + summary) | ✅ 2 (writer + summary) | report_ppt 와 분리 (D13) |
| ⑧ report_ppt | 5 (chart + template + pdf + word + excel + pptx) | 🟡 0 | python-pptx 신규 도입 |

**합계** ≈ 46~50 Tool. 진실 소스 카운트 = [32 §7.1](32_execution_agent_tools_v1.0.md).

### 3.2 8개 implemented Tool 의 체인 (POC 현재 시점)

```
naver_collector → format_normalizer → text_preprocessor
                                          ├──► sentiment_analyzer
                                          └──► keyword_extractor
                                                     │
                                              insight_extractor
                                                     │
                                              report_writer ──► summary_generator
```

→ 이게 현재 **유일하게 end-to-end 동작하는 시나리오**. 자세 = [tool/01_as_is_poc §3.2](../../docs/_claude/tool/01_as_is_poc.md).

---

## 4. ④ 툴 → 데이터 매핑

> 진실 소스: [tool/TOBE_MVP/01 메인 매트릭스](../../docs/_claude/tool/TOBE_MVP/01_tool_data_matrix.md) + [data/description/mock/SCHEMA](../../data/description/mock/SCHEMA.md) + [RELATIONSHIPS](../../data/description/mock/RELATIONSHIPS.md).

### 4.1 데이터 source 종류

| 종류 | 위치 | Phase |
|---|---|---|
| **POC mock CSV** | [`data/mock/*.csv`](../../data/mock/) — 12 파일 | 현재 (Sprint 0~5) |
| **MVP 실 API** | Meta/Naver/Kakao/Google/DataLab + 크롤러 | Sprint 6+ (권한 확보 후) |
| **Production DB** | 자체 PostgreSQL + ClickHouse | Sprint 11+ |

API 표면 동결 (`/api/mock/...` 12 endpoint) — 진화해도 frontend 변경 0. 상세 = [data/description/mock/ROADMAP](../../data/description/mock/ROADMAP.md).

### 4.2 CSV → 사용 Tool 역방향 매핑 (요약)

| CSV | 사용 Tool | 영향도 |
|---|---|---|
| `mock_data_daily_performance.csv` ⭐⭐ | format_normalizer, kpi_calculator, anomaly_flagger, kpi_anomaly_detector, kpi_forecaster, roas_cause_analyzer, fatigue_detector | **최대** — 변경 시 11+ Tool 영향 |
| `mock_data_creatives.csv` ⭐ | fatigue_detector, creative_quality_scorer (5축 학습), creative_history_updater | analysis + image |
| `mock_data_review_trends.csv` | naver_collector(→review_collector), sentiment_analyzer, keyword_extractor | collection + analysis |
| `mock_data_keyword_performance.csv` | zero_conv_keyword_detector | analysis (POC-06) |
| `mock_data_ab_tests.csv` | ab_test_runner | analysis (POC-05) |
| `mock_data_campaigns.csv` | kpi_forecaster, insight_synthesizer | analysis (LLM context) |
| `mock_data_company_info.csv` | brand_guideline_analyzer, storyboard_planner, template_selector | image/storyboard/report_ppt |
| (없음 — 사용자 작업 중) `mock_data_brand_style.csv` (D10) | brand_guideline_analyzer | image RAG |
| (없음 — 사용자 작업 중) `mock_data_external_variables.csv` (D3) | external_variables_joiner, roas_cause_analyzer | POC-03 핵심 |

전체 매트릭스 = [tool/TOBE_MVP/01 §5 역방향](../../docs/_claude/tool/TOBE_MVP/01_tool_data_matrix.md).

---

## 5. ⑤ Tool I/O 관리 메커니즘 ⭐ 본 문서 핵심

> 코드 진실 소스: [base_tool.py](../../backend/app/dream_agent/tools/base_tool.py), [executor.py](../../backend/app/dream_agent/execution/executor.py), [shared/helpers.py](../../backend/app/dream_agent/tools/shared/helpers.py).

### 5.1 BaseTool 계약

모든 Tool 은 다음 추상 클래스 구현:

```python
class BaseTool(ABC):
    def __init__(self, spec: ToolSpec): ...

    @abstractmethod
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """Tool 실제 수행. 반환 dict = TodoResult.data 로 저장."""
```

| 인자 | 의미 |
|---|---|
| `params` | Planner 가 지정한 `tool_params` + `_inject_prev_outputs` 자동 주입 결과 |
| `context` | `ExecutionContext(session_id, plan_id, client_id, user_id, language, previous_results, session_memory)` |
| 반환 | `dict[str, Any]` — `produces` YAML 선언 키 + 부가 정보. Tool 체인의 다음 단계로 자동 전파됨 |

상세 = [32 §5](32_execution_agent_tools_v1.0.md).

### 5.2 입력 자동 주입 — `_inject_prev_outputs` 룰

[`executor.py:_inject_prev_outputs`](../../backend/app/dream_agent/execution/executor.py) (line 201):

```python
def _inject_prev_outputs(params: dict, previous_results: dict[str, TodoResult]) -> dict:
    merged = dict(params)
    for r in previous_results.values():
        if r.status != TodoStatus.COMPLETED:
            continue
        if not isinstance(r.data, dict):
            continue
        for k, v in r.data.items():
            if k.startswith("_"):
                continue
            merged.setdefault(k, v)   # ← 핵심: setdefault
    return merged
```

**핵심 4 룰**:

| # | 룰 | 결과 |
|---|---|---|
| 1 | **`setdefault`** | 이미 `tool_params` 에 명시된 값이 있으면 절대 덮지 않음 → 사용자/Planner override 우선 |
| 2 | **`_` prefix 키 제외** | `_meta`, `_trace`, `_debug` 등 내부용 키는 전파 안 됨 |
| 3 | **COMPLETED 만 주입** | 실패한 Tool 의 data 는 무시 |
| 4 | **dict 만 주입** | data 가 dict 가 아니면 무시 |

### 5.3 명시 조회 — `find_in_previous`

자동 주입이 안 되는 경우 (예: 깊은 nested 키), Tool 내부에서 명시 조회:

[`shared/helpers.py:find_in_previous`](../../backend/app/dream_agent/tools/shared/helpers.py) (line 60):

```python
from app.dream_agent.tools.shared.helpers import find_in_previous

class MyTool(BaseTool):
    async def execute(self, params, context):
        # context.previous_results 에서 명시 조회
        normalized = find_in_previous(
            context.previous_results,
            "normalized_reviews"
        )
        if normalized is None:
            raise RuntimeError("no normalized_reviews in previous_results")
        ...
```

지원하는 결과 dict 구조 2 종:
- `previous_results[todo_id]["data"][key]`
- `previous_results[todo_id][key]` (flat)

### 5.4 출력 — `produces` 키 체이닝 원칙

Tool 의 return dict 키는 **다음 Tool 의 입력** 으로 자동 전파됨. 따라서 키 네이밍 통일이 중요.

**권장 체인 패턴**:

```
naver_collector       → return {"raw_reviews": [...], "count": N, ...}
                              │
                              ▼ (자동 주입 — setdefault)
format_normalizer     → return {"normalized_reviews": [...], "count": N, "schema_version": "v1"}
                              │
                              ▼
text_preprocessor     → return {"cleaned_texts": [...], "before_count": N, "after_count": M}
                              │
                              ▼
sentiment_analyzer    → return {"sentiment_distribution": {...}, ...}
keyword_extractor     → return {"top_keywords": [...], ...}
                              │
                              ▼ (양쪽 모두 주입)
insight_extractor     → return {"insights": [...], ...}
                              │
                              ▼
report_writer         → return {"report_text": "...", "length": N}
```

**원칙 3 가지**:

| # | 원칙 | 이유 |
|---|---|---|
| 1 | **produces 키 = 다음 Tool 의 params 키와 일치** | setdefault 자동 매칭 |
| 2 | **내부용은 `_` prefix** | `_trace`, `_debug`, `_meta` 등 전파 차단 |
| 3 | **큰 raw 데이터 (>100 항목) 는 파일 경로로** | LLM 토큰 폭증 + Checkpointer 직렬화 부담 |

### 5.5 실패 처리 — raise vs return error

| 방식 | 동작 | 권장 |
|---|---|---|
| `raise RuntimeError("msg")` | Executor 가 FAILED 로 잡음. `error` 필드에 메시지 | ⭐ 권장 |
| `return {"error": "msg"}` | Executor 가 FAILED 로 간주 (현재 코드 양쪽 지원) | 비권장 (혼재 — [32 §11.4](32_execution_agent_tools_v1.0.md)) |

실패 시:
- TodoResult `status=FAILED` + `data={}` + `error=str(e)`
- 다음 Phase 의 의존 Todo = depends_on 만족 못 함 → **자동 skip** 또는 halt
- spec §2.4: **no retry** (failed is final)

### 5.6 직렬화 / 재시작 복원

Tool.execute 의 return dict 는 결국:
1. `TodoResult.data` 에 저장
2. `AgentState` 에 누적
3. Postgres Checkpointer 가 pickle 직렬화

**금지 사항**:

| 객체 | 이유 |
|---|---|
| 파일 핸들 (`open()` 반환) | pickle 불가 |
| async generator | pickle 불가 |
| thread local 객체 | pickle 불가 |
| DB 연결 객체 | pickle 불가 |

**대안**:
- 파일은 **경로 (str) 만 저장**, 실 내용은 디스크
- 큰 dict 는 **요약만 data 에**, 상세는 별도 path

### 5.7 mock fallback (POC 단계)

[`agent_pool.py:is_tool_implemented`](../../backend/app/dream_agent/execution/agent_pool.py):

```python
if pool.is_tool_implemented(agent_name, tool_name):
    # 실제 Tool 클래스 실행
    tool_inst = pool.get_real_tool(tool_name)
    params = _inject_prev_outputs(todo.tool_params, previous_results)
    data = await tool_inst.execute(params, ctx)
    is_mock = False
elif pool.is_tool_stub(agent_name, tool_name):
    # mock_tools.mock_result() fallback
    data = mock_result(tool_name, todo.tool_params)
    is_mock = True
else:
    raise RuntimeError(...)
```

→ team_catalog.yaml 의 `status: stub` 인 Tool 은 `mock_tools.py:mock_result()` 가 그럴듯한 dict 반환. POC 시연 시 체인 통과 보장.

상세 = [32 §3 디렉토리 구조 + §10 잊기 쉬운 접점](32_execution_agent_tools_v1.0.md).

---

## 6. 종단 예시 한 시나리오

> 사용자: **"블루밍글로우 네이버 리뷰 감성 분석해줘"**

```
[① 기능] F-CH1 "감성 분석 요청"
   │
   ▼
[② 에이전트] chat_hub_agent
   - LLM 의도 추출 → POC-07 분류
   - HITL 카테고리 = 조회 (자동 실행)
   │
   ▼
[② → 라우팅] analysis_agent (POC-07 감성 분석)
   │
   ▼
[③ Planner] 5 todos 생성 (DAG):
   t1: naver_collector  (collection)
   t2: format_normalizer (channel_normalizing)  depends_on=[t1]
   t3: text_preprocessor (text_preprocessing)   depends_on=[t2]
   t4: sentiment_analyzer (analysis)            depends_on=[t3]
   t5: report_writer (report_text)              depends_on=[t4]
   │
   ▼
[④ 데이터 + ⑤ I/O] Executor 가 Phase 별 실행:

Phase 1: t1
   params = {brand: "블루밍글로우", source: "naver_blog"}
   t1 = naver_collector.execute(params, ctx)
   load_mock_csv("mock_data_review_trends.csv")
     [출처='naver_*' 필터 → N건]
   return {"raw_reviews": [...N건...], "count": N, "source": "naver_blog"}

Phase 2: t2 (raw_reviews 자동 주입)
   params = {schema: "brand_reviews"}  ← Planner
            + raw_reviews ← setdefault 자동 주입
   t2 = format_normalizer.execute(...)
   return {"normalized_reviews": [...], "schema_version": "v1"}

Phase 3: t3
   t3 = text_preprocessor.execute(...)
   HTML/URL 제거 + MD5 dedup
   return {"cleaned_texts": [...], "before_count": N, "after_count": M}

Phase 4: t4
   t4 = sentiment_analyzer.execute(...)
   POC: 규칙 분류
   return {"sentiment_distribution": {"positive": 65, "neutral": 20, "negative": 15}}

Phase 5: t5
   t5 = report_writer.execute(...)
   LLM 호출 → markdown 작성
   return {"report_text": "...", "length": 1024}

[Response Layer]
   사용자 응답: "블루밍글로우 네이버 리뷰 N건 분석 결과 — 긍정 65%, ..."
```

5단계가 한 흐름. 각 단계 멈춰서 위 §1~§5 참조.

---

## 7. 신규 Tool 추가 — 종단 체크리스트

`X` 라는 신규 Tool 을 만들 때 모든 단계 점검:

| ① 기능 | 이 Tool 이 어느 마케터 기능 (F-*) 의 일부? | §1 표에 신규 행? |
|---|---|---|
| ② 에이전트 | 어느 에이전트 소속? | team_catalog.yaml 의 해당 agent.tools 배열에 추가 |
| ③ 툴 메타 | YAML 작성 (`tools/catalog/<cat>/<X>.yaml`) | name, parameters, produces, requires_approval |
| ③ 툴 구현 | `tools/<cat>/<X>.py` 작성 | class X(BaseTool) + async execute |
| ④ 데이터 | 어느 CSV 의 어느 컬럼 쓰나? | [tool/TOBE_MVP/01 매트릭스](../../docs/_claude/tool/TOBE_MVP/01_tool_data_matrix.md) 행 추가 |
| ⑤ I/O | 이전 produces 키 무엇 받아 무엇 만드나? | YAML produces 명시 + 다음 Tool 호환 키 |
| 코드 status 마커 | docstring `Status: complete \| partial \| planned — 설명` | [feedback_code_status_markers](C:/Users/gobok/.claude/projects/c--kdy-Projects-octormate-beta-v001/memory/feedback_code_status_markers.md) 메모리 |
| 테스트 | unit + integration + DC-10 (Status 3중 정합) | `backend/tests/sprint*/` |

상세 = [32 §9 Step-by-Step](32_execution_agent_tools_v1.0.md).

---

## 8. 관련 spec

| 번호 | 제목 | 본 문서와의 관계 |
|---|---|---|
| [14](14_system_agent_overview_v1.0.md) | System Agent Overview | **Layer 관점** (Cognitive/Planning/Execution/Response) |
| [15](15_end_to_end_flow_v1.0.md) | End-to-End Flow | **시간 축** (한 사이클 sequence) |
| **17** (본 문서) | **Functions → I/O 종단** | **계층 축** (기능 → 에이전트 → 툴 → 데이터 → I/O) |
| [30](30_DATA_MODELS_v1.1.md) | Data Models | Pydantic — TodoResult, ExecutionResult |
| [31](31_execution_agent_function_list_v0.6.md) | Tool 요구사항 | §3 의 입력 |
| [32](32_execution_agent_tools_v1.0.md) | Tool 구현 현황 + 확장 가이드 | §3 / §5 의 깊이 있는 출처 |

---

## 9. 변경 정책

| 트리거 | 본 문서 갱신 |
|---|---|
| 신규 마케터 기능 추가 (화면 버튼 등) | §1 표 + §2 매핑 |
| 신규 에이전트 도입 | §2.2 9 에이전트 표 |
| 신규 Tool 구현 | §3.1 카운트 + §3.2 (체인 변경 시) |
| 신규 데이터 source / CSV | §4.2 역방향 매핑 |
| I/O 룰 변경 (BaseTool 계약 변경 등) | §5 |
| Tool 실패 정책 변경 | §5.5 |

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 |
|------|------|------|
| v1.0 | 2026-05-18 | 초안 — 5단계 종단 매핑 신규. agent_design (비전) + 31/32 (Tool spec) + tool/TOBE_MVP (Tool↔Data 매핑) + 코드 (base_tool/executor/helpers) 4 source 흡수. §5 I/O 메커니즘이 신규 가치 — 코드 룰 4종 박제 (setdefault / `_` prefix / COMPLETED만 / dict만). 시나리오 예시 §6. 신규 Tool 종단 체크리스트 §7. 14/15 와 자매 (Layer/시간/계층 3축 완성). |
