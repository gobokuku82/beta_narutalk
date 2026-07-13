"""erd_build 박제 — SQLite 빌드/적재/DISTINCT마스터/중복덤핑/무결성/쿼리가드.

실행: 리포지토리 루트에서  pytest tests/unit/db_design/test_erd_build.py -q
"""

from __future__ import annotations

import os
import tempfile

import pytest

from app.db_design.erd_build import build_sqlite, run_query


def _col(name, type="TEXT", pk=False, nullable=True, fk=None):
    return {"name": name, "type": type, "pk": pk, "nullable": nullable, "unique": False, "fk": fk}


def _design():
    return {
        "name": "t",
        "tables": [
            {"name": "거래처", "columns": [_col("거래처ID", pk=True, nullable=False), _col("원장명")]},
            {"name": "품목", "columns": [_col("품목", pk=True, nullable=False), _col("품목명")]},  # 데이터 없음 → DISTINCT
            {
                "name": "실적",
                "columns": [
                    _col("거래처ID", fk={"table": "거래처", "column": "거래처ID"}),
                    _col("품목", fk={"table": "품목", "column": "품목"}),
                    _col("값", "INTEGER"),
                ],
            },
        ],
    }


@pytest.fixture()
def dbfile():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_build_loads_and_distinct_master(dbfile):
    design = _design()
    datasets = {
        "거래처": [{"거래처ID": "A의원", "원장명": "김"}, {"거래처ID": "B의원", "원장명": "이"}],
        "실적": [
            {"거래처ID": "A의원", "품목": "가스몬", "값": 100},
            {"거래처ID": "A의원", "품목": "가스몬", "값": 50},
            {"거래처ID": "B의원", "품목": "레보", "값": 200},
        ],
    }
    rep = build_sqlite(design, datasets, dbfile)
    by = {t["name"]: t for t in rep["tables"]}
    assert by["거래처"]["loaded"] == 2 and by["거래처"]["source"] == "data"
    assert by["실적"]["loaded"] == 3
    # 품목 마스터: 실적.품목 DISTINCT → 가스몬/레보 = 2
    assert by["품목"]["loaded"] == 2 and by["품목"]["source"] == "distinct"
    # 부모(거래처/품목)가 자식(실적)보다 먼저
    assert rep["order"].index("거래처") < rep["order"].index("실적")
    assert rep["order"].index("품목") < rep["order"].index("실적")
    # 무결성 — 전부 OK
    assert all(v["orphans"] == 0 for v in rep["integrity"])


def test_single_pk_dedupes_with_report(dbfile):
    design = _design()
    datasets = {
        # 거래처ID 중복(A의원 2번) → OR IGNORE 로 1건만, 1건 버림 리포트
        "거래처": [
            {"거래처ID": "A의원", "원장명": "김"},
            {"거래처ID": "A의원", "원장명": "박"},
            {"거래처ID": "B의원", "원장명": "이"},
        ],
        "실적": [],
    }
    rep = build_sqlite(design, datasets, dbfile)
    cust = next(t for t in rep["tables"] if t["name"] == "거래처")
    assert cust["received"] == 3 and cust["loaded"] == 2 and cust["dropped_duplicates"] == 1


def test_integrity_reports_orphans(dbfile):
    design = _design()
    datasets = {
        "거래처": [{"거래처ID": "A의원", "원장명": "김"}],
        "실적": [
            {"거래처ID": "A의원", "품목": "가스몬", "값": 10},
            {"거래처ID": "없는의원", "품목": "가스몬", "값": 20},  # 고아
        ],
    }
    rep = build_sqlite(design, datasets, dbfile)
    viol = next(v for v in rep["integrity"] if v["child"] == "실적" and v["column"] == "거래처ID")
    assert viol["orphans"] == 1
    assert "없는의원" in viol["samples"]


def test_join_query_and_guard(dbfile):
    design = _design()
    datasets = {
        "거래처": [{"거래처ID": "A의원", "원장명": "김원장"}],
        "실적": [{"거래처ID": "A의원", "품목": "가스몬", "값": 100}],
    }
    build_sqlite(design, datasets, dbfile)
    # 조립(JOIN) — 실적에 원장명 붙이기
    res = run_query(
        dbfile,
        "SELECT s.값, c.원장명 FROM 실적 s JOIN 거래처 c ON s.거래처ID=c.거래처ID",
    )
    assert res["columns"] == ["값", "원장명"]
    assert res["rows"] == [[100, "김원장"]]
    # 쓰기/DDL 차단
    for bad in ["DROP TABLE 거래처", "DELETE FROM 실적", "UPDATE 실적 SET 값=0", "INSERT INTO 실적 VALUES (1,2,3)"]:
        with pytest.raises(ValueError):
            run_query(dbfile, bad)
