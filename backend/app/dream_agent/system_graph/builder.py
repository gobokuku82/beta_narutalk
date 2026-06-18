"""System Graph — 4-Layer LangGraph 조립

Cognitive → Planning → Execution → Response, Command hand-off 기반.

각 stage 함수는 해당 레이어 폴더의 `{layer}_stage.py`에 정의되어 있으며,
본 파일은 그것들을 StateGraph로 조립하는 역할만 담당.

프로덕션은 api_v2/main.py lifespan 이 AsyncPostgresSaver(PostgreSQL checkpointer)를
연결해 주입한다 (연결 실패 시 서버 기동 중단 — fail-fast). checkpointer=None 은
테스트·진단 스크립트 전용. (2026-06-12 docstring 정정: 구 "in-memory, 향후 연결 예정"
서술은 연결 완료 이전 세계의 doc drift.)

Reference: docs/agent_specs/10_system_architecture_v1.9.md §3
"""

from __future__ import annotations

from langgraph.graph import START, StateGraph

from app.dream_agent.cognitive.cognitive_stage import cognitive_stage
from app.dream_agent.execution.execution_stage import execution_stage
from app.dream_agent.planning.planning_stage import planning_stage
from app.dream_agent.response.response_stage import response_stage
from app.dream_agent.states.agent_state import AgentState


def build_graph(checkpointer=None):
    """4-Layer LangGraph 조립.

    Args:
        checkpointer: AsyncPostgresSaver 인스턴스 (None이면 in-memory)

    노드 이름 문자열("cognitive" 등)은 WebSocket layer_start/layer_complete
    이벤트에서 대시보드가 참조하므로 유지.
    """
    g = StateGraph(AgentState)
    g.add_node("cognitive", cognitive_stage)
    g.add_node("planning", planning_stage)
    g.add_node("execution", execution_stage)
    g.add_node("response", response_stage)

    g.add_edge(START, "cognitive")

    return g.compile(checkpointer=checkpointer)
