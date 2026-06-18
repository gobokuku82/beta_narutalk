# -*- coding: utf-8 -*-
"""Phase 1 M1b — Pipeline API (/api/admin/pipelines) 검증 (63 §2.3.3).

  A1 catalog       — GET /api/admin/pipelines → K01 등록 + required_variables
  A2 run+poll      — POST run/{name} → pending → polling → completed + 정답 key
  A3 not found     — POST run/{ghost} → 404 PIPELINE_NOT_FOUND
  A4 run not found — GET runs/{bad} → 404 PIPELINE_RUN_NOT_FOUND

httpx ASGITransport + AsyncClient → 비동기 background task (store.create_task) 진행 가능.
workspace = 실 repo (S001 정답 이미 존재 → cache hit 완료). 정답 보존은 test_pipeline_runner 가 compute path 검증.
"""
from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from httpx import ASGITransport

from api_v2.main import create_app
from app.pipelines.store import reset_run_store

BASE = "http://test"
RUN_NAME = "dashboard1_kpi_revenue"


@pytest.fixture
def app():
    return create_app()


@pytest.fixture(autouse=True)
def _reset_store():
    reset_run_store()
    yield
    reset_run_store()


def _ac(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=ASGITransport(app=app), base_url=BASE)


async def test_catalog_lists_k01(app):
    async with _ac(app) as ac:
        r = await ac.get("/api/admin/pipelines")
    assert r.status_code == 200
    data = r.json()
    entry = next((p for p in data["pipelines"] if p["name"] == RUN_NAME), None)
    assert entry is not None, data
    assert entry["visualization_id"] == "K01"
    assert {"client", "period"}.issubset(set(entry["required_variables"]))


async def test_run_and_poll_completes(app):
    async with _ac(app) as ac:
        r = await ac.post(f"/api/admin/pipelines/run/{RUN_NAME}",
                          json={"variables": {"client": "clumi", "period": "2026-04"}})
        assert r.status_code == 200, r.text
        created = r.json()
        assert created["status"] == "pending"
        assert created["poll_url"].endswith(created["run_id"])

        status = None
        for _ in range(150):
            s = await ac.get(created["poll_url"])
            status = s.json()
            if status["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.02)

    assert status is not None and status["status"] == "completed", status
    assert status["progress"]["percent"] == 100.0
    assert "S001_revenue_total_2026-04.json" in status["result_keys"]


async def test_run_pipeline_not_found(app):
    async with _ac(app) as ac:
        r = await ac.post("/api/admin/pipelines/run/ghost_pipeline_xyz",
                          json={"variables": {}})
    assert r.status_code == 404
    assert "PIPELINE_NOT_FOUND" in json.dumps(r.json())


async def test_run_status_not_found(app):
    async with _ac(app) as ac:
        r = await ac.get("/api/admin/pipelines/runs/nonexistent_run_id")
    assert r.status_code == 404
    assert "PIPELINE_RUN_NOT_FOUND" in json.dumps(r.json())


@pytest.mark.parametrize(
    "category,count",
    [("dashboard_v1", 6), ("channel", 3), ("trend", 8), ("creative", 7), ("cost", 7)],
)
async def test_category_results(app, category, count):
    """페이지 데이터 source — 카테고리 전체 산출 (visualization_id 별 completed)."""
    async with _ac(app) as ac:
        r = await ac.get(
            f"/api/admin/pipelines/category/{category}?client=clumi&period=2026-04"
        )
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) == count, data["results"].keys()
    bad = {k: v["status"] for k, v in data["results"].items() if v["status"] != "completed"}
    assert not bad, bad

