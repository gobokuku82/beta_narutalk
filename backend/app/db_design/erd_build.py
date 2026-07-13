"""ERD → 실제 SQLite DB 빌드 & 검증 (순수 로직, FastAPI 비의존).

DB설계 워크벤치의 "설계(ERD)"와 "엑셀에서 추출한 행 데이터"를 받아 진짜 SQLite DB 로
**조립(materialize)** 한다. 학습/검증용 — 설치 0(파일 기반), 무결성 위반을 리포트해
"이 설계로 정말 적재되는가"를 눈으로 확인하게 한다.

설계 의도(개념):
- DB 표 = 엑셀 시트. FK = 영구 VLOOKUP. JOIN = 부품(표)들을 질문 시점에 조립.
- 차원(마스터) 테이블 중 *데이터가 없는 것*(차원 추출로 구조만 만든 것)은 이를 참조하는
  팩트 칼럼에서 ``SELECT DISTINCT`` 로 PK 를 채운다(= 정규화 자동 적재).
- 단일 PK 마스터에 중복 키가 있으면 ``INSERT OR IGNORE`` 로 덧씌우고 *몇 건 버렸는지* 리포트
  (인사자료 999행/사번 80명 같은 실무 더러움을 드러냄).
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any

# ── ERD 타입 → SQLite affinity ────────────────────────────────────────────────
_INT = {"INTEGER", "BIGINT", "SMALLINT", "INT"}
_REAL = {"NUMERIC", "FLOAT", "REAL", "DOUBLE", "DECIMAL"}


def _affinity(erd_type: str) -> str:
    t = (erd_type or "").strip().upper()
    base = t.split("(")[0]
    if base in _INT:
        return "INTEGER"
    if base in _REAL:
        return "REAL"
    if base == "BOOLEAN":
        return "INTEGER"
    return "TEXT"  # VARCHAR/TEXT/DATE/TIMESTAMPTZ/UUID/JSONB → TEXT


def _q(ident: str) -> str:
    """식별자 인용 — 큰따옴표 이스케이프 (한글/공백/괄호 칼럼명 안전)."""
    return '"' + str(ident).replace('"', '""') + '"'


def _coerce(value: Any, affinity: str) -> Any:
    """JSON 값 → SQLite 저장값. 빈문자/None → NULL, 숫자 칼럼은 숫자화 시도."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    if affinity == "INTEGER":
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return int(value)
        try:
            return int(float(str(value).replace(",", "")))
        except (ValueError, TypeError):
            return value  # 숫자화 실패 시 원본 — affinity 가 흡수
    if affinity == "REAL":
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).replace(",", ""))
        except (ValueError, TypeError):
            return value
    return value if isinstance(value, (str, int, float)) else str(value)


# ── 설계 해석 헬퍼 ────────────────────────────────────────────────────────────
def _pk_cols(table: dict) -> list[dict]:
    return [c for c in table.get("columns", []) if c.get("pk")]


def _single_pk(table: dict) -> dict | None:
    pks = _pk_cols(table)
    return pks[0] if len(pks) == 1 else None


def _topo_order(tables: list[dict]) -> list[dict]:
    """FK 의존 순서 — 부모(참조 대상) 먼저. 사이클이면 남은 것을 뒤에 붙임."""
    by_name = {t["name"]: t for t in tables}
    ordered: list[dict] = []
    placed: set[str] = set()

    def deps(t: dict) -> set[str]:
        out = set()
        for c in t.get("columns", []):
            fk = c.get("fk")
            if fk and fk.get("table") in by_name and fk["table"] != t["name"]:
                out.add(fk["table"])
        return out

    remaining = list(tables)
    while remaining:
        progressed = False
        for t in list(remaining):
            if deps(t) <= placed:
                ordered.append(t)
                placed.add(t["name"])
                remaining.remove(t)
                progressed = True
        if not progressed:  # 사이클 — 남은 것 순서대로
            ordered.extend(remaining)
            break
    return ordered


def _create_sql(table: dict, known: set[str]) -> str:
    """CREATE TABLE — 칼럼/PK/NOT NULL/UNIQUE + (참조 대상이 존재할 때만) FK."""
    cols_sql: list[str] = []
    pks = _pk_cols(table)
    single_pk = len(pks) == 1
    for c in table.get("columns", []):
        parts = [_q(c["name"]), _affinity(c.get("type", "TEXT"))]
        if single_pk and c.get("pk"):
            parts.append("PRIMARY KEY")
        elif not c.get("nullable", True) and not c.get("pk"):
            parts.append("NOT NULL")
        if c.get("unique") and not c.get("pk"):
            parts.append("UNIQUE")
        cols_sql.append(" ".join(parts))

    if len(pks) > 1:  # 복합 PK
        cols_sql.append("PRIMARY KEY (" + ", ".join(_q(c["name"]) for c in pks) + ")")

    for c in table.get("columns", []):
        fk = c.get("fk")
        if fk and fk.get("table") in known and fk["table"] != table["name"]:
            cols_sql.append(
                f"FOREIGN KEY ({_q(c['name'])}) "
                f"REFERENCES {_q(fk['table'])} ({_q(fk['column'])})"
            )
    return f"CREATE TABLE {_q(table['name'])} (\n  " + ",\n  ".join(cols_sql) + "\n)"


def build_sqlite(
    design: dict,
    datasets: dict[str, list[dict]],
    db_path: str,
) -> dict:
    """설계 + 데이터로 SQLite DB 를 빌드하고 무결성 리포트를 돌려준다.

    datasets: {테이블명: [{칼럼: 값}, ...]} — 데이터가 없는(차원 추출로 만든) 마스터는 생략 가능.
    """
    tables: list[dict] = design.get("tables", [])
    by_name = {t["name"]: t for t in tables}
    known = set(by_name)
    ordered = _topo_order(tables)

    conn = sqlite3.connect(db_path)
    # FK 는 *선언만* 하고 강제하지 않는다(기본 OFF 유지). 이 도구의 목적은 위반을 막는 게
    # 아니라 *리포트*하는 것 — 더러운 실무 데이터를 그대로 적재해 고아를 드러내야 하고,
    # 구조 마스터(품목 등)는 팩트에서 DISTINCT 로 *나중에* 채우므로 강제 시 닭-달걀이 된다.
    report_tables: list[dict] = []

    try:
        # 기존 테이블 제거 후 재생성.
        for t in reversed(ordered):
            conn.execute(f"DROP TABLE IF EXISTS {_q(t['name'])}")
        for t in ordered:
            conn.execute(_create_sql(t, known))

        # 1) 데이터가 있는 테이블 적재.
        for t in ordered:
            rows = datasets.get(t["name"])
            if not rows:
                continue
            cols = t.get("columns", [])
            aff = {c["name"]: _affinity(c.get("type", "TEXT")) for c in cols}
            names = [c["name"] for c in cols]
            placeholders = ", ".join("?" for _ in names)
            col_sql = ", ".join(_q(n) for n in names)
            # 단일 PK 가 있으면 OR IGNORE(중복 키 덤핑) — 마스터 더러움 흡수.
            verb = "INSERT OR IGNORE" if _single_pk(t) else "INSERT"
            stmt = f"{verb} INTO {_q(t['name'])} ({col_sql}) VALUES ({placeholders})"
            payload = [
                tuple(_coerce(r.get(n), aff[n]) for n in names) for r in rows
            ]
            before = conn.execute(f"SELECT COUNT(*) FROM {_q(t['name'])}").fetchone()[0]
            conn.executemany(stmt, payload)
            after = conn.execute(f"SELECT COUNT(*) FROM {_q(t['name'])}").fetchone()[0]
            inserted = after - before
            report_tables.append(
                {
                    "name": t["name"],
                    "source": "data",
                    "received": len(rows),
                    "loaded": inserted,
                    "dropped_duplicates": len(rows) - inserted,
                }
            )

        # 2) 데이터 없는 마스터 → 이를 참조하는 팩트 칼럼에서 DISTINCT 채움.
        for t in ordered:
            if t["name"] in datasets and datasets.get(t["name"]):
                continue
            pk = _single_pk(t)
            if not pk:
                continue
            # 이 테이블.PK 를 가리키는 (child, col) 들.
            refs = [
                (child, c["name"])
                for child in tables
                for c in child.get("columns", [])
                if (c.get("fk") or {}).get("table") == t["name"]
            ]
            if not refs:
                report_tables.append(
                    {"name": t["name"], "source": "empty", "received": 0, "loaded": 0, "dropped_duplicates": 0}
                )
                continue
            union = " UNION ".join(
                f"SELECT DISTINCT {_q(col)} AS k FROM {_q(child['name'])} "
                f"WHERE {_q(col)} IS NOT NULL"
                for child, col in refs
            )
            conn.execute(
                f"INSERT OR IGNORE INTO {_q(t['name'])} ({_q(pk['name'])}) "
                f"SELECT k FROM ({union})"
            )
            cnt = conn.execute(f"SELECT COUNT(*) FROM {_q(t['name'])}").fetchone()[0]
            report_tables.append(
                {"name": t["name"], "source": "distinct", "received": 0, "loaded": cnt, "dropped_duplicates": 0}
            )

        conn.commit()

        # 3) 무결성 — FK orphan 검사 (선언 후에도 OR IGNORE 로 들어간 고아 가능).
        integrity: list[dict] = []
        for child in tables:
            for c in child.get("columns", []):
                fk = c.get("fk")
                if not fk or fk.get("table") not in known:
                    continue
                parent, pcol, col = fk["table"], fk["column"], c["name"]
                orphans = conn.execute(
                    f"SELECT COUNT(*) FROM {_q(child['name'])} ch "
                    f"WHERE ch.{_q(col)} IS NOT NULL AND ch.{_q(col)} NOT IN "
                    f"(SELECT {_q(pcol)} FROM {_q(parent)})"
                ).fetchone()[0]
                samples: list[Any] = []
                if orphans:
                    samples = [
                        row[0]
                        for row in conn.execute(
                            f"SELECT DISTINCT ch.{_q(col)} FROM {_q(child['name'])} ch "
                            f"WHERE ch.{_q(col)} IS NOT NULL AND ch.{_q(col)} NOT IN "
                            f"(SELECT {_q(pcol)} FROM {_q(parent)}) LIMIT 5"
                        ).fetchall()
                    ]
                integrity.append(
                    {
                        "child": child["name"],
                        "column": col,
                        "parent": parent,
                        "parent_column": pcol,
                        "orphans": orphans,
                        "samples": samples,
                    }
                )
    finally:
        conn.close()

    return {
        "db_path": db_path,
        "tables": report_tables,
        "order": [t["name"] for t in ordered],
        "integrity": integrity,
    }


# ── 읽기 전용 쿼리 (조립 미리보기 / 탐색) ─────────────────────────────────────
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|vacuum)\b",
    re.IGNORECASE,
)


def run_query(db_path: str, sql: str, *, max_rows: int = 200) -> dict:
    """SELECT 전용 읽기 쿼리. 쓰기/DDL 차단 + 행 수 상한."""
    s = (sql or "").strip().rstrip(";")
    if not s:
        raise ValueError("빈 쿼리")
    low = s.lower()
    if not (low.startswith("select") or low.startswith("with")):
        raise ValueError("SELECT(또는 WITH) 쿼리만 허용됩니다")
    if _FORBIDDEN.search(s):
        raise ValueError("읽기 전용 — 쓰기/DDL 키워드는 사용할 수 없습니다")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA query_only = ON")
        cur = conn.execute(s)
        columns = [d[0] for d in (cur.description or [])]
        rows = cur.fetchmany(max_rows + 1)
        truncated = len(rows) > max_rows
        rows = rows[:max_rows]
        return {
            "columns": columns,
            "rows": [list(r) for r in rows],
            "truncated": truncated,
        }
    finally:
        conn.close()
