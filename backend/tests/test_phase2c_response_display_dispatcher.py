"""Phase 2c — response 결정론 표시 dispatcher (2026-06-09).

사용자 모델: response = 받은 산출물 종류로 *분류* → 시각화(text/excel/pdf/ppt/chart). LLM 0.
build_display_payload(sq, exec_result) = 정직 degrade 게이트 통과 후 호출되는 결정론 매퍼.
(서술은 tool 책임, 표시는 response — Phase 2 "서술 tool / response 표시" 완성.)

2c-1 report_markdown 산출 → text 시각화
2c-2 summary 산출(no report) → text 시각화 + summary 필드
2c-3 metric 산출(no report/summary) → text 결정론 렌더(값 포함, 노이즈 제외)
2c-4 format = goal.output_format 직매핑
2c-5 pdf/excel 파일 산출 → attachments(kind 분류)
2c-6 halted → format=error
2c-7 meta.display 플래그(관측)
2c-8 LLM 미사용 — 순수 함수 (import 시 get_llm_client 호출 0)
"""
from __future__ import annotations

from app.dream_agent.response.responder import build_display_payload
from app.dream_agent.schemas.execution_result import ExecutionResult, TodoResult, TodoStatus
from app.dream_agent.schemas.response_payload import ResponseFormat
from app.dream_agent.schemas.structured_query import StructuredQuery


def _sq(output_format: str = "text") -> StructuredQuery:
    return StructuredQuery.model_validate({
        "targets": {},
        "goal": {"type": "metric", "output_format": output_format},
        "meta": {},
    })


def _todo(tool: str, data: dict, status: TodoStatus = TodoStatus.COMPLETED) -> TodoResult:
    return TodoResult(
        todo_id="t", task_type="x", tool=tool, status=status,
        data=data, started_at=0.0, ended_at=0.0, duration_ms=0.0,
    )


def _exec(*todos: TodoResult, overall: TodoStatus = TodoStatus.COMPLETED) -> ExecutionResult:
    return ExecutionResult(
        todos={f"t{i}": t for i, t in enumerate(todos)}, overall_status=overall,
    )


# ── 2c-1: report_markdown → text 시각화 ──

def test_2c_1_text_from_report_markdown():
    er = _exec(_todo("report_writer", {"report_markdown": "## 보고서\n본문..."}))
    p = build_display_payload(_sq("text"), er)
    assert p.text == "## 보고서\n본문...", "report_markdown 을 text 로 시각화"


# ── 2c-2: summary(no report) → text + summary 필드 ──

def test_2c_2_text_from_summary_when_no_report():
    er = _exec(_todo("summary_generator", {"summary": "4월 매출은 1.2억원입니다"}))
    p = build_display_payload(_sq("text"), er)
    assert p.text == "4월 매출은 1.2억원입니다"
    assert p.summary == "4월 매출은 1.2억원입니다"


# ── 2c-3: metric(no report/summary) → 결정론 렌더 ──

def test_2c_3_text_renders_metric_when_no_narration():
    er = _exec(_todo("revenue_total", {"revenue_total": 120000000, "count": 1, "_meta": {"a": 1}}))
    p = build_display_payload(_sq("text"), er)
    assert "120000000" in p.text and "revenue_total" in p.text, "metric 값을 text 로 결정론 렌더"
    assert "count" not in p.text and "_meta" not in p.text, "구조 노이즈는 렌더 제외"


# ── 2c-4: format = output_format ──

def test_2c_4_format_from_output_format():
    er = _exec(_todo("summary_generator", {"summary": "x"}))
    assert build_display_payload(_sq("text"), er).format == ResponseFormat.TEXT
    assert build_display_payload(_sq("pdf"), er).format == ResponseFormat.PDF


# ── 2c-5: 파일 산출 → attachments ──

def test_2c_5_file_artifacts_become_attachments():
    er = _exec(
        _todo("summary_generator", {"summary": "x"}),
        _todo("pdf_renderer", {"pdf_file_path": "/mock/r.pdf"}),
        _todo("excel_template_filler", {"excel_file_path": "/mock/r.xlsx"}),
    )
    p = build_display_payload(_sq("pdf"), er)
    by_kind = {a.kind: a.path for a in p.attachments}
    assert by_kind.get("pdf") == "/mock/r.pdf", "pdf 파일 → attachment(kind=pdf)"
    assert by_kind.get("excel") == "/mock/r.xlsx", "excel 파일 → attachment(kind=excel)"


# ── 2c-6: halted → format=error ──

def test_2c_6_halted_is_error_format():
    er = _exec(_todo("revenue_total", {}, status=TodoStatus.FAILED), overall=TodoStatus.FAILED)
    p = build_display_payload(_sq("text"), er)
    assert p.format == ResponseFormat.ERROR, "overall_status=FAILED 면 format=error (LLM 추론 불필요)"


# ── 2c-7: meta.display 플래그 ──

def test_2c_7_meta_has_display_flag():
    er = _exec(_todo("summary_generator", {"summary": "x"}))
    assert build_display_payload(_sq("text"), er).meta.get("display") is True, (
        "결정론 표시 식별 플래그(관측) — 빌더가 LLM산출/결정론 구분"
    )


# ── 2c-9: (2026-06-11 정직화) FAILED 는 성공 문구 금지 — 실패 고지 + error 필드 ──

def test_2c_9_failed_without_artifacts_has_honest_failure_text():
    """FAILED + 산출 0 이 "분석을 완료했습니다." 로 둔갑하던 fallback 차단 회귀 (정직 불변식 I1)."""
    er = ExecutionResult(
        todos={"t0": _todo("revenue_total", {}, status=TodoStatus.FAILED)},
        overall_status=TodoStatus.FAILED,
        halted_at="t0", halt_reason="ValueError: Missing required param: period",
    )
    p = build_display_payload(_sq("text"), er)
    assert "분석을 완료했습니다" not in p.text, "실패가 성공 문구로 표시되면 안 됨"
    assert "실패" in p.text
    assert "t0" in p.text, "중단 지점 표기"
    assert p.error, "format=error 면 error 필드 설정 (과거 설정처 0 이던 필드)"
    assert p.format == ResponseFormat.ERROR


def test_2c_9b_failed_with_partial_artifact_shows_failure_note_first():
    """부분 산출이 있어도 실패 고지가 먼저 — 그 뒤에 부분 결과를 보존 표시."""
    er = ExecutionResult(
        todos={
            "t0": _todo("summary_generator", {"summary": "4월 매출은 1.2억원"}),
            "t1": _todo("pdf_renderer", {}, status=TodoStatus.FAILED),
        },
        overall_status=TodoStatus.FAILED,
    )
    p = build_display_payload(_sq("text"), er)
    assert p.text.startswith("분석 중 일부 단계가 실패했습니다")
    assert "4월 매출은 1.2억원" in p.text, "부분 결과는 보존 표시"
    assert p.format == ResponseFormat.ERROR
