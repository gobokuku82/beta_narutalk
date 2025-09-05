"""
Document Generation Agent with Tools Integration
Tool을 사용하는 문서생성 에이전트
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
from datetime import datetime

from app.core.config import settings
from app.tools.document_tools import (
    DocumentGeneratorTool,
    ReportBuilderTool,
    TemplateManagerTool,
    DataFormatterTool
)


class DocGenerationToolState(TypedDict):
    """Tool을 사용하는 문서생성 State"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    document_type: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    generated_content: Dict[str, Any]
    final_document: str
    context: Dict[str, Any]
    error: Optional[str]


class DocGenerationWithTools:
    """Tool을 사용하는 문서생성 Subgraph"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Tools 초기화
        self.tools = [
            DocumentGeneratorTool(),
            ReportBuilderTool(),
            TemplateManagerTool(),
            DataFormatterTool()
        ]
        
        # Tool 이름 매핑
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # Agent 프롬프트
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문적인 문서 작성 AI 어시스턴트입니다.
            사용 가능한 도구들을 활용하여 고품질의 문서를 생성하세요.
            
            도구 사용 가이드:
            - document_generator: 기본 문서 생성
            - report_builder: 구조화된 보고서 작성
            - template_manager: 템플릿 기반 문서 생성
            - data_formatter: 데이터 포맷팅 및 시각화
            
            항상 정확한 정보를 포함하고 전문적인 형식을 유지하세요."""),
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
    
    async def analyze_request_node(self, state: DocGenerationToolState) -> Dict:
        """문서 요청 분석 및 Tool 선택"""
        logger.info("Analyzing document generation request")
        
        query = state.get("query", "")
        if not query and state.get("messages"):
            last_message = state["messages"][-1]
            query = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else str(last_message)
        
        # LLM으로 필요한 도구 결정
        tool_selection_prompt = f"""
        사용자 요청: {query}
        
        이 문서 생성 요청을 처리하기 위해 필요한 도구를 선택하세요.
        사용 가능한 도구:
        - document_generator: 일반 문서 생성
        - report_builder: 구조화된 보고서 작성
        - template_manager: 템플릿 기반 문서
        - data_formatter: 데이터 포맷팅
        
        JSON 형식으로 응답하세요:
        {{
            "document_type": "type",
            "tools": ["tool1", "tool2"],
            "format": "PDF/DOCX/HTML/markdown",
            "sections": ["section1", "section2"]
        }}
        """
        
        response = await self.llm.ainvoke(tool_selection_prompt)
        
        try:
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            analysis = json.loads(json_str)
            
            # Tool 호출 계획 생성
            tool_calls = []
            for tool_name in analysis.get("tools", ["document_generator"]):
                if tool_name in self.tool_map:
                    tool_calls.append({
                        "tool": tool_name,
                        "params": {
                            "query": query,
                            "document_type": analysis.get("document_type", "report"),
                            "format": analysis.get("format", "markdown")
                        },
                        "status": "pending"
                    })
            
            return {
                "query": query,
                "document_type": analysis.get("document_type", "report"),
                "tool_calls": tool_calls,
                "context": {"analysis": analysis}
            }
            
        except Exception as e:
            logger.error(f"Tool selection failed: {e}")
            # Fallback
            return {
                "query": query,
                "document_type": "report",
                "tool_calls": [{
                    "tool": "document_generator",
                    "params": {"query": query, "document_type": "report"},
                    "status": "pending"
                }]
            }
    
    async def execute_tools_node(self, state: DocGenerationToolState) -> Dict:
        """도구 실행"""
        logger.info("Executing document generation tools")
        
        tool_calls = state.get("tool_calls", [])
        tool_results = []
        
        for call in tool_calls:
            tool_name = call.get("tool")
            params = call.get("params", {})
            
            if tool_name not in self.tool_map:
                logger.warning(f"Tool {tool_name} not found")
                continue
            
            tool = self.tool_map[tool_name]
            
            try:
                logger.info(f"Executing tool: {tool_name}")
                
                # 각 도구에 맞는 입력 준비
                if tool_name == "document_generator":
                    result = await tool._arun(
                        content=params.get("query"),
                        document_type=params.get("document_type", "report"),
                        format=params.get("format", "markdown")
                    )
                elif tool_name == "report_builder":
                    analysis = state.get("context", {}).get("analysis", {})
                    result = await tool._arun(
                        title=f"Report: {params.get('query')[:50]}",
                        sections=analysis.get("sections", ["Introduction", "Body", "Conclusion"]),
                        data_sources=[],
                        format=params.get("format", "PDF")
                    )
                elif tool_name == "template_manager":
                    result = await tool._arun(
                        template_name=params.get("document_type", "drug_info"),
                        variables={"query": params.get("query")}
                    )
                elif tool_name == "data_formatter":
                    result = await tool._arun(
                        data={"query": params.get("query"), "timestamp": datetime.now().isoformat()},
                        format_type="table",
                        include_charts=True
                    )
                else:
                    continue
                
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
    
    async def agent_execution_node(self, state: DocGenerationToolState) -> Dict:
        """LangChain Agent 실행 (대안)"""
        logger.info("Executing LangChain agent for document generation")
        
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
            
            # 생성된 문서 추출
            generated_content = {}
            if tool_results:
                for tr in tool_results:
                    if isinstance(tr.get("output"), dict):
                        if "document" in tr["output"]:
                            generated_content["document"] = tr["output"]["document"]
                        elif "report" in tr["output"]:
                            generated_content["report"] = tr["output"]["report"]
                        elif "rendered_document" in tr["output"]:
                            generated_content["rendered"] = tr["output"]["rendered_document"]
            
            return {
                "tool_results": tool_results,
                "generated_content": generated_content,
                "final_document": result.get("output", ""),
                "context": {"agent_execution": "completed"}
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "error": str(e),
                "final_document": f"문서 생성 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def synthesize_document_node(self, state: DocGenerationToolState) -> Dict:
        """도구 결과 통합 및 최종 문서 생성"""
        logger.info("Synthesizing final document")
        
        query = state.get("query", "")
        tool_results = state.get("tool_results", [])
        document_type = state.get("document_type", "report")
        
        # Agent가 이미 문서를 생성한 경우
        if state.get("final_document"):
            return {
                "messages": [AIMessage(content=state["final_document"])]
            }
        
        # Tool 결과에서 콘텐츠 추출
        document_parts = []
        metadata = {
            "created_at": datetime.now().isoformat(),
            "document_type": document_type,
            "tools_used": []
        }
        
        for result in tool_results:
            if not result.get("success"):
                continue
            
            tool_name = result.get("tool", "unknown")
            data = result.get("data", {})
            metadata["tools_used"].append(tool_name)
            
            if tool_name == "document_generator" and data:
                if "document" in data:
                    document_parts.append(data["document"])
                
            elif tool_name == "report_builder" and data:
                if "report" in data and "content" in data["report"]:
                    document_parts.append(data["report"]["content"])
            
            elif tool_name == "template_manager" and data:
                if "rendered_document" in data:
                    document_parts.append(data["rendered_document"])
            
            elif tool_name == "data_formatter" and data:
                if "formatted_output" in data:
                    document_parts.append(data["formatted_output"])
        
        # 문서 조합
        if document_parts:
            final_content = "\n\n".join(document_parts)
        else:
            # Fallback: LLM으로 직접 생성
            generation_prompt = f"""
            사용자 요청: {query}
            
            문서 유형: {document_type}
            
            위 요구사항에 맞는 전문적인 문서를 작성하세요.
            """
            
            response = await self.llm.ainvoke(generation_prompt)
            final_content = response.content
        
        # 응답 메시지
        response_message = f"""문서가 성공적으로 생성되었습니다.

📄 문서 유형: {document_type}
🔧 사용된 도구: {', '.join(metadata["tools_used"]) if metadata["tools_used"] else "Direct Generation"}
📝 단어 수: {len(final_content.split())}
🕐 생성 시간: {metadata["created_at"]}

--- 문서 내용 ---
{final_content[:1000]}{'...' if len(final_content) > 1000 else ''}
        """
        
        return {
            "final_document": final_content,
            "generated_content": {"full_document": final_content},
            "messages": [AIMessage(content=response_message)],
            "context": {
                "tools_used": metadata["tools_used"],
                "document_type": document_type
            }
        }
    
    def should_use_agent(self, state: DocGenerationToolState) -> str:
        """Agent 사용 여부 결정"""
        # 복잡한 문서 요청인 경우 Agent 사용
        query = state.get("query", "")
        tool_calls = state.get("tool_calls", [])
        
        # 여러 도구가 필요하거나 복잡한 경우
        if len(tool_calls) > 2 or "복잡" in query or "상세" in query:
            return "agent_execution"
        return "execute_tools"
    
    def _build_graph(self) -> StateGraph:
        """Subgraph 구성"""
        workflow = StateGraph(DocGenerationToolState)
        
        # 노드 추가
        workflow.add_node("analyze_request", self.analyze_request_node)
        workflow.add_node("execute_tools", self.execute_tools_node)
        workflow.add_node("agent_execution", self.agent_execution_node)
        workflow.add_node("synthesize_document", self.synthesize_document_node)
        
        # 시작점
        workflow.add_edge(START, "analyze_request")
        
        # 조건부 라우팅: Agent 사용 여부
        workflow.add_conditional_edges(
            "analyze_request",
            self.should_use_agent,
            {
                "execute_tools": "execute_tools",
                "agent_execution": "agent_execution"
            }
        )
        
        # Tool 실행 후 문서 합성
        workflow.add_edge("execute_tools", "synthesize_document")
        
        # Agent 실행 후 문서 합성
        workflow.add_edge("agent_execution", "synthesize_document")
        
        # 종료
        workflow.add_edge("synthesize_document", END)
        
        # 그래프 컴파일
        return workflow.compile()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor에서 호출하는 메인 처리 함수"""
        logger.info("DocGeneration with Tools processing")
        
        # 입력 state를 subgraph state로 변환
        subgraph_state = DocGenerationToolState(
            messages=state.get("messages", []),
            query="",
            document_type="",
            tool_calls=[],
            tool_results=[],
            generated_content={},
            final_document="",
            context={},
            error=None
        )
        
        # Subgraph 실행
        try:
            result = await self.graph.ainvoke(subgraph_state)
            
            return {
                "messages": result.get("messages", []),
                "agent_outputs": {
                    "doc_generation": {
                        "query": result.get("query"),
                        "document_type": result.get("document_type"),
                        "tools_used": result.get("context", {}).get("tools_used", []),
                        "tool_results": result.get("tool_results", []),
                        "document": result.get("final_document"),
                        "context": result.get("context", {})
                    }
                },
                "next_agent": None
            }
            
        except Exception as e:
            logger.error(f"DocGeneration with Tools error: {e}")
            return {
                "messages": [AIMessage(content=f"문서 생성 중 오류가 발생했습니다: {str(e)}")],
                "agent_outputs": {"doc_generation": {"error": str(e)}},
                "next_agent": None
            }


# Subgraph 생성 함수
def create_doc_generation_with_tools():
    """Tool을 사용하는 DocGeneration Subgraph 생성"""
    return DocGenerationWithTools()