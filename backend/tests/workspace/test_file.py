# -*- coding: utf-8 -*-
"""FileWorkspace — save/load roundtrip + 호환 shim.

검증:
  W1 json save/load roundtrip
  W2 parquet save/load roundtrip
  W3 jsonl save/load roundtrip
  W4 meta 동반 _schema/ 생성
  W5 exists / list_keys (prefix)
  W6 shim — old storage.py import 작동 (StorageBackend = WorkspaceBackend, get_storage)

spec: docs/_claude/architecture/backend_data_agent_2026-05-26.md §6 Step 3b DoD
"""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd
import pytest

from app.workspace import FileWorkspace, get_default_workspace, reset_workspace


CLIENT = "clumi"  # workspace 단위 테스트 용 client (any 회사명 OK)


@pytest.fixture
def ws(tmp_path) -> FileWorkspace:
    return FileWorkspace(tmp_path)


def test_save_json_load_roundtrip(ws, tmp_path):
    """W1: json save → load."""
    loc = ws.save("normalized", "x.json", {"hello": "world"}, client=CLIENT)
    assert f"{CLIENT}/normalized" in loc
    loaded = ws.load("normalized", "x.json", client=CLIENT)
    assert loaded == {"hello": "world"}


def test_save_parquet_load_roundtrip(ws):
    """W2: parquet save → load (DataFrame)."""
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    ws.save("normalized", "x.parquet", df, client=CLIENT)
    loaded = ws.load("normalized", "x.parquet", client=CLIENT)
    assert loaded.equals(df)


def test_save_jsonl_load_roundtrip(ws):
    """W3: jsonl save → load (list[dict])."""
    items = [{"a": 1}, {"a": 2}, {"a": 3}]
    ws.save("normalized", "x.jsonl", items, client=CLIENT)
    loaded = ws.load("normalized", "x.jsonl", client=CLIENT)
    assert loaded == items


def test_meta_companion_schema(ws, tmp_path):
    """W4: meta 동반 → _schema/{stem}.json 생성."""
    ws.save("normalized", "x.json", {"a": 1}, meta={"source": "test", "rows": 1}, client=CLIENT)
    schema_path = tmp_path / f"data/{CLIENT}/normalized/_schema/x.json"
    assert schema_path.exists()
    schema = json.loads(schema_path.read_text("utf-8"))
    assert schema["rows"] == 1


def test_exists_and_list_keys(ws):
    """W5: exists + list_keys prefix."""
    ws.save("normalized", "_selfcheck.json", {}, client=CLIENT)
    ws.save("normalized", "_selfcheck_b.json", {}, client=CLIENT)
    ws.save("normalized", "other.json", {}, client=CLIENT)
    assert ws.exists("normalized", "_selfcheck.json", client=CLIENT)
    assert not ws.exists("normalized", "missing.json", client=CLIENT)
    prefixed = ws.list_keys("normalized", prefix="_selfcheck", client=CLIENT)
    assert prefixed == ["_selfcheck.json", "_selfcheck_b.json"]


def test_default_singleton():
    """W5b: get_default_workspace 싱글톤."""
    reset_workspace()
    ws1 = get_default_workspace()
    ws2 = get_default_workspace()
    assert ws1 is ws2
    assert isinstance(ws1, FileWorkspace)
    reset_workspace()


# ── W6: 호환 shim ──

def test_shim_storage_backend_alias():
    """W6: 옛 StorageBackend = WorkspaceBackend 동일."""
    from app.dream_agent.tools.shared.storage import StorageBackend
    from app.workspace import WorkspaceBackend
    assert StorageBackend is WorkspaceBackend


def test_shim_filestorage_alias():
    """W6: 옛 FileStorage = FileWorkspace 동일."""
    from app.dream_agent.tools.shared.storage import FileStorage as Old
    from app.workspace import FileWorkspace as New
    assert Old is New


def test_shim_get_storage(tmp_path):
    """W6: 옛 get_storage / set_storage 작동."""
    from app.dream_agent.tools.shared.storage import (
        FileStorage, get_storage, reset_storage, set_storage,
    )
    set_storage(FileStorage(tmp_path))
    ws = get_storage()
    ws.save("normalized", "shim_test.json", {"ok": True}, client=CLIENT)
    assert ws.load("normalized", "shim_test.json", client=CLIENT) == {"ok": True}
    reset_storage()
