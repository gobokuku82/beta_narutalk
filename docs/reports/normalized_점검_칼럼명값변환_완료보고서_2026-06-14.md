# normalized 레이어 점검 (칼럼명 변경 / 수치 변경) + 코드 수정 — 완료보고서 (2026-06-14)

> 오너 지시: normalized 문서 설계 확인(**칼럼명 변경 / 수치 변경** 두 축) + raw→normalized 코드(data_pilot_project) 점검.

---

## 1. 점검 결과 (두 축)

### 축1: 칼럼명 변경 (matching) = ✓ 정확
pipeline.py가 읽는 raw 컬럼이 contract sources와 **전부 일치**. 의미함정 포함 정확: `salesAmt→ad_cost_krw`(비용)·`convAmt→conversion_revenue_krw`(매출)·`ccnt→conversion_count`·`actions[omni]→conversion_count`.

### 축2: 수치 변경 (mapping) = ⚠ 결함 발견 → 수정
| 결함 (실측) | 위치 | 처리 |
|---|---|---|
| **meta currency 미적용** — `cast_int`만 하면서 라벨은 `"cast_int+KRW"` (거짓). mock=KRW라 우연히 정답, 실 USD면 silent 오류 | pipeline.py:38·42 | ✅ **수정** — config rate table(`make_currency_to_krw`) 연결, `account_currency`별 KRW 환산. 라벨 정직화 |
| pipeline이 conversion_config 미소비 (값변환 inline 하드코딩) | pipeline 전반 | ⚠ **부분 해소** — currency를 config rate table에서 소비하도록 연결. 단 cast_int/pct/date의 *완전* config-driven dispatch는 후속 |

> pct_to_ratio·date 변환은 roas(재계산)·time(미materialize) 대상이라 materialized measure엔 미적용 — 결함 아님.

## 2. 수정 내역

### 코드 (pipeline.py)
- `import yaml` + conversion_config 로드 → `CUR = make_currency_to_krw(config.currency_rates)`. **값변환 외부화**(matching≠mapping, 리서치 ⓓ)의 currency 축 실제 연결.
- `m_meta`: `ad_cost_krw`·`conversion_revenue_krw`에 `CUR(v, account_currency)` 적용. 라벨 `cast_int+KRW`(거짓) → `cast_int+currency_to_krw(KRW)`(정직).
- mock=KRW라 ×1.0 identity → **8/8 보존**, 실 USD 데이터면 이제 정상 환산.

### 문서 (canonical_layers.md — 생성)
- **★ raw→normalized 변환 맵** 신설: measure × 채널별 `raw 컬럼(이름변경 IN)` + `값변환(수치변경)` 한 표에 명시. 두 축을 단일 뷰로 검증 가능. (gen_layer_docs 확장 → 생성, 손수 X)

## 3. 검증 (✓ 실행)
- run_pilot 8/8 · verify 14/14 critical · coverage 18/44 · gate **OVERALL PASS**
- meta ad_cost_krw=9,235,826 불변(KRW identity) · lineage 라벨 `cast_int+currency_to_krw(KRW)` 정직화 확인

## 4. 남은 것
- **완전 config-driven dispatch**: pipeline이 config `apply` 바인딩을 일반적으로 소비(cast_int/pct/date까지)하는 제너릭 디스패처 = 후속(현재 currency만 config 소비, 나머지 inline cast_int — materialized measure엔 충분).
- link_ctr/acquisition_mer/msg_aov 새 measure = 오너 영역(직전 보고서).

## 변경표
| 파일 | git | 변경 |
|---|---|---|
| `backend/app/data_pilot_project/pipeline.py` | ✅커밋 | currency config 연결 + 라벨 정직화 |
| `docs/agent_specs/ERD/erd_octorad_canonical_layers_v0.1.md` | ✅커밋 | raw→normalized 변환 맵(칼럼명+값변환) 생성 |
| `docs/_claude/data/erd/gen_layer_docs.py` | gitignore | 변환 맵 생성 로직 |

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-14 | normalized 두 축 점검. 이름=정확. 값=meta currency 미적용/거짓라벨 수정(config rate 연결). 변환 맵 doc 생성. 8/8 보존. |
