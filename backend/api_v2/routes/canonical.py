"""Canonical Read API — `/api/canonical/*` (World-A 정형 테이블 직접 SELECT·집계).

새 canonical 테이블(`clumi.*_normalized`/`blended_computed`)을 프론트로 서빙. dashboard1의
`_cached_or_run`(구 World-B `_workspace` 캐시 경로)을 **따르지 않고** asyncpg 풀로 직접 SELECT
(`data_console.py` 패턴). schema-per-client(`?client=`) · period(`YYYY-MM`).

수직 슬라이스 1호 = 마케팅 성과: blended KPI + 광고 매체 채널 집계 + 메시징(분리) + 일별 추이.

Status: complete — 마케팅 성과 슬라이스 (2026-06-17). 회원/프로모션/세그먼트 = 도메인 피봇 후 별 endpoint.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query, Request

from api_v2.routes.data_console import _columns, _pool, _qt, _require_schema, _require_table
from app.schemas.outputs.canonical import (
    AdChannelPerf,
    CampaignPerf,
    CatalogColumn,
    CatalogOutput,
    CatalogSource,
    CatalogTable,
    DailyPoint,
    MarketingKpi,
    MarketingPerformanceOutput,
    MsgChannelPerf,
)

router = APIRouter(prefix="/api/canonical", tags=["Canonical"])

_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")
_AD_TABLES = ("meta_ads_performance_normalized", "naver_searchad_normalized",
              "naver_advoost_normalized", "google_ads_performance_normalized")
# (테이블, campaign_name 컬럼 — meta·google 보유, 나머지는 NULL). 값은 하드코딩 상수(주입 무관).
_AD_CAMPAIGN = (
    ("meta_ads_performance_normalized", "campaign_name"),
    ("naver_searchad_normalized", None),
    ("naver_advoost_normalized", None),
    ("google_ads_performance_normalized", "campaign_name"),
)
_MSG_TABLES = ("kakao_bizmessage_normalized", "naver_talktalk_normalized")

# ── 데이터 카탈로그 (canonical 전체 펼쳐보기) ──
_REL_SUFFIX = ("_normalized", "_computed", "_blended")
_LAYER_LABEL = {"normalized": "정규화", "computed": "계산", "blended": "통합"}
# stem(테이블 - layer 접미사) → (라벨, 그룹). 미등재 stem은 fallback (convention — 새 소스 자동 등장).
_SOURCE_META = {
    "meta_ads_performance": ("메타", "광고"),
    "naver_searchad": ("네이버 검색", "광고"),
    "naver_advoost": ("네이버 GFA", "광고"),
    "google_ads_performance": ("구글", "광고"),
    "kakao_bizmessage": ("카카오 알림톡", "메시징"),
    "naver_talktalk": ("네이버 톡톡", "메시징"),
    "orders": ("주문", "커머스"),
    "blended": ("전사 통합", "통합"),
}
_SOURCE_ORDER = list(_SOURCE_META.keys())
# 지표 사전 — 각 컬럼이 무엇인가 (메뉴얼). 미등재 컬럼은 desc=None.
# COL_DESC 폐기(2026-06-19): canonical 의미는 contract(SSOT) 파생 + tool-output 합성 규칙.
# 카탈로그 컬럼 desc 도 동일 SSOT 경로(describe_or_synth) 사용 — 손코딩 사본 제거.
from app.dream_agent.tools.shared.col_dictionary import describe_or_synth as _col_desc


def _stem(table: str) -> str:
    for suf in _REL_SUFFIX:
        if table.endswith(suf):
            return table[: -len(suf)]
    return table


def _layer(table: str) -> str:
    for suf in _REL_SUFFIX:
        if table.endswith(suf):
            return suf[1:]
    return ""


def _ratio(num, den, *, mult: float = 1, nd: int = 2) -> float | None:
    return round(num / den * mult, nd) if den else None


def _i(v) -> int:
    return int(v or 0)


@router.get("/marketing-performance", response_model=MarketingPerformanceOutput,
            summary="마케팅 성과 — blended KPI + 광고채널 + 메시징 + 일별 (canonical 직접 SELECT)")
async def marketing_performance(
    request: Request,
    period: str = Query(..., examples=["2026-04"], description="YYYY-MM"),
    client: str = Query(..., description="회사 식별자 (= schema)"),
) -> MarketingPerformanceOutput:
    if not _PERIOD_RE.match(period):
        raise HTTPException(400, {"code": "BAD_PERIOD", "message": f"YYYY-MM 형식 필요: {period!r}"})
    pool = _pool(request)
    await _require_schema(pool, client)
    await _require_table(pool, client, "blended_computed")

    # ── KPI = blended_computed 1행 (period) ──
    b = await pool.fetchrow(
        f"SELECT * FROM {_qt(client, 'blended_computed')} WHERE period=$1", period
    )
    if b is None:
        raise HTTPException(404, {"code": "NO_BLENDED",
                                  "message": f"blended_computed에 period={period} 없음"})
    kpi = MarketingKpi(
        total_ad_cost_krw=_i(b["total_ad_cost_krw"]),
        total_msg_cost_krw=_i(b["total_msg_cost_krw"]),
        total_marketing_cost_krw=_i(b["total_marketing_cost_krw"]),
        total_order_revenue_krw=_i(b["total_order_revenue_krw"]),
        mer=b["mer"], tacos_pct=b["tacos_pct"],
    )

    # ── 광고 매체 채널 집계 (테이블별 Σ → 집계 후 비율) ──
    ad_channels: list[AdChannelPerf] = []
    for t in _AD_TABLES:
        rows = await pool.fetch(
            f"SELECT channel, sum(ad_cost_krw) cost, sum(impressions) imp, sum(clicks) clk, "
            f"sum(conversion_count) conv, sum(conversion_revenue_krw) rev "
            f"FROM {_qt(client, t)} WHERE to_char(report_date,'YYYY-MM')=$1 GROUP BY channel",
            period,
        )
        for r in rows:
            cost, imp, clk, conv, rev = (_i(r["cost"]), _i(r["imp"]), _i(r["clk"]),
                                         _i(r["conv"]), _i(r["rev"]))
            ad_channels.append(AdChannelPerf(
                channel=r["channel"], ad_cost_krw=cost, impressions=imp, clicks=clk,
                conversion_count=conv, conversion_revenue_krw=rev,
                roas_x=_ratio(rev, cost), ctr_pct=_ratio(clk, imp, mult=100),
                cpc_krw=(round(cost / clk) if clk else None),
                cvr_pct=_ratio(conv, clk, mult=100),
            ))
    ad_channels.sort(key=lambda c: c.ad_cost_krw, reverse=True)

    # ── 캠페인 드릴다운 (channel, campaign_id 집계 + 파생) ──
    campaigns: list[CampaignPerf] = []
    for t, namecol in _AD_CAMPAIGN:
        name_sel = namecol or "NULL"
        name_grp = f", {namecol}" if namecol else ""
        rows = await pool.fetch(
            f"SELECT channel, campaign_id, {name_sel} AS campaign_name, "
            f"sum(ad_cost_krw) cost, sum(impressions) imp, sum(clicks) clk, "
            f"sum(conversion_count) conv, sum(conversion_revenue_krw) rev "
            f"FROM {_qt(client, t)} WHERE to_char(report_date,'YYYY-MM')=$1 "
            f"GROUP BY channel, campaign_id{name_grp}",
            period,
        )
        for r in rows:
            cost, imp, clk, conv, rev = (_i(r["cost"]), _i(r["imp"]), _i(r["clk"]),
                                         _i(r["conv"]), _i(r["rev"]))
            campaigns.append(CampaignPerf(
                channel=r["channel"], campaign_id=str(r["campaign_id"]),
                campaign_name=r["campaign_name"], ad_cost_krw=cost,
                conversion_count=conv, conversion_revenue_krw=rev,
                roas_x=_ratio(rev, cost), ctr_pct=_ratio(clk, imp, mult=100),
                cpc_krw=(round(cost / clk) if clk else None),
                cvr_pct=_ratio(conv, clk, mult=100),
            ))
    campaigns.sort(key=lambda c: c.ad_cost_krw, reverse=True)

    # ── 메시징 채널 (msg_roi — 광고 ROAS와 분리, C6.3) ──
    msg_channels: list[MsgChannelPerf] = []
    for t in _MSG_TABLES:
        rows = await pool.fetch(
            f"SELECT channel, sum(msg_cost_krw) cost, sum(msg_target_count) tgt, "
            f"sum(msg_conversion_count) conv, sum(msg_conversion_revenue_krw) rev "
            f"FROM {_qt(client, t)} WHERE to_char(report_date,'YYYY-MM')=$1 GROUP BY channel",
            period,
        )
        for r in rows:
            cost, rev = _i(r["cost"]), _i(r["rev"])
            msg_channels.append(MsgChannelPerf(
                channel=r["channel"], msg_cost_krw=cost, msg_target_count=_i(r["tgt"]),
                msg_conversion_count=_i(r["conv"]), msg_conversion_revenue_krw=rev,
                msg_roi_pct=(round((rev / cost - 1) * 100, 1) if cost else None),
            ))
    msg_channels.sort(key=lambda c: c.msg_cost_krw, reverse=True)

    # ── 일별 추이 (광고 매체 합산) ──
    union = " UNION ALL ".join(
        f"SELECT report_date, ad_cost_krw, conversion_count, conversion_revenue_krw "
        f"FROM {_qt(client, t)} WHERE to_char(report_date,'YYYY-MM')=$1" for t in _AD_TABLES
    )
    drows = await pool.fetch(
        f"SELECT report_date, sum(ad_cost_krw) cost, sum(conversion_count) conv, "
        f"sum(conversion_revenue_krw) rev FROM ({union}) u "
        f"GROUP BY report_date ORDER BY report_date",
        period,
    )
    daily = [DailyPoint(
        report_date=str(r["report_date"]), ad_cost_krw=_i(r["cost"]),
        conversion_count=_i(r["conv"]), conversion_revenue_krw=_i(r["rev"]),
        roas_x=_ratio(_i(r["rev"]), _i(r["cost"])),
    ) for r in drows]

    return MarketingPerformanceOutput(
        client=client, period=period, kpi=kpi,
        ad_channels=ad_channels, campaigns=campaigns,
        msg_channels=msg_channels, daily=daily,
    )


@router.get("/catalog", response_model=CatalogOutput,
            summary="데이터 카탈로그 — canonical 전체(정규화/계산/통합) 소스별 테이블·컬럼 사전 (raw 제외)")
async def catalog(
    request: Request,
    client: str = Query(..., description="회사 식별자 (= schema)"),
) -> CatalogOutput:
    """canonical 정형 테이블을 소스별로 묶어 메타·컬럼 의미·행수 반환. 행 데이터는 /api/data 콘솔 재사용."""
    pool = _pool(request)
    await _require_schema(pool, client)
    rows = await pool.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema=$1 AND table_type='BASE TABLE'", client,
    )
    canon = [r["table_name"] for r in rows if r["table_name"].endswith(_REL_SUFFIX)]
    by_stem: dict[str, list[str]] = {}
    for tbl in canon:
        by_stem.setdefault(_stem(tbl), []).append(tbl)

    # 알려진 순서 우선 + 미등재 stem은 알파벳 (convention — 새 소스 자동 등장)
    ordered = [s for s in _SOURCE_ORDER if s in by_stem] + \
              sorted(s for s in by_stem if s not in _SOURCE_META)

    sources: list[CatalogSource] = []
    for stem in ordered:
        label, group = _SOURCE_META.get(stem, (stem, "기타"))
        ctables: list[CatalogTable] = []
        for tbl in by_stem[stem]:
            cols = await _columns(pool, client, tbl)
            count = await pool.fetchval(f"SELECT count(*) FROM {_qt(client, tbl)}")
            lyr = _layer(tbl)
            ctables.append(CatalogTable(
                table=tbl, layer=lyr, layer_label=_LAYER_LABEL.get(lyr, lyr),
                row_count=int(count),
                columns=[CatalogColumn(name=c["name"], type=c["type"],
                                       desc=_col_desc(c["name"])) for c in cols],
            ))
        ctables.sort(key=lambda x: 0 if x.layer == "normalized" else 1)  # 정규화 먼저
        sources.append(CatalogSource(source=stem, label=label, group=group, tables=ctables))

    return CatalogOutput(client=client, sources=sources)
