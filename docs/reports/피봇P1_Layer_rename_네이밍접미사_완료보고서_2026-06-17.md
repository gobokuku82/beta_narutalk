# 완료보고서 — 피봇 P1: Layer rename + 네이밍 접미사 (2026-06-17)

> 세부계획 [03 기타 구현](../_claude/plans/normalized_pivot_세부03_기타_구현_2026-06-16.md) I1+I3의 받침대 구현. 오너 승인("응") 후 착수.
> 방식: `feedback_no_mixed_codebases`(전환 sprint — 한 번에 정리) · `feedback_test_no_resource_limit`(전체 회귀).

## 무엇을 / 왜
오너 기준점(`{raw}` → `{raw}_normalized` → `{raw}_computed`, layer=접미사)을 코드에 반영. 피봇 중간 레이어 `cleaned`를 `normalized`로 전면 rename하고, typed 테이블 네이밍을 접두사(`{layer}_{name}`)→접미사(`{name}_{layer}`)로 전환.

## 변경 (✓ 실측)
| 영역 | 내용 |
|---|---|
| **Layer 타입** | `base.py`·`models/tool.py` Literal `cleaned`→`normalized` |
| **FileWorkspace** | `file.py` LAYER_DIR `cleaned`→`normalized` |
| **네이밍 SSOT** | `data_pg_util.typed_table_name(layer,key)` = `{stem}_{layer}` 접미사 신설 · `postgres.py` 2곳이 사용 |
| **tool 콜사이트** | 12 tool `.py` `_storage` + 12 catalog `.yaml` `layer` cleaned→normalized |
| **파이프라인** | `pipelines/flows/*.yaml` 8개 `cache.layer` cleaned→normalized |
| **라우트** | `api_v2/routes/dashboard1.py` 4곳 `layer="cleaned"`→normalized (★app 밖이라 1차 grep 누락분) |
| **contract** | report_date sources +4(kakao/talktalk/google/orders) · campaign_id +google (gap 보완, 별 커밋) |
| **테스트** | tripwire·translator storage·workspace path·하드코딩 테이블명(`raw_ga4_*`→`ga4_*_raw`)·e2e SQL layer 갱신 |
| **라이브 DB** | clumi raw 재적재(`load_raw_to_data_db.py`) — 접미사 테이블명 통일 (blob 29 + streamed 2) |

## 검증 (✓ 실행)
- **전체 회귀**: **976 passed** / 5 failed / 2 skipped / 25 deselected.
- **5 failed = 전부 pre-existing** (내 변경 net 신규 실패 **0**): parquet 환경(pyarrow/fastparquet 미설치) ×3 · `test_DC_PERM_6` · `test_o04` (앞서 stash로 pre-existing 증명).
- **data_pilot gate**: OVERALL PASS (run_pilot·verify·coverage·dict 4/4) — 프로토타입 미접촉.
- 피봇 핵심: canonical_translator·baseline·dimension 테스트 green (회귀 안의 포함).

## 정직 — 작업 중 잡은 함정
- **grep 스코프 누락**: 1차 `backend/app`만 grep → `api_v2/routes/dashboard1.py`(app 밖) 4곳을 놓쳐 라우트 KeyError 발생 → 발견·수정. 교훈: 전 repo 스코프로 재확인(최종 grep 0).
- **파이프라인 flow yaml**: tool catalog 외에 `pipelines/flows/*.yaml`에도 `cache.layer: cleaned`가 있어 PipelineDef 검증 실패 → 수정.
- **라이브 DB 마이그레이션**: 기존 clumi 데이터가 옛 prefix 테이블명(`raw_ga4_traffic_source` 38319행)이라 G28 마커 테스트(test_pq6) RED → 재적재로 통일(접미사). ⚠ 옛 prefix 테이블은 orphan으로 잔존(데이터 정합엔 무해, 마커는 신 테이블 가리킴).
- **data_pilot 프로토타입의 `cleaned`**: 격리(자체 폴더 레이아웃, gate 검증) — 의도적 미접촉.

## 한계 / 다음
- **테이블 DDL·translator 소스별 적재 아직**: 본 P1은 *레이어/네이밍 받침대*. 소스별 `{*}_normalized`/`{*}_computed`/`blended_computed` 실제 테이블 생성 + translator의 소스별 emission은 다음 단계.
- google 6채널·measure16·aMER·re-baseline = P2.
- order_status 활성정의(A/B, N00 입금전 포함 여부) = 오너 미결정(P2서 데이터 채울 때 필요).
