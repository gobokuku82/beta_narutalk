"""Response Stage — ExecutionResult → ResponsePayload 역번역

4-Layer 파이프라인의 마지막 단계. 기계 언어(ExecutionResult)를
사용자 언어(ResponsePayload)로 역번역한다. goal.output_format에
따라 text/pdf/image/mixed/error 포맷으로 라우팅.

실동작 (2c, 2026-06-09 — LLM 0): 정직 degrade 2 게이트 → 결정론 표시 dispatcher
(build_display_payload). 서술 텍스트는 execution 단계의 LLM tool(report_writer/
summary_generator/qa_responder) 책임 — response 레이어는 LLM 을 호출하지 않는다.
(2026-06-12 docstring 정정: 구 "⑭ formatter = LLM 기반 자연어 생성" 서술은 2c 전환
이전 세계 — 진입점 첫인상이 실동작과 반대였던 doc drift.)

Reference: docs/agent_specs/14_system_agent_overview_v1.0.md (Response 레이어)
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END
from langgraph.types import Command

from app.core.logging import get_logger
from app.dream_agent.response.responder import Responder
from app.dream_agent.schemas.execution_result import ExecutionResult
from app.dream_agent.schemas.response_payload import ResponsePayload
from app.dream_agent.schemas.structured_query import StructuredQuery
from app.dream_agent.states.agent_state import AgentState

logger = get_logger(__name__)


async def response_stage(state: AgentState) -> Command[Any]:
    """ExecutionResult → ResponsePayload 역번역.

    Args:
        state: AgentState (structured_query, execution_result 읽음)

    Returns:
        Command(update={response}, goto=END)
    """
    sq_dict = state.get("structured_query") or {}
    exec_dict = state.get("execution_result") or {}

    if not sq_dict:
        return Command(update={"error": "no structured_query for response"}, goto=END)

    sq = StructuredQuery.model_validate(sq_dict)
    exec_result = ExecutionResult.model_validate(exec_dict) if exec_dict else ExecutionResult()

    responder = Responder()
    payload: ResponsePayload = await responder.respond(sq, exec_result)

    logger.info(
        "response done",
        format=payload.format.value if hasattr(payload.format, "value") else payload.format,
        attachments=len(payload.attachments),
    )
    return Command(update={"response": payload.model_dump(mode="json")}, goto=END)
