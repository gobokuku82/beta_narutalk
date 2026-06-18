"""QA Responder — 질의응답 카테고리 단일 tool (2026-06-10).

질문에 데이터 계산이 아니라 *지식·메타·대화*로 답한다 (질의응답_설계서_260610.md).
분석 tool 과 다른 점: 입력이 이전 결과가 아니라 *사용자 질문 + 정적 컨텍스트*.

입력: params["question"] (planner 가 결정론 QA 라우팅 시 주입) + client_id 로 용어집.
출력: {answer, answer_type}.
RAG = hook(_retrieve_context)만 — 추후(사용자 명시 연기, 설계서 §5).

Status: complete — 단일 QA. 종류분기·RAG·동적 introspect 는 추후(planned, 설계서 §5·§7).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.llm_manager.client import get_llm_client
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.llm_tool import LLMTool
from app.dream_agent.tools.shared.col_dictionary import load_client_glossary
from app.dream_agent.tools.shared.prompt_loader import load_tool_prompt

logger = get_logger(__name__)

# 프롬프트는 tools/prompts/qa_responder.yaml 로 외부화 (spec 16 §1 콘텐츠/로직 분리)
_PROMPT = load_tool_prompt("qa_responder")
SYSTEM_PROMPT = _PROMPT["system_prompt"]
USER_TEMPLATE = _PROMPT["user_template"]

# '시스템 메타' 질문용 정적 능력 blurb. 추후 동적 introspect(설계서 §7).
_SYSTEM_CAPABILITIES = (
    "이 시스템(OctorAD)이 할 수 있는 것: "
    "① 매출·ROAS·CAC·전환 등 마케팅 지표 조회·분해·비교, "
    "② 지표 진단(왜 변했나)·예측·해석(추론), "
    "③ 리뷰 감성·키워드 분석, "
    "④ 보고서/PDF 생성. "
    "데이터 소스: 주문·광고(meta/ga4 등)·고객·리뷰 등."
)


class QaResponder(LLMTool):
    """질의응답 단일 tool. 질문 + 컨텍스트(용어집·능력) → LLM 답변.

    빈입력 가드(LLMTool.execute): question 항상 존재 → 통과(항상 답함). 가드는 안전망.
    분석 tool 과 달리 previous_results 가 아니라 *질문 자체*를 입력으로 받음 (params 주입).
    """

    def _retrieve_context(self, question: str, context: ExecutionContext) -> list[str]:
        """RAG hook — 추후 문서/KB 검색. 지금은 자리만([]).

        Status: planned — RAG 미구현(사용자 명시 연기). 연결 시 여기만 채움(설계서 §5).
        """
        return []

    def collect_inputs(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """질문 수집 (planner 가 tool_params["question"] 에 주입). 항상 값 있음 → 답함."""
        merged = self.merge_params(params)
        question = str(merged.get("question") or "").strip()
        return {"question": question}

    async def run_llm(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        question = inputs["question"]
        glossary = load_client_glossary(context.client_id)
        retrieved = self._retrieve_context(question, context)   # RAG 자리(현 [])

        prompt = USER_TEMPLATE.format(
            question=question,
            glossary=glossary or "(제공된 용어집 없음 — 일반 지식으로 답)",
            capabilities=_SYSTEM_CAPABILITIES,
            retrieved="\n".join(retrieved) or "(없음)",
        )

        client = get_llm_client("execution")
        result = await client.generate_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)

        answer = (result.get("answer") if isinstance(result, dict) else None) or ""
        answer_type = (
            result.get("answer_type") if isinstance(result, dict) else None
        ) or "unknown"

        logger.info("qa_responder completed", answer_type=answer_type, has_answer=bool(answer))

        return {"answer": answer, "answer_type": answer_type}
