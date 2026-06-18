"""I11-a — Layer Guard Unit 테스트.

명세서: docs/_claude/checkpointer/sprint13_i11_i12_plan.md §2.5 + §2.7

7 케이스:
  LG-01 COGNITIVE_EMPTY_QUERY (fatal)
  LG-02 PLANNING_EMPTY_PLAN (fatal)
  LG-03 EXECUTION_ALL_FAILED (fatal)
  LG-04 EXECUTION_PARTIAL_FAILED (warning)
  LG-05 RESPONSE_EMPTY (fatal)
  LG-06 inspect_layer_output 순수함수 (5 case matrix)
  LG-07 key-presence guard — planning reject 경로 false fatal 방지
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ──────────────────────────────────────────────────────────────────
# LG-01 COGNITIVE_EMPTY_QUERY
# ──────────────────────────────────────────────────────────────────

def test_LG01_cognitive_empty_query_fatal():
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    errs = inspect_layer_output("cognitive", {"structured_query": {}})
    assert len(errs) == 1
    assert errs[0]["code"] == "COGNITIVE_EMPTY_QUERY"
    assert errs[0]["severity"] == "fatal"
    assert errs[0]["layer"] == "cognitive"


def test_LG01b_diagnose_degrade_is_not_empty():
    """진단 degrade(tasks=[])라도 brand/domain 있으면 빈 쿼리 아님 → 중단 안 함 (2026-06-10 버그픽스).

    brand 는 targets 안에 있다. 과거 top-level sq.get("brand") 만 보던 버그로, "진단하고 비교"·
    "왜 매출 줄었어?" 같은 모든 degrade(tasks=[]) 가 COGNITIVE_EMPTY_QUERY fatal 로 죽었음.
    """
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    sq = {
        "targets": {"brand": "C:LUMI"},
        "intent": {"operation": "diagnose", "domain": ["revenue"]},
        "tasks": [],
    }
    errs = inspect_layer_output("cognitive", {"structured_query": sq})
    assert errs == [], "brand/domain 있는 degrade 는 빈 쿼리가 아니라 중단되면 안 됨"


def test_LG01c_truly_empty_still_fatal():
    """brand/domain/tasks 다 없으면 여전히 빈 쿼리 → fatal (가드 본래 기능 보존)."""
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    sq = {"targets": {}, "intent": {"domain": []}, "tasks": []}
    errs = inspect_layer_output("cognitive", {"structured_query": sq})
    assert len(errs) == 1
    assert errs[0]["code"] == "COGNITIVE_EMPTY_QUERY"


# ──────────────────────────────────────────────────────────────────
# LG-02 PLANNING_EMPTY_PLAN
# ──────────────────────────────────────────────────────────────────

def test_LG02_planning_empty_plan_fatal():
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    errs = inspect_layer_output("planning", {"plan": {"todos": []}})
    assert len(errs) == 1
    assert errs[0]["code"] == "PLANNING_EMPTY_PLAN"
    assert errs[0]["severity"] == "fatal"


# ──────────────────────────────────────────────────────────────────
# LG-03 EXECUTION_ALL_FAILED
# ──────────────────────────────────────────────────────────────────

def test_LG03_execution_all_failed_fatal():
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    errs = inspect_layer_output("execution", {
        "execution_result": {
            "todos": [
                {"id": "t1", "status": "failed"},
                {"id": "t2", "status": "failed"},
            ],
        },
    })
    assert len(errs) == 1
    assert errs[0]["code"] == "EXECUTION_ALL_FAILED"
    assert errs[0]["severity"] == "fatal"
    assert errs[0]["detail"]["failed_count"] == 2


def test_LG03b_partial_failure_is_not_all_failed_regression():
    """(2026-06-11) 'success'≠'completed' 어휘 drift 수정 회귀.

    옛 가드는 존재하지 않는 status "success" 를 세어 succeeded 가 항상 0 → 부분 실패가
    전부 ALL_FAILED(fatal)로 격상됐다 (루트 logs/layer_guard.jsonl 06-10 실발화:
    12개 중 1 실패 → "모든 Todo 실행이 실패했습니다" abort). 실제 enum 값으로 박제.
    """
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    todos = [{"id": f"t{i}", "status": "completed"} for i in range(11)]
    todos.append({"id": "t12", "status": "failed"})
    errs = inspect_layer_output("execution", {"execution_result": {"todos": todos}})
    assert len(errs) == 1
    assert errs[0]["code"] == "EXECUTION_PARTIAL_FAILED", "부분 실패가 ALL_FAILED 로 격상되면 안 됨"
    assert errs[0]["severity"] == "warning"
    assert errs[0]["detail"]["succeeded_count"] == 11


# ──────────────────────────────────────────────────────────────────
# LG-04 EXECUTION_PARTIAL_FAILED (warning, 계속 진행)
# ──────────────────────────────────────────────────────────────────

def test_LG04_execution_partial_failed_warning():
    # (2026-06-11) 픽스처 어휘 교정: "success"(실재하지 않는 값) → "completed"(TodoStatus enum).
    # 옛 픽스처는 가드의 같은 오타와 동어반복으로 GREEN 이라 drift 를 영속화했었음.
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    errs = inspect_layer_output("execution", {
        "execution_result": {
            "todos": [
                {"id": "t1", "status": "completed"},
                {"id": "t2", "status": "failed"},
                {"id": "t3", "status": "completed"},
            ],
        },
    })
    assert len(errs) == 1
    assert errs[0]["code"] == "EXECUTION_PARTIAL_FAILED"
    assert errs[0]["severity"] == "warning"
    assert errs[0]["detail"]["failed_count"] == 1
    assert errs[0]["detail"]["succeeded_count"] == 2


# ──────────────────────────────────────────────────────────────────
# LG-05 RESPONSE_EMPTY
# ──────────────────────────────────────────────────────────────────

def test_LG05_response_empty_fatal():
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    errs = inspect_layer_output("response", {"response": {"text": "   "}})
    assert len(errs) == 1
    assert errs[0]["code"] == "RESPONSE_EMPTY"
    assert errs[0]["severity"] == "fatal"


# ──────────────────────────────────────────────────────────────────
# LG-06 순수함수 matrix — 정상 케이스는 빈 리스트
# ──────────────────────────────────────────────────────────────────

def test_LG06_clean_outputs_return_empty():
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    # cognitive 정상
    assert inspect_layer_output("cognitive", {
        "structured_query": {"brand": "블루밍글로우", "tasks": ["analysis"]},
    }) == []

    # planning 정상
    assert inspect_layer_output("planning", {
        "plan": {"todos": [{"id": "t1"}]},
    }) == []

    # execution 정상 (모든 todo completed — 실제 TodoStatus enum 값)
    assert inspect_layer_output("execution", {
        "execution_result": {
            "todos": [{"status": "completed"}, {"status": "completed"}],
        },
    }) == []

    # response 정상
    assert inspect_layer_output("response", {
        "response": {"text": "결과입니다"},
    }) == []

    # 알려지지 않은 node — 빈 리스트
    assert inspect_layer_output("unknown_node", {"anything": {}}) == []


# ──────────────────────────────────────────────────────────────────
# LG-07 🔴 key-presence guard (R4 발견 — false fatal 방지)
# ──────────────────────────────────────────────────────────────────

def test_LG07_planning_reject_path_skipped():
    """planning 노드가 reject 경로 `{"response": {...}}` 만 emit 시
    PLANNING_EMPTY_PLAN fatal 오판하지 않음."""
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    # reject → planning이 response만 emit (plan key 없음)
    errs = inspect_layer_output("planning", {
        "response": {"text": "실행 계획이 거부되었습니다.", "format": "text"},
    })
    assert errs == []


def test_LG07b_cognitive_error_only_skipped():
    """cognitive가 error만 emit 시 COGNITIVE_EMPTY_QUERY 오판 방지."""
    from app.dream_agent.system_graph.layer_inspector import inspect_layer_output

    errs = inspect_layer_output("cognitive", {"error": "LLM call failed"})
    assert errs == []


# ──────────────────────────────────────────────────────────────────
# summarize_state 단위 테스트
# ──────────────────────────────────────────────────────────────────

def test_summarize_state_basic():
    from app.dream_agent.system_graph.layer_inspector import summarize_state

    fs = {
        "structured_query": {"brand": "블루밍글로우", "tasks": ["x"]},
        "plan": {"todos": [
            {"id": "t1", "team": "analysis_team"},
            {"id": "t2", "team": "analysis_team"},
        ]},
        "execution_result": {"todos": [{"status": "success"}]},
    }
    s = summarize_state(fs)
    assert s["brand"] == "블루밍글로우"
    assert s["plan_todos"] == 2
    assert s["plan_teams"] == ["analysis_team"]
    assert s["execution_todos_total"] == 1


def test_summarize_state_brand_nested_in_targets():
    """(2026-06-11) brand 는 targets 중첩 — 요약 함수의 잔존 top-level 버그 수정 회귀.

    실제 StructuredQuery 는 targets.brand 라 옛 요약은 JSONL 의 brand 가 항상 null
    (루트 logs 전수 실측) — 페어 누적의 brand 축이 통째로 훼손됐었음.
    """
    from app.dream_agent.system_graph.layer_inspector import summarize_state

    s = summarize_state({
        "structured_query": {"targets": {"brand": "C:LUMI"}, "tasks": []},
    })
    assert s["brand"] == "C:LUMI"


def test_summarize_state_empty():
    from app.dream_agent.system_graph.layer_inspector import summarize_state

    s = summarize_state({})
    assert s["brand"] is None
    assert s["plan_todos"] == 0


# ──────────────────────────────────────────────────────────────────
# append_guard_log 단위 테스트 (tmp_path 격리)
# ──────────────────────────────────────────────────────────────────

def test_append_guard_log_appends_jsonl(tmp_path, monkeypatch):
    import app.dream_agent.system_graph.layer_inspector as lg_mod

    log_file = tmp_path / "layer_guard.jsonl"
    monkeypatch.setattr(lg_mod, "_LOG_PATH", log_file)

    lg_mod.append_guard_log({"code": "X", "ts": "2026-04-21T00:00:00Z"})
    lg_mod.append_guard_log({"code": "Y", "ts": "2026-04-21T00:00:01Z"})

    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["code"] == "X"
    assert json.loads(lines[1])["code"] == "Y"
