# canonical data contract — octorad_canonical_contract (companion)

> **v0.1 — normalized/computed 표준 SPEC. 머신 = [`octorad_canonical_contract_v0.1.yaml`](octorad_canonical_contract_v0.1.yaml).**
> 이 SPEC = 채널별 translator + conversion 규칙의 **단일 권위**. normalized ERD/metadata/desc·lineage를 여기서 *생성*(손수작성 X — [INDEX §2](INDEX.md) 정정).
> 입력: [명명](normalize_canonical_naming_v0.1.md) · [분류 §3 충돌](referrence/normalize_synonym_classification_v0.1.md) · [06 검증](referrence/06_erd_and_verification.md) · [07 업계](referrence/07_industry_raw_to_standard.md).

---

## ① 확정 결정 (오너 confirm — "전부 권장대로")

| 결정 | 값 |
|---|---|
| 언어 | **영문 snake_case** + 단위접미사(`_krw`/`_pct`/`_x`/`_count`) |
| 값 표현 | **정규화값 + 원본 lineage 보존** (Funnel siloed+unified, 07) |
| 파생 | **computed에서 재계산** (채널 보고값은 lineage 대조용만) |
| blended | **`mer`**(=total_revenue/total_ad_cost) 신설. 채널 roas는 비교성⚠ (07 MER) |
| 분리 | `member_id`↔`anon_client_id` · `membership_grade`↔`rfm_tier` |
| 보류 | M2·M5·M7·M8 (Kakao 대행사 doc 블로커, 06 PARTIAL) |

## ② 필드 구조 = 5요소

각 필드 = `name + unit + transform + 표현전략 + 비교성`. measure(cleaned, 원자값) vs metric(computed, 파생) 분리.

```yaml
ad_cost_krw:                      # name (canonical)
  unit: KRW; type: int           # unit
  semantic: 집행 광고비. ⚠ Naver salesAmt=비용
  comparability: ok              # 비교성
  sources:                       # transform (채널별 매핑)
    meta: {column: "data[].spend", transform: "str→int; →KRW"}
    naver_sa: {column: "data[].salesAmt", note: "=비용"}
    ...
# 표현전략(meta.representation_strategy): 정규화값 + lineage{channel,raw_value} 보존
```

## ③ 필드 인벤토리 (42)

| 분류 | 수 | 예 |
|---|--:|---|
| **measures** (cleaned) | 14 | `ad_cost_krw`·`impressions`·`clicks`·`link_clicks`·`conversion_count`·`conversion_revenue_krw`·`paid_reach` + 메시징 5 |
| **metrics** (computed, 파생) | 11 | `roas_x`(재계산)·`link_ctr_pct`·`cpc_krw`·`cvr_pct` · ★`mer`·`acquisition_mer`·`tacos` · `msg_roi_pct` |
| **dimensions** | 15 | `campaign_id`(+channel)·`member_id`·`anon_client_id`·`channel_group`·`membership_grade`·`rfm_tier`·`region`·`utm_*` |
| **time** | 2 | `report_date`(KST)·`event_ts`(KST ISO) |

> ★ 핵심 처방 박제: `roas_x`=conversion_revenue_krw/ad_cost_krw **재계산** · `mer`=전사 blended(=18.3M 분모) · Meta 전환=`omni_purchase` 필터 · `salesAmt`=비용/`convAmt`=매출 · Naver ror·advoost roas **÷100**.

## ④ 거버넌스 (07 업계 반영)

- **품질룰**: salesAmt=비용 semantic·omni_purchase 필터·비교성 flag = 계약 위반 검출 대상(향후 RED 테스트).
- **schema_version + append-only**: API 진화 시 backward-compat(memory `extension_ease`).
- **lineage**: 모든 normalized 값이 `{source_channel, source_column, raw_value, transform}` 동반 → 신뢰.

## ⑤ 이 SPEC이 생성하는 것 (다음)

```
canonical_contract.yaml (이 문서) ──┐
                                    ├─▶ 채널별 translator (declarative, raw→cleaned)
data/clumi/raw (실파일) ────────────┘         │
                                              ▼
                          {client}/cleaned [정규화값 + lineage]
                                              │ 파생 재계산
                                              ▼
                          {client}/computed [roas_x·mer·cvr…]
                          → normalized/computed ERD·metadata·desc 자동생성 + lineage 표시
```

## ⑥ 다음 단계
1. **conversion config** 분리 파일 (통화 rate+effective date · ÷100 · 날짜/TZ · 캐스팅) — 변환룰 외부화.
2. **campaign_crosswalk** (채널 ID → name/UTM 매핑) — C5 join불가 해소.
3. **채널 1개 PILOT translator** (예: Meta) — 이 SPEC 충족 cleaned 배선 (memory `no_mixed_codebases`: 점진).
4. **지표 registry** = 이 contract의 metrics 섹션 확장(mer·channel roas 정의 단일화).
5. M2/M5/M7/M8 = Kakao 블로커 해소 시.

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-14 | v0.1 — 오너 confirm("전부 권장대로") 후 canonical contract SPEC 작성. 42 필드(measures 14·metrics 11·dims 15·time 2). 명명+값표현+lineage+MER+거버넌스 통합. YAML 파싱 검증. |
