"""Canonical Read API 출력 schema — World-A 정형 테이블(/api/canonical/*) → frontend typed contract.

dashboard1(World-B `_workspace` 캐시)과 별개. 본 모델은 `clumi.*_normalized/_computed/blended_computed`
를 SELECT·집계한 결과와 1:1. extra='ignore'(dashboard1 _OutputBase 패턴 답습).

Status: complete — 마케팅 성과 수직 슬라이스 (2026-06-17).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _OutputBase(BaseModel):
    model_config = ConfigDict(extra="ignore")


class MarketingKpi(_OutputBase):
    """blended_computed 1행 — period 단위 교차소스 지표."""

    total_ad_cost_krw: int
    total_msg_cost_krw: int
    total_marketing_cost_krw: int
    total_order_revenue_krw: int
    mer: float | None
    tacos_pct: float | None


class AdChannelPerf(_OutputBase):
    """광고 매체 채널별 집계 + 파생(ROAS·CTR·CPC·CVR). roas = Σrev/Σcost (집계 후 비율)."""

    channel: str
    ad_cost_krw: int
    impressions: int
    clicks: int
    conversion_count: int
    conversion_revenue_krw: int
    roas_x: float | None
    ctr_pct: float | None
    cpc_krw: int | None
    cvr_pct: float | None


class MsgChannelPerf(_OutputBase):
    """메시징 채널 — msg_roi(≠ROAS, C6.3). 광고 ROAS와 동일 축 비교 금지."""

    channel: str
    msg_cost_krw: int
    msg_target_count: int
    msg_conversion_count: int
    msg_conversion_revenue_krw: int
    msg_roi_pct: float | None


class DailyPoint(_OutputBase):
    """일별 광고 집계 (광고 매체 합산)."""

    report_date: str
    ad_cost_krw: int
    conversion_count: int
    conversion_revenue_krw: int
    roas_x: float | None


class CampaignPerf(_OutputBase):
    """캠페인 단위 광고 성과 (드릴다운). normalized를 (channel, campaign_id)로 집계."""

    channel: str
    campaign_id: str
    campaign_name: str | None
    ad_cost_krw: int
    conversion_count: int
    conversion_revenue_krw: int
    roas_x: float | None
    ctr_pct: float | None
    cpc_krw: int | None
    cvr_pct: float | None


class MarketingPerformanceOutput(_OutputBase):
    """마케팅 성과 페이지 = 조립형 1 응답 (KPI + 광고채널 + 캠페인 + 메시징 + 일별)."""

    client: str
    period: str
    kpi: MarketingKpi
    ad_channels: list[AdChannelPerf]
    campaigns: list[CampaignPerf]
    msg_channels: list[MsgChannelPerf]
    daily: list[DailyPoint]


# ── 데이터 카탈로그 (canonical 전체 펼쳐보기 — 메뉴얼/데이터 사전) ──


class CatalogColumn(_OutputBase):
    """컬럼 = 지표 사전 (이름·타입·의미)."""

    name: str
    type: str
    desc: str | None


class CatalogTable(_OutputBase):
    """canonical 테이블 메타 — 행은 별도(/api/data 콘솔 재사용)."""

    table: str
    layer: str          # normalized | computed | blended
    layer_label: str    # 정규화 | 계산 | 통합
    row_count: int
    columns: list[CatalogColumn]


class CatalogSource(_OutputBase):
    """소스 묶음 (광고/메시징/커머스/통합)."""

    source: str
    label: str
    group: str
    tables: list[CatalogTable]


class CatalogOutput(_OutputBase):
    """canonical 데이터 카탈로그 — 소스별 테이블·컬럼 사전 (raw 제외)."""

    client: str
    sources: list[CatalogSource]
