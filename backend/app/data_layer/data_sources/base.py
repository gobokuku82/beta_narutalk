"""DataSource — tool 과 data 사이 '관절' (사용자 표현, 2026-05-26).

표준 패턴: Repository (Martin Fowler 1990s) + Hexagonal Adapter (Cockburn 2005).
*사서* 비유: tool (손님) 이 "orders 책 줘" 라고 사서 (Repository) 에게 부탁하면,
사서는 client·환경별 *어디서* 가져올지 알아서 가져온다.

사용 예:
    ds = FileDataSource(repo_root)
    df = ds.get(client=context.client_id, source_id='orders')
    # → pandas DataFrame (data/{client}/raw/orders.csv)

agent · direct API 모두 본 인터페이스 경유 → 일관성. tool 은 *어떤 source 필요한지* (의미)
만 안다. *어디서/어떻게* 는 DataSource 책임.

위치: backend/app/data_sources/ (dream_agent 형제 — agent + API 공유).

spec: docs/_claude/architecture/backend_data_agent_2026-05-26.md §4.2
memory: project_tool_data_agent_separation
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Iterator


class DataSourceError(Exception):
    """DataSource layer 의 base exception."""


class DataSourceNotFound(DataSourceError):
    """source 매핑 없음 / 파일 없음 / API 응답 없음."""


# ── pushdown v1 (ADR-031): where 두 연산자 — 동등 / __prefix ──

_PREFIX_OP = "__prefix"


def _match(rec: dict, where: dict | None) -> bool:
    """ADR-031-1: 값 비교는 텍스트 의미론(v1) — jsonb `->>` 와 동일 결과를 위해
    양 백엔드 모두 str 비교. None(컬럼 부재 포함)은 어떤 조건과도 불일치."""
    if not where:
        return True
    for k, v in where.items():
        if k.endswith(_PREFIX_OP):
            cur = rec.get(k[: -len(_PREFIX_OP)])
            if cur is None or not str(cur).startswith(str(v)):
                return False
        else:
            cur = rec.get(k)
            if cur is None or str(cur) != str(v):
                return False
    return True


def _as_records(data: Any) -> list[dict]:
    """get() 결과 → list[dict] 정규화 (DataFrame/records/{rows:[...]}/단일 dict)."""
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    try:
        import pandas as pd
        if isinstance(data, pd.DataFrame):
            return data.to_dict("records")
    except ImportError:
        pass
    if isinstance(data, dict):
        rows = data.get("rows")
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)]
        return [data]
    raise DataSourceError(f"query/aggregate: record 화 불가 타입 {type(data).__name__}")


class DataSource(ABC):
    """tool 과 data source 사이 인터페이스 ('관절').

    구현체:
        - FileDataSource: data/{client}/raw/{file} 파일 기반 (POC)
        - ApiDataSource: 외부 광고 API (네이버광고·메타광고, MVP+)
        - DbDataSource: PostgreSQL clumi.<table> (MVP+)
    """

    @abstractmethod
    def get(self, client: str, source_id: str) -> Any:
        """단일 source 로드.

        Args:
            client: 회사 식별자 (디렉토리·테넌트 키) — context.client_id
            source_id: 'orders' · 'customers' · 'grade_history' 등 — semantic name

        Returns:
            확장자/포맷에 따라:
              - .csv  → pandas.DataFrame
              - .json → dict | list
              - .jsonl → list[dict]
              - .sql → str (SQL dump raw text)

        Raises:
            DataSourceNotFound: client·source_id 매핑 없거나 파일 없음
        """

    @abstractmethod
    def list_sources(self, client: str) -> list[str]:
        """client 가 가진 source_id 목록 (UI · 디버그 · workflow tool palette 용)."""

    @abstractmethod
    def has(self, client: str, source_id: str) -> bool:
        """source 존재 여부 (lookup 가벼움)."""

    # ── pushdown v1 (ADR-031) — additive: 기존 get 계약 불변 ──

    def stream_jsonl(self, client: str, source_id: str) -> Iterator[dict]:
        """record 단위 yield. ABC 구체 기본 메서드 (계획 §8.2 승격 결정 2026-06-12).

        구현체(File/Postgres)는 진짜 스트리밍으로 override. 기본 구현은 get() 결과가
        record 목록일 때만 — 아니면 DataSourceNotFound (호출측 fallback 신호).
        """
        data = self.get(client, source_id)
        if isinstance(data, list):
            yield from (r for r in data if isinstance(r, dict))
        else:
            raise DataSourceNotFound(
                f"stream_jsonl: '{source_id}' 는 record 목록 아님 ({type(data).__name__})"
            )

    def _iter_records(self, client: str, source_id: str) -> Iterator[dict]:
        """query/aggregate 의 공급원 — V3: jsonl 은 stream_jsonl 1-pass (전량 적재 역행 금지).

        stream_jsonl 이 NotFound(비 jsonl)면 get() 정규화로 fallback.
        (구현체 stream_jsonl 은 첫 yield 전에 raise 하는 계약 — File/Postgres 실측.)
        """
        gen = self.stream_jsonl(client, source_id)
        try:
            first = next(gen)
        except StopIteration:
            return
        except DataSourceNotFound:
            yield from _as_records(self.get(client, source_id))
            return
        yield first
        yield from gen

    def query_iter(
        self, client: str, source_id: str, *,
        where: dict | None = None, columns: list[str] | None = None,
    ) -> Iterator[dict]:
        """query 의 스트리밍 형태 — 행을 한 건씩 yield (V3: 피크 메모리 일정).

        결과가 클 수 있는 호출(대용량 투영 등)은 이쪽을 쓸 것. 계약은 query 와 동일.
        """
        for rec in self._iter_records(client, source_id):
            if not _match(rec, where):
                continue
            yield {c: rec.get(c) for c in columns} if columns else dict(rec)

    def query(
        self, client: str, source_id: str, *,
        where: dict | None = None, columns: list[str] | None = None,
    ) -> list[dict]:
        """부분 행 조회 — where(동등/`__prefix`)로 행 축소 + columns 투영 (ADR-031-1).

        기본 구현: 스트리밍 순회 + Python 필터 (File 자동 지원, 동작 변화 0).
        Postgres 행-테이블 소스는 override 가 SQL 로 내림 (같은답 계약 ADR-031-3).
        결과 전체를 list 로 들기 때문에 대용량 결과는 query_iter 권장.
        """
        return list(self.query_iter(client, source_id, where=where, columns=columns))

    def aggregate(
        self, client: str, source_id: str, *,
        op: str = "count", column: str | None = None,
        by: str | None = None, where: dict | None = None,
    ) -> Any:
        """집계 내리기 — 행 대신 값/분포 반환. op ∈ {count, sum} (v1, ADR-031-1).

        by 지정 시 {그룹값(str|None): 집계값} dict, 미지정 시 스칼라 (count=int, sum=float).
        sum 대상의 비숫자 값은 시끄럽게 실패 (tool 책임 — 침묵 보정 금지).
        """
        if op not in ("count", "sum"):
            raise DataSourceError(f"aggregate: 미지원 op '{op}' (v1 = count/sum)")
        if op == "sum" and not column:
            raise DataSourceError("aggregate: op=sum 은 column 필수")

        groups: dict[Any, float] = {}
        scalar: float = 0.0
        for rec in self._iter_records(client, source_id):
            if not _match(rec, where):
                continue
            if op == "count":
                inc = 1.0
            else:
                v = rec.get(column)
                if v is None:
                    continue
                inc = float(v)   # 비숫자 → ValueError (계약: 시끄러운 실패)
            if by is None:
                scalar += inc
            else:
                key = rec.get(by)
                key = None if key is None else str(key)
                groups[key] = groups.get(key, 0.0) + inc

        if by is not None:
            return {k: (int(v) if op == "count" else v) for k, v in groups.items()}
        return int(scalar) if op == "count" else scalar


__all__ = ["DataSource", "DataSourceError", "DataSourceNotFound"]
