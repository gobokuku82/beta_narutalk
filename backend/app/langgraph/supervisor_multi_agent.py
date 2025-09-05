"""
Enhanced Supervisor with Multi-Agent Coordination
복합 질의 처리 및 병렬 실행을 지원하는 개선된 Supervisor
"""

from typing import Dict, Any, List, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import logging
import asyncio
import json
from app.api.v1.chat_stream import update_progress

logger = logging.getLogger(__name__)

from app.langgraph.state import AgentState, initialize_state
from app.langgraph.agents.info_retrieval_with_tools import create_info_retrieval_with_tools
from app.langgraph.agents.doc_generation_with_tools import create_doc_generation_with_tools
from app.langgraph.agents.compliance_with_tools import create_compliance_with_tools
from app.langgraph.agents.analytics_with_tools import create_analytics_with_tools
from app.core.config import settings


class MultiAgentSupervisor:
    """복합 질의를 처리하는 향상된 Supervisor"""
    
    def __init__(self):
        # LLM 초기화 - OpenAI만 사용
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Subgraph 에이전트 초기화
        logger.info("Initializing Subgraph agents for multi-agent coordination")
        self.agents = {
            "info_retrieval": create_info_retrieval_with_tools(),
            "doc_generation": create_doc_generation_with_tools(),
            "compliance": create_compliance_with_tools(),
            "analytics": create_analytics_with_tools()
        }
        logger.info(f"✅ Initialized {len(self.agents)} Subgraph agents")
    
    async def analyze_complex_query(self, query: str) -> Dict[str, Any]:
        """복합 질의 분석 및 작업 계획 생성"""
        
        prompt = f"""
        사용자 질의를 분석하여 필요한 작업들을 식별하세요.
        여러 작업이 필요한 경우 모두 나열하고, 실행 순서와 병렬 실행 가능 여부를 판단하세요.

        사용자 질의: {query}

        사용 가능한 에이전트:
        - info_retrieval: 의약품 정보, 학술자료 검색
        - doc_generation: 문서 작성, 보고서 생성
        - compliance: 규정 확인, 리스크 평가
        - analytics: 데이터 분석, 통계 생성

        응답 형식 (JSON):
        {{
            "tasks": [
                {{
                    "agent": "agent_name",
                    "action": "specific action",
                    "dependencies": [],  // 선행 작업이 필요한 경우
                    "parallel": true/false  // 병렬 실행 가능 여부
                }}
            ],
            "execution_plan": "sequential" or "parallel" or "mixed",
            "explanation": "작업 계획 설명"
        }}
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content
            
            # JSON 파싱 시도
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            plan = json.loads(json_str)
            
            # 기본값 설정
            if "tasks" not in plan:
                plan["tasks"] = []
            if "execution_plan" not in plan:
                plan["execution_plan"] = "sequential"
            
            logger.info(f"Query analysis complete: {len(plan['tasks'])} tasks identified")
            return plan
            
        except Exception as e:
            logger.error(f"Failed to analyze complex query: {e}")
            
            # Fallback: 단일 에이전트 결정
            return {
                "tasks": [{
                    "agent": self._fallback_agent_selection(query),
                    "action": query,
                    "dependencies": [],
                    "parallel": False
                }],
                "execution_plan": "sequential",
                "explanation": "단일 작업으로 처리"
            }
    
    def _fallback_agent_selection(self, query: str) -> str:
        """Fallback 에이전트 선택"""
        query_lower = query.lower()
        
        # 키워드 기반 매칭
        if any(word in query_lower for word in ["검색", "찾", "조회", "search", "find"]):
            return "info_retrieval"
        elif any(word in query_lower for word in ["작성", "생성", "만들", "create", "generate"]):
            return "doc_generation"
        elif any(word in query_lower for word in ["규정", "확인", "검사", "compliance", "check"]):
            return "compliance"
        elif any(word in query_lower for word in ["분석", "통계", "데이터", "analyze", "statistics"]):
            return "analytics"
        
        return "info_retrieval"  # 기본값
    
    async def execute_parallel_tasks(self, tasks: List[Dict], state: AgentState) -> Dict[str, Any]:
        """병렬 작업 실행"""
        logger.info(f"Executing {len(tasks)} tasks in parallel")
        
        # 진행 상황 업데이트
        session_id = state.get("session_id", "unknown")
        agent_list = [t["agent"] for t in tasks]
        update_progress(session_id, {
            "status": "processing",
            "message": f"{len(tasks)}개 작업을 병렬로 처리 중...",
            "total_steps": len(tasks),
            "current_step": 0,
            "agents": agent_list
        })
        
        # 병렬 실행할 작업들
        async_tasks = []
        for task in tasks:
            agent_name = task["agent"]
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                
                # 각 에이전트에 전달할 state 수정
                task_state = state.copy()
                task_state["messages"] = [{"role": "user", "content": task["action"]}]
                
                async_tasks.append(agent.process(task_state))
        
        # 모든 작업 병렬 실행
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # 결과 통합
        combined_outputs = {}
        combined_messages = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {result}")
                continue
            
            agent_name = tasks[i]["agent"]
            combined_outputs[agent_name] = result.get("agent_outputs", {})
            
            # 진행 상황 업데이트
            update_progress(session_id, {
                "current_step": i + 1,
                "active_agent": agent_name,
                "message": f"{agent_name} 작업 완료"
            })
            
            # 메시지 수집
            if "messages" in result:
                for msg in result["messages"]:
                    # Handle both dict and Message objects
                    if isinstance(msg, (HumanMessage, AIMessage)):
                        if isinstance(msg, AIMessage):
                            combined_messages.append({
                                "agent": agent_name,
                                "content": msg.content
                            })
                    elif isinstance(msg, dict) and msg.get("role") == "assistant":
                        combined_messages.append({
                            "agent": agent_name,
                            "content": msg.get("content", "")
                        })
        
        return {
            "agent_outputs": combined_outputs,
            "messages": combined_messages,
            "execution_type": "parallel"
        }
    
    async def execute_sequential_tasks(self, tasks: List[Dict], state: AgentState) -> Dict[str, Any]:
        """순차 작업 실행"""
        logger.info(f"Executing {len(tasks)} tasks sequentially")
        
        combined_outputs = {}
        combined_messages = []
        current_state = state.copy()
        
        for task in tasks:
            agent_name = task["agent"]
            if agent_name not in self.agents:
                logger.warning(f"Agent {agent_name} not found")
                continue
            
            agent = self.agents[agent_name]
            
            # 이전 결과를 context에 추가
            current_state["context"]["previous_outputs"] = combined_outputs
            current_state["messages"] = [{"role": "user", "content": task["action"]}]
            
            # 에이전트 실행
            try:
                result = await agent.process(current_state)
                
                # 결과 저장
                combined_outputs[agent_name] = result.get("agent_outputs", {})
                
                # 메시지 수집
                if "messages" in result:
                    for msg in result["messages"]:
                        # Handle both dict and Message objects
                        if isinstance(msg, (HumanMessage, AIMessage)):
                            if isinstance(msg, AIMessage):
                                combined_messages.append({
                                    "agent": agent_name,
                                    "content": msg.content
                                })
                        elif isinstance(msg, dict) and msg.get("role") == "assistant":
                            combined_messages.append({
                                "agent": agent_name,
                                "content": msg.get("content", "")
                            })
                
                # State 업데이트
                current_state["agent_outputs"] = combined_outputs
                
            except Exception as e:
                logger.error(f"Task execution failed for {agent_name}: {e}")
        
        return {
            "agent_outputs": combined_outputs,
            "messages": combined_messages,
            "execution_type": "sequential"
        }
    
    async def execute_mixed_tasks(self, tasks: List[Dict], state: AgentState) -> Dict[str, Any]:
        """혼합 실행 (병렬 + 순차)"""
        logger.info(f"Executing {len(tasks)} tasks in mixed mode")
        
        # 의존성 기반 그룹화
        execution_groups = []
        processed = set()
        
        while len(processed) < len(tasks):
            current_group = []
            
            for i, task in enumerate(tasks):
                if i in processed:
                    continue
                
                # 의존성 체크
                dependencies = task.get("dependencies", [])
                if all(dep in processed for dep in dependencies):
                    current_group.append(task)
                    processed.add(i)
            
            if current_group:
                execution_groups.append(current_group)
            else:
                # 순환 의존성 방지
                logger.warning("Circular dependency detected, breaking...")
                break
        
        # 그룹별 실행
        combined_outputs = {}
        combined_messages = []
        current_state = state.copy()
        
        for group in execution_groups:
            if len(group) == 1:
                # 단일 작업: 순차 실행
                result = await self.execute_sequential_tasks(group, current_state)
            else:
                # 여러 작업: 병렬 실행
                result = await self.execute_parallel_tasks(group, current_state)
            
            # 결과 통합
            combined_outputs.update(result.get("agent_outputs", {}))
            combined_messages.extend(result.get("messages", []))
            
            # State 업데이트
            current_state["agent_outputs"] = combined_outputs
        
        return {
            "agent_outputs": combined_outputs,
            "messages": combined_messages,
            "execution_type": "mixed"
        }
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """Multi-Agent Supervisor 처리"""
        logger.info(f"Multi-Agent Supervisor processing: session {state.get('session_id')}")
        
        # 메시지 확인
        if not state.get("messages"):
            return {
                "messages": [{"role": "assistant", "content": "요청이 없습니다."}],
                "should_end": True
            }
        
        last_message = state["messages"][-1]
        user_query = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else str(last_message)
        
        # 복합 질의 분석
        plan = await self.analyze_complex_query(user_query)
        
        if not plan["tasks"]:
            return {
                "messages": [{"role": "assistant", "content": "처리할 작업을 식별할 수 없습니다."}],
                "should_end": True
            }
        
        # 실행 계획에 따라 처리
        execution_plan = plan["execution_plan"]
        tasks = plan["tasks"]
        
        logger.info(f"Execution plan: {execution_plan} with {len(tasks)} tasks")
        
        if execution_plan == "parallel":
            result = await self.execute_parallel_tasks(tasks, state)
        elif execution_plan == "sequential":
            result = await self.execute_sequential_tasks(tasks, state)
        else:  # mixed
            result = await self.execute_mixed_tasks(tasks, state)
        
        # 최종 응답 생성
        final_response = await self.synthesize_response(result, plan)
        
        return {
            "messages": [{"role": "assistant", "content": final_response}],
            "agent_outputs": result.get("agent_outputs", {}),
            "metadata": {
                "execution_plan": plan,
                "execution_type": result.get("execution_type")
            },
            "should_end": True
        }
    
    async def synthesize_response(self, result: Dict, plan: Dict) -> str:
        """여러 에이전트 결과를 통합하여 최종 응답 생성"""
        
        messages = result.get("messages", [])
        
        if not messages:
            return "요청을 처리했지만 결과가 없습니다."
        
        if len(messages) == 1:
            # 단일 에이전트 결과
            return messages[0]["content"]
        
        # 여러 에이전트 결과 통합
        prompt = f"""
        여러 에이전트의 작업 결과를 통합하여 일관성 있는 응답을 생성하세요.
        
        작업 계획: {plan.get('explanation', '')}
        
        에이전트 결과들:
        """
        
        for msg in messages:
            prompt += f"\n\n[{msg['agent']}]\n{msg['content'][:500]}"
        
        prompt += "\n\n위 결과들을 통합하여 사용자에게 전달할 최종 응답을 작성하세요:"
        
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content
        except:
            # Fallback: 단순 연결
            combined = "다음은 요청하신 작업들의 결과입니다:\n\n"
            for msg in messages:
                agent_name = msg['agent'].replace('_', ' ').title()
                combined += f"## {agent_name}\n{msg['content']}\n\n"
            return combined


def create_multi_agent_supervisor_graph():
    """Multi-Agent Supervisor 그래프 생성"""
    
    # StateGraph 초기화
    workflow = StateGraph(AgentState)
    
    # Multi-Agent Supervisor 인스턴스
    supervisor = MultiAgentSupervisor()
    
    # 노드 추가
    workflow.add_node("multi_supervisor", supervisor.process)
    
    # 각 Subgraph도 개별 노드로 추가 (직접 호출 가능)
    workflow.add_node("info_retrieval", supervisor.agents["info_retrieval"].process)
    workflow.add_node("doc_generation", supervisor.agents["doc_generation"].process)
    workflow.add_node("compliance", supervisor.agents["compliance"].process)
    workflow.add_node("analytics", supervisor.agents["analytics"].process)
    
    # 엣지 설정
    workflow.add_edge(START, "multi_supervisor")
    
    # 조건부 엣지
    def route_after_supervisor(state: AgentState) -> str:
        """Supervisor 이후 라우팅"""
        if state.get("should_end", False):
            return "end"
        
        # 추가 작업이 필요한 경우 개별 에이전트로 라우팅
        next_agent = state.get("next_agent")
        if next_agent and next_agent in ["info_retrieval", "doc_generation", "compliance", "analytics"]:
            return next_agent
        
        return "end"
    
    workflow.add_conditional_edges(
        "multi_supervisor",
        route_after_supervisor,
        {
            "info_retrieval": "info_retrieval",
            "doc_generation": "doc_generation",
            "compliance": "compliance",
            "analytics": "analytics",
            "end": END
        }
    )
    
    # 개별 에이전트에서 다시 Supervisor로
    for agent in ["info_retrieval", "doc_generation", "compliance", "analytics"]:
        workflow.add_edge(agent, "multi_supervisor")
    
    # 그래프 컴파일
    app = workflow.compile()
    
    logger.info("✅ Multi-Agent Supervisor graph created")
    
    return app


# 실행 헬퍼 함수
async def run_multi_agent_supervisor(user_input: str, session_id: str, user_id: str = None):
    """Multi-Agent Supervisor 실행"""
    
    logger.info(f"Starting Multi-Agent Supervisor: session {session_id}")
    
    # 그래프 생성
    app = create_multi_agent_supervisor_graph()
    
    # 초기 State 생성
    initial_state = initialize_state(session_id, user_id)
    initial_state["messages"] = [{"role": "user", "content": user_input}]
    
    # 그래프 실행
    try:
        result = await app.ainvoke(initial_state)
        
        # 결과 추출 - Handle both dict and Message objects
        assistant_messages = []
        for msg in result.get("messages", []):
            if isinstance(msg, AIMessage):
                assistant_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                assistant_messages.append(msg)
        
        final_message = assistant_messages[-1].get("content") if assistant_messages else "처리 완료"
        
        return {
            "success": True,
            "message": final_message,
            "session_id": session_id,
            "agent_outputs": result.get("agent_outputs", {}),
            "metadata": result.get("metadata", {}),
            "execution_type": result.get("metadata", {}).get("execution_type", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Multi-Agent Supervisor execution error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"처리 중 오류가 발생했습니다: {str(e)}",
            "session_id": session_id
        }