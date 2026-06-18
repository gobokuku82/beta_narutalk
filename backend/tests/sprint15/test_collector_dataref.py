"""L4 — collector 참조 반환(_dataref) 계약 테스트.

발원지 수정: RawCollectorBase 가 데이터셋 대신 참조 스텁을 반환.
근거: docs/reports/계획_L4_collector참조반환_2026-06-11.md §4
안전: 21 collector produces 키의 previous_results 소비자 0 (근본원인 v2 §7 전수 감사).
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.collection._base import (
    ExternalRawCollectorBase,
    InternalRawCollectorBase,
)
from app.dream_agent.tools.shared.helpers import find_in_previous


def _big_rows(n: int = 40_000) -> list[dict]:
    return [
        {"event_name": "session_start", "user_pseudo_id": f"u{i:08d}",
         "event_timestamp": 1700000000 + i}
        for i in range(n)
    ]


class _FakeDS:
    """창고 모사 — 대형 데이터셋 반환."""

    def __init__(self, data):
        self._data = data
        self.calls: list[tuple[str, str]] = []

    def get(self, client: str, source_id: str):
        self.calls.append((client, source_id))
        return self._data


class _OrdersCollector(InternalRawCollectorBase):
    FILE_NO = 5  # orders
    PRODUCES_KEY = "orders_raw"


class _Ga4Collector(ExternalRawCollectorBase):
    FILE_NO = 7  # ga4_traffic_source
    PRODUCES_KEY = "clumi_ga4_traffic_raw"


def _spec(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, parameters=[])


def _ctx() -> ExecutionContext:
    return ExecutionContext(session_id="t_l4", plan_id="t_l4", client_id="clumi")


class TestDatarefContract:
    @pytest.mark.asyncio
    async def test_internal_returns_ref_not_dataset(self):
        rows = _big_rows()
        tool = _OrdersCollector(spec=_spec("orders_collector"), data_source=_FakeDS(rows))
        out = await tool.execute({}, _ctx())

        ref = out["orders_raw"]
        assert isinstance(ref, dict) and ref.get("_dataref") is True
        assert ref["source_id"] == "orders"
        assert ref["count"] == len(rows)
        # 데이터셋 자체는 결과 어디에도 없어야 함
        assert not any(isinstance(v, list) and len(v) > 100 for v in out.values())

    @pytest.mark.asyncio
    async def test_external_same_contract(self, tmp_path):
        # mock_api 디렉토리 부재 → fetch no-op (test_external_seam 동일 패턴)
        rows = _big_rows(1000)
        ds = _FakeDS(rows)  # repo_root 없음 → _fetch_from_mock_api 가 모듈 _REPO_ROOT 사용
        tool = _Ga4Collector(spec=_spec("ga4_traffic_source_collector"), data_source=ds)
        out = await tool.execute({}, _ctx())

        ref = out["clumi_ga4_traffic_raw"]
        assert ref.get("_dataref") is True
        assert ref["source_id"] == "ga4_traffic_source"
        assert out["count"] == 1000

    @pytest.mark.asyncio
    async def test_result_total_size_tiny(self):
        # 38k행 소스여도 반환 전체 < 4KB (계획 §4-3)
        tool = _OrdersCollector(spec=_spec("orders_collector"), data_source=_FakeDS(_big_rows()))
        out = await tool.execute({}, _ctx())
        size = len(json.dumps(out, ensure_ascii=False, default=str))
        assert size < 4 * 1024, f"반환이 {size}B — 참조 계약 위반"

    @pytest.mark.asyncio
    async def test_generate_summary_count_preserved(self):
        # executor._generate_summary "N건 수집" 경로 보존 (count top-level)
        from app.dream_agent.execution.executor import _generate_summary
        tool = _OrdersCollector(spec=_spec("orders_collector"), data_source=_FakeDS(_big_rows(123)))
        out = await tool.execute({}, _ctx())
        assert _generate_summary("orders_collector", out, False, "completed") == "123건 수집"

    @pytest.mark.asyncio
    async def test_find_in_previous_truthy(self):
        # 존재성 검사 호환 — produces 키는 truthy dict 로 유지 (계획 §2.1)
        tool = _OrdersCollector(spec=_spec("orders_collector"), data_source=_FakeDS(_big_rows(10)))
        out = await tool.execute({}, _ctx())
        previous = {"todo_001": {"data": out}}
        v = find_in_previous(previous, "orders_raw")
        assert v and isinstance(v, dict)

    @pytest.mark.asyncio
    async def test_count_dataframe_source(self):
        # CSV 소스(DataFrame) count 경로 — len(df)
        import pandas as pd
        df = pd.DataFrame({"order_id": range(57), "amount": [100] * 57})
        tool = _OrdersCollector(spec=_spec("orders_collector"), data_source=_FakeDS(df))
        out = await tool.execute({}, _ctx())
        assert out["orders_raw"]["count"] == 57
        assert out["count"] == 57
