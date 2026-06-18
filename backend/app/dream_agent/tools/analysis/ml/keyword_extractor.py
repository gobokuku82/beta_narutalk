"""Keyword Extractor — 빈도 기반 한글 키워드 추출 (POC).

입력: cleaned_texts
출력: top_keywords (list[{keyword, count, rank}])
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.helpers import find_in_previous

logger = get_logger(__name__)

STOPWORDS: set[str] = {
    "이거", "저거", "그거", "정말", "진짜", "너무", "그냥", "조금", "근데",
    "하지만", "그리고", "그래서", "아주", "매우", "많이", "되게", "약간",
    "그런데", "이런", "저런", "그런",
}


class KeywordExtractor(BaseTool):
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        top_k = int(merged.get("top_k", 10))
        min_chars = int(merged.get("min_chars", 2))

        texts = find_in_previous(context.previous_results, "cleaned_texts") or []
        pattern = re.compile(rf"[가-힣]{{{min_chars},}}")

        words: list[str] = []
        for t in texts:
            words.extend(pattern.findall(t["cleaned_text"]))

        words = [w for w in words if w not in STOPWORDS]
        counter = Counter(words)

        top = [
            {"keyword": kw, "count": cnt, "rank": idx + 1}
            for idx, (kw, cnt) in enumerate(counter.most_common(top_k))
        ]

        logger.info(
            "keyword_extractor completed",
            total_tokens=len(words),
            unique=len(counter),
            top_k=len(top),
        )

        return {
            "top_keywords": top,
            "total_tokens": len(words),
            "unique_tokens": len(counter),
        }
