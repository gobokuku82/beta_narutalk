"""Text Preprocessor — 리뷰 텍스트 통합 클렌징.

입력: normalized_reviews (review_normalizer 출력 — ADR-014 v2)
출력: cleaned_texts (list[dict])
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.helpers import find_in_previous

logger = get_logger(__name__)

SPONSORED_KEYWORDS = ["협찬", "제공받", "유료광고", "내돈내산 아님", "광고", "PR "]

_RE_HTML = re.compile(r"<[^>]+>")
_RE_URL = re.compile(r"https?://\S+")
_RE_REPEAT = re.compile(r"(.)\1{2,}")
_RE_WS = re.compile(r"\s+")


class TextPreprocessor(BaseTool):
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        min_len = int(merged.get("min_length", 5))
        max_len = int(merged.get("max_length", 500))

        reviews = find_in_previous(context.previous_results, "normalized_reviews") or []

        cleaned: list[dict] = []
        seen: set[str] = set()

        for rv in reviews:
            original = str(rv.get("text", "") or "")
            text = self._clean(original)

            if len(text) < min_len:
                continue
            if len(text) > max_len:
                text = text[:max_len]

            h = hashlib.md5(text.encode("utf-8")).hexdigest()
            if h in seen:
                continue
            seen.add(h)

            is_sponsored = any(k in original for k in SPONSORED_KEYWORDS)

            cleaned.append({
                "text_id": rv.get("review_id") or h[:8],
                "original_text": original,
                "cleaned_text": text,
                "is_sponsored": is_sponsored,
                "is_valid": True,
                "language": "ko",
                "channel": rv.get("channel"),
                "sentiment": rv.get("sentiment"),
            })

        logger.info(
            "text_preprocessor completed",
            input=len(reviews),
            output=len(cleaned),
            dropped=len(reviews) - len(cleaned),
        )

        return {
            "cleaned_texts": cleaned,
            "before_count": len(reviews),
            "after_count": len(cleaned),
        }

    @staticmethod
    def _clean(text: str) -> str:
        text = _RE_HTML.sub("", text)
        text = _RE_URL.sub("", text)
        text = _RE_REPEAT.sub(r"\1\1", text)
        text = _RE_WS.sub(" ", text)
        return text.strip()
