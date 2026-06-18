# -*- coding: utf-8 -*-
"""pushdown v1 (ADR-031) — DataSource.query/aggregate 기본 구현 박제 (File 백엔드).

검증:
  Q1  where 동등 / __prefix (텍스트 의미론 — int 값도 str 비교, None 불일치)
  Q2  columns 투영 (부재 컬럼 = None)
  Q3  aggregate count 스칼라 / by 그룹 (키 str 강제)
  Q4  aggregate sum 스칼라 / by / None 값 skip
  Q5  빈 결과 계약 (query=[] / count=0 / sum=0.0 / by={})
  Q6  csv(DataFrame) 소스 정규화
  Q7  V3 — jsonl 소스는 stream_jsonl 1-pass (get() 전량 적재 경유 금지)
  Q8  미지원 op / sum without column → 시끄러운 실패
"""
from __future__ import annotations

import json

import pytest

from app.data_sources.base import DataSourceError
from app.data_sources.file import FileDataSource

CLIENT = "testc"


@pytest.fixture()
def ds(tmp_path):
    raw = tmp_path / "data" / CLIENT / "raw"
    raw.mkdir(parents=True)
    events = [
        {"event_name": "session_start", "event_date": "20260401", "value": 10, "src": "meta"},
        {"event_name": "session_start", "event_date": "20260402", "value": 5, "src": "naver"},
        {"event_name": "purchase", "event_date": "20260403", "value": 3, "src": "meta"},
        {"event_name": "purchase", "event_date": "20260301", "value": None, "src": None},
    ]
    (raw / "ga4_traffic_source.jsonl").write_text(
        "\n".join(json.dumps(r) for r in events), encoding="utf-8")
    (raw / "orders.csv").write_text(
        "order_id,channel,amount\n1,meta,100\n2,naver,50\n3,meta,25\n", encoding="utf-8")
    return FileDataSource(tmp_path)


# ── Q1 where ──

def test_q1_where_eq_and_prefix(ds):
    rows = ds.query(CLIENT, "ga4_traffic_source", where={"event_name": "session_start"})
    assert len(rows) == 2 and all(r["event_name"] == "session_start" for r in rows)
    # __prefix: 4월만
    rows = ds.query(CLIENT, "ga4_traffic_source", where={"event_date__prefix": "202604"})
    assert len(rows) == 3
    # 텍스트 의미론: int 저장값 10 을 str "10" 으로 매치
    rows = ds.query(CLIENT, "ga4_traffic_source", where={"value": "10"})
    assert len(rows) == 1 and rows[0]["src"] == "meta"
    # None 값(src=None 행)은 동등 조건과 불일치
    rows = ds.query(CLIENT, "ga4_traffic_source", where={"src": "None"})
    assert rows == []


# ── Q2 columns 투영 ──

def test_q2_columns_projection(ds):
    rows = ds.query(CLIENT, "ga4_traffic_source",
                    where={"event_name": "purchase"}, columns=["src", "ghost"])
    assert rows == [{"src": "meta", "ghost": None}, {"src": None, "ghost": None}]


# ── Q3 count ──

def test_q3_count_scalar_and_by(ds):
    assert ds.aggregate(CLIENT, "ga4_traffic_source", op="count") == 4
    by = ds.aggregate(CLIENT, "ga4_traffic_source", op="count", by="event_name")
    assert by == {"session_start": 2, "purchase": 2}
    # where + by + None 그룹 키
    by = ds.aggregate(CLIENT, "ga4_traffic_source", op="count", by="src")
    assert by == {"meta": 2, "naver": 1, None: 1}


# ── Q4 sum ──

def test_q4_sum_scalar_by_and_none_skip(ds):
    total = ds.aggregate(CLIENT, "ga4_traffic_source", op="sum", column="value")
    assert total == 18.0   # None 값 행은 skip
    by = ds.aggregate(CLIENT, "ga4_traffic_source", op="sum", column="value", by="src")
    assert by == {"meta": 13.0, "naver": 5.0}   # src=None 행은 value 도 None → 그룹 자체 없음


# ── Q5 빈 결과 계약 ──

def test_q5_empty_results(ds):
    assert ds.query(CLIENT, "ga4_traffic_source", where={"event_name": "ghost"}) == []
    assert ds.aggregate(CLIENT, "ga4_traffic_source", op="count", where={"event_name": "ghost"}) == 0
    assert ds.aggregate(CLIENT, "ga4_traffic_source", op="sum", column="value",
                        where={"event_name": "ghost"}) == 0.0
    assert ds.aggregate(CLIENT, "ga4_traffic_source", op="count", by="src",
                        where={"event_name": "ghost"}) == {}


# ── Q6 csv(DataFrame) 소스 ──

def test_q6_csv_source_normalized(ds):
    rows = ds.query(CLIENT, "orders", where={"channel": "meta"}, columns=["order_id", "amount"])
    assert [r["amount"] for r in rows] == [100, 25]
    assert ds.aggregate(CLIENT, "orders", op="sum", column="amount", by="channel") == {
        "meta": 125.0, "naver": 50.0}


# ── Q7 V3: jsonl 은 stream 경로 (전량 get() 금지) ──

def test_q7_jsonl_uses_stream_not_get(ds, monkeypatch):
    def _boom(client, source_id):
        raise AssertionError("V3 위반: jsonl query 가 get() 전량 적재로 역행")
    monkeypatch.setattr(ds, "get", _boom)
    assert ds.aggregate(CLIENT, "ga4_traffic_source", op="count") == 4
    assert len(ds.query(CLIENT, "ga4_traffic_source", where={"src": "meta"})) == 2


# ── Q8 계약 위반 = 시끄러운 실패 ──

def test_q8_loud_failures(ds):
    with pytest.raises(DataSourceError):
        ds.aggregate(CLIENT, "ga4_traffic_source", op="avg")
    with pytest.raises(DataSourceError):
        ds.aggregate(CLIENT, "ga4_traffic_source", op="sum")   # column 없음
    with pytest.raises(ValueError):
        ds.aggregate(CLIENT, "ga4_traffic_source", op="sum", column="src")  # 비숫자
