# data_pilot_project — raw → normalized(cleaned) → computed 참조 구현 (PILOT)

> **격리된 파일럿.** 기존 `app/dream_agent/tools/` 를 *건드리지 않고*, canonical contract + conversion config 가 실제로 작동하는지 검증한다. 이후 이걸 **레퍼런스로 tools 를 업데이트**한다 (memory `no_mixed_codebases`: 점진 추가 후 전환).

## 무엇을 증명하나
SPEC(문서) → 코드가 도는가 + 알려진 정답을 재현하는가.

```
data/clumi/raw/  ──translator(contract+config)──▶  cleaned [정규화값 + lineage]
                                                        │ compute(파생 재계산)
                                                        ▼
                                                   computed [roas_x · mer]
검증: ad_cost_krw 합 = 18,306,923 / orders 매출 = 119,539,660 / mer = 6.53
```

## 설계 출처 (SPEC)
- 이름·필드(matching): `docs/agent_specs/ERD/octorad_canonical_contract_v0.1.yaml`
- 값 변환(mapping): `docs/agent_specs/ERD/octorad_conversion_config_v0.1.yaml`
- 검증 근거: 06(공식 doc) · 07(업계 MER) · 2026-04 mock 재계산 기준값

## 핵심 원칙 (구현으로 박제)
1. **matching ≠ mapping** — 이름 매핑(채널 spec)과 값 변환(transforms)을 분리.
2. **정규화값 + lineage** — 모든 cleaned 값이 `{channel, source_column, raw_value, transform}` 동반(신뢰).
3. **파생은 computed 재계산** — roas_x = conversion_revenue/ad_cost (채널 보고값 아님).
4. **MER(blended)** = orders 매출 / 총 ad_cost — 채널 roas(과대) vs 전사 mer 대비.
5. **grain 주의** — meta by_age/instagram_inapp 은 performance 의 breakdown → ad_cost 합산서 제외(이중계상 방지).
6. **의미함정** — naver salesAmt=비용 / convAmt=매출. Meta omni_purchase 필터.

## 파일
| 파일 | 역할 |
|---|---|
| `transforms.py` | conversion config op 구현 (cast·÷100·omni_purchase 필터·KST 등) |
| `pipeline.py` | 채널 spec + translator(raw→cleaned canonical + lineage) + 집계 |
| `compute.py` | cleaned → computed (channel roas_x · blended mer) |
| `run_pilot.py` | 오케스트레이터 + 정답 검증 + 리포트 |

## 실행
```
python backend/app/data_pilot_project/run_pilot.py
```

## tools 반영 시 (다음)
이 파일럿이 통과하면 → `tools/normalization/` 의 `format_normalizer`(폐기 예정)·`ad_cost_helper`(산발) 를 이 구조(채널 translator + config)로 전환. 기존 코드는 격리 후 한 번에 정리.
