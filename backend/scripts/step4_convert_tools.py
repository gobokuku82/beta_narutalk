# -*- coding: utf-8 -*-
"""Step 4 일괄 변환 — load_clumi_source → DataSource DI.

Scope: cleaning + metrics + preprocessing/marketing + normalization + comparison
(collection/clumi 21개는 Step 4e 별도)

변환:
  1. `from app.dream_agent.tools.shared.clumi_loader import load_clumi_source` → 제거
  2. `from app.dream_agent.tools.shared.storage import ...` → `from app.workspace import get_default_workspace`
  3. `get_storage()` → `get_default_workspace()`
  4. `load_clumi_source(N)` (직접 숫자) → `self.ds.get(client, "<source_id>")`
  5. `load_clumi_source(CONST)` → 동일 (CONST 라인은 별도 유지, 후 정리)
  6. `aggregate_ad_cost(load_clumi_source, ...)` → `aggregate_ad_cost(self.ds, client, ...)`
  7. tool execute() 안에 `client = merged.get("client", "clumi")` 자동 삽입 (period 다음)

본 스크립트는 idempotent — 이미 변환된 파일은 skip.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app" / "dream_agent" / "tools"

# file_no → source_id (data_sources/file.py 의 DEFAULT_MAPPING 와 일치)
FILE_NO = {
    1: "meta_ads_performance", 2: "meta_ads_by_age", 3: "meta_instagram_inapp",
    4: "naver_searchad", 5: "orders", 6: "customers",
    7: "ga4_traffic_source", 8: "ga4_page_events", 9: "signup_events",
    10: "customer_rfm", 11: "promotions", 12: "category_sales",
    13: "naver_interest_alert", 14: "instagram_engagement",
    15: "naver_advoost", 16: "kakao_bizmessage", 17: "naver_talktalk",
    18: "crm_messages", 19: "household_structure", 20: "ad_change_history",
    21: "grade_history",
}

# 대상 파일 (collection/clumi 제외)
TARGETS = [
    "cleaning/active_orders_filter.py",
    "cleaning/member_metrics_validator.py",
    "cleaning/missing_value_diagnostic.py",
    "metrics/promotion_revenue.py",
    "metrics/promotion_roas.py",
    "metrics/roas_overall.py",
    "metrics/cac_overall.py",
    "metrics/new_members_monthly.py",
    "metrics/aov_monthly.py",
    "metrics/signup_conversion.py",
    "metrics/repurchase_rate_mom.py",
    "metrics/grade_revenue.py",
    "metrics/age_segment.py",
    "metrics/unknown_revenue_share.py",
    "preprocessing/marketing/ad_cost_aggregator.py",
    "preprocessing/marketing/category_multi_distributor.py",
    "preprocessing/marketing/member_guest_splitter.py",
    "preprocessing/marketing/ga4_session_aggregator.py",
    "normalization/channel_attribution_normalizer.py",
    "normalization/grade_system_unifier.py",
    "normalization/kst_timezone_normalizer.py",
    "normalization/utm_normalizer.py",
    "comparison/channel_cac_compare.py",
    "comparison/inapp_ad_ab_compare.py",
    "comparison/grade_timeseries.py",
]

DEFAULT_CLIENT_BLOCK = '\n\nDEFAULT_CLIENT = "clumi"  # POC — Step 5 ExecutionContext.client 로 분기\n'


def find_const_file_no(text: str) -> dict[str, int]:
    """ORDERS_FILE_NO = 5 같은 상수 → {const_name: file_no} 매핑 추출."""
    pattern = re.compile(r"^(\w+_FILE_NO)\s*=\s*(\d+)", re.MULTILINE)
    return {m.group(1): int(m.group(2)) for m in pattern.finditer(text)}


def convert_file(path: Path) -> tuple[bool, str]:
    """단일 파일 변환. (changed, info)."""
    if not path.exists():
        return False, f"NOT FOUND: {path}"

    text = path.read_text(encoding="utf-8")
    orig = text

    # idempotent: 이미 self.ds.get 등 있으면 skip
    if "self.ds.get(" in text and "load_clumi_source" not in text:
        return False, f"SKIP (already converted): {path.name}"

    # 1. import 제거 (load_clumi_source)
    text = re.sub(
        r"from app\.dream_agent\.tools\.shared\.clumi_loader import load_clumi_source\n",
        "",
        text,
    )

    # 2. storage import → workspace
    text = re.sub(
        r"from app\.dream_agent\.tools\.shared\.storage import get_storage",
        "from app.workspace import get_default_workspace",
        text,
    )

    # 3. get_storage() → get_default_workspace()
    text = text.replace("get_storage()", "get_default_workspace()")

    # 4. load_clumi_source(N) — 숫자 직접
    def replace_direct(m):
        n = int(m.group(1))
        sid = FILE_NO.get(n, f"unknown_{n}")
        return f'self.ds.get(client, "{sid}")'

    text = re.sub(r"load_clumi_source\((\d+)\)", replace_direct, text)

    # 5. load_clumi_source(CONST_NAME) — 상수 참조
    const_map = find_const_file_no(orig)  # 변환 전 텍스트에서 추출
    for const_name, n in const_map.items():
        sid = FILE_NO.get(n, f"unknown_{n}")
        text = re.sub(
            rf"load_clumi_source\({re.escape(const_name)}\)",
            f'self.ds.get(client, "{sid}")',
            text,
        )

    # 6. aggregate_ad_cost(load_clumi_source, period=...) → aggregate_ad_cost(self.ds, client, period=...)
    text = re.sub(
        r"aggregate_ad_cost\(\s*load_clumi_source\s*,\s*period=",
        "aggregate_ad_cost(self.ds, client, period=",
        text,
    )

    # 7. async def execute 안에 client = merged.get(...) 자동 삽입
    # 패턴: "merged = self.merge_params(params)" 다음 줄에 period 같은 게 있으면 그 위에 추가
    def insert_client(m):
        block = m.group(0)
        if "client = " in block:
            return block  # 이미 있음
        # merged = self.merge_params(params) 다음에 client 라인 추가
        return block + '        client = merged.get("client", "clumi")\n'

    text = re.sub(
        r"        merged = self\.merge_params\(params\)\n",
        insert_client,
        text,
    )

    if text == orig:
        return False, f"NO CHANGE: {path.name}"

    path.write_text(text, encoding="utf-8")
    diff = sum(1 for a, b in zip(orig.splitlines(), text.splitlines()) if a != b)
    return True, f"CONVERTED: {path.name} (~{diff} lines changed)"


def main():
    print(f"Step 4 변환 시작 — {len(TARGETS)} 파일\n")
    changed = 0
    for rel in TARGETS:
        p = ROOT / rel
        ok, info = convert_file(p)
        print(f"  {info}")
        if ok:
            changed += 1
    print(f"\n총 변환: {changed}/{len(TARGETS)}")


if __name__ == "__main__":
    main()
