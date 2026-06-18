# ADR-031 — data 조회 pushdown 계약 (query/aggregate 관절 확장 + 마커 생존)

| 항목 | 내용 |
|---|---|
| 상태 | **Accepted** (오너 승인 2026-06-12 — [계획_pushdown_수직슬라이스](../../reports/계획_pushdown_수직슬라이스_2026-06-12.md) §2 "좋아" + §8 V2, 마스터 [2] 착수) |
| 결정자 | 오너 (계획서 승인) · 작성 도윤 |
| 날짜 | 2026-06-12 |
| 관련 | ADR-022(관절 신설) · ADR-023(금지어 compose) · 43 게이트 대장 G28 · 19 헌법 I-계열 |

## 배경

CSV 의미론(`get()`=통째 로드)에 조회의 두 번째 차원(범위·집계)이 없어, 38,319행을 매번 전량
Python 순회. 테스트 기반 검증 실측: 같은 집계가 SQL GROUP BY 로 **604ms → 23.6ms (≈26배)**,
정답값 3개 양측 일치 (E4~E5). Postgres raw 의 대용량은 이미 행-테이블로 SQL-ready.

## 결정 5건

1. **필터 표현 = 최소 dict** — `where: {컬럼: 값}` (동등) + `{컬럼__prefix: "2026-04"}` (접두) **두 연산자만**.
   값 비교는 **텍스트 의미론(v1)** — jsonb `->>` 와 일치시키기 위해 양 백엔드 모두 str 비교, None 은 불일치.
   필요해질 때 연산자 추가 (과설계 금지 — convention 우선).
2. **도메인 규칙의 거처 = tool** — 관절(DataSource)은 **범위 축소(행·컬럼·count/sum)만**.
   "활성 주문 정의"·"GA4 소스 추출 fallback" 같은 비즈니스 규칙은 tool 코드 한 곳 (이중화 금지).
3. **두 백엔드 같은답 계약** — 같은 `query/aggregate` 호출은 File·Postgres 에서 동일 결과.
   교차 일관성 테스트로 강제 (`tests/sprint15/test_datasource_query.py`).
4. **text2SQL 비채택 (본 계산 경로)** — pushdown 은 사람이 쓴 파라미터화 SQL(결정론).
   LLM 이 숫자 계산 경로에 개입 금지. text2SQL 은 별도 롱테일 즉석조회 레인 후보로만 (정답값 아님 라벨 전제).
5. **마커 생존 = 저장 계약 (G28)** — `PostgresWorkspace.save()` 는 ⓐ 기존 항목이 `__streamed__` 마커이거나
   ⓑ 신규 데이터가 대용량 record 목록(`STREAM_ROUTE_THRESHOLD=10,000행 이상`)이면 **blob 덮어쓰기 금지 →
   `save_stream` 라우팅**. 근거: 2026-06-11 20:47 외부 수집 save 가 traffic 마커를 blob 으로 덮고
   스트림 테이블을 typed 콘솔 테이블로 DROP/재생성 — pushdown 경로가 수집 1회마다 침묵 소멸하는 구조였음 (실측 E2).
   가드 테스트가 clumi 실DB 마커 존재를 assert (침묵 강등 → RED).

## 결과

- 관절 시그니처: `query(client, source_id, *, where, columns) -> list[dict]` ·
  `query_iter(...)` (query 의 스트리밍 형태 — 대용량 투영의 materialize 방지, 구현 중 V3 실측으로 추가:
  query 만으로는 File 피크 0.1MB→186MB 역행) ·
  `aggregate(client, source_id, *, op∈{count,sum}, column, by, where) -> 스칼라 | {그룹: 값}`.
- 기본 구현은 base 에 (File 자동 지원, 기존 tool 0개 수정). **jsonl 소스는 stream_jsonl 기반 1-pass**
  (전량 적재 역행 금지 — 계획 §8 V3). `stream_jsonl` 은 ABC 의 구체 기본 메서드로 승격 (§8.2 결정).
- Postgres override 는 행-테이블만 SQL — **두 모양 모두 인지**: generic `(_id, data jsonb)` 는 `data->>키`,
  typed(31컬럼 등) 는 컬럼 직접. blob 은 기본 구현 fallback.
- 시범 전환 1개 = `ga4_session_aggregator` (정답값 3개 회귀: 24,000 / 12,496 / 1,823).

## 비채택

- 전체 tool 일괄 전환 (점진 — 트리거 시) · JSONB blob 의 SQL 화 (이득 0) · DataSource async 화 (sync 계약 유지).
