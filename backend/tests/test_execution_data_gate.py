"""Execution 데이터 게이트 (B2.1) — tool 경계 non-empty 소비 계약 검사.

완성 함수(311fb0f)가 "파이프 연결"(올바른 tool 이 체인에 있음)을 보장한 위에,
이 게이트는 "물 흐름"(받은 데이터가 충분함)을 검사한다. tool 의 선언된 consumes
artifact 가 이전 결과에 존재+non-empty 가 아니면 → silent-0 거짓 성공 대신
SKIPPED + 정밀 사유(어느 artifact 가 0건/부재).

순수 함수라 LLM·실행 없이 결정론 검증. find_in_previous 와 같은 조회를 써서
"게이트가 검사한 것 = tool 이 실제로 읽는 것" 을 보장.
"""
from __future__ import annotations

from app.dream_agent.execution.data_gate import check_consume_sufficiency


# ── 정상(충분) — false positive 0 ───────────────────────────────────────

def test_sufficient_nonempty_list_passes():
    prev = {"t1": {"raw_reviews": [{"text": "좋아요"}, {"text": "별로"}]}}
    assert check_consume_sufficiency(["raw_reviews"], prev) is None


def test_sufficient_nested_data_shape_passes():
    # find_in_previous 의 result["data"][key] 형태도 동일하게 통과
    prev = {"t1": {"data": {"raw_reviews": [{"text": "x"}]}}}
    assert check_consume_sufficiency(["raw_reviews"], prev) is None


def test_no_consumes_declared_passes():
    # consumes 미선언 tool 은 무검사 (점진 확대 — false positive 0)
    assert check_consume_sufficiency([], {"t1": {"anything": []}}) is None


def test_scalar_value_is_not_empty():
    # 숫자 0 은 "값 있음" — 0건 컬렉션과 구분 (consumes 는 보통 컬렉션이지만 방어)
    prev = {"t1": {"threshold": 0}}
    assert check_consume_sufficiency(["threshold"], prev) is None


# ── 불충분 — 0건 / 부재 ──────────────────────────────────────────────────

def test_empty_list_is_insufficient():
    prev = {"t1": {"raw_reviews": []}}
    reason = check_consume_sufficiency(["raw_reviews"], prev)
    assert reason is not None
    assert reason["reason"] == "data_insufficient"
    assert reason["artifact"] == "raw_reviews"
    assert "0건" in reason["detail"]


def test_empty_dict_is_insufficient():
    prev = {"t1": {"sentiment_distribution": {}}}
    reason = check_consume_sufficiency(["sentiment_distribution"], prev)
    assert reason is not None
    assert reason["artifact"] == "sentiment_distribution"


def test_missing_artifact_is_insufficient():
    prev = {"t1": {"other_key": [1, 2, 3]}}
    reason = check_consume_sufficiency(["raw_reviews"], prev)
    assert reason is not None
    assert reason["artifact"] == "raw_reviews"
    assert "부재" in reason["detail"]


def test_empty_string_is_insufficient():
    prev = {"t1": {"report_markdown": ""}}
    reason = check_consume_sufficiency(["report_markdown"], prev)
    assert reason is not None


def test_empty_previous_is_insufficient():
    # 이전 결과 자체가 없음 (첫 단계가 죽었거나 부모 skip)
    reason = check_consume_sufficiency(["raw_reviews"], {})
    assert reason is not None
    assert "부재" in reason["detail"]


# ── 복수 consumes — 첫 불충분을 정밀 보고 ─────────────────────────────────

def test_reports_first_insufficient_artifact():
    prev = {"t1": {"cleaned_texts": ["t"], "top_keywords": []}}
    reason = check_consume_sufficiency(["cleaned_texts", "top_keywords"], prev)
    assert reason is not None
    assert reason["artifact"] == "top_keywords"  # 첫 번째(cleaned_texts)는 충분, 두 번째가 빈


def test_all_sufficient_multi_passes():
    prev = {"t1": {"cleaned_texts": ["t"], "top_keywords": [{"keyword": "배송"}]}}
    assert check_consume_sufficiency(["cleaned_texts", "top_keywords"], prev) is None


# ── L4 _dataref 스텁 (85ef5de) — truthy 스텁의 0건 맹점 차단 (근본원인 §9.3-1) ──

def test_dataref_stub_with_zero_count_is_insufficient():
    # 스텁 dict 는 항상 truthy → 존재성 검사는 통과하므로 count 로 판정해야 함.
    prev = {"t1": {"orders_raw": {
        "_dataref": True, "source_id": "orders", "layer": "raw", "count": 0,
        "where": "data 레이어",
    }}}
    reason = check_consume_sufficiency(["orders_raw"], prev)
    assert reason is not None
    assert reason["reason"] == "data_insufficient"
    assert reason["artifact"] == "orders_raw"
    assert "0건" in reason["detail"]


def test_dataref_stub_with_rows_passes():
    prev = {"t1": {"orders_raw": {
        "_dataref": True, "source_id": "orders", "layer": "raw", "count": 3420,
        "where": "data 레이어",
    }}}
    assert check_consume_sufficiency(["orders_raw"], prev) is None
