# ADR-032 — normalized 피봇 영속화 결정 (소스별 정형 테이블 · blended 레이어 · 활성주문 정의)

| | |
|---|---|
| **Status** | **Accepted (잠정 — ⚠ 추후 UX 디자인 시 대폭 수정 가능, 오너 2026-06-17)** |
| 작성일 | 2026-06-17 |
| 영향 범위 | `app/workspace/`(Layer) · `app/data_pg_util.py`(writer) · `canonical_translator`(emission) · contract(order filter) · `setup_data_db` |
| 관련 | ADR-022(DataSource/Workspace 관절) · ADR-020(computed metrics layer) · ADR-031(pushdown G28) · memory `project_normalized_pivot_scope` |

## Context

normalized 피봇 기준점(raw `{*}` → `{*}_normalized` → `{*}_computed`, 소스별 1:1, layer=접미사) 위에 **소스별 정형 테이블**을 실제로 만들려는 단계. 기준점 점검(ultracode 워크플로 `wykcrn2iw`, 5에이전트 적대 감사)이 "빈 테이블 사전생성 = 순서 틀림"을 3 critical로 적발:

1. `write_typed_table`이 save마다 `DROP+CREATE`(추론타입) → 명시 스키마 사전생성 테이블을 첫 save가 삼킴.
2. `canonical_translator`가 채널 *집계 1행*만 emit → 소스별(행단위) 테이블을 채울 경로 자체가 없음.
3. `blended_computed`(MER 등 교차소스)의 채움 주체·레이어 미설계 — Layer Literal에 'blended' 없음.

→ 테이블 생성 전 결정 3건이 선결. 오너: "일단 권장대로 하고, 추후 UX 디자인 시 대폭 수정할 수 있으니 잘 기록."

## Decision

**D1 — 정형 테이블 = 전용 relational writer (append/upsert, DROP 금지).**
`write_typed_table`(추론타입·DROP+CREATE, /db 표시용)과 *별개*로, 명시 스키마·UPSERT writer를 둔다. 정형 테이블(ERD 14종)은 이 경로로만 적재 — 추론타입 경로의 DROP이 정형 스키마를 삼키지 못하게 namespace를 분리. (G28식 불변식: 정형 테이블명엔 DROP 금지 가드.)

**D2 — `blended_computed` = Layer Literal 4번째 'blended'.**
`Layer = ["raw","normalized","computed","blended"]`. 교차소스 지표(MER·총마케팅비·tacos·aMER)는 소스별 computed와 grain이 달라(period 1행) 별 레이어. 채움 주체 = 소스별 normalized 적재 완료 후 별도 집계 단계(orchestration 순서 불변식), PK=period UPSERT.

**D3 — 활성주문 = 취소(C계열) 전체 제외.**
`order_status not startswith 'C'`(C00·C40 등 모든 취소 제외). 기존 `!= C40`보다 견고(미래 C00 대비). 현 mock엔 C40만 존재 → 수치 동일.
⚠ **N00(입금전/미결제)은 N계열이라 *포함*** — 즉 입금전 주문이 매출(order_revenue_krw)에 잡힘. 이는 "입금전을 매출로 인정"하는 잠정 정의(기존 methodology 정신=취소만 제외 계승). **결제완료만 인정(N00 제외)으로 바꾸려면 별도 변경 + orders_normalized 재적재** — 계산정의=오너/UX 영역.

## Consequences

- `canonical_translator`를 **행 emitter로 재작성** 필요(집계 합 → 소스별 행 리스트, channel const 주입 + report_date 파생). 이게 후속 최대 작업.
- 소스별 PK는 ERD대로 *개별* 명시(meta=campaign×date / naver_sa=campaign×device×date / kakao·talktalk=campaign / orders=order). 공통 PK 강요 금지.
- 정형 writer + 추론 writer 2경로 공존 — 적재 주체가 어느 경로인지 명확해야(혼선 시 D1 가드가 차단).
- blended는 적재 순서 의존(소스별 normalized 선행) — orchestration 계약.

## ⚠ 잠정성 — UX 디자인 시 재검토 대상 (오너 명시)

본 결정은 **엔지니어링 기준점**이며, 추후 UX 디자인(대시보드 실제 수요 확정)에서 **대폭 수정 가능**. 예상 변경 축:
- **테이블 grain/PK** — 대시보드가 요구하는 집계 단위에 따라 소스별 분할/병합 재설계.
- **컬럼 노출 범위** — measure16/dimension/time 중 실제 surface할 것만(현 ERD는 풀스펙).
- **blended 레이어 vs computed key** — UX 질의 패턴에 따라.
- **order_status 정의** — 입금전(N00) 매출 인정 여부 = 비즈니스/회계 판단.
- **네이밍·관계형 vs blob** — UX 어휘·질의 성능 요구에 따라.

→ 구현 시 이 결정들을 *하드 가정*으로 박지 말고 교체 용이하게(`project_extension_ease_priority`). 재검토 시 본 ADR Superseded + 새 ADR.

## Alternatives (기각)

- **D1 대안**: write_typed_table 그대로(DROP+infer) — 기각: 정형 스키마(PK·jsonb lineage·타입)를 매 save가 삼킴(점검 critical#1).
- **D2 대안**: blended를 computed 레이어 key로 — 기각: grain(period 1행) 혼재·오너 기준점이 별 테이블 뉘앙스. (단 UX서 재검토 가능.)
- **D3 대안**: `!= C40`만(현행) — 기각: C00 미대비. / 결제완료만(N00 제외) — 보류: 매출정의=오너, 현 단계 과변경.

## Related
ADR-022 · ADR-020 · ADR-031 · memory `project_normalized_pivot_scope`(기준점·FE/BE/통신규약/DB 전 범위) · `project_extension_ease_priority` · [점검리포트](../../reports/피봇기준점_점검리포트_2026-06-17.md)
