"""Diagnoser — LLM으로 분석 결과의 '왜'(인과)를 진단 (분석레이어 v2 '진단' 단계, 2026-06-10).

도메인 무관: metric(매출·ROAS·퍼널 등)·추세를 받아 원인 가설 도출. diagnose operation 해소
(구 DEGRADE_OPS → 실제 LLM 인과추론). fatigue(소재 피로) 등 ML 지각 산출도 evidence 로.

입력: previous_results 의 분석 산출 전반 (insight_extractor 패턴 — 도메인 무관)
출력: diagnosis (list[{observation, likely_cause, evidence, confidence}])
"""

from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.llm_manager.client import get_llm_client
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.llm_tool import LLMTool
from app.dream_agent.tools.shared.col_dictionary import build_data_glossary
from app.dream_agent.tools.shared.prompt_loader import load_tool_prompt

logger = get_logger(__name__)

_PROMPT = load_tool_prompt("diagnoser")
SYSTEM_PROMPT = _PROMPT["system_prompt"]
USER_TEMPLATE = _PROMPT["user_template"]


class Diagnoser(LLMTool):
    """분석 결과 → 인과 진단 ('왜'). 도메인 무관 LLM 추론. silent-0 = in-tool 빈입력 가드."""

    _NOISE = frozenset({
        "count", "file_no", "source_id", "is_mock", "reason", "detail", "artifact",
        "word_count", "char_count", "length", "summary", "insights", "diagnosis",
    })

    def collect_inputs(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """previous_results 의 분석 산출 전반 수집 (도메인 무관)."""
        previous = context.previous_results or {}
        out: dict[str, Any] = {}
        for result in previous.values():
            data = result.get("data") if isinstance(result, dict) else None
            src = data if isinstance(data, dict) else (result if isinstance(result, dict) else {})
            if not isinstance(src, dict):
                continue
            for k, v in src.items():
                if k in out or k.startswith("_") or k in self._NOISE:
                    continue
                if v is None or (hasattr(v, "__len__") and len(v) == 0):
                    continue
                if len(json.dumps(v, ensure_ascii=False, default=str)) > 600:
                    continue
                out[k] = v
        return out

    async def run_llm(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        max_causes = int(merged.get("max_causes", 4))

        # S2-ext(2026-06-18): 인과 진단 LLM 도 단위·함정을 인지하게 의미 동봉(insight 와 동일).
        glossary = build_data_glossary(inputs, context.client_id)
        prompt = USER_TEMPLATE.format(
            max_causes=max_causes,
            glossary=glossary,
            analysis=json.dumps(inputs, ensure_ascii=False, default=str)[:3000],
        )

        client = get_llm_client("execution")
        result = await client.generate_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)

        diagnosis = result.get("diagnosis", []) if isinstance(result, dict) else []

        logger.info("diagnoser completed", count=len(diagnosis))

        return {"diagnosis": diagnosis, "count": len(diagnosis)}
