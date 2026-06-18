"""Canonical Translator — raw → normalized canonical 행(소스별 테이블) + computed + lineage.

피봇 §3.2 REPLACE 의 심장: 산발 하드코딩 normalizer(ad_cost_helper·format_normalizer)를
**단일 contract-driven translator** 로 흡수. data_pilot 프로토타입을 production BaseTool 로 포팅.

★ 2단계 산출 (ADR-032 / 세부05):
  1. execute() = *순수* — 소스별 **행 리스트**(PK 그룹핑) + 채널 sums + computed(MER) 반환. DB 무관.
  2. persist_normalized() = 행 리스트를 `{source}_normalized` 정형 테이블로 적재(write_relational_table, UPSERT).

검증 명제: 행을 펼쳐도 Σ=채널합 보존(세부05 §1 raw 실측: meta90·naver_sa1680→180·advoost90·google180·kakao2·talktalk2·orders1919).
★ 가 결정 A-5.2(2026-06-17): google 광고 매체 포함 re-baseline — 총마케팅비 18,306,923 → 26,806,923 · MER 6.53 → 4.46.

데이터 접근: BaseTool.fetch(source_id)=ds.get(client,source_id). raw 직접 로드 금지.
Status: partial — DB제작 Step3~6 + google 피봇 (2026-06-17). 7 normalized + 6 computed + blended_computed(google 포함).
  잔여: acquisition_mer·blended_platform_roas_x(measure16/P2).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.data_pg_util import connect, write_relational_table
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_float, safe_int
from app.dream_agent.tools.shared.order_helper import is_active_order  # 활성주문 SSOT (ADR-032 D3)

logger = get_logger(__name__)

PERIOD_DEFAULT = "2026-04"
AD_CHANNELS = ("meta", "naver_sa", "advoost", "google")  # 광고 매체 (C6.3: 메시징 분리 / 가 결정 A-5.2: google 포함)
MSG_CHANNELS = ("kakao", "talktalk")                  # 메시징 (msg_ measure)
_DEVICE = {"P": "desktop", "M": "mobile"}             # naver M/P 디코딩 (ERD)


def _to_date(v: Any) -> str | None:
    """report_date 파생 — ISO date 그대로 / datetime은 날짜파트 앞 10자 ('YYYY-MM-DDThh..'→'YYYY-MM-DD')."""
    if v is None:
        return None
    s = str(v).strip()
    return s[:10] if len(s) >= 10 else None


def _meta_action_extract(actions: Any, action_type: str = "omni_purchase") -> int:
    """Meta actions[]/action_values[] 에서 action_type 필터 → value. 미필터=silent-0(C6.2). 없으면 0."""
    if not isinstance(actions, list):
        return 0
    for a in actions:
        if isinstance(a, dict) and a.get("action_type") == action_type:
            return safe_int(a.get("value"))
    return 0


# ── measure 추출 (row → {canonical: (raw_repr, value, transform)}) — contract sources 미러 ──

def _m_meta(row: dict) -> dict:
    return {
        "ad_cost_krw":            (row.get("spend"),              safe_int(row.get("spend")),              "cast_int"),
        "impressions":            (row.get("impressions"),        safe_int(row.get("impressions")),        "cast_int"),
        "clicks":                 (row.get("clicks"),             safe_int(row.get("clicks")),             "cast_int"),
        "link_clicks":            (row.get("inline_link_clicks"), safe_int(row.get("inline_link_clicks")), "cast_int (Meta CTR 분자)"),
        "conversion_count":       ("actions[omni]",               _meta_action_extract(row.get("actions")),       "meta_action_extract"),
        "conversion_revenue_krw": ("action_values[omni]",         _meta_action_extract(row.get("action_values")), "meta_action_extract"),
        "paid_reach":             (row.get("reach"),              safe_int(row.get("reach")),              "cast_int"),
        "impression_frequency":   (row.get("frequency"),          safe_float(row.get("frequency")),        "cast_float"),
    }


def _m_naver_sa(row: dict) -> dict:
    return {
        "ad_cost_krw":            (row.get("salesAmt"), safe_int(row.get("salesAmt")), "cast_int (salesAmt=비용 C6.1)"),
        "conversion_revenue_krw": (row.get("convAmt"),  safe_int(row.get("convAmt")),  "cast_int (convAmt=매출 C6.1)"),
        "conversion_count":       (row.get("ccnt"),     safe_int(row.get("ccnt")),     "cast_int (ccnt=전환수)"),
        "impressions":            (row.get("impCnt"),   safe_int(row.get("impCnt")),   "cast_int"),
        "clicks":                 (row.get("clkCnt"),   safe_int(row.get("clkCnt")),   "cast_int"),
    }


def _m_advoost(row: dict) -> dict:
    return {
        "ad_cost_krw":            (row.get("cost"),                       safe_int(row.get("cost")),                       "cast_int"),
        "conversion_revenue_krw": (row.get("conversion_value"),          safe_int(row.get("conversion_value")),          "cast_int"),
        "conversion_count":       (row.get("click_through_conversions"), safe_int(row.get("click_through_conversions")), "cast_int (CT only)"),
        "vt_conversion_count":    (row.get("view_through_conversions"),  safe_int(row.get("view_through_conversions")),  "cast_int (VT — CT와 분리)"),
        "impressions":            (row.get("impressions"),               safe_int(row.get("impressions")),               "cast_int"),
        "clicks":                 (row.get("clicks"),                    safe_int(row.get("clicks")),                    "cast_int"),
    }


def _m_google(row: dict) -> dict:
    # google_ads_performance.csv — flat CSV, 값 KRW(mock). advoost 와 동형(광고 매체, 가 결정 A-5.2).
    return {
        "ad_cost_krw":            (row.get("cost"),             safe_int(row.get("cost")),             "cast_int"),
        "conversion_revenue_krw": (row.get("conversion_value"), safe_int(row.get("conversion_value")), "cast_int"),
        "conversion_count":       (row.get("conversions"),      safe_int(row.get("conversions")),      "cast_int"),
        "impressions":            (row.get("impressions"),      safe_int(row.get("impressions")),      "cast_int"),
        "clicks":                 (row.get("clicks"),           safe_int(row.get("clicks")),           "cast_int"),
    }


def _make_m_msg(target_field: str):
    """kakao/talktalk — campaigns[].summary (C6.3 메시징 msg_ measure). target 필드만 소스차."""
    def _m(row: dict) -> dict:
        s = row.get("summary") or {}
        return {
            "msg_cost_krw":               (s.get("total_cost_krw"),        safe_int(s.get("total_cost_krw")),        "cast_int (메시징비)"),
            "msg_target_count":           (s.get(target_field),            safe_int(s.get(target_field)),            f"cast_int ({target_field})"),
            "msg_open_count":             (s.get("open_count"),            safe_int(s.get("open_count")),            "cast_int"),
            "msg_click_count":            (s.get("click_count"),           safe_int(s.get("click_count")),           "cast_int"),
            "msg_conversion_count":       (s.get("conversion_count"),      safe_int(s.get("conversion_count")),      "cast_int"),
            "msg_conversion_revenue_krw": (s.get("conversion_amount_krw"), safe_int(s.get("conversion_amount_krw")), "cast_int"),
            "msg_avg_order_value_krw":    (s.get("avg_order_value"),       safe_int(s.get("avg_order_value")),       "cast_int (채널보고값 M12)"),
        }
    return _m


_m_kakao = _make_m_msg("target_recipients")
_m_talktalk = _make_m_msg("target_friends")


def _m_orders(row: dict) -> dict:
    return {"order_revenue_krw": (row.get("payment_amount"), safe_int(row.get("payment_amount")), "cast_int")}


# ── 소스별 spec (keys=dim/PK 추출, pk_cols, col_types=ERD SSOT, table) — 세부05 §2 ──
_INT, _FLT, _TXT, _DATE, _JSONB = "int", "float", "text", "date", "jsonb"

_CHANNELS = [
    {"channel": "meta", "source_id": "meta_ads_performance", "rows_path": "data", "period_col": "date_start",
     "measures": _m_meta,
     "keys": lambda r: {"campaign_id": r.get("campaign_id"), "report_date": _to_date(r.get("date_start")),
                        "channel": "meta", "campaign_name": r.get("campaign_name")},
     "pk_cols": ["campaign_id", "report_date"],
     "col_types": {"campaign_id": _TXT, "report_date": _DATE, "channel": _TXT, "campaign_name": _TXT,
                   "ad_cost_krw": _INT, "impressions": _INT, "clicks": _INT, "link_clicks": _INT,
                   "conversion_count": _INT, "conversion_revenue_krw": _INT, "paid_reach": _INT,
                   "impression_frequency": _FLT, "_lineage": _JSONB}},

    {"channel": "naver_sa", "source_id": "naver_searchad", "rows_path": "data", "period_col": "statDt",
     "measures": _m_naver_sa,
     "keys": lambda r: {"campaign_id": r.get("nccCampaignId"),
                        "device_type": _DEVICE.get(str(r.get("device")), r.get("device")),
                        "report_date": _to_date(r.get("statDt")), "channel": "naver_sa"},
     "pk_cols": ["campaign_id", "device_type", "report_date"],
     "col_types": {"campaign_id": _TXT, "device_type": _TXT, "report_date": _DATE, "channel": _TXT,
                   "ad_cost_krw": _INT, "impressions": _INT, "clicks": _INT,
                   "conversion_count": _INT, "conversion_revenue_krw": _INT, "_lineage": _JSONB}},

    {"channel": "advoost", "source_id": "naver_advoost", "rows_path": None, "period_col": "report_date",
     "measures": _m_advoost,
     "keys": lambda r: {"campaign_id": r.get("campaign_id"), "report_date": _to_date(r.get("report_date")),
                        "channel": "advoost"},
     "pk_cols": ["campaign_id", "report_date"],
     "col_types": {"campaign_id": _TXT, "report_date": _DATE, "channel": _TXT,
                   "ad_cost_krw": _INT, "impressions": _INT, "clicks": _INT, "conversion_count": _INT,
                   "vt_conversion_count": _INT, "conversion_revenue_krw": _INT, "_lineage": _JSONB}},

    {"channel": "google", "source_id": "google_ads_performance", "rows_path": None, "period_col": "report_date",
     "measures": _m_google,
     "keys": lambda r: {"campaign_id": r.get("campaign_id"), "report_date": _to_date(r.get("report_date")),
                        "channel": "google", "campaign_name": r.get("campaign_name")},
     "pk_cols": ["campaign_id", "report_date"],
     "col_types": {"campaign_id": _TXT, "report_date": _DATE, "channel": _TXT, "campaign_name": _TXT,
                   "ad_cost_krw": _INT, "impressions": _INT, "clicks": _INT, "conversion_count": _INT,
                   "conversion_revenue_krw": _INT, "_lineage": _JSONB}},

    {"channel": "kakao", "source_id": "kakao_bizmessage", "rows_path": "campaigns", "period_col": None,
     "measures": _m_kakao,
     "keys": lambda r: {"campaign_id": r.get("campaign_id"), "channel": "kakao",
                        "report_date": _to_date(r.get("send_request_date"))},
     "pk_cols": ["campaign_id"],
     "col_types": {"campaign_id": _TXT, "channel": _TXT, "report_date": _DATE,
                   "msg_cost_krw": _INT, "msg_target_count": _INT, "msg_open_count": _INT, "msg_click_count": _INT,
                   "msg_conversion_count": _INT, "msg_conversion_revenue_krw": _INT, "msg_avg_order_value_krw": _INT,
                   "_lineage": _JSONB}},

    {"channel": "talktalk", "source_id": "naver_talktalk", "rows_path": "campaigns", "period_col": None,
     "measures": _m_talktalk,
     "keys": lambda r: {"campaign_id": r.get("campaign_id"), "channel": "talktalk",
                        "report_date": _to_date(r.get("send_request_date"))},
     "pk_cols": ["campaign_id"],
     "col_types": {"campaign_id": _TXT, "channel": _TXT, "report_date": _DATE,
                   "msg_cost_krw": _INT, "msg_target_count": _INT, "msg_open_count": _INT, "msg_click_count": _INT,
                   "msg_conversion_count": _INT, "msg_conversion_revenue_krw": _INT, "msg_avg_order_value_krw": _INT,
                   "_lineage": _JSONB}},
]

# ADR-032 D3: 활성주문 = is_active_order(취소 C계열 전체 제외). ⚠ N00 입금전 포함(매출정의=오너/UX).
_ORDERS = {"channel": "orders", "source_id": "orders", "rows_path": None, "period_col": "order_date",
           "row_filter": lambda r: is_active_order(r.get("order_status")),
           "measures": _m_orders,
           "keys": lambda r: {"order_id": r.get("order_id"), "report_date": _to_date(r.get("order_date")),
                              "channel_group": r.get("channel_attribution"), "member_id": r.get("member_id"),
                              "utm_source": r.get("utm_source"), "utm_medium": r.get("utm_medium"),
                              "utm_campaign": r.get("utm_campaign")},
           "pk_cols": ["order_id"],
           "col_types": {"order_id": _TXT, "report_date": _DATE, "channel_group": _TXT, "member_id": _TXT,
                         "utm_source": _TXT, "utm_medium": _TXT, "utm_campaign": _TXT,
                         "order_revenue_krw": _INT, "_lineage": _JSONB}}

_ALL_SPECS = _CHANNELS + [_ORDERS]


def _to_rows(data: Any, rows_path: str | None) -> list[dict]:
    """ds.get 산출(JSON dict / DataFrame / list) → row dict 목록 통일."""
    if hasattr(data, "to_dict"):           # pandas DataFrame
        return data.to_dict("records")
    if rows_path is not None and isinstance(data, dict):
        return data.get(rows_path, [])
    if isinstance(data, list):
        return data
    return []


# ── computed 파생 (normalized 행 → 소스별 파생지표) — ERD {source}_computed, _compute 공식 행단위 재사용 ──
_AD_COMPUTED_TYPES = {"roas_x": "float", "ctr_pct": "float", "cpc_krw": "int",
                      "cpm_krw": "int", "cvr_pct": "float"}
_MSG_COMPUTED_TYPES = {"msg_roi_pct": "float", "msg_avg_order_value_krw": "int"}


def _computed_ad(row: dict, *, link: bool = False) -> dict:
    """ad normalized 행 → 파생지표. _compute 채널식과 동일 공식, 행단위. meta만 link_ctr_pct(ERD)."""
    cost = row.get("ad_cost_krw", 0) or 0
    rev = row.get("conversion_revenue_krw", 0) or 0
    imp = row.get("impressions", 0) or 0
    clk = row.get("clicks", 0) or 0
    conv = row.get("conversion_count", 0) or 0
    out = {
        "roas_x":  round(rev / cost, 2) if cost else None,
        "ctr_pct": round(clk / imp * 100, 2) if imp else None,
        "cpc_krw": round(cost / clk) if clk else None,
        "cpm_krw": round(cost / imp * 1000) if imp else None,
        "cvr_pct": round(conv / clk * 100, 2) if clk else None,
    }
    if link:   # meta 전용 — link_clicks/imp*100 (ERD meta_computed)
        lc = row.get("link_clicks", 0) or 0
        out["link_ctr_pct"] = round(lc / imp * 100, 2) if imp else None
    return out


def _computed_msg(row: dict) -> dict:
    """msg normalized 행 → 파생지표. ROI≠ROAS(C6.3). AOV=매출/전환수(ERD '재계산' 원칙, normalized=채널보고)."""
    cost = row.get("msg_cost_krw", 0) or 0
    rev = row.get("msg_conversion_revenue_krw", 0) or 0
    conv = row.get("msg_conversion_count", 0) or 0
    return {
        "msg_roi_pct":             round((rev / cost - 1) * 100, 1) if cost else None,
        "msg_avg_order_value_krw": round(rev / conv) if conv else None,
    }


class CanonicalTranslator(BaseTool):
    """단일 contract-driven translator — raw → normalized 행(소스별) + computed + lineage."""

    def _translate(self, ch: dict, context: ExecutionContext, period: str | None) -> dict:
        """채널 raw → PK 그룹핑 행 리스트 + 채널 sums(compute 보존) + 행단위 lineage.

        세부05 §3: filter → keys(dim/PK)·measures → PK 그룹핑(measure 합산) → 행 emit. sums = 채널 총합.
        """
        data = self.fetch(ch["source_id"], context)
        rows = _to_rows(data, ch.get("rows_path"))
        pcol, rfilt = ch.get("period_col"), ch.get("row_filter")
        keys_fn, meas_fn, pk_cols = ch["keys"], ch["measures"], ch["pk_cols"]
        groups: dict[tuple, dict] = {}
        sums: dict[str, float] = {}
        raw_n = 0
        for row in rows:
            if period and pcol and not str(row.get(pcol, "")).startswith(period):
                continue
            if rfilt and not rfilt(row):
                continue
            raw_n += 1
            dims = keys_fn(row)
            pk = tuple(dims[c] for c in pk_cols)
            g = groups.get(pk)
            if g is None:
                g = {**dims, "_lineage": {}}
                groups[pk] = g
            for canon, (raw, val, tname) in meas_fn(row).items():
                if val is None:
                    continue
                g[canon] = g.get(canon, 0) + val
                sums[canon] = sums.get(canon, 0) + val
                g["_lineage"].setdefault(canon, {"source": raw, "transform": tname})
        return {"channel": ch["channel"], "table": f'{ch["source_id"]}_normalized',
                "pk_cols": pk_cols, "col_types": ch["col_types"],
                "rows": list(groups.values()), "row_count": len(groups), "raw_count": raw_n,
                "measures": sums}

    def _compute(self, normalized: dict) -> dict:
        """normalized sums → computed metrics (파생 재계산). ad/msg 분리·MER. (기존 보존)"""
        ad = {c: normalized[c]["measures"] for c in AD_CHANNELS}
        msg = {c: normalized[c]["measures"] for c in MSG_CHANNELS}

        total_ad_cost = sum(m.get("ad_cost_krw", 0) for m in ad.values())
        total_msg_cost = sum(m.get("msg_cost_krw", 0) for m in msg.values())
        total_marketing_cost = total_ad_cost + total_msg_cost

        channel_roas_x = {}
        for c in AD_CHANNELS:
            cost, rev = ad[c].get("ad_cost_krw", 0), ad[c].get("conversion_revenue_krw", 0)
            channel_roas_x[c] = round(rev / cost, 2) if cost else None

        channel_metrics = {}
        for c in AD_CHANNELS:
            m = ad[c]
            imp, clk = m.get("impressions", 0), m.get("clicks", 0)
            cost, conv = m.get("ad_cost_krw", 0), m.get("conversion_count", 0)
            channel_metrics[c] = {
                "ctr_pct": round(clk / imp * 100, 2) if imp else None,
                "cpc_krw": round(cost / clk) if clk else None,
                "cpm_krw": round(cost / imp * 1000) if imp else None,
                "cvr_pct": round(conv / clk * 100, 2) if clk else None,
            }

        msg_roi_pct = {}
        for c in MSG_CHANNELS:
            cost, rev = msg[c].get("msg_cost_krw", 0), msg[c].get("msg_conversion_revenue_krw", 0)
            msg_roi_pct[c] = round((rev / cost - 1) * 100, 1) if cost else None

        total_revenue = normalized["orders"]["measures"].get("order_revenue_krw", 0)
        mer = round(total_revenue / total_marketing_cost, 2) if total_marketing_cost else None
        tacos_pct = round(total_ad_cost / total_revenue * 100, 2) if total_revenue else None

        return {
            "ad_cost_by_channel": {c: ad[c].get("ad_cost_krw", 0) for c in AD_CHANNELS},
            "msg_cost_by_channel": {c: msg[c].get("msg_cost_krw", 0) for c in MSG_CHANNELS},
            "total_ad_cost_krw": total_ad_cost,
            "total_msg_cost_krw": total_msg_cost,
            "total_marketing_cost_krw": total_marketing_cost,
            "channel_roas_x": channel_roas_x,
            "channel_metrics": channel_metrics,
            "msg_roi_pct": msg_roi_pct,
            "tacos_pct": tacos_pct,
            "total_order_revenue_krw": total_revenue,
            "mer": mer,
        }

    def _build_computed(self, normalized: dict) -> dict:
        """normalized 행 → 소스별 computed 행 (ERD {source}_computed). 행단위 파생. orders=제외(blended 분자만).

        PK = normalized와 동일. 컬럼 = pk dims + channel + 파생지표(_computed_ad/msg). _lineage 없음(파생값만).
        """
        out: dict[str, dict] = {}
        for sp in _CHANNELS:                       # commerce(orders)는 computed 없음
            ch = sp["channel"]
            pk = sp["pk_cols"]
            dim_types = {c: sp["col_types"][c] for c in pk}
            dim_types["channel"] = _TXT
            if ch in AD_CHANNELS:
                metric_types = dict(_AD_COMPUTED_TYPES)
                if ch == "meta":
                    metric_types["link_ctr_pct"] = _FLT
                fn = (lambda r, _ch=ch: _computed_ad(r, link=(_ch == "meta")))
            else:                                  # MSG
                metric_types = dict(_MSG_COMPUTED_TYPES)
                fn = _computed_msg
            col_types = {**dim_types, **metric_types}
            rows = []
            for r in normalized[ch]["rows"]:
                row = {c: r.get(c) for c in pk}
                row["channel"] = r.get("channel")
                row.update(fn(r))
                rows.append(row)
            out[ch] = {"table": f'{sp["source_id"]}_computed', "pk_cols": list(pk),
                       "col_types": col_types, "rows": rows}
        return out

    def _build_blended(self, period: str, computed: dict) -> dict:
        """_compute 산출 → blended_computed 1행 (PK=period, layer='blended'). google 포함 26.8M·MER 4.46.

        ⚠ ERD의 acquisition_mer·blended_platform_roas_x = measure16/P2(미산출). 본 step = 계획 §4 6지표.
        """
        row = {
            "period": period,
            "total_ad_cost_krw":        computed["total_ad_cost_krw"],
            "total_msg_cost_krw":       computed["total_msg_cost_krw"],
            "total_marketing_cost_krw": computed["total_marketing_cost_krw"],
            "total_order_revenue_krw":  computed["total_order_revenue_krw"],
            "mer":       computed["mer"],
            "tacos_pct": computed["tacos_pct"],
            "_lineage": {"ad": list(AD_CHANNELS), "msg": list(MSG_CHANNELS), "revenue": "orders",
                         "note": "가 결정 A-5.2: google 포함 re-baseline 26.8M·MER 4.46"},
        }
        return {"table": "blended_computed", "pk_cols": ["period"], "rows": [row],
                "col_types": {"period": _TXT, "total_ad_cost_krw": _INT, "total_msg_cost_krw": _INT,
                              "total_marketing_cost_krw": _INT, "total_order_revenue_krw": _INT,
                              "mer": _FLT, "tacos_pct": _FLT, "_lineage": _JSONB}}

    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        """순수 — 소스별 normalized/computed 행 + blended 1행 + sums 반환. DB 적재는 persist_*()."""
        merged = self.merge_params(params)
        period = merged.get("period") or PERIOD_DEFAULT

        normalized = {sp["channel"]: self._translate(sp, context, period) for sp in _ALL_SPECS}
        computed = self._compute(normalized)
        computed_tables = self._build_computed(normalized)
        blended = self._build_blended(period, computed)

        logger.info("canonical_translator", period=period,
                    total_marketing_cost=computed["total_marketing_cost_krw"], mer=computed["mer"])
        return {
            "period": period,
            "normalized": normalized,          # {channel: {table, pk_cols, col_types, rows[list], measures(sums), ...}}
            "computed": computed,              # 스칼라 집계(MER 등) — _compute, 기존 보존
            "computed_tables": computed_tables,  # {channel: {table, pk_cols, col_types, rows[list]}} 행단위 파생
            "blended": blended,                # {table:'blended_computed', pk_cols:['period'], rows:[1행]}
            "lineage": [{"channel": v["channel"], "canonical": canon, "value": r.get(canon), **info}
                        for v in normalized.values() for r in v["rows"]
                        for canon, info in (r.get("_lineage") or {}).items()][:50],   # 샘플(행단위)
            "_storage": {"layer": "normalized", "key": f"canonical_normalized_{period.replace('/', '_')}.json"},
            "_meta": {"channels": [sp["channel"] for sp in _ALL_SPECS],
                      "status": "DB제작 Step3~6: 6 normalized + 5 computed + blended (google 제외 G5)"},
        }

    def persist_normalized(self, result: dict, client: str) -> dict[str, int]:
        """execute() 결과의 소스별 행을 {source}_normalized 정형 테이블로 적재(UPSERT, DROP 금지).

        ADR-032 D1: write_relational_table(명시 스키마·소스별 PK·_lineage jsonb). 반환 {table: 행수}.
        """
        out: dict[str, int] = {}
        with connect() as conn:
            for v in result["normalized"].values():
                n = write_relational_table(conn, client, v["table"], v["rows"],
                                           pk_cols=v["pk_cols"], col_types=v["col_types"])
                out[v["table"]] = n
                logger.info("persist_normalized", table=v["table"], rows=n, client=client)
        return out

    def persist_computed(self, result: dict, client: str) -> dict[str, int]:
        """execute() 결과의 소스별 파생 행을 {source}_computed 정형 테이블로 적재(UPSERT, DROP 금지)."""
        out: dict[str, int] = {}
        with connect() as conn:
            for v in result["computed_tables"].values():
                n = write_relational_table(conn, client, v["table"], v["rows"],
                                           pk_cols=v["pk_cols"], col_types=v["col_types"])
                out[v["table"]] = n
                logger.info("persist_computed", table=v["table"], rows=n, client=client)
        return out

    def persist_blended(self, result: dict, client: str) -> dict[str, int]:
        """blended_computed 1행(PK=period) UPSERT (layer='blended', ADR-032 D2)."""
        b = result["blended"]
        with connect() as conn:
            n = write_relational_table(conn, client, b["table"], b["rows"],
                                       pk_cols=b["pk_cols"], col_types=b["col_types"])
            logger.info("persist_blended", table=b["table"], rows=n, client=client)
        return {b["table"]: n}

    def persist_all(self, result: dict, client: str) -> dict[str, int]:
        """전 정형 테이블 적재 — normalized → computed → blended (G7 순서: 소스별 전부 → blended)."""
        out = self.persist_normalized(result, client)
        out.update(self.persist_computed(result, client))
        out.update(self.persist_blended(result, client))
        return out
