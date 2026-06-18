"""M0 측정기 판정기 박제 — T3 표시(judge_display)·T4 귀속(judge_attribution) (2026-06-12).

계획_멀티쿼리 §2: 판정기는 측정 전용 순수 함수 — LLM·graph 불요로 여기서 결정론 박제.
corpus_compound 의 expect_display 계약(14쿼리·키 보존)도 함께 지킨다.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from scripts.agent_lang_diagnostics.judges import (
    display_blob, judge_attribution, judge_display,
)

_CORPUS = (Path(__file__).resolve().parents[1]
           / "scripts" / "agent_lang_diagnostics" / "corpus_compound.yaml")


# ── display_blob ──

def test_display_blob_includes_surfaces_and_excludes_noise():
    payload = {
        "text": "4월 ROAS 는 320% 입니다.",
        "summary": "ROAS 양호",
        "error": None,
        "attachments": [{"type": "table", "title": "채널별 ROAS"}],
        "next_actions": ["부진 채널 개선안 추천"],     # 오염원 — 제외돼야
        "meta": {"degraded": True, "details": "진단 준비 중"},  # 제외돼야
    }
    blob = display_blob(payload)
    assert "ROAS 는 320%" in blob and "채널별 ROAS" in blob
    assert "개선안 추천" not in blob, "next_actions 가 새면 '추천' 의도 거짓 충족"
    assert "진단 준비 중" not in blob, "meta 가 새면 degrade 내부 정보로 거짓 충족"
    assert display_blob(None) == ""


# ── T3 judge_display ──

def test_judge_display_any_all_and_missing():
    blob = "4월 매출은 1.2억 원, 채널별 ROAS 표를 첨부했습니다."
    res = judge_display(
        [
            {"label": "매출", "any": ["매출"]},
            {"label": "채널별 ROAS", "all": ["채널", "ROAS"]},
            {"label": "소재별 CTR", "all": ["소재", "CTR"]},   # 미표출
            {"label": "기준 미기재"},                           # 분모 제외 (None)
        ],
        blob,
    )
    assert res["n_expect"] == 3 and res["n_displayed"] == 2
    assert res["display_rate"] == 0.67
    assert res["missing"] == ["소재별 CTR"]
    assert res["items"][3]["displayed"] is None


def test_judge_display_empty_expect_is_not_judged():
    res = judge_display(None, "아무 텍스트")
    assert res["n_expect"] == 0 and res["display_rate"] is None


# ── T4 judge_attribution ──

def test_judge_attribution_completed_lost_broken():
    requested = [
        {"intent": "매출 측정", "covered": True, "evidence_tool": "revenue_total"},
        {"intent": "개선안 추천", "covered": False, "evidence_tool": ""},        # lost (계획 소실)
        {"intent": "채널 비교", "covered": True, "evidence_tool": "roas_by_channel"},  # broken
    ]
    plan_todos = [
        {"id": "t1", "tool": "revenue_total"},
        {"id": "t2", "tool": "roas_by_channel"},
    ]
    exec_todos = {
        "t1": {"status": "completed", "tool": "revenue_total"},
        "t2": {"status": "skipped", "tool": None},   # tool 누락 → plan id→tool fallback 으로 join
    }
    res = judge_attribution(requested, plan_todos, exec_todos)
    assert res["n_intents"] == 3 and res["n_attributed"] == 2 and res["n_completed"] == 1
    assert res["completion_rate"] == 0.5
    assert res["lost"] == ["개선안 추천"]
    assert res["broken"] == ["채널 비교"]


def test_judge_attribution_same_tool_multi_todo_any_completed():
    requested = [{"intent": "ROAS", "covered": True, "evidence_tool": "roas_overall"}]
    plan_todos = [{"id": "a", "tool": "roas_overall"}, {"id": "b", "tool": "roas_overall"}]
    exec_todos = {"a": {"status": "failed", "tool": "roas_overall"},
                  "b": {"status": "completed", "tool": "roas_overall"}}
    res = judge_attribution(requested, plan_todos, exec_todos)
    assert res["items"][0]["completed"] is True and res["completion_rate"] == 1.0


def test_judge_attribution_empty_inputs():
    res = judge_attribution([], [], {})
    assert res["n_intents"] == 0 and res["completion_rate"] is None


# ── corpus 계약 (T3 — 쿼리 원문 보존 + expect_display 전수) ──

def test_corpus_compound_14_queries_all_have_expect_display():
    corpus = yaml.safe_load(_CORPUS.read_text(encoding="utf-8"))
    qs = corpus["queries"]
    assert len(qs) == 14, "쿼리 추가/삭제는 기준선 비교성 파괴 — 별도 corpus 로"
    for item in qs:
        assert item.get("type", "").startswith("compound_lv")
        ed = item.get("expect_display")
        assert ed and isinstance(ed, list), f"expect_display 누락: {item['q'][:20]}"
        for e in ed:
            assert e.get("label") and (e.get("any") or e.get("all"))
