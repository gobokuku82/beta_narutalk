# -*- coding: utf-8 -*-
"""ExternalRawCollectorBase raw-write seam (P3, 2026-06-07) — 백엔드 분기.

검증:
  S1 비-파일 백엔드(ds 에 repo_root 없음) → mock_api 파싱 후 workspace.save("raw", ...)
  S2 파일 백엔드(FileDataSource) → data/{client}/raw/ 복사, workspace 미사용
  S3 _parse_raw_file 확장자 규약 (FileDataSource.get 과 동일 타입)

set_workspace 스파이로 격리, _REPO_ROOT monkeypatch 로 tmp mock_api 사용.
"""
from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from app.data_sources.file import FileDataSource
from app.dream_agent.tools.collection import _base
from app.dream_agent.tools.collection._base import ExternalRawCollectorBase, _parse_raw_file
from app.workspace import reset_workspace, set_workspace


class _SpyWorkspace:
    """save 호출만 기록하는 스파이 — 비-파일 백엔드 역할."""

    def __init__(self):
        self.saved: list[tuple] = []

    def save(self, layer, key, data, meta=None, *, client):
        self.saved.append((layer, key, data, client))
        return f"spy://{client}/{layer}/{key}"


class _NoRepoDS:
    """repo_root 없는 DataSource — workspace 분기 유도 (PostgresDataSource 대역)."""


def _collector(ds):
    return ExternalRawCollectorBase(spec=SimpleNamespace(name="test_collector"), data_source=ds)


# ── S1: 비-파일 백엔드 → workspace.save("raw") ──
def test_workspace_branch_parses_and_saves(tmp_path, monkeypatch):
    mock_dir = tmp_path / "data" / "mock_api" / "clumi"
    mock_dir.mkdir(parents=True)
    (mock_dir / "clumi_mock_01_meta_ads_performance.json").write_text(
        '{"campaign": "c1", "spend": 50}', encoding="utf-8"
    )
    monkeypatch.setattr(_base, "_REPO_ROOT", tmp_path)

    spy = _SpyWorkspace()
    set_workspace(spy)
    try:
        _collector(_NoRepoDS())._fetch_from_mock_api("clumi", "meta_ads_performance")
    finally:
        reset_workspace()

    assert len(spy.saved) == 1
    layer, key, data, client = spy.saved[0]
    assert (layer, key, client) == ("raw", "meta_ads_performance.json", "clumi")
    assert data == {"campaign": "c1", "spend": 50}


def test_workspace_branch_csv_to_dataframe(tmp_path, monkeypatch):
    mock_dir = tmp_path / "data" / "mock_api" / "clumi"
    mock_dir.mkdir(parents=True)
    (mock_dir / "clumi_mock_15_naver_advoost.csv").write_text(
        "k,v\n1,a\n2,b\n", encoding="utf-8-sig"
    )
    monkeypatch.setattr(_base, "_REPO_ROOT", tmp_path)

    spy = _SpyWorkspace()
    set_workspace(spy)
    try:
        _collector(_NoRepoDS())._fetch_from_mock_api("clumi", "naver_advoost")
    finally:
        reset_workspace()

    layer, key, data, client = spy.saved[0]
    assert key == "naver_advoost.csv"
    assert isinstance(data, pd.DataFrame)
    assert list(data.columns) == ["k", "v"]
    assert len(data) == 2


# ── S2: 파일 백엔드 → 복사, workspace 미사용 ──
def test_file_branch_copies_and_skips_workspace(tmp_path):
    mock_dir = tmp_path / "data" / "mock_api" / "clumi"
    mock_dir.mkdir(parents=True)
    (mock_dir / "clumi_mock_01_meta_ads_performance.json").write_text(
        '{"a": 1}', encoding="utf-8"
    )

    spy = _SpyWorkspace()
    set_workspace(spy)
    try:
        _collector(FileDataSource(tmp_path))._fetch_from_mock_api("clumi", "meta_ads_performance")
    finally:
        reset_workspace()

    raw_path = tmp_path / "data" / "clumi" / "raw" / "meta_ads_performance.json"
    assert raw_path.exists()
    assert raw_path.read_text(encoding="utf-8") == '{"a": 1}'
    assert spy.saved == []  # 파일 분기 → workspace 미호출


def test_no_mock_file_is_noop(tmp_path, monkeypatch):
    (tmp_path / "data" / "mock_api" / "clumi").mkdir(parents=True)
    monkeypatch.setattr(_base, "_REPO_ROOT", tmp_path)
    spy = _SpyWorkspace()
    set_workspace(spy)
    try:
        _collector(_NoRepoDS())._fetch_from_mock_api("clumi", "meta_ads_performance")
    finally:
        reset_workspace()
    assert spy.saved == []  # 매칭 mock 없음 → skip


# ── S3: _parse_raw_file 규약 ──
def test_parse_raw_file_extensions(tmp_path):
    csv = tmp_path / "x.csv"
    csv.write_text("a,b\n1,2\n", encoding="utf-8-sig")
    assert isinstance(_parse_raw_file(csv), pd.DataFrame)

    js = tmp_path / "x.json"
    js.write_text('{"k": 1}', encoding="utf-8")
    assert _parse_raw_file(js) == {"k": 1}

    jl = tmp_path / "x.jsonl"
    jl.write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")
    assert _parse_raw_file(jl) == [{"a": 1}, {"a": 2}]

    sq = tmp_path / "x.sql"
    sq.write_text("SELECT 1;", encoding="utf-8")
    assert _parse_raw_file(sq) == "SELECT 1;"
