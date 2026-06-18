"""Dashboard1 Routes — `/dashboard1` 페이지의 backend API.

20 endpoint (KPI 9 + MoM 4 + Segment 7) — frontend 28 요소 한 페이지 데이터 source.

API path = 기능 단위 (/api/dashboard1/...). client 는 ?client= param 으로 분기 (P3).
어떤 회사든 같은 endpoint 사용 — file/path 가 회사 이름이 아니라 *기능 이름* (P3 일관).

캐시 정책:
    storage.exists(layer, key) hit 시 즉시 반환 (캐시된 정답값)
    miss 시 tool.execute() → storage 자동 save → 응답
    → 정답 17 이 이미 data/{client}/normalized·computed/ 에 박제됨 → ms 응답

응답:
    각 endpoint 의 response_model = Pydantic Output (extra='ignore' 로 _storage·_meta 자동 무시)

계획서: docs/_claude/architecture/clumi_to_dashboard1_path_rename_2026-05-27.md
spec: backend_data_agent_2026-05-26.md (Step 5)

Rename history:
  2026-05-27 — routes/clumi.py → routes/dashboard1.py (path 가 회사 이름 박힘 정정)

Status: complete — 2026-05-27 path rename.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Type

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.shared.canonical_daily import load_canonical_ad_rows
from app.schemas.outputs.dashboard1 import (
    AdCostOutput,
    AgeSegmentOutput,
    AovMomOutput,
    AovOutput,
    CacOutput,
    CategoryDistOutput,
    ChannelDistOutput,
    GradeRevenueOutput,
    GradeTimeseriesOutput,
    MemberGuestOutput,
    MomRevenueOutput,
    NewMembersMomOutput,
    NewMembersOutput,
    PromoRevenueOutput,
    PromoRoasOutput,
    RepurchaseMomOutput,
    RevenueOutput,
    RoasOutput,
    SignupConversionOutput,
    UnknownShareOutput,
)
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.comparison.aov_mom import AovMom
from app.dream_agent.tools.comparison.grade_timeseries import GradeTimeseries
from app.dream_agent.tools.comparison.mom_revenue import MomRevenue
from app.dream_agent.tools.comparison.new_members_mom import NewMembersMom
from app.dream_agent.tools.comparison.repurchase_mom import RepurchaseMom
from app.dream_agent.tools.metrics.age_segment import AgeSegment
from app.dream_agent.tools.metrics.aov_monthly import AovMonthly
from app.dream_agent.tools.metrics.cac_overall import CacOverall
from app.dream_agent.tools.metrics.grade_revenue import GradeRevenue
from app.dream_agent.tools.metrics.new_members_monthly import NewMembersMonthly
from app.dream_agent.tools.metrics.promotion_revenue import PromotionRevenue
from app.dream_agent.tools.metrics.promotion_roas import PromotionRoas
from app.dream_agent.tools.metrics.revenue_total import RevenueTotal
from app.dream_agent.tools.metrics.roas_overall import RoasOverall
from app.dream_agent.tools.metrics.signup_conversion import SignupConversion
from app.dream_agent.tools.metrics.unknown_revenue_share import UnknownRevenueShare
from app.dream_agent.tools.normalization.channel_attribution_normalizer import (
    ChannelAttributionNormalizer,
)
from app.dream_agent.tools.metrics.ad_cost_total import AdCostTotal
from app.dream_agent.tools.metrics.category_multi_distributor import (
    CategoryMultiDistributor,
)
from app.dream_agent.tools.metrics.member_guest_stats import (
    MemberGuestStats,
)
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.storage import Layer, get_storage
from app.data_sources import get_default_data_source
from app.pipelines import PipelineRunner, load_pipeline

logger = get_logger(__name__)

router = APIRouter(prefix="/api/dashboard1", tags=["Dashboard1"])

# ─────────────────────────────────────────────────────────────────
# 공통 — period 검증 + cache helper
# ─────────────────────────────────────────────────────────────────

_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


def _validate_period(period: str) -> None:
    if not _PERIOD_RE.match(period):
        raise HTTPException(400, f"Invalid period (YYYY-MM expected): {period!r}")


def _ctx(client: str | None = None) -> ExecutionContext:
    """ExecutionContext — client_id 채워서 tool 들이 동적 분기 가능 (Step 5, 2026-05-27)."""
    return ExecutionContext(session_id="api", plan_id="dashboard1", client_id=client)


async def _cached_or_run(
    *,
    client: str,
    layer: Layer,
    cache_key: str,
    tool_name: str,
    tool_cls: Type[BaseTool],
    tool_params: dict[str, Any],
    output_model: Type[BaseModel],
) -> BaseModel:
    """storage hit → model_validate(loaded). miss → tool 실행 → save → validate.

    Step 5 (2026-05-27): client 인자 추가. tool params 에 자동 주입 + ExecutionContext.client_id.
    단계 2 (2026-05-29): 캐시가 **client 별 경로**(data/{client}/{layer})로 분리 — storage.exists/load
    에 client 전달. clumi=정상, 데이터 부족 client(blooming 등)=miss→재계산→raw 없어 에러(의도).
    """
    storage = get_storage()
    if storage.exists(layer, cache_key, client=client):
        loaded = storage.load(layer, cache_key, client=client)
        logger.info("cache hit", layer=layer, key=cache_key, client=client)
        return output_model.model_validate(loaded)
    logger.info("cache miss → exec",
                layer=layer, key=cache_key, tool=tool_name, client=client)
    spec = get_registry().get(tool_name)
    tool = tool_cls(spec)
    full_params = {"client": client, **tool_params}
    result = await tool.execute(full_params, _ctx(client))
    # ②-b expand: tool 이 저장 안 했으면 진입점이 저장 (저장 권한 = 진입점/data layer).
    # 현재는 tool self-save 가 남아 exists=True → skip(무해). contract(self-save 제거) 후 활성화.
    if isinstance(result, dict) and not storage.exists(layer, cache_key, client=client):
        clean = {k: v for k, v in result.items() if not k.startswith("_")}
        storage.save(layer, cache_key, clean, meta=result.get("_meta"), client=client)
    return output_model.model_validate(result)


# =========================================================================
# Overview — /dashboard 페이지 (퍼널 사슬 + 일별 ROAS + 월목표) 조립 (2026-06-09)
# 데이터 전부 Postgres 경유 (파이프라인 → workspace/datasource). 목표=marketing_targets raw.
# =========================================================================


def _day_roas(r: dict) -> float:
    cost = float(r.get("ad_cost") or 0)
    rev = float(r.get("conversion_revenue") or 0)
    return round(rev / cost * 100, 1) if cost else 0.0


@router.get("/overview", summary="대시보드(/dashboard) 조립 — 퍼널·ROAS·일별·목표 (Postgres)")
async def get_overview(
    period: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> dict[str, Any]:
    """퍼널(노출/클릭/전환)·ROAS/AOV·일별ROAS·월목표를 한 번에 반환 (DashboardPage 데이터 source)."""
    _validate_period(period)
    runner = PipelineRunner()
    pool = {"client": client, "period": period}

    async def _run(name: str) -> dict:
        try:
            r = await runner.run(load_pipeline(name), pool)
            return (r.output or {}) if r.status == "completed" else {}
        except Exception as e:  # noqa: BLE001
            logger.warning("overview pipeline failed", name=name, error=str(e))
            return {}

    funnel = await _run("trend_kpi_impressions")
    aov = await _run("dashboard1_kpi_aov")
    daily_out = await _run("dashboard_v1_daily_performance_line")

    imp = int(funnel.get("total_impressions") or 0)
    clk = int(funnel.get("total_clicks") or 0)
    cnv = int(funnel.get("total_conversions") or 0)
    ad_cost = float(funnel.get("total_ad_cost") or 0)
    daily_rows = daily_out.get("rows") or []
    conv_rev = sum(float(r.get("conversion_revenue") or 0) for r in daily_rows)
    # ROAS = 광고성과 기준(전환매출÷광고비) — 일별 라인·퍼널과 동일 기준으로 통일.
    # (dashboard1_kpi_roas 의 653%는 전체매출÷마케팅비 = 다른 정의 → 월간결산용)
    ad_roas = round(conv_rev / ad_cost * 100, 1) if ad_cost else 0.0

    # 월목표 (marketing_targets raw, Postgres) — 해당 period 행
    targets: dict[str, Any] = {}
    try:
        df = get_default_data_source().get(client, "marketing_targets")
        match = df[df["period"].astype(str) == period]
        if len(match):
            targets = {
                k: (float(v) if v is not None else None)
                for k, v in match.iloc[0].to_dict().items()
                if k != "period"
            }
    except Exception as e:  # noqa: BLE001
        logger.warning("overview targets load failed", client=client, error=str(e))

    return {
        "client": client,
        "period": period,
        "funnel": {
            "impressions": imp,
            "clicks": clk,
            "conversions": cnv,
            "conversion_revenue": round(conv_rev),
        },
        "ratios": {
            "ctr": round(clk / imp * 100, 2) if imp else 0.0,
            "cvr": round(cnv / clk * 100, 2) if clk else 0.0,
            "aov": round(float(aov.get("aov") or 0)),
            "roas": ad_roas,  # 광고성과 ROAS(전환매출÷광고비), 일별 라인과 동일 기준
        },
        "daily": [{"date": r.get("date"), "roas": _day_roas(r)} for r in daily_rows],
        "targets": targets,
    }


# =========================================================================
# Cost Overview — /cost 페이지 (KPI + 채널비중 + 키워드 ROI 표) 조립 (2026-06-09)
# =========================================================================


def _kw_row(r: dict) -> dict:
    """cost_table_keyword_top12(T07) 행 → 키워드 표 모양. cpa 유도, qs←quality_score."""
    cost = int(r.get("ad_cost") or 0)
    conv = int(r.get("conversions") or 0)
    return {
        "keyword": r.get("keyword"),
        "channel": r.get("channel"),
        "cost": cost,
        "conv": conv,
        "cpa": round(cost / conv) if conv else 0,
        "roas": float(r.get("roas") or 0),
        "qs": int(r.get("quality_score") or 0),
    }


@router.get("/cost-overview", summary="비용(/cost) 조립 — KPI·채널비중·키워드표 (Postgres)")
async def get_cost_overview(
    period: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> dict[str, Any]:
    """예산/집행률·키워드평균ROAS·채널 예산비중·키워드 ROI Top12 (CostPage 데이터 source)."""
    _validate_period(period)
    runner = PipelineRunner()
    pool = {"client": client, "period": period}

    async def _run(name: str) -> dict:
        try:
            r = await runner.run(load_pipeline(name), pool)
            return (r.output or {}) if r.status == "completed" else {}
        except Exception as e:  # noqa: BLE001
            logger.warning("cost-overview pipeline failed", name=name, error=str(e))
            return {}

    budget = await _run("cost_kpi_budget_total")       # total_budget, avg_exec_rate
    kw = await _run("cost_kpi_keyword_metrics")         # avg_roas, keyword_count
    channel = await _run("cost_pie_channel_share")      # rows[{channel, budget, share}], total_budget
    table = await _run("cost_table_keyword_top12")      # rows[...]

    return {
        "client": client,
        "period": period,
        "kpi": {
            "total_budget": int(budget.get("total_budget") or 0),
            "avg_exec_rate": round(float(budget.get("avg_exec_rate") or 0), 1),
            "avg_roas": round(float(kw.get("avg_roas") or 0), 1),
            "keyword_count": int(kw.get("keyword_count") or 0),
        },
        "channels": [
            {
                "channel": r.get("channel"),
                "budget": int(r.get("budget") or 0),
                "share": round(float(r.get("share") or 0), 1),
            }
            for r in (channel.get("rows") or [])
        ],
        "keywords": [_kw_row(r) for r in (table.get("rows") or [])],
        # 캠페인별 예산 페이싱 제거 (A-5.3, 오너 결정): 기획예산(campaigns)↔실플랫폼 campaign_id
        # 크로스워크 부재로 canonical 재현 불가(daily_performance.csv가 가짜ID로 위조했던 조인).
        # 크로스워크 생기면 복원. 프론트 CostPage pacing 섹션은 ③에서 정리.
        "pacing": [],
    }


def _route_ctx(client: str) -> ExecutionContext:
    """라우트에서 canonical_translator(self.fetch) 호출용 최소 컨텍스트 (A-5.3)."""
    return ExecutionContext(session_id="route", plan_id="route", client_id=client)


# =========================================================================
# Channel Overview — /channel 페이지 (채널 비교 + 전환 퍼널) 조립 (2026-06-09)
# =========================================================================


@router.get("/channel-overview", summary="채널(/channel) 조립 — 채널비교·스파크라인·목표·퍼널 (Postgres)")
async def get_channel_overview(
    period: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> dict[str, Any]:
    """채널별 ROAS/CPA/전환(T05) + 일별 ROAS 스파크라인 + 목표(channel_targets) + 3단계 퍼널(C06)."""
    _validate_period(period)
    runner = PipelineRunner()
    pool = {"client": client, "period": period}

    async def _run(name: str) -> dict:
        try:
            r = await runner.run(load_pipeline(name), pool)
            return (r.output or {}) if r.status == "completed" else {}
        except Exception as e:  # noqa: BLE001
            logger.warning("channel-overview pipeline failed", name=name, error=str(e))
            return {}

    detail = await _run("channel_table_detailed")   # rows[per channel]
    funnel = await _run("channel_funnel")           # rows[노출/클릭/전환]

    ds = get_default_data_source()
    # 스파크라인 — 채널×일자 roas (canonical AD, A-5.3). canonical엔 행단위 roas 없음 → 일자별 rev/cost 재계산(배수).
    spark: dict[str, list] = {}
    try:
        rows = await load_canonical_ad_rows(_route_ctx(client), period)
        by_cd: dict[str, dict[str, dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: {"cost": 0, "rev": 0}))
        for r in rows:
            cd = by_cd[r["channel"]][r["date"]]
            cd["cost"] += r["ad_cost"]
            cd["rev"] += r["conversion_revenue"]
        for ch, dates in by_cd.items():
            spark[ch] = [round(dates[d]["rev"] / dates[d]["cost"], 2) if dates[d]["cost"] else 0.0
                         for d in sorted(dates)]
    except Exception as e:  # noqa: BLE001
        logger.warning("channel spark failed", error=str(e))
    # 목표 — channel_targets
    tgt: dict[str, dict] = {}
    try:
        tdf = ds.get(client, "channel_targets")
        tdf = tdf[tdf["period"].astype(str) == period]
        for _, r in tdf.iterrows():
            tgt[str(r["channel"])] = {
                "target_roas": float(r["target_roas"]),
                "target_cpa": float(r["target_cpa"]),
            }
    except Exception as e:  # noqa: BLE001
        logger.warning("channel targets failed", error=str(e))

    channels = []
    for row in (detail.get("rows") or []):
        ch = str(row.get("channel"))
        t = tgt.get(ch, {})
        channels.append({
            "channel": ch,
            "roas": round(float(row.get("roas") or 0), 1),
            "cpa": int(row.get("cpa") or 0),
            "conversions": int(row.get("conversions") or 0),
            "spark": spark.get(ch, []),
            "target_roas": t.get("target_roas"),
            "target_cpa": t.get("target_cpa"),
        })

    return {
        "client": client,
        "period": period,
        "channels": channels,
        "funnel": [
            {"label": r.get("stage"), "value": int(r.get("value") or 0)}
            for r in (funnel.get("rows") or [])
        ],
    }


# =========================================================================
# Trend Overview — /trend 페이지 (일별 시계열) 조립 (2026-06-09)
# =========================================================================


@router.get("/trend-overview", summary="트렌드(/trend) 조립 — 일별 노출·전환·ROAS 시계열 (Postgres)")
async def get_trend_overview(
    period: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> dict[str, Any]:
    """일별 노출/클릭/전환/ROAS(daily_performance 날짜 집계) + 목표선·BE선(marketing_targets)."""
    _validate_period(period)
    ds = get_default_data_source()
    series: list[dict] = []
    try:
        rows = await load_canonical_ad_rows(_route_ctx(client), period)  # A-5.3 canonical AD 집계
        by_date: dict[str, dict[str, int]] = defaultdict(
            lambda: {"impressions": 0, "clicks": 0, "conversions": 0, "ad_cost": 0, "conversion_revenue": 0})
        for r in rows:
            a = by_date[r["date"]]
            for f in ("impressions", "clicks", "conversions", "ad_cost", "conversion_revenue"):
                a[f] += r[f]
        for d in sorted(by_date):
            a = by_date[d]
            series.append({
                "date": d,
                "impressions": a["impressions"],
                "clicks": a["clicks"],
                "conversions": a["conversions"],
                "roas": round(a["conversion_revenue"] / a["ad_cost"], 2) if a["ad_cost"] else 0.0,  # 배수
            })
    except Exception as e:  # noqa: BLE001
        logger.warning("trend daily failed", client=client, error=str(e))

    target_roas = None
    breakeven_roas = None
    try:
        t = ds.get(client, "marketing_targets")
        tm = t[t["period"].astype(str) == period]
        if len(tm):
            target_roas = float(tm.iloc[0]["target_roas"])
            breakeven_roas = float(tm.iloc[0]["breakeven_roas"])
    except Exception as e:  # noqa: BLE001
        logger.warning("trend targets failed", client=client, error=str(e))

    return {
        "client": client,
        "period": period,
        "daily": series,
        "target_roas": target_roas,
        "breakeven_roas": breakeven_roas,
    }


# =========================================================================
# Creative Overview — /creatives 페이지 (소재 표) 조립 (2026-06-09)
# =========================================================================

# 피로 임계 — frequency 이상이면 노출 피로(표준 광고 휴리스틱). data 분포에 맞춰 2/12 플래그.
_FATIGUE_FREQ = 3.5


@router.get("/creative-overview", summary="소재(/creatives) 조립 — 소재별 성과 표 (Postgres)")
async def get_creative_overview(
    period: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> dict[str, Any]:
    """소재별 CTR/CVR/ROAS/Freq(creatives raw) + 피로 플래그(frequency≥3.5 유도)."""
    _validate_period(period)
    ds = get_default_data_source()
    creatives: list[dict] = []
    try:
        df = ds.get(client, "creatives")
        for _, r in df.iterrows():
            freq = float(r["frequency"])
            creatives.append({
                "id": str(r["creative_id"]),
                "name": str(r["name"]),
                "channel": str(r["channel"]),
                "ctr": round(float(r["ctr"]), 2),
                "cvr": round(float(r["cvr"]), 2),
                "roas": round(float(r["roas"]), 1),
                "frequency": round(freq, 1),
                "fatigue": freq >= _FATIGUE_FREQ,
            })
    except Exception as e:  # noqa: BLE001
        logger.warning("creative-overview failed", client=client, error=str(e))

    return {"client": client, "period": period, "creatives": creatives}


# =========================================================================
# Section 1. KPI 9
# =========================================================================


@router.get("/kpi/revenue", response_model=RevenueOutput, summary="K-1 매출")
async def get_kpi_revenue(period: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> RevenueOutput:
    """methodology §S001 — 활성주문 payment_amount 합 (4월 정답 119,539,660)."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S001_revenue_total_{period}.json",
        tool_name="revenue_total",
        tool_cls=RevenueTotal,
        tool_params={"period": period},
        output_model=RevenueOutput,
    )


@router.get("/kpi/ad-cost", response_model=AdCostOutput, summary="K-2 마케팅비")
async def get_kpi_ad_cost(period: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> AdCostOutput:
    """methodology §S003 / 정제 5 — 광고비 합산 (4월 정답 26,806,923 — 가 결정 A-5.2 google 포함; §S003 원안 5매체 18,306,923)."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="normalized",
        cache_key=f"ad_cost_total_{period}.json",
        tool_name="ad_cost_total",
        tool_cls=AdCostTotal,
        tool_params={"period": period},
        output_model=AdCostOutput,
    )


@router.get("/kpi/roas", response_model=RoasOutput, summary="K-3 전체 ROAS")
async def get_kpi_roas(period: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> RoasOutput:
    """methodology §S004 — 매출/마케팅비 (4월 정답 4.46 — 가 결정 A-5.2 google 포함; §S004 원안 6.53)."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S004_roas_overall_{period}.json",
        tool_name="roas_overall",
        tool_cls=RoasOverall,
        tool_params={"period": period},
        output_model=RoasOutput,
    )


@router.get("/kpi/cac", response_model=CacOutput, summary="K-4 전체 CAC")
async def get_kpi_cac(period: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> CacOutput:
    """methodology §S032 — 마케팅비/신규회원 (4월 정답 44,678 — 가 결정 A-5.2 google 포함; §S032 원안 30,512)."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S032_cac_overall_{period}.json",
        tool_name="cac_overall",
        tool_cls=CacOverall,
        tool_params={"period": period},
        output_model=CacOutput,
    )


@router.get("/kpi/promotion-revenue", response_model=PromoRevenueOutput,
            summary="K-5 프로모션 매출")
async def get_kpi_promotion_revenue(
    period: str = Query(..., examples=["2026-04"]),

    client: str = Query(..., description="회사 식별자"),
) -> PromoRevenueOutput:
    """methodology §S002 — 활성 + promotion_code != NULL (4월 정답 43,400,360 · 36.3%)."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S002_promotion_revenue_{period}.json",
        tool_name="promotion_revenue",
        tool_cls=PromotionRevenue,
        tool_params={"period": period},
        output_model=PromoRevenueOutput,
    )


@router.get("/kpi/promotion-roas", response_model=PromoRoasOutput,
            summary="K-6 프로모션 ROAS")
async def get_kpi_promotion_roas(
    period: str = Query(..., examples=["2026-04"]),

    client: str = Query(..., description="회사 식별자"),
) -> PromoRoasOutput:
    """methodology §S005 — 프모매출/마케팅비 (4월 정답 1.62 — 가 결정 A-5.2 google 포함; §S005 원안 2.37)."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S005_promotion_roas_{period}.json",
        tool_name="promotion_roas",
        tool_cls=PromotionRoas,
        tool_params={"period": period},
        output_model=PromoRoasOutput,
    )


@router.get("/kpi/new-members", response_model=NewMembersOutput, summary="K-7 신규 회원")
async def get_kpi_new_members(
    period: str = Query(..., examples=["2026-04"]),

    client: str = Query(..., description="회사 식별자"),
) -> NewMembersOutput:
    """methodology §S069 — customers.signup_date prefix (4월 정답 600)."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S069_new_members_{period}.json",
        tool_name="new_members_monthly",
        tool_cls=NewMembersMonthly,
        tool_params={"period": period},
        output_model=NewMembersOutput,
    )


@router.get("/kpi/aov", response_model=AovOutput, summary="K-8 객단가")
async def get_kpi_aov(period: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> AovOutput:
    """methodology §S048 — 매출/주문수 (4월 정답 62,293)."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S048_aov_{period}.json",
        tool_name="aov_monthly",
        tool_cls=AovMonthly,
        tool_params={"period": period},
        output_model=AovOutput,
    )


@router.get("/kpi/signup-conversion", response_model=SignupConversionOutput,
            summary="K-9 가입 전환율")
async def get_kpi_signup_conversion(
    period: str = Query(..., examples=["2026-04"]),

    client: str = Query(..., description="회사 식별자"),
) -> SignupConversionOutput:
    """methodology §S067 — 신규/세션 (4월 정답 2.50%)."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S067_signup_conversion_{period}.json",
        tool_name="signup_conversion",
        tool_cls=SignupConversion,
        tool_params={"period": period},
        output_model=SignupConversionOutput,
    )


# =========================================================================
# Section 2. MoM 4 (4월 vs 3월)
# =========================================================================


@router.get("/mom/revenue", response_model=MomRevenueOutput, summary="M-1 매출 MoM")
async def get_mom_revenue(
    a: str = Query(..., examples=["2026-03"], description="기준 월 (전월)"),
    b: str = Query(..., examples=["2026-04"], description="비교 월"),
    client: str = Query(..., description="회사 식별자"),
) -> MomRevenueOutput:
    """methodology §S001 MoM — 정답 +50.5%."""
    _validate_period(a)
    _validate_period(b)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S001mom_revenue_{a}_to_{b}.json",
        tool_name="mom_revenue",
        tool_cls=MomRevenue,
        tool_params={"period_a": a, "period_b": b},
        output_model=MomRevenueOutput,
    )


@router.get("/mom/repurchase", response_model=RepurchaseMomOutput,
            summary="M-3·M-4·B-2·B-3 재구매율 MoM")
async def get_mom_repurchase(
    a: str = Query(..., examples=["2026-03"]),
    b: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> RepurchaseMomOutput:
    """methodology §S028 MoM — existing +19.2% / new +1.4% / rate +2.8%p."""
    _validate_period(a)
    _validate_period(b)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S028mom_repurchase_{a}_to_{b}.json",
        tool_name="repurchase_mom",
        tool_cls=RepurchaseMom,
        tool_params={"period_a": a, "period_b": b},
        output_model=RepurchaseMomOutput,
    )


@router.get("/mom/aov", response_model=AovMomOutput, summary="M-2 주문·객단가 MoM")
async def get_mom_aov(
    a: str = Query(..., examples=["2026-03"]),
    b: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> AovMomOutput:
    """methodology §S048 MoM — orders +42.6% / aov +5.6%."""
    _validate_period(a)
    _validate_period(b)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S048mom_aov_{a}_to_{b}.json",
        tool_name="aov_mom",
        tool_cls=AovMom,
        tool_params={"period_a": a, "period_b": b},
        output_model=AovMomOutput,
    )


@router.get("/mom/new-members", response_model=NewMembersMomOutput,
            summary="B-4 신규 가입 MoM")
async def get_mom_new_members(
    a: str = Query(..., examples=["2026-03"]),
    b: str = Query(..., examples=["2026-04"]),
    client: str = Query(..., description="회사 식별자"),
) -> NewMembersMomOutput:
    """methodology §S069 MoM — 정답 601→600 = -0.2%."""
    _validate_period(a)
    _validate_period(b)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S069mom_new_members_{a}_to_{b}.json",
        tool_name="new_members_mom",
        tool_cls=NewMembersMom,
        tool_params={"period_a": a, "period_b": b},
        output_model=NewMembersMomOutput,
    )


# =========================================================================
# Section 3-8. Segment 7
# =========================================================================


@router.get("/segment/grade", response_model=GradeRevenueOutput, summary="L-2 등급별 회원·매출")
async def get_segment_grade(
    period: str = Query(..., examples=["2026-04"]),

    client: str = Query(..., description="회사 식별자"),
) -> GradeRevenueOutput:
    """methodology §S046 — SILVER 65,757,080 · WELCOME 74.5%."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S046_grade_revenue_{period}.json",
        tool_name="grade_revenue",
        tool_cls=GradeRevenue,
        tool_params={"period": period},
        output_model=GradeRevenueOutput,
    )


@router.get("/segment/grade-timeseries", response_model=GradeTimeseriesOutput,
            summary="L-1 등급 회원수 시계열 (4시점)")
async def get_segment_grade_timeseries(client: str = Query(..., description="회사 식별자")) -> GradeTimeseriesOutput:
    """methodology §S045 — 6,680 → 7,299 → 7,900 → 8,500 (period-less)."""
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key="S045_grade_timeseries.json",
        tool_name="grade_timeseries",
        tool_cls=GradeTimeseries,
        tool_params={},
        output_model=GradeTimeseriesOutput,
    )


@router.get("/segment/age", response_model=AgeSegmentOutput,
            summary="G-1·G-2 연령 5세 bucket 분포")
async def get_segment_age(client: str = Query(..., description="회사 식별자")) -> AgeSegmentOutput:
    """methodology §S037 — 11 bucket + 35-44 합 2,884 (period-less)."""
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key="S037_age_segment.json",
        tool_name="age_segment",
        tool_cls=AgeSegment,
        tool_params={},
        output_model=AgeSegmentOutput,
    )


@router.get("/segment/category", response_model=CategoryDistOutput,
            summary="T-1 카테고리 5 균등 분배")
async def get_segment_category(
    period: str = Query(..., examples=["2026-04"]),

    client: str = Query(..., description="회사 식별자"),
) -> CategoryDistOutput:
    """methodology §정제 7 옵션 A — 스킨케어 67,652,216 · 클렌징 19,126,163."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="normalized",
        cache_key=f"category_distributed_{period}.json",
        tool_name="category_multi_distributor",
        tool_cls=CategoryMultiDistributor,
        tool_params={"period": period, "method": "equal"},
        output_model=CategoryDistOutput,
    )


@router.get("/segment/channel", response_model=ChannelDistOutput,
            summary="C-1 채널 분포 (10채널 + 7 그룹)")
async def get_segment_channel(
    period: str = Query(..., examples=["2026-04"]),

    client: str = Query(..., description="회사 식별자"),
) -> ChannelDistOutput:
    """methodology §정제 4 — Naver 530 · Unknown 481 · Meta 388 · ..."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="normalized",
        cache_key=f"channel_normalized_{period}.json",
        tool_name="channel_attribution_normalizer",
        tool_cls=ChannelAttributionNormalizer,
        tool_params={"period": period},
        output_model=ChannelDistOutput,
    )


@router.get("/segment/member-guest", response_model=MemberGuestOutput,
            summary="B-1 회원/비회원 분리")
async def get_segment_member_guest(
    period: str = Query(..., examples=["2026-04"]),

    client: str = Query(..., description="회사 식별자"),
) -> MemberGuestOutput:
    """methodology §정제 10 — 회원 1,779 / 비회원 140."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="normalized",
        cache_key=f"orders_split_{period}.json",
        tool_name="member_guest_stats",
        tool_cls=MemberGuestStats,
        tool_params={"period": period},
        output_model=MemberGuestOutput,
    )


@router.get("/segment/unknown-share", response_model=UnknownShareOutput,
            summary="C-2 알수없음 매출비중")
async def get_segment_unknown_share(
    period: str = Query(..., examples=["2026-04"]),

    client: str = Query(..., description="회사 식별자"),
) -> UnknownShareOutput:
    """methodology §S054 — unknown 매출/총매출 (4월 정답 39.8%)."""
    _validate_period(period)
    return await _cached_or_run(
        client=client,
        layer="computed",
        cache_key=f"S054_unknown_share_{period}.json",
        tool_name="unknown_revenue_share",
        tool_cls=UnknownRevenueShare,
        tool_params={"period": period},
        output_model=UnknownShareOutput,
    )


# ─────────────────────────────────────────────────────────────────
# Catalog endpoint — frontend 가 spec 가져갈 때 (Step 7 tooltip 용 — 선택)
# ─────────────────────────────────────────────────────────────────


@router.get("/_catalog", summary="20 endpoint 메타 + tool 매핑 (디버그)")
async def get_catalog() -> dict[str, Any]:
    """20 endpoint 의 path · tool · 정답값 — frontend tooltip 빌드 보조."""
    return {
        "endpoints": [
            {"path": r.path, "method": list(r.methods)[0], "tool": r.summary}
            for r in router.routes
            if hasattr(r, "path") and r.path != "/api/dashboard1/_catalog"
        ],
        "count": len(router.routes) - 1,
    }
