"""FileDataSource — POC. data/{client}/raw/{file} 파일 기반.

확장자 분기:
    .csv   → pandas.DataFrame
    .json  → dict | list
    .jsonl → list[dict]
    .sql   → str

DEFAULT_MAPPING = source_id → 파일명 (확장자 포함, client 무관 공통).
신규 client 추가 시 데이터 파일만 동일 이름으로 두면 자동 작동.

향후 client 별로 다른 mapping 필요 시 __init__ 에 client_mappings: dict[str, dict] 추가.

spec: docs/_claude/architecture/backend_data_agent_2026-05-26.md §4.2
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.logging import get_logger

from .base import DataSource, DataSourceNotFound

logger = get_logger(__name__)


# ── 단일 진실 소스: source_id → SourceSpec (filename + kind + platform) ──
# kind     : external(API, 현재 mock=data/mock_api/{client}, 외부커넥터 수집) | internal(내 서버, 내부리더)
# platform : 외부 플랫폼명(meta/naver/kakao/google). 내부·미정 = None.
# 설계: docs/reports/수집_datasource_설계노트_2026-05-28.md (external/internal 구분은 폴더 아닌 매핑표·tool)


@dataclass(frozen=True)
class SourceSpec:
    """수집 소스 1개 메타 — 파일명 + 종류 + 플랫폼."""
    filename: str
    kind: str                 # "external" | "internal"
    platform: str | None = None


SOURCE_REGISTRY: dict[str, SourceSpec] = {
    # ── external = API (현재 mock = data/mock_api/{client}) ──
    # Meta (Instagram 포함)
    "meta_ads_performance":  SourceSpec("meta_ads_performance.json", "external", "meta"),
    "meta_ads_by_age":       SourceSpec("meta_ads_by_age.json", "external", "meta"),
    "meta_instagram_inapp":  SourceSpec("meta_instagram_inapp.json", "external", "meta"),
    "instagram_engagement":  SourceSpec("instagram_engagement.json", "external", "meta"),
    # Naver
    "naver_searchad":        SourceSpec("naver_searchad.json", "external", "naver"),
    "naver_advoost":         SourceSpec("naver_advoost.csv", "external", "naver"),
    "naver_talktalk":        SourceSpec("naver_talktalk.json", "external", "naver"),
    "naver_interest_alert":  SourceSpec("naver_interest_alert.csv", "external", "naver"),
    # Kakao
    "kakao_bizmessage":      SourceSpec("kakao_bizmessage.json", "external", "kakao"),
    # Google (GA4 + Ads)
    "ga4_traffic_source":    SourceSpec("ga4_traffic_source.jsonl", "external", "google"),
    "ga4_page_events":       SourceSpec("ga4_page_events.jsonl", "external", "google"),
    "google_ads_performance": SourceSpec("google_ads_performance.csv", "external", "google"),  # 유료 광고 실적 (canonical 18번째, A1 2026-06-16)
    # 외부 (플랫폼 미정)
    "ad_change_history":     SourceSpec("ad_change_history.json", "external", None),
    "household_structure":   SourceSpec("household_structure.csv", "external", None),
    "reviews":               SourceSpec("reviews.csv", "external", None),            # 리뷰 사이트
    "keyword_performance":   SourceSpec("keyword_performance.csv", "external", None),  # 검색광고 키워드
    # daily_performance 제거 (A-5.3): World-C 별개 mock(raw 미reconcile) — 4 tool·라우트가 canonical 전환. csv 폐기.

    # ── internal = 내 서버 (data/{client}) ──
    "orders":                SourceSpec("orders.csv", "internal"),
    "customers":             SourceSpec("customers.csv", "internal"),
    "customer_rfm":          SourceSpec("customer_rfm.csv", "internal"),
    "grade_history":         SourceSpec("customer_grade_history.csv", "internal"),
    "signup_events":         SourceSpec("signup_events.csv", "internal"),
    "promotions":            SourceSpec("promotions.sql", "internal"),
    "category_sales":        SourceSpec("category_sales.csv", "internal"),
    "crm_messages":          SourceSpec("crm_messages.sql", "internal"),
    "campaigns":             SourceSpec("campaigns.csv", "internal"),          # 캠페인 기획
    "creatives":             SourceSpec("creatives.csv", "internal"),          # 소재 (내부 자산)
    "budget_allocation":     SourceSpec("budget_allocation.csv", "internal"),  # 예산 배분
    "ab_tests":              SourceSpec("ab_tests.csv", "internal"),           # A/B 결과
    "marketing_targets":     SourceSpec("marketing_monthly_targets.csv", "internal"),  # 월별 마케팅 목표 (대시보드 목표대비, 2026-06-09)
    "channel_targets":       SourceSpec("channel_targets.csv", "internal"),            # 채널별 ROAS/CPA 목표 (채널 페이지, 2026-06-09)
}


# 하위호환: source_id → 파일명 (기존 import·테스트 유지). SOURCE_REGISTRY 에서 파생.
DEFAULT_MAPPING: dict[str, str] = {sid: s.filename for sid, s in SOURCE_REGISTRY.items()}


def source_kind(source_id: str) -> str | None:
    """source_id → 'external' | 'internal' | None(미등록)."""
    s = SOURCE_REGISTRY.get(source_id)
    return s.kind if s else None


def source_platform(source_id: str) -> str | None:
    """source_id → 외부 플랫폼명(meta/naver/kakao/google) | None."""
    s = SOURCE_REGISTRY.get(source_id)
    return s.platform if s else None


def sources_by_kind(kind: str) -> list[str]:
    """kind('external'|'internal') 의 source_id 목록 (정렬)."""
    return sorted(sid for sid, s in SOURCE_REGISTRY.items() if s.kind == kind)


class FileDataSource(DataSource):
    """data/{client}/raw/{filename} 파일 기반 DataSource."""

    def __init__(
        self,
        repo_root: Path,
        mapping: dict[str, str] | None = None,
    ):
        """
        Args:
            repo_root: project repo root (data/ 의 부모)
            mapping: source_id → 파일명 (None 이면 DEFAULT_MAPPING)
        """
        self.repo_root = Path(repo_root)
        self.mapping = mapping or DEFAULT_MAPPING

    def _path(self, client: str, source_id: str) -> Path:
        if source_id not in self.mapping:
            raise DataSourceNotFound(
                f"source_id '{source_id}' not in mapping "
                f"(registered: {sorted(self.mapping.keys())})"
            )
        filename = self.mapping[source_id]
        return self.repo_root / "data" / client / "raw" / filename

    # ── DataSource 구현 ──
    def has(self, client: str, source_id: str) -> bool:
        try:
            return self._path(client, source_id).exists()
        except DataSourceNotFound:
            return False

    def get(self, client: str, source_id: str) -> Any:
        path = self._path(client, source_id)
        if not path.exists():
            raise DataSourceNotFound(
                f"file not found: client={client} source_id={source_id} path={path}"
            )

        suffix = path.suffix.lower()
        logger.info("data_source.get", client=client, source_id=source_id,
                    suffix=suffix, path=str(path))

        if suffix == ".csv":
            return pd.read_csv(path, encoding="utf-8-sig")
        if suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if suffix == ".jsonl":
            return [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        if suffix == ".sql":
            return path.read_text(encoding="utf-8")

        raise DataSourceNotFound(f"unsupported extension: {suffix}")

    def list_sources(self, client: str) -> list[str]:
        client_dir = self.repo_root / "data" / client / "raw"
        if not client_dir.exists():
            return []
        return sorted(
            sid for sid, fname in self.mapping.items()
            if (client_dir / fname).exists()
        )

    def stream_jsonl(self, client: str, source_id: str):
        """jsonl 파일을 record 단위 yield — 대용량 메모리 절약 (예: ga4_page_events 265MB).

        Note: FileDataSource 특화 메서드. abstract DataSource 인터페이스에는 포함하지 않음
              (다른 client/storage 가 jsonl stream 일반화 필요해진 시점에 옮김).
        """
        path = self._path(client, source_id)
        if not path.exists():
            raise DataSourceNotFound(
                f"file not found: client={client} source_id={source_id} path={path}"
            )
        if path.suffix.lower() != ".jsonl":
            raise DataSourceNotFound(
                f"stream_jsonl 는 jsonl 만 지원: source_id={source_id} suffix={path.suffix}"
            )
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


__all__ = [
    "FileDataSource",
    "DEFAULT_MAPPING",
    "SourceSpec",
    "SOURCE_REGISTRY",
    "source_kind",
    "source_platform",
    "sources_by_kind",
]
