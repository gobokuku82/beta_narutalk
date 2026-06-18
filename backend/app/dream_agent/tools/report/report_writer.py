"""Report Writer — 인사이트 기반 마케팅 분석 보고서 생성 (LLM)."""

from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.llm_manager.client import get_llm_client
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.llm_tool import LLMTool
from app.dream_agent.tools.shared.col_dictionary import build_data_glossary
from app.dream_agent.tools.shared.helpers import find_in_previous
from app.dream_agent.tools.shared.prompt_loader import load_tool_prompt

logger = get_logger(__name__)

# 프롬프트는 tools/prompts/report_writer.yaml 로 외부화 (spec 16 §1 콘텐츠/로직 분리)
_PROMPT = load_tool_prompt("report_writer")
SYSTEM_PROMPT = _PROMPT["system_prompt"]
USER_TEMPLATE = _PROMPT["user_template"]


class ReportWriter(LLMTool):
    # 빈입력 가드(silent-0)는 LLMTool.execute 가 소유 — collect_inputs 가 전부 빔이면
    # LLM 호출 전 data_insufficient. 정상 경로는 B2.1 게이트(consumes=[insights])가 먼저 SKIP.
    def collect_inputs(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        previous = context.previous_results or {}
        return {
            "sentiment": find_in_previous(previous, "sentiment_distribution") or {},
            "keywords": find_in_previous(previous, "top_keywords") or [],
            "insights": find_in_previous(previous, "insights") or [],
        }

    async def run_llm(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        # S2-ext(2026-06-18): 입력이 해석된 insights(canonical 키 0)라 칼럼 사전은 비지만,
        # [지표 정의](metric_glossary)는 동봉 — 프로즈에서 'ROAS 4.46배'를 %로 둔갑시키지 않게.
        glossary = build_data_glossary(inputs, context.client_id)
        prompt = USER_TEMPLATE.format(
            glossary=glossary,
            sentiment=json.dumps(inputs["sentiment"], ensure_ascii=False),
            keywords=json.dumps(inputs["keywords"], ensure_ascii=False),
            insights=json.dumps(inputs["insights"], ensure_ascii=False, indent=2),
        )

        client = get_llm_client("execution")
        text = await client.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)

        logger.info("report_writer completed", length=len(text))

        return {
            "report_markdown": text,        # D5(2026-06-08): catalog produces·다운스트림(pdf/ppt)과 정합 (구 report_text)
            "word_count": len(text.split()),
            "char_count": len(text),
        }
