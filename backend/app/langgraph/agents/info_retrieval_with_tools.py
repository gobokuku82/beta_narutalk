"""
Information Retrieval Agent with Tools Integration
Tool을 사용하는 정보검색 에이전트
"""

from typing import Dict, Any, List, TypedDict, Annotated, Sequence, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import logging
logger = logging.getLogger(__name__)
import operator
import json

from app.core.config import settings
from app.tools.database_tools import DrugSearchTool, CustomerSearchTool
from app.tools.search_tools import VectorSearchTool, LiteratureSearchTool, WebSearchTool


class InfoRetrievalToolState(TypedDict):
    """Tool을 사용하는 정보검색 State"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    final_response: str
    context: Dict[str, Any]
    error: Optional[str]


class InfoRetrievalWithTools:
    """Tool을 사용하는 정보검색 Subgraph"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Tools 초기화
        self.tools = [
            DrugSearchTool(),
            CustomerSearchTool(),
            VectorSearchTool(),
            LiteratureSearchTool(),
            WebSearchTool()
        ]
        
        # Tool 이름 매핑
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # Agent 프롬프트
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 의약품 정보를 검색하는 전문 AI 어시스턴트입니다.
            사용 가능한 도구들을 활용하여 정확한 정보를 제공하세요.
            
            도구 사용 가이드:
            - drug_search: 특정 의약품 정보 검색
            - customer_search: 병원/의원 정보 검색  
            - vector_search: 지식베이스에서 유사 문서 검색
            - literature_search: 학술 문헌 검색
            - web_search: 최신 웹 정보 검색
            
            항상 정확한 출처를 명시하고 부작용/주의사항을 포함하세요."""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # OpenAI Tools Agent 생성
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Agent Executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=3
        )
        
        # Subgraph 생성
        self.graph = self._build_graph()
    
    async def analyze_query_node(self, state: InfoRetrievalToolState) -> Dict:
        """쿼리 분석 및 Tool 선택"""
        logger.info("Analyzing query and selecting tools")
        
        query = state.get("query", "")
        if not query and state.get("messages"):
            last_message = state["messages"][-1]
            query = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else str(last_message)
        
        # LLM으로 필요한 도구 결정
        tool_selection_prompt = f"""
        사용자 쿼리: {query}
        
        이 쿼리를 처리하기 위해 필요한 도구들을 선택하세요.
        사용 가능한 도구:
        - drug_search: 의약품 정보
        - customer_search: 고객(병원/의원) 정보
        - vector_search: 지식베이스 검색
        - literature_search: 학술 문헌
        - web_search: 웹 검색
        
        JSON 형식으로 응답하세요:
        {{
            "tools": ["tool1", "tool2"],
            "reasoning": "선택 이유"
        }}
        """
        
        response = await self.llm.ainvoke(tool_selection_prompt)
        
        try:
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            selection = json.loads(json_str)
            selected_tools = selection.get("tools", ["vector_search"])
            
            # Tool 호출 계획 생성
            tool_calls = []
            for tool_name in selected_tools:
                if tool_name in self.tool_map:
                    tool_calls.append({
                        "tool": tool_name,
                        "query": query,
                        "status": "pending"
                    })
            
            return {
                "query": query,
                "tool_calls": tool_calls
            }
            
        except Exception as e:
            logger.error(f"Tool selection failed: {e}")
            # Fallback: 기본 도구 사용
            return {
                "query": query,
                "tool_calls": [{
                    "tool": "vector_search",
                    "query": query,
                    "status": "pending"
                }]
            }
    
    async def execute_tools_node(self, state: InfoRetrievalToolState) -> Dict:
        """도구 실행"""
        logger.info("Executing selected tools")
        
        tool_calls = state.get("tool_calls", [])
        tool_results = []
        
        for call in tool_calls:
            tool_name = call.get("tool")
            query = call.get("query")
            
            if tool_name not in self.tool_map:
                logger.warning(f"Tool {tool_name} not found")
                continue
            
            tool = self.tool_map[tool_name]
            
            try:
                # Tool 실행
                logger.info(f"Executing tool: {tool_name}")
                
                # 각 도구에 맞는 입력 준비
                if tool_name == "drug_search":
                    result = await tool._arun(keyword=query)
                elif tool_name == "customer_search":
                    result = await tool._arun(keyword=query)
                elif tool_name in ["vector_search", "literature_search", "web_search"]:
                    result = await tool._arun(query=query)
                else:
                    result = await tool._arun(query)
                
                tool_results.append({
                    "tool": tool_name,
                    "success": result.success,
                    "data": result.data,
                    "error": result.error,
                    "execution_time": result.execution_time
                })
                
            except Exception as e:
                logger.error(f"Tool {tool_name} execution failed: {e}")
                tool_results.append({
                    "tool": tool_name,
                    "success": False,
                    "data": None,
                    "error": str(e),
                    "execution_time": 0
                })
        
        return {"tool_results": tool_results}
    
    async def agent_execution_node(self, state: InfoRetrievalToolState) -> Dict:
        """LangChain Agent 실행 (대안)"""
        logger.info("Executing LangChain agent")
        
        query = state.get("query", "")
        
        try:
            # Agent Executor 실행
            result = await self.agent_executor.ainvoke({
                "input": query,
                "messages": state.get("messages", [])
            })
            
            # 중간 단계 추출
            tool_results = []
            for action, observation in result.get("intermediate_steps", []):
                tool_results.append({
                    "tool": action.tool,
                    "input": action.tool_input,
                    "output": observation,
                    "success": True
                })
            
            return {
                "tool_results": tool_results,
                "final_response": result.get("output", ""),
                "context": {"agent_execution": "completed"}
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "error": str(e),
                "final_response": f"정보 검색 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def synthesize_response_node(self, state: InfoRetrievalToolState) -> Dict:
        """도구 결과 통합 및 최종 응답 생성"""
        logger.info("Synthesizing final response")
        
        query = state.get("query", "")
        tool_results = state.get("tool_results", [])
        
        # Agent가 이미 응답을 생성한 경우
        if state.get("final_response"):
            return {
                "messages": [AIMessage(content=state["final_response"])]
            }
        
        # Tool 결과 요약
        context_parts = []
        
        for result in tool_results:
            if not result.get("success"):
                continue
            
            tool_name = result.get("tool", "unknown")
            data = result.get("data", {})
            
            if tool_name == "drug_search" and data:
                if isinstance(data, dict) and "drugs" in data:
                    drugs = data["drugs"][:3]  # 상위 3개
                    for drug in drugs:
                        context_parts.append(f"""
[의약품 정보]
- 제품명: {drug.get('korean_name')}
- 성분명: {drug.get('generic_name')}
- 적응증: {', '.join(drug.get('indication', [])[:3])}
- 용법용량: {drug.get('dosage', {}).get('adult', 'N/A')}
""")
                elif isinstance(data, dict):
                    context_parts.append(f"""
[의약품 정보]
- 제품명: {data.get('korean_name')}
- 성분명: {data.get('generic_name')}
- 적응증: {', '.join(data.get('indication', [])[:3])}
""")
            
            elif tool_name == "vector_search" and data:
                results = data.get("results", [])[:2]
                for r in results:
                    context_parts.append(f"[관련 정보]\n{r.get('content', '')}")
            
            elif tool_name == "literature_search" and data:
                papers = data.get("papers", [])[:2]
                for paper in papers:
                    context_parts.append(f"""
[학술 문헌]
- 제목: {paper.get('title')}
- 저자: {', '.join(paper.get('authors', [])[:3])}
- 저널: {paper.get('journal')}
""")
            
            elif tool_name == "web_search" and data:
                results = data.get("results", [])[:3]
                for r in results:
                    context_parts.append(f"[웹 정보]\n{r.get('title')}: {r.get('snippet')}")
        
        # 컨텍스트 생성
        full_context = "\n\n".join(context_parts) if context_parts else "검색 결과가 없습니다."
        
        # 최종 응답 생성
        response_prompt = f"""
        사용자 질문: {query}
        
        검색 결과:
        {full_context}
        
        위 정보를 바탕으로 사용자 질문에 대해 정확하고 유용한 답변을 작성하세요.
        중요 정보를 명확히 전달하고, 필요시 부작용이나 주의사항을 포함하세요.
        """
        
        response = await self.llm.ainvoke(response_prompt)
        
        return {
            "final_response": response.content,
            "messages": [AIMessage(content=response.content)],
            "context": {
                "tools_used": [r.get("tool") for r in tool_results if r.get("success")],
                "total_results": len(tool_results)
            }
        }
    
    def should_use_agent(self, state: InfoRetrievalToolState) -> str:
        """Agent 사용 여부 결정"""
        # 복잡한 쿼리인 경우 Agent 사용
        query = state.get("query", "")
        if len(query.split()) > 10 or "그리고" in query or "또한" in query:
            return "agent_execution"
        return "execute_tools"
    
    def _build_graph(self) -> StateGraph:
        """Subgraph 구성"""
        workflow = StateGraph(InfoRetrievalToolState)
        
        # 노드 추가
        workflow.add_node("analyze_query", self.analyze_query_node)
        workflow.add_node("execute_tools", self.execute_tools_node)
        workflow.add_node("agent_execution", self.agent_execution_node)
        workflow.add_node("synthesize_response", self.synthesize_response_node)
        
        # 시작점
        workflow.add_edge(START, "analyze_query")
        
        # 조건부 라우팅: Agent 사용 여부
        workflow.add_conditional_edges(
            "analyze_query",
            self.should_use_agent,
            {
                "execute_tools": "execute_tools",
                "agent_execution": "agent_execution"
            }
        )
        
        # Tool 실행 후 응답 합성
        workflow.add_edge("execute_tools", "synthesize_response")
        
        # Agent 실행 후 응답 합성
        workflow.add_edge("agent_execution", "synthesize_response")
        
        # 종료
        workflow.add_edge("synthesize_response", END)
        
        # 그래프 컴파일
        return workflow.compile()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor에서 호출하는 메인 처리 함수"""
        logger.info("InfoRetrieval with Tools processing")
        
        # 진행 상황 보고를 위한 정보 추출
        progress_info = state.get("progress_info", {})
        session_id = progress_info.get("session_id") or state.get("session_id")
        
        # 진행 상황 업데이트 가능 여부 확인
        if session_id:
            from app.api.v1.chat_stream import update_progress
            
            # 도구 검색 시작 알림
            update_progress(session_id, {
                "message": "의약품 및 관련 정보 검색 중...",
                "active_agent": "info_retrieval"
            })
        
        # 입력 state를 subgraph state로 변환
        subgraph_state = InfoRetrievalToolState(
            messages=state.get("messages", []),
            query="",
            tool_calls=[],
            tool_results=[],
            final_response="",
            context={},
            error=None
        )
        
        # Subgraph 실행
        try:
            result = await self.graph.ainvoke(subgraph_state)
            
            # 진행 상황 업데이트
            if session_id:
                tools_used = result.get("context", {}).get("tools_used", [])
                update_progress(session_id, {
                    "message": f"정보 검색 완료 (도구 {len(tools_used)}개 사용)",
                    "active_agent": "info_retrieval"
                })
            
            return {
                "messages": result.get("messages", []),
                "agent_outputs": {
                    "info_retrieval": {
                        "query": result.get("query"),
                        "tools_used": result.get("context", {}).get("tools_used", []),
                        "tool_results": result.get("tool_results", []),
                        "response": result.get("final_response"),
                        "context": result.get("context", {})
                    }
                },
                "next_agent": None
            }
            
        except Exception as e:
            logger.error(f"InfoRetrieval with Tools error: {e}")
            
            # 오류 상황 보고
            if session_id:
                update_progress(session_id, {
                    "message": "정보 검색 중 오류 발생",
                    "active_agent": "info_retrieval",
                    "status": "error"
                })
            
            return {
                "messages": [AIMessage(content=f"정보 검색 중 오류가 발생했습니다: {str(e)}")],
                "agent_outputs": {"info_retrieval": {"error": str(e)}},
                "next_agent": None
            }


# Subgraph 생성 함수
def create_info_retrieval_with_tools():
    """Tool을 사용하는 InfoRetrieval Subgraph 생성"""
    return InfoRetrievalWithTools()