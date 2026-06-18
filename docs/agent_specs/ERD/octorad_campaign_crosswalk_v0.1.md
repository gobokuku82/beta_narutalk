# campaign_crosswalk — 채널 campaign_id 매핑 (C5)

> **v0.1 — 채널별 campaign ID 네임스페이스 매핑.** 직접 join 불가(C5) → name 정규화 매칭.
> 생성: data_pilot crosswalk. 2026-06-14.

---

## 현황 (materialized 실측)

| 항목 | 값 |
|---|---|
| 총 campaign | 25 |
| ID 공간(채널) | advoost, internal, kakao, meta, naver_sa, talktalk |
| canonical 그룹 | 22 |
| **cross-channel 그룹** | **0** |
| unlinked | 3 (naver_sa 등 campaign_name raw 부재) |

> ★ **실측 발견**: cross-channel 그룹 = **0**. 채널 간 campaign이 이름으로도 자동연결 안 됨 → ID뿐 아니라 *이름 체계도 채널마다 달라* **의도적 매핑(UTM 규칙·수동) 필요**. C5가 ID만의 문제가 아님을 실증.

## 처방

- 직접 ID join 금지(네임스페이스 분리). 교차 연결 = `utm_campaign` 규칙 or 수동 매핑테이블.
- naver_sa는 raw에 campaign_name 부재 → utm/키워드 기반 별도 매핑.

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-14 | v0.1 — pilot materialized crosswalk. cross-channel 0 실측. |