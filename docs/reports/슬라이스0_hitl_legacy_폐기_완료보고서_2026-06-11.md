# 슬라이스 0-① 완료보고서 — hitl legacy(Sprint 12 event 트랙) 폐기

> 일자: 2026-06-11 · 커밋: `b75df88` (13파일, +67/−291)
> 분류: 버그 수정 (죽은 코드 제거가 곧 수정 — "정리"가 아님)
> 상위 맥락: [아키텍처 분석종합](../_claude/4layer_system/아키텍처_분석종합_조직모델_260611.md) §6 슬라이스 0 / [2차 재분석](../_claude/4layer_system/재분석_2차_fresh_eyes_결과_260611.md)

---

## 1. 무엇을 왜

**버그**: 모든 plan 승인/거부에서 `hitl_ack`가 `accepted: false`로 발신 — 실제 재개는 정상인데 프로토콜이 거짓말.

**근본 원인 (git 고고학으로 확정)**:
- 2026-04-03 `2ce4aff`: Sprint 12 event 트랙(요청 장부 + create_request/submit_response) 출생 — 당시의 현역 구현.
- 2026-04-20 `e85bc4b`/`100fe23`: Sprint 13 Queue 트랙(signal_resume)으로 대체.
- 2026-05-31 `533a632`: 구세대 본체 `_run_agent`(351줄) 폐기 — **그러나 장부와 ws_hitl의 submit_response 호출은 잔존(반쪽 철거)**.
- 이후 ~11일간: 빈 장부 조회 → accepted 항상 false.

**파급(전부 검증됨)**: ① frontend pending 영구 미해제 → PlanReviewModal 잔존 + 중복 응답이 Queue에 버퍼링되어 이후 [중지]가 0초에 풀리는 유령 resume 경로 ② 관찰 콘솔이 모든 승인을 'rejected' 오표기 ③ 프로토콜 계약 거짓.

**판정 근거**: "죽음 vs 미구현" 4문항 체크리스트 — ①한때 현역이었다가 대체됨 ②대체재(Queue) 가동 중 ③부활 계획 0건(ADR-001 dual-track은 폐기된 과거 결정) ④코드 스스로 legacy 선언. → 확정 사망, 보관 가치 없음(git이 보관소).

## 2. 변경 내역 (짝 단위 일괄 철거 — 5/31 반쪽 철거의 교훈)

| 구분 | 내용 |
|---|---|
| **수정 본체** | `ws_hitl.py`: submit_response 호출 제거. `accepted` = 재개 신호 실전달 기준(활성 turn 가드 통과 + signal_resume put). 미전달 시 `reason: missing_turn_id` |
| **코드 삭제** | `hitl_manager/manager.py`: 장부 3종(_pending_requests/_response_events/_responses) + 메서드 6개(create_request/wait_for_response/submit_response/get_pending_request/cancel_request/cleanup, ~140줄) + 死 `get_execution_result`(progress 부재 시 "completed" 조작 반환하던 거짓-성공 제조기) |
| **모델 삭제** | `models/hitl.py` 파일(HITLRequest/HITLResponse), `enums.py` HITLRequestType, `models/__init__` export 정리 |
| **설정 삭제** | `config.py` HITL_TIMEOUT_SEC·HITL_MAX_RETRIES(legacy 예약 슬롯 — 사용처 0 확인) |
| **테스트** | conftest + e2e live 2파일의 장부 clear 제거. WH-03·HT-06f에 `accepted is True` 정직 단언 **추가**(새 동작 박제) |
| **spec 동반 갱신** | 12_manager_layer: 죽은 API 표기 제거, §4.4 이중 트랙 → 단일 Queue 트랙. 30_DATA_MODELS §8: HITLRequestType 폐기 표기 + ToolCategory 11값 정정(기존 4값 표기는 stale이었음) |
| **묘비** | 삭제 지점마다 무엇을·왜·대체재·복원 위치(git 해시) 주석 |

## 3. 검증

| 항목 | 결과 |
|---|---|
| 직접 영향 HITL 테스트 (ws_hitl 통합·timeout 가드·A3 편집 통합 3종·resume 루프) | **53/53 통과** |
| 전체 회귀 | **865 통과 / 16 실패 / 2 skip** |
| 실패 16건 원인 분리 | **변경 전 HEAD에 stash 후 동일 16건 실패 재현** → 전부 사전 존재, 본 변경의 신규 파손 **0건** |
| 잔존 참조 전수 grep | 묘비 주석 + `_scratch/`(pytest 수집 제외, 자체 mock 정의)만 — 코드 잔존 0 |
| 임포트 스모크 | models/manager/ws_hitl/Settings 전부 정상 |

**사용자 가시 효과**: 승인 시 `accepted: true` 정상 발신 → pending 해제·모달 정상 종료·유령 resume 경로 폐쇄·관찰 콘솔 'approved' 정상 표기.

## 4. 사전 존재 실패 16건 (본 작업 범위 밖 — 후속 추적)

`test_hitl_timeout_integration` 10 + `test_hitl_timeout_resume_query_unit` 1 (mock WS 경유 broadcast 쪽 깨짐 — 슬라이스 0 잔여 작업 시 동반 점검 권장) · `test_dc_perm` DC_PERM_6 1 · `test_batch5` o04 ROAS 정렬 1 · `test_phase3_pptx*` 3.

## 5. 다음

- 슬라이스 0 잔여: **layer_inspector `"success"`→`"completed"`**(+LG-03/04 테스트 어휘 교정, spec 20이 05-15에 문서화한 그 버그) + **FAILED→"분석을 완료했습니다" 문구 차단**(responder + ws complete status).
- 오너 검증(기준질문): 채팅에서 계획 승인 1회 → 관찰 콘솔에 'approved' 표기 확인.
