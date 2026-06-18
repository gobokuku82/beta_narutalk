# -*- coding: utf-8 -*-
"""FileDataSource — 21 source_id × clumi PASS + 보조 검증.

검증:
  T1 21 source_id 모두 has() True (clumi 회사)
  T2 12 csv/json/jsonl/sql 확장자 분기 정상 (대용량 ga4_page_events 제외)
  T3 list_sources('clumi') = 21
  T4 미등록 source_id → DataSourceNotFound
  T5 미존재 client → list_sources 0, get NotFound
  T6 싱글톤 + DI override

spec: docs/_claude/architecture/backend_data_agent_2026-05-26.md §6 Step 3a DoD
"""
from __future__ import annotations
from pathlib import Path

import pandas as pd
import pytest

from app.data_sources import (
    DEFAULT_MAPPING,
    SOURCE_REGISTRY,
    DataSource,
    DataSourceNotFound,
    FileDataSource,
    get_default_data_source,
    reset_data_source,
    set_data_source,
    source_kind,
    source_platform,
    sources_by_kind,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
CLUMI = "clumi"


@pytest.fixture
def ds() -> DataSource:
    return FileDataSource(REPO_ROOT)


# ── T1: 21 source_id 모두 has() ──
@pytest.mark.parametrize("source_id", sorted(DEFAULT_MAPPING.keys()))
def test_all_21_source_ids_present_for_clumi(ds, source_id):
    """clumi 회사의 21 source 모두 파일 존재."""
    assert ds.has(CLUMI, source_id), f"missing: {source_id}"


# ── T2: 확장자 분기 ──

def test_get_csv_orders(ds):
    """orders.csv → DataFrame, payment_amount 컬럼 존재."""
    df = ds.get(CLUMI, "orders")
    assert isinstance(df, pd.DataFrame)
    assert "payment_amount" in df.columns
    assert len(df) > 0


def test_get_json_meta_ads(ds):
    """meta_ads_performance.json → dict or list."""
    data = ds.get(CLUMI, "meta_ads_performance")
    assert isinstance(data, (dict, list))


def test_get_jsonl_ga4_traffic(ds):
    """ga4_traffic_source.jsonl → list[dict]."""
    data = ds.get(CLUMI, "ga4_traffic_source")
    assert isinstance(data, list)
    assert len(data) > 0
    assert isinstance(data[0], dict)


def test_get_sql_promotions(ds):
    """promotions.sql → str."""
    text = ds.get(CLUMI, "promotions")
    assert isinstance(text, str)


# ── T3: list_sources ──

def test_list_sources_clumi_returns_21(ds):
    """clumi 의 sources 21개 (DEFAULT_MAPPING 전체)."""
    sources = ds.list_sources(CLUMI)
    assert len(sources) == len(DEFAULT_MAPPING)
    assert set(sources) == set(DEFAULT_MAPPING.keys())


# ── T4: 미등록 source_id ──

def test_unknown_source_id_raises(ds):
    with pytest.raises(DataSourceNotFound, match="not in mapping"):
        ds.get(CLUMI, "totally_made_up_source")


def test_unknown_source_has_returns_false(ds):
    assert ds.has(CLUMI, "totally_made_up_source") is False


# ── T5: 미존재 client ──

def test_unknown_client_list_returns_empty(ds):
    assert ds.list_sources("nonexistent-client") == []


def test_unknown_client_get_raises(ds):
    with pytest.raises(DataSourceNotFound, match="file not found"):
        ds.get("nonexistent-client", "orders")


# ── T6: 싱글톤 + DI override ──

def test_default_singleton_returns_filedatasource():
    reset_data_source()
    ds1 = get_default_data_source()
    ds2 = get_default_data_source()
    assert ds1 is ds2
    assert isinstance(ds1, FileDataSource)
    reset_data_source()


def test_set_data_source_override():
    custom = FileDataSource(REPO_ROOT, mapping={"x": "x.csv"})
    set_data_source(custom)
    assert get_default_data_source() is custom
    reset_data_source()


# ── T7: SourceSpec — kind(external/internal) + platform (설계노트 2026-05-28) ──

def test_default_mapping_derived_from_registry():
    """DEFAULT_MAPPING(하위호환) = SOURCE_REGISTRY 파생 — 키·파일명 일치."""
    assert set(DEFAULT_MAPPING.keys()) == set(SOURCE_REGISTRY.keys())
    for sid, spec in SOURCE_REGISTRY.items():
        assert DEFAULT_MAPPING[sid] == spec.filename


def test_every_source_has_valid_kind():
    """모든 source 는 external | internal 중 하나."""
    for sid, spec in SOURCE_REGISTRY.items():
        assert spec.kind in ("external", "internal"), f"{sid}: {spec.kind}"


def test_kind_counts_16_external_14_internal():
    """확정 분류: 외부 16 / 내부 14 (총 30). (A-5.3: daily_performance 제거 — World-C 별개 mock, canonical 전환)."""
    assert len(sources_by_kind("external")) == 16
    assert len(sources_by_kind("internal")) == 14
    assert len(SOURCE_REGISTRY) == 30


def test_known_external_sources():
    """외부 = API 소스 (대표 확인 + 파이프라인 3종)."""
    for sid in ("meta_ads_performance", "naver_searchad", "kakao_bizmessage",
                "ga4_traffic_source", "reviews", "keyword_performance", "google_ads_performance"):
        assert source_kind(sid) == "external", sid


def test_known_internal_sources():
    """내부 = 내 서버 (대표 확인 + 파이프라인 4종)."""
    for sid in ("orders", "customers", "promotions",
                "creatives", "campaigns", "budget_allocation", "ab_tests"):
        assert source_kind(sid) == "internal", sid


def test_platform_only_for_external():
    """platform 은 외부에만 (내부는 None). 외부 플랫폼명 검증."""
    assert source_platform("meta_ads_performance") == "meta"
    assert source_platform("instagram_engagement") == "meta"
    assert source_platform("naver_searchad") == "naver"
    assert source_platform("kakao_bizmessage") == "kakao"
    assert source_platform("ga4_traffic_source") == "google"
    # 내부는 platform 없음
    assert source_platform("orders") is None
    assert source_platform("creatives") is None
    # 플랫폼 미정 외부도 None
    assert source_platform("reviews") is None


def test_internal_has_no_platform():
    """모든 internal source 는 platform=None."""
    for sid in sources_by_kind("internal"):
        assert source_platform(sid) is None, sid


def test_unregistered_source_kind_none():
    assert source_kind("totally_made_up") is None
    assert source_platform("totally_made_up") is None
