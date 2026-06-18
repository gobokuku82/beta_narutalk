"""Insight Extractor — LLM으로 분석 결과에서 인사이트 도출.

도메인 무관(2026-06-10, 분석레이어 v2 '추론' 단계): metric(매출·ROAS·퍼널 등)·리뷰 감성/키워드
어떤 분석 산출이든 받아 의미(추세·기여·목표대비)로 해석. (구: sentiment+keywords 리뷰 전용 = CP#1 뿌리)

입력: previous_results 의 분석 산출 전반 (summary_generator 패턴)
출력: insights (list[{title, description, importance, evidence}])
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

# 프롬프트는 tools/prompts/insight_extractor.yaml 로 외부화 (spec 16 §1 콘텐츠/로직 분리)
_PROMPT = load_tool_prompt("insight_extractor")
SYSTEM_PROMPT = _PROMPT["system_prompt"]
USER_TEMPLATE = _PROMPT["user_template"]


class InsightExtractor(LLMTool):
    """분석 결과(metric·리뷰 무관) → 인사이트. 도메인 무관 LLM '추론' 단계.

    빈입력 가드(LLMTool.execute 소유): collect_inputs 전부 빔이면 LLM 호출 전 degrade
      (가짜 insights 차단). 게이트(consumes) 미선언 — OR-입력이라 in-tool 가드에 의존
      (summary_generator 와 동일 패턴). catalog consumes 도 비움([[project_catalog_code_drift]]).
    """

    # 수집 제외: 구조 노이즈 + 자기 산출(insights).
    _NOISE = frozenset({
        "count", "file_no", "source_id", "is_mock", "reason", "detail", "artifact",
        "word_count", "char_count", "length", "summary", "insights",
    })

    def collect_inputs(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """previous_results 의 분석 산출 전반 수집 (도메인 무관 — metric·감성·키워드 무차별).

        summary_generator._collect_payload 패턴: 표시가능 값만, 구조 노이즈·과대 raw 덤프 제외.
        """
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
                    continue  # 빈 값 제외 (0 은 스칼라 — 값 있음)
                if len(json.dumps(v, ensure_ascii=False, default=str)) > 600:
                    continue  # raw 덤프 등 과대 — 해석 대상 아님
                out[k] = v
        return out

    async def run_llm(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        max_insights = int(merged.get("max_insights", 5))

        # S2(2026-06-18): 데이터 의미(단위·함정라벨)를 동봉 — LLM이 벌거벗은 숫자를 오독하지 않게.
        # inputs(dict) 전달 → rows[] 중첩 함정키(ctr/cpc 등)까지 사전이 닿음(G-B).
        glossary = build_data_glossary(inputs, context.client_id)
        prompt = USER_TEMPLATE.format(
            max_insights=max_insights,
            glossary=glossary,
            analysis=json.dumps(inputs, ensure_ascii=False, default=str)[:3000],
        )

        client = get_llm_client("execution")
        result = await client.generate_json(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
        )

        insights = result.get("insights", []) if isinstance(result, dict) else []

        logger.info("insight_extractor completed", count=len(insights))

        return {
            "insights": insights,
            "count": len(insights),
        }
