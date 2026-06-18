# -*- coding: utf-8 -*-
"""M1 수술 박제 — S1 표시 합성 · S2 G19 의도 단위화 · S3 실행 드롭 가시화 (2026-06-12).

근거 = 측정_M0 보고서 §2 (3축) + 계획_멀티쿼리 v2. 합격 임계는 T3 재실행이 판정 —
여기서는 각 수술의 결정론 계약을 박제한다.
"""
from __future__ import annotations

import time

import pytest

from app.dream_agent.response.responder import (
    build_display_payload,
    build_missing_period_payload,
)
from app.dream_agent.schemas.execution_result import ExecutionResult, TodoResult, TodoStatus
from app.dream_agent.schemas.structured_query import (
    Goal, GoalType, OutputFormat, QueryMeta, StructuredQuery, Targets,
)


def _tr(tid: str, tool: str, status: TodoStatus, data: dict) -> TodoResult:
    now = time.time()
    return TodoResult(todo_id=tid, task_type="t", tool=tool, status=status,
                      data=data, started_at=now, ended_at=now, duration_ms=1.0)


def _er(*results: TodoResult, status: TodoStatus = TodoStatus.COMPLETED) -> ExecutionResult:
    return ExecutionResult(plan_id="p", todos={r.todo_id: r for r in results},
                           overall_status=status)


def _sq() -> StructuredQuery:
    return StructuredQuery(
        targets=Targets(),
        goal=Goal(type=GoalType.ANSWER, output_format=OutputFormat.TEXT),
        meta=QueryMeta(raw_input="q"),
        tasks=[],
    )


# ── S1: 서술 합성 — or-체인 단일선택 폐지 ──

def test_s1_multiple_narratives_all_displayed():
    """M0 축1: summary 가 있으면 recommendation_text 가 침묵하던 기전 — 둘 다 표시."""
    er = _er(
        _tr("t1", "revenue_total", TodoStatus.COMPLETED,
            {"label": "4월 매출", "value": 119539660, "unit": "원"}),
        _tr("t2", "summary_generator", TodoStatus.COMPLETED, {"summary": "매출 양호"}),
        _tr("t3", "recommender", TodoStatus.COMPLETED,
            {"recommendation_text": "부진 채널 개선안: 카카오 예산 재배분 추천"}),
    )
    p = build_display_payload(_sq(), er)
    assert "개선안" in p.text and "추천" in p.text          # 추천 의도 표출
    assert "119539660" in p.text                            # 매출 수치 표출 (G7 양축)


def test_s1_breakdown_rows_rendered():
    """M0 축1: '채널별 ROAS' — rows 산출이 표출 0% 였던 기전 — 컴팩트 렌더."""
    er = _er(
        _tr("t1", "channel_aggregate", TodoStatus.COMPLETED,
            {"rows": [{"channel": "meta", "roas": 6.5}, {"channel": "naver", "roas": 3.2}],
             "count": 2}),
        _tr("t2", "summary_generator", TodoStatus.COMPLETED, {"summary": "ROAS 6.53 전체 양호"}),
    )
    p = build_display_payload(_sq(), er)
    assert "meta" in p.text and "naver" in p.text and "3.2" in p.text


def test_s1_breakdown_dict_rendered_and_capped():
    er = _er(_tr("t1", "ga4_session_aggregator", TodoStatus.COMPLETED,
                 {"by_source": {f"s{i}": i for i in range(15)},
                  "session_start_total": 24000}))
    p = build_display_payload(_sq(), er)
    assert "by_source" in p.text and "s0" in p.text
    assert "s12" not in p.text                              # cap 10 — 시끄러움 방지


def test_s1_metric_dedup_against_narrative():
    """서술이 이미 말한 수치는 중복 렌더 금지 (단일 의도 노이즈 방지 — 계획 리스크 §5)."""
    er = _er(
        _tr("t1", "roas_overall", TodoStatus.COMPLETED,
            {"label": "ROAS", "value": 6.53, "unit": "배"}),
        _tr("t2", "report_writer", TodoStatus.COMPLETED,
            {"report_markdown": "## 보고\nROAS: 6.53배 로 양호합니다."}),
    )
    p = build_display_payload(_sq(), er)
    assert p.text.count("6.53") == 1


def test_s1_single_narrative_unchanged():
    """단일 서술 + 수치 없음 = 기존 동작 보존."""
    er = _er(_tr("t1", "qa_responder", TodoStatus.COMPLETED, {"answer": "회원 등급은 4단계입니다."}))
    p = build_display_payload(_sq(), er)
    assert p.text == "회원 등급은 4단계입니다."


# ── S3: 드롭 가시화 — responder 고지 ──

def test_s3_not_executed_disclosed():
    """M0 축3: 계획 11/실행 8 무기록 증발 → SKIPPED(not_executed) 고지."""
    er = _er(
        _tr("t1", "channel_aggregate", TodoStatus.COMPLETED,
            {"rows": [{"channel": "meta", "cac": 100}], "count": 1}),
        _tr("t2", "diagnoser", TodoStatus.SKIPPED,
            {"reason": "not_executed", "detail": "DAG 미해결"}),
        _tr("t3", "ai_recommendation", TodoStatus.SKIPPED,
            {"reason": "not_executed", "detail": "DAG 미해결"}),
    )
    p = build_display_payload(_sq(), er)
    assert "실행되지 않은 분석" in p.text
    assert "diagnoser" in p.text and "ai_recommendation" in p.text
    assert "분석을 완료했습니다" not in p.text               # EMPTY 둔갑 금지


def test_s3_build_execution_result_marks_unexecuted():
    """execution_stage._build_execution_result — 계획 대비 누락 todo 를 SKIPPED 등기."""
    from app.dream_agent.execution.execution_stage import _build_execution_result

    class _FakeProgress:
        plan = {"plan_id": "p", "todos": [
            {"id": "a", "tool": "orders_collector", "task_type": "collect"},
            {"id": "b", "tool": "diagnoser", "task_type": "analyze"},
        ]}
        completed_todos = {
            "a": _tr("a", "orders_collector", TodoStatus.COMPLETED, {"count": 3}).model_dump(),
        }

    class _FakeHitl:
        def get_progress(self, sid):
            return _FakeProgress()

    result = _build_execution_result("s", _FakeHitl(), [], time.time())
    assert result["todos"]["b"]["status"] == "skipped"
    assert result["todos"]["b"]["data"]["reason"] == "not_executed"
    assert result["todos"]["b"]["tool"] == "diagnoser"


# ── S2: G19 의도 단위화 ──

def _scope_skip(tid: str, tool: str) -> TodoResult:
    return _tr(tid, tool, TodoStatus.SKIPPED, {"reason": "missing_param", "param": "period"})


def test_s2_ask_leads_and_completed_narrative_coexists():
    """M0 축2: ask 가 완료 의도(추천)까지 점령 — ask 선두 + 완료 서술 공존 + 보류 명시."""
    er = _er(
        _scope_skip("t1", "channel_cac_compare"),
        _tr("t2", "insight_extractor", TodoStatus.COMPLETED,
            {"recommendation_text": "리뷰 키워드 기반 개선안: 향 강조 캠페인 제안"}),
    )
    p = build_missing_period_payload(er)
    assert p is not None
    assert p.text.startswith("기간을 알려주세요")             # D3 — ask 선두 불변
    assert "개선안" in p.text                                 # 완료 의도 공존 (G8)
    assert "보류된 분석" in p.text and "channel_cac_compare" in p.text
    assert p.meta["reason"] == "missing_period"


def test_s2_scope_only_stays_pure_ask():
    """완료 서술이 없으면 기존 슬라이스 1 동작 보존 (ask + 보류 목록만, 수치 0)."""
    er = _er(_scope_skip("t1", "channel_cac_compare"))
    p = build_missing_period_payload(er)
    assert p.text.startswith("기간을 알려주세요")
    assert "완료된 결과" not in p.text


def test_s2_no_unscoped_metrics_rendered():
    """스코프 미정 수치(_render_metrics 류)는 G19 경로에서 계속 미표시 (D3)."""
    er = _er(
        _scope_skip("t1", "channel_cac_compare"),
        _tr("t2", "revenue_total", TodoStatus.COMPLETED,
            {"label": "매출(전기간?)", "value": 999, "unit": "원"}),
    )
    p = build_missing_period_payload(er)
    assert "999" not in p.text


def test_s2_attachments_listed():
    er = _er(
        _scope_skip("t1", "channel_cac_compare"),
        _tr("t2", "pdf_renderer", TodoStatus.COMPLETED,
            {"pdf_file_path": "data/clumi/outputs/r.pdf"}),
    )
    p = build_missing_period_payload(er)
    assert len(p.attachments) == 1 and p.attachments[0].kind == "pdf"
