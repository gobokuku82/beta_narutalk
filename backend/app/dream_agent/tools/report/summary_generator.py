"""Summary Generator — 분석 결과 전체를 한 문장 요약 (LLM)."""

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

# 프롬프트는 tools/prompts/summary_generator.yaml 로 외부화 (spec 16 §1 콘텐츠/로직 분리)
_PROMPT = load_tool_prompt("summary_generator")
SYSTEM_PROMPT = _PROMPT["system_prompt"]
USER_TEMPLATE = _PROMPT["user_template"]


class SummaryGenerator(LLMTool):
    # 요약 입력은 4 후보 키 중 *아무거나*(OR). LLMTool.execute 가드가 'collect_inputs 전부 빔'
    # 일 때만 degrade → 4 키 전부 0건/부재일 때만 차단(silent-0 축2). 게이트(consumes)는
    # AND-의미라 OR-입력에 안 맞아 미선언, 본 in-tool 가드에 의존.
    def collect_inputs(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        return self._collect_payload(context.previous_results or {})

    async def run_llm(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        max_length = int(merged.get("max_length", 100))

        # S2(2026-06-18): 데이터 의미(단위·함정라벨) 동봉 — 수치를 단위 틀리게 서술하지 않게.
        # inputs(dict) 전달 → rows[] 중첩 함정키까지 사전이 닿음(G-B).
        glossary = build_data_glossary(inputs, context.client_id)
        prompt = USER_TEMPLATE.format(
            max_length=max_length,
            glossary=glossary,
            payload=json.dumps(inputs, ensure_ascii=False, default=str)[:3000],
        )

        client = get_llm_client("execution")
        summary = await client.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        summary = summary.strip().strip('"').splitlines()[0][:max_length]

        logger.info("summary_generator completed", length=len(summary))

        return {"summary": summary}

    # 2a(2026-06-08): 서술 대상 = 분석/metric 산출(표시가능). 우선키 + 일반 결과(숫자 등).
    #   produces 기반 필터가 이상적이나 previous_results(집계 dict)에 tool 명이 없어 불가 →
    #   구조 노이즈 상수 + 크기 가드(raw 덤프 제외)로 실용 처리(POC, 조정가능).
    _PRIORITY = ("sentiment_distribution", "top_keywords", "insights", "report_markdown")
    _NOISE = frozenset({
        "count", "file_no", "source_id", "is_mock", "reason", "detail", "artifact",
        "word_count", "char_count", "length", "summary",
    })

    @staticmethod
    def _collect_payload(previous: dict) -> dict:
        """이전 결과에서 서술할 산출 수집 (2a: 일반 결과 — metric 포함).

        우선키(분석 산출) + 그 외 표시가능 값. 구조 노이즈(_*, count 류)와 과대 값(raw 덤프,
        우선키 제외)은 제외. LLM 이 수치·키워드를 문장으로 서술(프롬프트가 '수치 포함' 지시).
        """
        out: dict = {}
        for result in previous.values():
            data = result.get("data") if isinstance(result, dict) else None
            src = data if isinstance(data, dict) else (result if isinstance(result, dict) else {})
            if not isinstance(src, dict):
                continue
            for k, v in src.items():
                if k in out or k.startswith("_") or k in SummaryGenerator._NOISE:
                    continue
                if v is None or (hasattr(v, "__len__") and len(v) == 0):
                    continue  # 빈 값 제외 (0 은 스칼라라 통과 — 값 있음)
                if k not in SummaryGenerator._PRIORITY and \
                        len(json.dumps(v, ensure_ascii=False, default=str)) > 600:
                    continue  # raw 덤프 등 과대 — 서술 대상 아님
                out[k] = v
        return out
