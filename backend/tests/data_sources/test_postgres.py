# -*- coding: utf-8 -*-
"""PostgresDataSource — raw 읽기 + 복원 (octormate_data 통합 테스트).

검증 (FileDataSource 와 대칭):
  P1 .csv → DataFrame 복원 (records 라운드트립)
  P2 .json → dict|list 그대로
  P3 .jsonl → list[dict] 그대로
  P4 .sql → str 그대로
  P5 has() / list_sources()
  P6 미등록 source_id → DataSourceNotFound
  P7 미존재 raw → DataSourceNotFound

DB 미가용 시 전체 skip. throwaway schema(test_pgds) 사용 후 drop.
"""
from __future__ import annotations

import pandas as pd
import pytest

psycopg = pytest.importorskip("psycopg")

from app.data_pg_util import connect, data_dsn  # noqa: E402
from app.data_sources.base import DataSourceNotFound  # noqa: E402
from app.data_sources.postgres import PostgresDataSource  # noqa: E402
from app.workspace.postgres import PostgresWorkspace  # noqa: E402

CLIENT = "test_pgds"


@pytest.fixture(scope="module")
def pg_available():
    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
    except psycopg.Error as e:
        pytest.skip(f"octormate_data 미가용 — skip ({data_dsn()}): {e}")


@pytest.fixture(scope="module")
def seeded(pg_available):
    """throwaway schema 에 4종 raw 적재 (PostgresWorkspace.save) → 테스트 후 drop."""
    ws = PostgresWorkspace()
    ws.save("raw", "orders.csv", [{"id": 1, "amt": 100}, {"id": 2, "amt": 200}], client=CLIENT)
    ws.save("raw", "meta_ads_performance.json", {"campaign": "c1", "spend": 50.5}, client=CLIENT)
    ws.save("raw", "ga4_traffic_source.jsonl", [{"src": "google"}, {"src": "naver"}], client=CLIENT)
    ws.save("raw", "promotions.sql", "INSERT INTO promo VALUES (1);", client=CLIENT)
    yield PostgresDataSource()
    # cleanup
    with connect() as conn, conn.cursor() as cur:
        cur.execute(f'DROP SCHEMA IF EXISTS "{CLIENT}" CASCADE')
        conn.commit()


# ── P1~P4: 확장자별 복원 (FileDataSource.get 과 동일 타입) ──
def test_csv_reconstructs_dataframe(seeded):
    df = seeded.get(CLIENT, "orders")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["id", "amt"]
    assert len(df) == 2
    assert df.iloc[0]["amt"] == 100


def test_json_returns_dict(seeded):
    data = seeded.get(CLIENT, "meta_ads_performance")
    assert isinstance(data, dict)
    assert data["campaign"] == "c1"
    assert data["spend"] == 50.5


def test_jsonl_returns_list_of_dict(seeded):
    data = seeded.get(CLIENT, "ga4_traffic_source")
    assert isinstance(data, list)
    assert data[0]["src"] == "google"
    assert len(data) == 2


def test_sql_returns_str(seeded):
    text = seeded.get(CLIENT, "promotions")
    assert isinstance(text, str)
    assert "INSERT INTO promo" in text


# ── P5: has / list_sources ──
def test_has_true_for_seeded(seeded):
    assert seeded.has(CLIENT, "orders") is True
    assert seeded.has(CLIENT, "meta_ads_performance") is True


def test_has_false_for_unseeded(seeded):
    assert seeded.has(CLIENT, "customers") is False  # 적재 안 함


def test_list_sources_reverse_maps_filenames(seeded):
    sources = seeded.list_sources(CLIENT)
    assert set(sources) == {"orders", "meta_ads_performance", "ga4_traffic_source", "promotions"}


# ── P6/P7: 에러 ──
def test_unknown_source_id_raises(seeded):
    with pytest.raises(DataSourceNotFound, match="not in SOURCE_REGISTRY"):
        seeded.get(CLIENT, "totally_made_up_source")


def test_missing_raw_raises(seeded):
    with pytest.raises(DataSourceNotFound, match="raw not found"):
        seeded.get(CLIENT, "customers")  # 미적재 source


def test_unknown_source_has_false(seeded):
    assert seeded.has(CLIENT, "totally_made_up_source") is False
