# 계획 — L4: collector 참조 반환 (발원지 수정) · 2026-06-11

> 상태: **구현·검증 완료** (사용자 허가 2026-06-11 → 커밋 `85ef5de`). §5 통과 결과 아래 박제.
> 체인: [근본원인 v2](근본원인_execution_state_raw누수_2026-06-11.md) §6 "L4=진짜 근본" → [L3+L5 보고](보고_state경계게이트_구현검증_2026-06-11.md) §2 "L3가 못 푼 것" → 본 계획.

---

## 1. 무엇을 고치나 — 발원지

[collection/_base.py:126](../../backend/app/dream_agent/tools/collection/_base.py#L126) `RawCollectorBase.execute`가 창고에서 읽은 **데이터셋 전체를 결과에 실어 반환**(`{PRODUCES_KEY: data}`). 이로 인해 (L3 적용 후에도) 남는 비용:
- 실행 중 **RAM 104MB 상주** (hitl completed_todos 보관)
- executor `_json_safe` **딥카피 CPU — 이벤트루프 수십 초 블록** (e2e에서 ws keepalive 끊김으로 실증)
- previous_results로 **모든 다음 todo에 전달** (소비자 0 — 전수 감사 확정)

**수정**: collector는 데이터 대신 **참조(영수증)** 반환. "데이터는 데이터 평면에 산다. tool 결과는 그 주소다."

## 2. 설계

### 2.1 반환 계약 변경 (베이스클래스 1곳 = 21개 collector 커버)
```python
# RawCollectorBase.execute — 변경 후
data = self.ds.get(context.client_id, source_id)   # count 용 적재 (transient — 반환 안 하므로 GC)
count = ...  # 현행 로직 유지
return {
    self.PRODUCES_KEY: {            # 키 유지(truthy dict) — planning produces 의미·표시 호환
        "_dataref": True,
        "source_id": source_id,
        "layer": "raw",
        "count": count,
        "where": "data 레이어에서 self.ds.get/stream_jsonl 로 조회 (결과 비탑재 정책)",
    },
    "count": count,                  # _generate_summary "N건 수집" 보존
    "file_no": self.FILE_NO,
    "source_id": source_id,
    "_meta": {"params": self.merge_params(params)},
}
```
- `ExternalRawCollectorBase._fetch_from_mock_api`(수집 side-effect)·`InternalRawCollectorBase` — **변경 없음** (상속으로 자동 적용).
- `ReviewCollector`는 **BaseTool 직속(베이스 밖, [review_collector.py:37](../../backend/app/dream_agent/tools/collection/review_collector.py#L37))** → 유일한 진짜 raw 체인(리뷰)은 **무영향. 확인 완료.**
- count 적재 비용(일시 로드)은 현행 유지 — POC 단순성. MVP+ 옵션: jsonl `stream_jsonl` 카운트/DB COUNT pushdown (계획 외, 박제만).

### 2.2 안전 근거 (전수 감사 — 근본원인 v2 §7)
- 21개 collector produces 키의 previous_results 소비자 **0** (find_in_previous 전수·gate consumes 8건 전수·params 주입 0·pipeline 체이닝 0).
- 키를 없애지 않고 **truthy dict 로 유지** → 미지의 존재성 검사(혹시 있어도)는 통과, 내용 소비는 없음(감사).
- `_generate_summary`는 `count` top-level 읽음 — 보존.
- state_guard(L3)는 그대로 — 이중 방어. L4 후 collector 턴에서 **slim warning 이 더 이상 안 떠야 정상** (= 검증 신호로 활용).

## 3. 영향 확인 대상 (구현 시 체크리스트)
| 대상 | 예상 | 조치 |
|---|---|---|
| [test_execution_dataframe_serialization.py](../../backend/tests/test_execution_dataframe_serialization.py) | fake collector 가 DataFrame 반환하는 시뮬 — `_json_safe` 검증이라 유지될 듯 | 실행해 확인, 필요 시 주석 갱신 |
| [tests/dashboard1/test_collectors.py](../../backend/tests/dashboard1/test_collectors.py) | subclass·PRODUCES_KEY 속성 검사 — 무영향 예상 | 실행 확인 |
| [tests/collection/test_external_seam.py](../../backend/tests/collection/test_external_seam.py) | fetch side-effect 검사 — 무영향 | 실행 확인 |
| `dashboard1_kpi_revenue` pipeline | collector step 산출 미소비(다음 step self-load) | e2e 1회 |
| kst_timezone_normalizer 기존 버그 | L4 와 무관(이미 깨져 있음) — 본 계획 범위 밖 | 별도 과제 유지 |

## 4. 테스트 계획 (TDD)
신규 `backend/tests/sprint15/test_collector_dataref.py`:
1. Internal collector: 반환에 데이터셋 부재 + `_dataref` 스텁 + count 정확 (fake DataSource 주입)
2. External collector: fetch side-effect 후 동일 계약
3. 반환 전체 json 크기 < 4KB (대형 소스 모사에도)
4. `_generate_summary` "N건 수집" 보존
5. find_in_previous(PRODUCES_KEY) → truthy dict (존재성 호환)
회귀: 전체 suite + §3 대상 직접 실행.

## 5. 실측 e2e (통과 조건) — **전부 통과 (2026-06-11, 커밋 `85ef5de`)**
- [x] GA4 턴: collector data = **`clumi_ga4_traffic_raw=◆DATAREF(count=38319)`** — 발원지에서 이미 참조, ★SLIMMED 부재(게이트가 일할 필요 없어짐). checkpoint 총 3,509B.
- [x] **ws keepalive(ping 기본값) 켠 채 완주** — L3 때 끊기던 이벤트루프 블록(거대 _json_safe) 해소 증명.
- [x] metric 턴: 답변 무손상 "2026-04 매출 1억1954만원, 주문 3,420건 중 활성 1,919건…" + collector summary "38319건/3420건 수집" 보존. checkpoint 3,433B.
- [x] 리뷰 턴: 체인 6 todo 전부 정상(수집→정규화 24건→정제→감성 58.3/25.0/16.7→인사이트 5→요약). ReviewCollector 무영향 실증. checkpoint 8,824B.
- 단위 6/6 + 영향 체크리스트 3건 green(특히 collectors count 회귀가 **실데이터로 21종 실행**, ga4=38,319 정확) + 전체 865 passed(기존실패 16 동일).

### 보너스 실증 — 경계 게이트(L3)의 보편성 라이브 증명
metric 턴에서 `active_orders_filter`(collector 아님, cleaning tool)의 `orders_active`(주문 3,420행)가 **★SLIMMED** — **L4가 못 덮는 "비슷한 다른 케이스"를 L3가 그 자리에서 잡았다.** 답은 무손상(revenue_total 은 데이터 평면 직접 읽음). 두 층(발원지 수정 + 경계 게이트)이 함께 있어야 하는 이유의 실측 사례. (orders_active 도 추후 L4식 정리 후보 — 급하지 않음, 게이트가 막는 중.)

## 6. 롤백
베이스클래스 1파일 revert 로 즉시 복구 (subclass 21개 무수정이므로).

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-11 | v1 — 발원지 수정 설계. 반환 계약(참조 스텁)·안전 근거(감사)·영향 체크리스트·TDD·e2e 기준·롤백. **구현 허가 대기.** |
| 2026-06-11 | v2 — 사용자 허가 → 구현·검증 완료(`85ef5de`). §5 전부 통과 + 보너스(active_orders_filter ★SLIMMED = L3 보편성 라이브 실증). |
