"""state_guard (L3+L5) — 제어 평면(state/checkpoint) 입구 크기 게이트 테스트.

근거: docs/reports/근본원인_execution_state_raw누수_2026-06-11.md (소비자 전수 감사 v2)
계획: docs/reports/계획_state경계게이트_L3L5_2026-06-11.md §4

검증:
  - 소형 값 보존 / 초과 값 스텁 치환 (todos[*].data top-level 단위)
  - 메타 필드(status·error·duration) 불변
  - approx_json_size 조기탈출 (대형 입력 전량 직렬화 금지)
  - 통합: GA4 모사 execution_result → 슬림 후 KB대 + responder 무손상
  - L5: execution_stage 최종 update 에 execution_progress 미러 없음
"""
from __future__ import annotations

import json

import pytest

from app.dream_agent.execution.state_guard import (
    STATE_VALUE_MAX_BYTES,
    approx_json_size,
    slim_execution_result,
)


def _make_er(data: dict, todo_id: str = "todo_001") -> dict:
    """ExecutionResult.model_dump(mode='json') 형태 최소 모사."""
    return {
        "plan_id": "p1",
        "todos": {
            todo_id: {
                "todo_id": todo_id,
                "task_type": "DATA_COLLECTION",
                "tool": "ga4_traffic_source_collector",
                "agent": "collection_agent",
                "status": "completed",
                "data": data,
                "error": None,
                "is_mock": False,
                "started_at": 1.0,
                "ended_at": 2.0,
                "duration_ms": 1000.0,
            }
        },
        "phase_timings": [{"phase": 1, "duration_ms": 1000.0}],
        "total_duration_ms": 1000.0,
        "overall_status": "completed",
        "halted_at": None,
        "halt_reason": None,
    }


def _big_rows(n: int = 3000) -> list[dict]:
    """임계치(256KB)를 확실히 넘는 레코드 배열 (~n*120B)."""
    return [
        {"event_name": "session_start", "user_pseudo_id": f"u{i:08d}",
         "event_timestamp": 1700000000 + i, "params": {"source": "naver", "medium": "cpc"}}
        for i in range(n)
    ]


# ───────────────────────── approx_json_size ─────────────────────────

class TestApproxJsonSize:
    def test_scalar_sizes_reasonable(self):
        # 정확값 아닌 추정 — json.dumps 대비 같은 자릿수면 충분
        for v in [12345, 3.14, True, None, "hello", "한글텍스트"]:
            approx = approx_json_size(v, budget=10_000)
            real = len(json.dumps(v, ensure_ascii=False, default=str))
            assert approx <= real * 4 + 8 and real <= approx * 4 + 8

    def test_small_collection_under_budget(self):
        v = {"a": [1, 2, 3], "b": "x" * 100}
        assert approx_json_size(v, budget=10_000) < 1_000

    def test_early_exit_on_huge_input(self):
        # 조기탈출: budget 초과 시 budget 초과값을 *즉시* 반환 (전량 순회 금지).
        huge = _big_rows(200_000)  # ~24MB 상당 — 전량 순회면 느림
        import time
        t0 = time.perf_counter()
        size = approx_json_size(huge, budget=1_000)
        elapsed = time.perf_counter() - t0
        assert size > 1_000          # 초과 판정
        assert elapsed < 0.2         # 조기탈출 (전량 직렬화면 수 초)


# ───────────────────────── slim_execution_result ─────────────────────────

class TestSlim:
    def test_small_values_preserved(self):
        er = _make_er({"session_start_total": 24000, "label": "ROAS", "value": 389.0,
                       "by_source": {"naver": 100, "meta": 50}})
        out = slim_execution_result(er)
        assert out["todos"]["todo_001"]["data"] == er["todos"]["todo_001"]["data"]

    def test_oversized_list_replaced_with_stub(self):
        rows = _big_rows()
        er = _make_er({"clumi_ga4_traffic_raw": rows, "count": len(rows)})
        out = slim_execution_result(er)
        d = out["todos"]["todo_001"]["data"]
        assert d["count"] == len(rows)                      # 소형 값 보존
        stub = d["clumi_ga4_traffic_raw"]
        assert isinstance(stub, dict) and stub.get("_state_guard") == "slimmed"
        assert stub["size_bytes_approx"] > STATE_VALUE_MAX_BYTES

    def test_oversized_nested_dict_replaced(self):
        big = {"nested": {f"k{i}": "v" * 200 for i in range(3000)}}
        er = _make_er({"blob": big})
        out = slim_execution_result(er)
        assert out["todos"]["todo_001"]["data"]["blob"]["_state_guard"] == "slimmed"

    def test_meta_fields_preserved(self):
        er = _make_er({"clumi_ga4_traffic_raw": _big_rows()})
        out = slim_execution_result(er)
        t = out["todos"]["todo_001"]
        assert t["status"] == "completed"
        assert t["duration_ms"] == 1000.0
        assert out["overall_status"] == "completed"
        assert out["phase_timings"] == er["phase_timings"]

    def test_threshold_boundary(self):
        under = "x" * (STATE_VALUE_MAX_BYTES // 2)
        over = "x" * (STATE_VALUE_MAX_BYTES * 2)
        er = _make_er({"small_text": under, "big_text": over})
        out = slim_execution_result(er)
        d = out["todos"]["todo_001"]["data"]
        assert d["small_text"] == under
        assert isinstance(d["big_text"], dict) and d["big_text"]["_state_guard"] == "slimmed"

    def test_original_not_mutated(self):
        # hitl completed_todos(원본·in-memory 체이닝)는 불변이어야 함 — 계획 §2.1
        rows = _big_rows()
        er = _make_er({"clumi_ga4_traffic_raw": rows})
        slim_execution_result(er)
        assert er["todos"]["todo_001"]["data"]["clumi_ga4_traffic_raw"] is rows

    def test_non_dict_data_safe(self):
        er = _make_er({})
        er["todos"]["todo_001"]["data"] = None  # 방어: 비정형 data
        out = slim_execution_result(er)
        assert out["todos"]["todo_001"]["data"] is None

    def test_empty_and_missing_todos_safe(self):
        assert slim_execution_result({"todos": {}})["todos"] == {}
        assert slim_execution_result({}) == {}


# ───────────────────────── 통합 — GA4 모사 + responder 무손상 ─────────────────────────

class TestIntegration:
    def test_ga4_like_turn_result_shrinks_to_kb(self):
        rows = _big_rows(38_000)  # 실제 사건 규모 모사
        er = _make_er({"clumi_ga4_traffic_raw": rows, "count": 38_000, "source_id": "ga4_traffic_source"})
        # 집계·해석 todo (소형) 동반
        er["todos"]["todo_002"] = {**er["todos"]["todo_001"], "todo_id": "todo_002",
                                   "tool": "ga4_session_aggregator",
                                   "data": {"session_start_total": 24000, "label": "세션", "value": 24000}}
        out = slim_execution_result(er)
        total = len(json.dumps(out, ensure_ascii=False, default=str))
        assert total < 64 * 1024, f"슬림 후에도 {total}B — 게이트 실패"

    def test_responder_renders_metrics_and_skips_stub(self):
        # responder._render_metrics — 스텁(dict)은 스킵, 소형 metric 은 렌더 (감사 §7.2-4)
        from app.dream_agent.response.responder import _render_metrics
        from app.dream_agent.schemas.execution_result import ExecutionResult

        er = _make_er({"clumi_ga4_traffic_raw": _big_rows(), "count": 3000})
        er["todos"]["todo_002"] = {**er["todos"]["todo_001"], "todo_id": "todo_002",
                                   "data": {"label": "세션수", "value": 24000, "unit": "건"}}
        slimmed = ExecutionResult.model_validate(slim_execution_result(er))
        text = _render_metrics(slimmed)
        assert "세션수: 24000건" in text
        assert "_state_guard" not in text and "slimmed" not in text


# ───────────────────────── L5 — execution_progress 미러 제거 ─────────────────────────

class TestL5MirrorRemoved:
    @pytest.mark.asyncio
    async def test_empty_plan_update_has_no_progress_mirror(self):
        from app.dream_agent.execution.execution_stage import execution_stage
        cmd = await execution_stage({"plan": {}, "session_id": "t_state_guard"})
        assert "execution_result" in cmd.update
        assert "execution_progress" not in cmd.update

    def test_source_no_longer_writes_mirror(self):
        # 정적 검사 — 메인 경로 Command 에서도 미러 쓰기 부재 (회귀 가드)
        from pathlib import Path
        import app.dream_agent.execution.execution_stage as es
        src = Path(es.__file__).read_text(encoding="utf-8")
        assert '"execution_progress": hitl.get_progress_snapshot' not in src
