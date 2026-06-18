# -*- coding: utf-8 -*-
"""FileStorage 8 케이스 — 세부계획 §3 Step 3.

검증 항목:
  T1 save_json_load_roundtrip
  T2 save_parquet
  T3 save_jsonl
  T4 exists_false_then_true
  T5 list_keys
  T6 list_keys_prefix
  T7 load_missing_raises
  T8 meta_companion_schema
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from app.dream_agent.tools.shared.storage import FileStorage


@pytest.fixture
def storage(tmp_path) -> FileStorage:
    """매 테스트마다 임시 디렉토리 기반 — 실 data/ 변경 없음."""
    return FileStorage(tmp_path)


CLIENT = "clumi"  # workspace 단위 테스트 용 client (any 회사명 OK)


def test_save_json_load_roundtrip(storage):
    """T1: JSON 라운드트립 + location 반환."""
    loc = storage.save("normalized", "x.json", {"a": 1, "b": "한글"}, client=CLIENT)
    assert storage.load("normalized", "x.json", client=CLIENT) == {"a": 1, "b": "한글"}
    assert loc.endswith("x.json")
    assert f"{CLIENT}/normalized" in loc


def test_save_parquet(storage):
    """T2: DataFrame ↔ parquet."""
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
    storage.save("normalized", "x.parquet", df, client=CLIENT)
    out = storage.load("normalized", "x.parquet", client=CLIENT)
    assert len(out) == 3
    assert list(out.columns) == ["id", "name"]


def test_save_jsonl(storage):
    """T3: list[dict] ↔ jsonl."""
    data = [{"a": 1}, {"b": 2}, {"c": "한"}]
    storage.save("normalized", "x.jsonl", data, client=CLIENT)
    assert storage.load("normalized", "x.jsonl", client=CLIENT) == data


def test_exists_false_then_true(storage):
    """T4: 저장 전 False, 후 True."""
    assert storage.exists("normalized", "x.json", client=CLIENT) is False
    storage.save("normalized", "x.json", {}, client=CLIENT)
    assert storage.exists("normalized", "x.json", client=CLIENT) is True


def test_list_keys(storage):
    """T5: 저장 키 목록 반환 (정렬됨)."""
    storage.save("normalized", "b.json", {}, client=CLIENT)
    storage.save("normalized", "a.json", {}, client=CLIENT)
    keys = storage.list_keys("normalized", client=CLIENT)
    # 우리 파일 2개가 있고, _schema 폴더는 file 아니므로 제외됨
    file_keys = [k for k in keys if k.endswith(".json")]
    assert file_keys == ["a.json", "b.json"]  # 정렬


def test_list_keys_prefix(storage):
    """T6: prefix 필터."""
    storage.save("normalized", "orders_a.json", {}, client=CLIENT)
    storage.save("normalized", "members_b.json", {}, client=CLIENT)
    storage.save("normalized", "orders_c.json", {}, client=CLIENT)
    keys = storage.list_keys("normalized", prefix="orders_", client=CLIENT)
    assert keys == ["orders_a.json", "orders_c.json"]


def test_load_missing_raises(storage):
    """T7: 없는 키 load 시 FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        storage.load("normalized", "nope.json", client=CLIENT)


def test_meta_companion_schema(storage, tmp_path):
    """T8: meta 제공 시 _schema/ 아래 동반 저장."""
    storage.save(
        "normalized",
        "x.parquet",
        pd.DataFrame({"id": [1]}),
        meta={"columns": ["id"], "rows": 1, "filter": "order_status != 'C40'"},
        client=CLIENT,
    )
    schema_path = tmp_path / f"data/{CLIENT}/normalized/_schema/x.json"
    assert schema_path.exists()
    schema = json.loads(schema_path.read_text("utf-8"))
    assert schema["rows"] == 1
    assert schema["columns"] == ["id"]
    assert schema["filter"] == "order_status != 'C40'"
