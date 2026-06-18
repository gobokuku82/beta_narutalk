# 근본원인 분석 — execution state에 raw 데이터 누수 (104MB checkpoint) · 2026-06-11

> 증상: 재접속 시 채팅 복원이 5.5초. → 측정·추적 결과 **한 턴 checkpoint가 155MB**로 비대해진 게 근본.
> 본 문서 = 증상에서 **구조가 꼬인 지점까지 코드로 타고 올라간** 추적 기록 + 처방 옵션. (수정 전 합의용)

---

## 0. 한 줄 결론

수집 tool이 **raw 데이터셋 전체(GA4 38,319행)를 자기 "결과"에 담아** agent state(`execution_result`)로 흘려보내고, 그게 **checkpoint에 통째로 저장**된다. 그런데 **downstream tool은 그 raw를 안 쓰고 data 레이어에서 직접 읽는다** → 그 raw는 **아무도 안 쓰는 죽은 104MB**이고, 이게 모든 느림·비대의 근원. **tool/data 분리 원칙([[project_tool_data_agent_separation]])이 collector 경계에서 깨진 것.**

---

## 1. 증상 & 측정 (사실)

| 측정 | 값 | 출처 |
|---|---|---|
| `/api/conversations/{id}/turns` 응답 | **5,564ms** | REST 실측 |
| 분해: `SELECT DISTINCT thread_id` | **0ms** (151행밖에 없음) | 프로파일러 |
| 분해: `aget_tuple` × 3턴 | **1564 + 4 + 1466 ms** | 프로파일러 |
| 큰 턴 2개의 state blob | **execution_result ~79MB + execution_progress ~79MB = 155MB/턴** | checkpoint_blobs |
| 작은 턴 1개(GA4 안 씀) | execution_result 117KB → **4ms** | 프로파일러 |
| 104MB의 정체 | `execution_result.todos.todo_003.data.clumi_ga4_traffic_raw` = **38,319행 = 103.94MB** | blob walk |

→ **DISTINCT도, turn 개수도 아니다. 거대 blob 역직렬화가 100% 범인.** 그리고 그 blob = **raw 데이터셋 한 덩어리.**

---

## 2. 타고 올라가기 — 104MB가 흐른 경로 (downstream → upstream)

```
[채팅 복원이 느림]  ← 증상
  ↑ get_turns 가 aget_tuple 로 그 턴 state 전체(155MB)를 역직렬화 (user_input+response 수KB만 필요한데)
      manager.py:159  tup = await self._cp.aget_tuple(...)
  ↑ checkpoint 에 execution_result + execution_progress 채널이 통째 저장됨 (155MB)
  ↑ execution_stage 가 두 채널 모두 state 에 업데이트
      execution_stage.py:294-300
        update={ "execution_result": execution_result,                  # 104MB
                 "execution_progress": hitl.get_progress_snapshot(...) } # 같은 결과 미러 → 또 79MB
  ↑ execution_result.todos[tid].data = 완료 TodoResult 의 .data 그대로
      execution_stage.py:331-356  _build_execution_result → TodoResult.model_validate(r)
  ↑ hitl.completed_todos[tid] = TodoResult.model_dump() (raw 포함)
      hitl_manager/manager.py:301-308  report_phase_complete
  ↑ TodoResult.data = tool 이 반환한 dict 그대로
      executor.py:210  data = await tool_inst.execute(params, ctx)
      executor.py:221  safe_data = _json_safe(data)        ← 38k행 통째 json-safe
      executor.py:232  return TodoResult(data=safe_data)
  ↑ ★ 수집 tool 이 raw 전체를 결과로 반환 ★  ← 꼬임의 발원지
      collection/_base.py:106  data = self.ds.get(client, source_id)   # 38,319행
      collection/_base.py:126  return { self.PRODUCES_KEY: data, "count": ... }
```

### 발원지 코드 ([collection/_base.py:97-132](../../backend/app/dream_agent/tools/collection/_base.py#L97))
```python
data = self.ds.get(context.client_id, source_id)   # ← raw 38,319행
# 주석(L116): "raw 자체는 *저장 안 함* — 이미 data/{client}/raw/ 에 있음."  ← raw가 data 레이어에 있음을 알면서
return {
    self.PRODUCES_KEY: data,   # ← 그런데도 결과에 통째로 실어 보냄 ("PRODUCES_KEY = 다음 tool 의 입력 키")
    "count": count, ...
}
```

---

## 3. 어디서 꼬였나 — "다음 tool에 넘긴다"는 가정이 틀렸다

collector는 **`PRODUCES_KEY: data`로 raw를 "다음 tool의 입력"으로 넘긴다**고 가정한다 ([_base.py:92, 95](../../backend/app/dream_agent/tools/collection/_base.py#L92)). **그런데 실제 다음 tool은 그걸 안 쓴다.**

### 증거 — downstream은 data 레이어에서 직접 읽음
[Ga4SessionAggregator:37](../../backend/app/dream_agent/tools/metrics/ga4_session_aggregator.py#L37):
```python
for rec in self.ds.stream_jsonl(context.client_id, GA4_SOURCE_ID):   # ← previous_results 안 씀!
    ...
```
집계 tool은 `previous_results[collector].data`(state로 넘어온 raw)를 **무시하고**, `self.ds.stream_jsonl(...)`로 **data 레이어에서 스트리밍**으로 읽는다 (메모리 절약 주석까지 있음, L8).

> **즉 collector가 state로 흘려보낸 38k행은 아무도 안 쓰는 죽은 무게.** 데이터는 이미 data 레이어(`raw/`)에 있고 downstream이 거기서 읽으므로, collector가 결과로 또 실어 보낼 이유가 없다.

### 이게 위반하는 설계 의도
[[project_tool_data_agent_separation]] (사용자 명시): **tool=순수기능 / data=별도 DataSource Repository / client→data 동적. "관절" 부재가 현 코드 진단.**
- data 레이어 "관절"은 이미 있다 (`self.ds.get` / `stream_jsonl`).
- 그런데 collector는 그 관절을 쓰면서도 **결과에 raw를 또 싣는** 반쯤-마이그레이션 상태 → state가 raw 운반 트럭이 됨.

---

## 4. 보조 꼬임 2개 (compounding)

1. **execution_progress = execution_result 중복 저장.**
   [execution_stage.py:297](../../backend/app/dream_agent/execution/execution_stage.py#L297) `execution_progress = hitl.get_progress_snapshot(...)` 이 `completed_results`(= 같은 TodoResult들, raw 포함)를 담는다 ([hitl get_progress_snapshot:324-338](../../backend/app/dream_agent/workflow_managers/hitl_manager/manager.py#L324)). → **같은 104MB가 두 채널에 = 디스크 155MB.**

2. **state에 "넣기 전 슬리밍" 경계가 없다.**
   tool 결과가 크든 작든 `_json_safe` 후 그대로 TodoResult.data → completed_todos → 두 state 채널 → checkpoint. **"checkpoint에 영속할 가치가 있는 결과" vs "다음 tool용 임시 데이터"를 구분하는 경계가 없다.** 이 경계가 있었다면 (a)의 raw가 새어도 막혔을 안전망.

---

## 5. 파급 — 채팅 복원만의 문제가 아니다

| 영역 | 영향 |
|---|---|
| **DB** | 매 (raw 쓰는) 턴 checkpoint에 ~155MB 저장. 누적 비대. |
| **저장 지연** | checkpoint 쓰기도 79MB×2 직렬화 (실행 자체가 느려짐). |
| **복원/조회** | get_turns·list_conversations가 aget_tuple로 통째 로드 (현 증상). |
| **WS 전송** ✅확정 | **2경로로 브라우저에 감 (2차 검증으로 코드 확정)**: (a) [ws_agent.py:302-308](../../backend/api_v2/ws_agent.py#L302) `_broadcast_chunks`가 execution 노드 chunk(= execution_result+execution_progress ≈208MB)를 node_event로 송신, (b) [ws_agent.py:289](../../backend/api_v2/ws_agent.py#L289) `_emit_complete` success가 execution_result 재송신. 각각 `_json_safe` 딥카피 + `json.dumps` + ws 전송. 프론트 zod는 `passthrough`라 통째 파싱, obs eventLog ring buffer(500개)에 raw 보존 → 브라우저 메모리 비대. |
| **메모리** | 실행 중 state·hitl 싱글톤에 104MB 상주. |

---

## 6. 처방 옵션 (컷 지점별)

| # | 컷 지점 | 내용 | 효과 | 범위/리스크 |
|---|---|---|---|---|
| **L1** | get_turns | `aget_tuple` 대신 `user_input`+`response` 채널만 직접 로드 | 채팅 복원 5.5s→~ms | 작음·안전 (내 파일). **증상만** 막음, 근본 그대로. |
| **L2** | WS | `_emit_complete`에서 `execution_result` 제외/슬림 | 브라우저 104MB 전송 차단 | 작음. 프론트가 execution_result 쓰는지 확인 필요. |
| **L3** | state 저장 경계 | `_build_execution_result`/`get_progress_snapshot`에서 **`data`의 대용량 payload를 슬림**(요약/참조만 남김) 후 채널 저장 | checkpoint 155MB→KB, **모든 파급 동시 해결** | 중간. "무엇을 남기고 무엇을 버릴지" 기준 필요. downstream이 previous_results.data 의존하면 깨짐 → §7 감사 선행. |
| **L4** | collector 계약 (진짜 근본) | collector가 **참조(source_id+count+status)만 반환**, downstream은 data 레이어에서 읽음 (이미 aggregator는 그럼) | 근본 제거 + L3 효과 | 중간. **previous_results.data 소비자 전수 감사 필수**(§7). 소비자 있으면 그 tool도 data 레이어 읽기로 전환. |
| **L5** | 중복 제거 | execution_progress가 execution_result 미러 안 하게 (참조/상태만) | 디스크 2배→1배 | 작음. hitl 스냅샷 용도 재검토. |

> **중복 제거(L4+L5)가 정답.** L1은 즉효 반창고(채팅 복원만), L3는 안전망. **순서 권장: L1(즉시 숨통) → §7 감사 → L4+L5(근본) → L2(WS 확인·정리).**

---

## 7. 소비자 전수 감사 — 완료 (1차 + 2차 반증 검증, 2026-06-11)

> 질문: **collector가 결과로 넘긴 raw(`PRODUCES_KEY`)를 previous_results에서 실제로 소비하는 곳이 있는가?**
> 방법: find_in_previous 호출 전수 + team_catalog `consumes` 전수 + params 주입 경로 grep + LLM tool 입력 수집부 + responder + pipeline runner 까지 반증 시도.

### 7.1 결론 표

| 소스 (PRODUCES_KEY) | 크기 | previous_results 소비자 | 판정 |
|---|---|---|---|
| `clumi_ga4_traffic_raw` (104MB) / `clumi_ga4_page_raw` (96MB) | 거대 | **0** — aggregator는 [ds.stream_jsonl 직접](../../backend/app/dream_agent/tools/metrics/ga4_session_aggregator.py#L37). catalog `consumes` 전체 8건에 GA4 없음. params 주입 읽기 0. | **순수 죽은 무게 확정** |
| `raw_reviews` (리뷰, 소형) | 소 | ✅ [review_normalizer:51](../../backend/app/dream_agent/tools/normalization/review_normalizer.py#L51) + 게이트 `consumes:[raw_reviews]` | **유일한 진짜 raw 체인** |
| 광고 daily (meta_ads_raw·naver_sa_raw·kakao_raw 등) | KB~MB | ⚠️ [format_normalizer:92-100](../../backend/app/dream_agent/tools/normalization/format_normalizer.py#L92)가 읽는 키는 `raw_meta_ads`·`meta_raw_daily` 류 — **현 collector PRODUCES_KEY와 불일치**(meta_ads_raw≠raw_meta_ads) → 실질 소비 0 (또 하나의 [[project_catalog_code_drift]]) | 사실상 죽은 체인 (직접주입/테스트 fixture 만 유효) |
| `orders_raw` (pipeline 경로) | 소 | 0 — collector step이 있는 유일 flow `dashboard1_kpi_revenue`의 다음 step `revenue_total`은 `self.fetch("orders")` 직접 (yaml 주석도 "self-load라 중복" 명시) | pipeline도 체이닝 소비 0 |

### 7.2 2차 검증에서 확정/정정된 사실

1. **게이트 안전** — `consumes` 선언 전수 8건(normalized_reviews/raw_reviews/cleaned_texts×2/insights/report_markdown×2 등), GA4 계열 0 → 거대 raw 슬리밍이 데이터 게이트를 깨지 않음.
2. **LLM tool 4종 모두 raw 방어 있음** — insight_extractor·diagnoser·forecaster·summary_generator 전부 `len(json)>600 skip` + 프롬프트 `[:3000]` 절단. raw가 프롬프트로 새지 않음.
3. **`execution_progress` 채널은 write-only** — 쓰는 곳 [execution_stage:297](../../backend/app/dream_agent/execution/execution_stage.py#L297) 하나, **읽는 곳 0**. (pause 복원은 채널이 아니라 interrupt payload의 progress를 읽음.) → **미러 79MB는 100% 죽은 무게, L5(미러 중단) 완전 안전.** 단 pause 시 interrupt payload로 들어가는 snapshot은 restore_progress가 읽으므로 *그쪽* 슬리밍은 임계치 방식 필요.
4. **Responder는 todo data를 실제 소비** — [_render_metrics](../../backend/app/dream_agent/response/responder.py#L163)(스칼라만, **list/dict 스킵** L186)·`_find_artifact`(summary/report_markdown 문자열)·`_collect_attachments`(파일경로). → **blanket strip은 최종 답을 깨뜨림. L3는 반드시 "크기 임계치" 방식**(예: >256KB 값만 슬림)이어야 함 — 임계치면 responder가 읽는 값(스칼라·문자열·경로)은 전부 보존됨.
5. **WS 2경로 송신 = 코드 확정** (§5 표 갱신) — node_event(execution)로 ~208MB + complete로 ~104MB. 프론트 zod `passthrough` 통째 파싱 + obs eventLog ring buffer(500)에 raw 보존.
6. **recommender 주의(MVP+)** — [recommender:47](../../backend/app/dream_agent/tools/decision/recommender.py#L47)이 `previous` 전체를 ml_model에 전달. POC mock은 무시하지만 **LlmMlModel swap 시 raw 누수 위험** — L3 적용 시 자동 완화.
7. **response_stage CPU 비용** — [response_stage:47](../../backend/app/dream_agent/response/response_stage.py#L47)이 104MB dict를 Pydantic 재검증. L3(임계치 슬림)가 같이 해결.
8. **대화이력 목록도 같은 비용** — `list_conversations`의 `_load_latest_states`가 전 thread aget_tuple → 거대 턴 2개 포함 시 목록 페이지도 ~3s.

---

## 8. 감사 후 처방 재확정

| | 내용 | 안전성 (감사 근거) |
|---|---|---|
| **L3 (권장 1순위)** | state 채널에 넣기 전 **크기 임계치 슬림**(예: 값 >256KB → `{"_slimmed": true, "key": .., "size": ..}` 참조로 치환) — `_build_execution_result` 출력에 적용 | ✅ 안전: responder(스칼라·문자열·경로만 읽음, §7.2-4)·게이트(GA4 미선언)·LLM(600캡)·review 체인(소형이라 임계치 미달) 전부 영향 0. checkpoint·WS·response 재검증 동시 해결 |
| **L5 (같이)** | `execution_progress` 채널 미러 중단(또는 빈 dict) | ✅ 완전 안전: 읽는 곳 0 (§7.2-3) |
| **L4 (후속)** | 거대 collector(GA4 2종)만 참조 반환으로 전환 → 실행 중 RAM까지 정리 | ✅ 안전(소비자 0 확정). 단 작은 collector까지 일괄 전환은 review_normalizer 마이그레이션 선행 필요 |
| L1 (선택) | get_turns 채널 선별 로드 | L3 적용 후 신규 턴은 자연 해결. **기존 비대 턴**(이미 저장된 155MB×2)은 여전히 느림 → 기존 체크포인트 정리(삭제/마이그레이션)와 택일 |
| L2 (불요화) | WS에서 execution_result 제외 | L3가 해결 (슬림된 결과가 그대로 ws로 감) |

**잔여**: 실행 *중* RAM 104MB 상주(hitl completed_todos + `_inject_prev_outputs` 참조 병합)는 L3로 안 풀림(턴 종료 시 해제되는 transient) → L4(거대 소스)가 잡음.

---

## 9. 외부 검토 (2026-06-12) — 슬라이스 1과의 관계 · 방향 평가 · 이 수정이 만든 잠재 문제

> 검토자: 슬라이스 1(period 정직, `e101a48`·`8605f0d`) 작업 세션. 접점 전부 코드 실측, 동조 없이 기록.

### 9.1 슬라이스 1과의 관계 — 충돌 0, 같은 상위 문제의 양면

본 수술(L3·L4·L5)은 tool **출구** 경계(결과→state로 데이터셋이 새는 것), 슬라이스 1은 tool **입구** 경계(상류 데이터→param으로 스코프가 새는 것)를 닫음. 둘 다 **헌법 19 I3 "경계 계약 부재"의 사례**이며 패턴이 3중첩: ①경계 계약 부재(암묵 저장 ↔ 암묵 주입) ②catalog≠code drift(format_normalizer 키 불일치 ↔ params_required 17:2) ③게이트>컨벤션. 현재 executor 경계 게이트 3종 공존: 입구 param(`_param_boundary_issue`) · 입구 consumes(data_gate) · 출구 크기(state_guard) + 발원지(_dataref). 상보적 — 통합 불요(과설계 경계).

접점 실측 4건 전부 안전: ⓐ `_dataref` 스텁은 비-스코프 키라 period 차단과 무관 ⓑ 슬림은 state 사본에만 — responder 게이트가 읽는 `data.reason/param`(소형 문자열)·스텁 dict는 `_render_metrics`가 자동 스킵 ⓒ 슬라이스 1 R-8(ctx.previous_results COMPLETED만 병합)은 L3 불변식("in-memory 체이닝 불변")과 정합(빼는 건 SKIP/FAILED 사유 dict뿐) ⓓ 두 작업 겹친 상태의 전체 회귀 894 pass (sprint15 state_guard·collector_dataref 포함).

### 9.2 방향 평가 — 좋았다 (과설계 아님)

- **방법이 헌법 그 자체**: 측정(155MB 실측) → 체인 추적 → **소비자 전수 감사 + 2차 반증** → 컷 지점 비교 → 최소 변경(베이스 1곳·게이트 1곳·미러 제거). blanket strip 대신 임계치를 고른 것도 감사 결과(responder가 data 소비)에서 도출 — 증거 주도.
- **안 만든 것이 적절**: artifact store/content-addressable ref/직렬화 미들웨어 같은 일반해를 만들지 않고 132줄 게이트 + 스텁으로 끝냄. POC 비례성 충족.
- L1(반창고)→감사→L4+L5(근본)→레거시 삭제(v6) 순서도 옳음. **수정방향에 대한 답: 좋지 못한 점 없음.** 단, 아래 9.3의 빚은 이 수정이 *새로* 만든 것이므로 같이 박제.

### 9.3 이 수정이 만든 잠재 문제 (현재 무해 — 발화 조건 명시)

| # | 문제 | 발화 조건 | 처방 |
|---|---|---|---|
| **9.3-1** | **truthy `_dataref` 스텁 = "데이터 있는 척" 신호.** 존재성 호환을 위해 키를 truthy dict로 유지 → data_gate non-empty 검사가 **count=0이어도 통과**. 게다가 catalog produces는 여전히 `meta_ads_raw`(:71)·`clumi_ga4_traffic_raw`(:119)·`orders_raw`(:151) 등을 artifact로 선언 → complete_dataflow_chain이 미래 소비자에게 collector를 자동 배선하면 **파이프는 연결되는데 물 대신 모형이 흐름** (G2와 동형의 silent 실패 클래스). `_dataref`를 인지하는 코드는 _base.py 1곳뿐 — 소비측·게이트 인지 0 | RawCollectorBase 계열 PRODUCES_KEY에 consumes 소비자가 생기는 순간 (현재 0 — §7 감사) | ✅ **처리됨 (2026-06-12)** — data_gate가 `_dataref` 인지: count==0 → insufficient + 박제 테스트 2건. 장기(소비자 생길 때): produces 의미를 "참조 스텁"으로 카탈로그 주석 동기 or 키를 `*_ref`로 개명 |
| 9.3-2 | count 산정용 **전량 적재 잔존** — `self.ds.get`으로 38k행 로드 후 len만 쓰고 버림 (transient RAM·로드 시간) | GA4급 소스 수집 턴마다 (상주는 아님 — GC) | stream count 전환 후속 가능. POC 무해 |
| 9.3-3 | **크래시-복구 엣지**: graceful pause는 비슬림 snapshot(interrupt payload) 경로라 무영향이나, 프로세스 크래시 후 checkpoint(슬림된 채널)에서 체인 재구성하는 미래 경로가 생기면 대용량 체인 데이터가 스텁 — 단 그 경우 data_gate가 정직 SKIP하므로 **거짓 성공은 아님** | 크래시 mid-turn 복구 기능 도입 시 (현 POC 범위 밖) | 도입 시점에 L3b와 함께 설계 |
| 9.3-4 | state_guard·_dataref가 **헌법 19 신호 라우팅 표 미등재** — "감지=정책 입력(I5)" 정합을 위해 슬림 warning 로그의 소비자도 명시 필요 | — | 헌법 표에 한 줄 등재 (다음 헌법 갱신 시 묶음) |


| 날짜 | 내용 |
|---|---|
| 2026-06-11 | v1 신규 — 채팅 복원 5.5s 근본원인 추적. 측정(104MB=GA4 38,319행) → 체인 추적(collector 결과→state→checkpoint) → 꼬임 발원지(collector가 안 쓰이는 raw를 state로 운반, tool/data 분리 위반) → 처방 L1~L5 + 감사 선행 항목. |
| 2026-06-11 | v2 — §7 소비자 전수 감사 완료(1차+2차 반증). GA4 raw 소비자 0 확정(게이트 consumes 8건 전수·params 주입 0·pipeline 체이닝 0) / LLM 4종 600캡 확인 / execution_progress write-only 확정 / **responder가 todo data 소비 → L3는 임계치 방식 필수**(blanket 금지) / WS 2경로(~312MB) 송신 코드 확정 / format_normalizer 키 불일치(catalog≠code drift) / recommender MVP+ 누수 위험. §8 처방 재확정: L3(임계치)+L5 우선, L4(거대 소스) 후속. |
| 2026-06-11 | **v3 — L3+L5 구현·실측 검증 완료** (커밋 `33ac21a`, 계획·결과=[계획_state경계게이트_L3L5](계획_state경계게이트_L3L5_2026-06-11.md)). `state_guard.py` 신규(>256KB 값→참조 스텁, 원본 불변) + 미러 제거. 실 e2e: GA4 턴 execution_result **104MB→1,082B**(★SLIMMED in vivo) · metric 턴 답변 무손상 · WS complete 4.5KB · progress 블롭 0 · 경로 8ms. **잔존 = 레거시 비대 턴 2개**(삭제 시 해소) + L4(실행 중 RAM·_json_safe 딥카피) 후속. |
| 2026-06-11 | **v4 — L4 발원지 수정 완료** (커밋 `85ef5de`, 계획·결과=[계획_L4_collector참조반환](계획_L4_collector참조반환_2026-06-11.md)). RawCollectorBase 반환 계약 → `_dataref` 참조 스텁(21 collector 커버, ReviewCollector 무영향). e2e 3턴: GA4 **◆DATAREF(38319) + keepalive 켠 채 완주**(이벤트루프 블록 해소) · metric 답변 무손상 · 리뷰 체인 6 todo 정상. 보너스: `active_orders_filter`가 ★SLIMMED — **L3 보편성 라이브 실증**(비-collector 누수를 게이트가 잡음). **근본원인 체인 전 층 닫힘**: 발원지(L4)+경계(L3)+미러(L5). 잔존 = 레거시 비대 턴 2개 삭제(사용자 🗑)·kst_timezone_normalizer 배선 버그(별도)·orders_active 류 후속 정리 후보. |
| 2026-06-12 | **v5 — 다음 층 박제**: 오너 도출 통찰 "조회 계약(어디서 얼마를)의 부재 = CSV 의미론 잔재" — 본 누수(출구 계약)와 **다른 층**, POC 무해, MVP+ ADR 트리거. 진화는 additive 3단계(갈아엎기 아님 — 60호출/52파일 단일관절 실측). → [설계노트_data조회계약_진화](설계노트_data조회계약_진화_2026-06-12.md). |
| 2026-06-12 | **v6 — 잔여 지연 종결 + 귀속 정정**: ① 레거시 비대 대화 2개 삭제(오너 승인, API) — DB blob 155MB+→**26KB**, 목록 7.1s→2.0s. ② 남은 고정 ~2s 의 진짜 원인 = ~~레거시 경합(v4 가설)~~ → **클라이언트 `localhost`→::1 타임아웃** (404조차 2.2s / 127.0.0.1=16ms 로 분리 증명). 프론트 rest·ws·vite proxy 3곳 127.0.0.1 고정(`bcee112`) → **목록 16ms**. 원신고 "복원 5.5s" 분해 = localhost 2s + 거대블롭 역직렬화 3.5s — 양쪽 모두 해소. |
| 2026-06-12 | **v7 — §9 외부 검토 박제** (슬라이스 1 세션, 접점 코드 실측): 슬라이스 1(입구 경계)과 충돌 0 — 같은 상위 문제(I3 경계 계약 부재)의 출구/입구 형제 수술, 패턴 3중첩(경계·drift·게이트>컨벤션). **방향 평가 = 좋음·과설계 아님**(증거 주도 최소 변경, 일반해 안 만든 것이 적절). 단 이 수정이 만든 잠재 빚 4건 박제(§9.3): ★truthy `_dataref` 스텁의 data_gate 0건 맹점 + catalog produces가 여전히 raw 키를 artifact 로 선언(미래 소비자에게 "물 대신 모형") / count용 전량 적재 잔존 / 크래시-복구 엣지 / 헌법 라우팅 표 미등재. 처방 1순위 = data_gate `_dataref` 인지 한 줄 (슬라이스 2 후보 편입). |
