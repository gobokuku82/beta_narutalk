"""Age Segment — methodology §S037 (연령 5세 bucket 분포).

회귀 (정답표):
    bucket 40-44 = 1,455 / 35-39 = 1,429 → 핵심 35-44 합 = 2,884
    bucket 30-34 = 1,407 / 25-29 = 1,393
    bucket 50-54 = 800   / 45-49 = 778
    bucket 20-24 = 477
    bucket 60-64 = 254   / 55-59 = 241 / 15-19 = 182
    기타(65+)    = 84
    합계 = 8,500

규칙: FLOOR(age / 5) * 5 → "35-39", "40-44" 등 라벨

Status: complete — 2026-05-23 metrics 7번째.
"""
from __future__ import annotations
from collections import Counter
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_int

logger = get_logger(__name__)

CUSTOMERS_FILE_NO = 6
SENIOR_THRESHOLD = 65  # 65+ 는 "기타" 통합


def age_to_bucket(age: int) -> str:
    """FLOOR(age/5)*5 → 'NN-NN' 라벨. 65+ = '65+(기타)'."""
    if age >= SENIOR_THRESHOLD:
        return "65+"
    floor = (age // 5) * 5
    return f"{floor}-{floor + 4}"


class AgeSegment(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        df = self.fetch("customers", context)
        total_members = len(df)

        # age 정수만 bucket 화
        buckets: Counter = Counter()
        for v in df["age"]:
            age = safe_int(v, default=0)
            if age <= 0:
                continue
            buckets[age_to_bucket(age)] += 1

        # 정렬: count 내림차순
        table: dict[str, dict] = {}
        for bucket, count in buckets.most_common():
            share = round(count / total_members * 100, 1) if total_members else 0.0
            table[bucket] = {"count": count, "share_pct": share}

        # 핵심 회귀 — 35-44 합
        core_35_44 = (table.get("35-39", {}).get("count", 0)
                      + table.get("40-44", {}).get("count", 0))

        key = "S037_age_segment.json"
        logger.info("age_segment", total=total_members, core_35_44=core_35_44, buckets=len(table))

        return {
            "table": table,
            "total_members": total_members,
            "core_segment_35_44": core_35_44,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "FLOOR(age/5)*5 GROUP BY bucket (65+ = 기타)"},
        }
