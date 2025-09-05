"""
Compliance Agent with Tools Integration
Tool을 사용하는 규정확인 에이전트
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
from app.tools.compliance_tools import (
    ComplianceCheckTool,
    RegulatorySearchTool,
    RiskAssessmentTool,
    AuditTrailTool
)


class ComplianceToolState(TypedDict):
    """Tool을 사용하는 규정확인 State"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    compliance_type: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    compliance_report: str
    context: Dict[str, Any]
    error: Optional[str]


class ComplianceWithTools:
    """Tool을 사용하는 규정확인 Subgraph"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.2,  # 더 일관된 응답을 위해 낮은 temperature
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Tools 초기화
        self.tools = [
            ComplianceCheckTool(),
            RegulatorySearchTool(),
            RiskAssessmentTool(),
            AuditTrailTool()
        ]
        
        # Tool 이름 매핑
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # Agent 프롬프트
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 제약 산업의 컴플라이언스 전문가 AI 어시스턴트입니다.
            사용 가능한 도구들을 활용하여 규정 준수를 확인하고 리스크를 평가하세요.
            
            도구 사용 가이드:
            - compliance_check: 컴플라이언스 확인
            - regulatory_search: 규제 검색
            - risk_assessment: 리스크 평가
            - audit_trail: 감사 추적
            
            항상 정확한 규정을 인용하고 리스크를 명확히 평가하세요."""),
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
    
    async def analyze_compliance_query_node(self, state: ComplianceToolState) -> Dict:
        """컴플라이언스 쿼리 분석 및 Tool 선택"""
        logger.info("Analyzing compliance query")
        
        query = state.get("query", "")
        if not query and state.get("messages"):
            last_message = state["messages"][-1]
            query = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else str(last_message)
        
        # LLM으로 필요한 도구 결정
        tool_selection_prompt = f"""
        사용자 쿼리: {query}
        
        이 컴플라이언스 관련 요청을 처리하기 위해 필요한 도구를 선택하세요.
        사용 가능한 도구:
        - compliance_check: 규정 준수 확인
        - regulatory_search: 규제 검색
        - risk_assessment: 리스크 평가
        - audit_trail: 감사 기록 추적
        
        JSON 형식으로 응답하세요:
        {{
            "compliance_type": "drug_regulation/clinical_trial/marketing/quality",
            "tools": ["tool1", "tool2"],
            "target": "확인 대상",
            "jurisdiction": "KFDA/FDA/EMA"
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
            for tool_name in analysis.get("tools", ["compliance_check"]):
                if tool_name in self.tool_map:
                    tool_calls.append({
                        "tool": tool_name,
                        "params": {
                            "query": query,
                            "compliance_type": analysis.get("compliance_type", "drug_regulation"),
                            "target": analysis.get("target", query[:50]),
                            "jurisdiction": analysis.get("jurisdiction", None)
                        },
                        "status": "pending"
                    })
            
            return {
                "query": query,
                "compliance_type": analysis.get("compliance_type", "drug_regulation"),
                "tool_calls": tool_calls,
                "context": {"analysis": analysis}
            }
            
        except Exception as e:
            logger.error(f"Tool selection failed: {e}")
            # Fallback
            return {
                "query": query,
                "compliance_type": "drug_regulation",
                "tool_calls": [{
                    "tool": "compliance_check",
                    "params": {
                        "check_type": "drug_regulation",
                        "target": query[:50]
                    },
                    "status": "pending"
                }]
            }
    
    async def execute_compliance_tools_node(self, state: ComplianceToolState) -> Dict:
        """컴플라이언스 도구 실행"""
        logger.info("Executing compliance tools")
        
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
                if tool_name == "compliance_check":
                    result = await tool._arun(
                        check_type=params.get("compliance_type", "drug_regulation"),
                        target=params.get("target", ""),
                        regulations=None
                    )
                elif tool_name == "regulatory_search":
                    result = await tool._arun(
                        keyword=params.get("query", ""),
                        jurisdiction=params.get("jurisdiction", None),
                        category="drug"
                    )
                elif tool_name == "risk_assessment":
                    result = await tool._arun(
                        assessment_type="product",
                        target=params.get("target", ""),
                        criteria=None
                    )
                elif tool_name == "audit_trail":
                    result = await tool._arun(
                        entity=params.get("target", ""),
                        period=datetime.now().strftime("%Y-%m"),
                        scope=None
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
    
    async def agent_compliance_execution_node(self, state: ComplianceToolState) -> Dict:
        """LangChain Agent 실행 (대안)"""
        logger.info("Executing LangChain agent for compliance")
        
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
            
            # 리스크 평가 추출
            risk_assessment = {}
            if tool_results:
                for tr in tool_results:
                    if isinstance(tr.get("output"), dict):
                        if "overall_risk_level" in tr["output"]:
                            risk_assessment = tr["output"]
                            break
            
            return {
                "tool_results": tool_results,
                "risk_assessment": risk_assessment,
                "compliance_report": result.get("output", ""),
                "context": {"agent_execution": "completed"}
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "error": str(e),
                "compliance_report": f"컴플라이언스 확인 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def synthesize_compliance_report_node(self, state: ComplianceToolState) -> Dict:
        """도구 결과 통합 및 최종 컴플라이언스 보고서 생성"""
        logger.info("Synthesizing compliance report")
        
        query = state.get("query", "")
        tool_results = state.get("tool_results", [])
        compliance_type = state.get("compliance_type", "drug_regulation")
        
        # Agent가 이미 보고서를 생성한 경우
        if state.get("compliance_report"):
            return {
                "messages": [AIMessage(content=state["compliance_report"])]
            }
        
        # Tool 결과 분석
        compliance_checks = []
        regulations_found = []
        risk_factors = []
        overall_risk = "Low"
        
        for result in tool_results:
            if not result.get("success"):
                continue
            
            tool_name = result.get("tool", "unknown")
            data = result.get("data", {})
            
            if tool_name == "compliance_check" and data:
                compliance_checks.append({
                    "compliance_rate": data.get("compliance_rate", 0),
                    "issues": data.get("issues_found", []),
                    "risk_level": data.get("risk_level", "Low")
                })
                if data.get("risk_level") in ["High", "Critical"]:
                    overall_risk = data.get("risk_level")
                
            elif tool_name == "regulatory_search" and data:
                regulations_found.extend(data.get("regulations", []))
            
            elif tool_name == "risk_assessment" and data:
                risk_factors.extend(data.get("risk_factors", []))
                if data.get("overall_risk_level") in ["High", "Critical"]:
                    overall_risk = data.get("overall_risk_level")
            
            elif tool_name == "audit_trail" and data:
                compliance_checks.append({
                    "audit_compliance": data.get("compliance_rate", 0),
                    "findings": data.get("findings", [])
                })
        
        # 보고서 생성
        current_datetime = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')
        report_parts = [f"## 컴플라이언스 보고서\n"]
        report_parts.append(f"**확인 대상**: {query[:100]}")
        report_parts.append(f"**확인 유형**: {compliance_type}")
        report_parts.append(f"**확인 일시**: {current_datetime}\n")
        
        # 컴플라이언스 체크 결과
        if compliance_checks:
            report_parts.append("### 컴플라이언스 확인 결과")
            for check in compliance_checks:
                if "compliance_rate" in check:
                    report_parts.append(f"- 준수율: {check['compliance_rate']}%")
                if "issues" in check and check["issues"]:
                    report_parts.append(f"- 발견된 이슈: {len(check['issues'])}건")
                if "risk_level" in check:
                    report_parts.append(f"- 리스크 수준: {check['risk_level']}")
            report_parts.append("")
        
        # 적용 규정
        if regulations_found:
            report_parts.append("### 관련 규정")
            for reg in regulations_found[:3]:  # 상위 3개만
                report_parts.append(f"- {reg.get('title', 'Unknown')}")
                if "regulation_code" in reg:
                    report_parts.append(f"  - 규정 코드: {reg['regulation_code']}")
                if "jurisdiction" in reg:
                    report_parts.append(f"  - 관할: {reg['jurisdiction']}")
            report_parts.append("")
        
        # 리스크 평가
        report_parts.append("### 리스크 평가")
        report_parts.append(f"**종합 리스크 수준**: {overall_risk}")
        if risk_factors:
            report_parts.append("\n**주요 리스크 요인**:")
            for factor in risk_factors[:5]:  # 상위 5개
                if isinstance(factor, dict):
                    report_parts.append(f"- {factor.get('factor', 'Unknown')}: {factor.get('level', 'N/A')}")
                else:
                    report_parts.append(f"- {factor}")
        report_parts.append("")
        
        # 권고사항
        report_parts.append("### 권고사항")
        if overall_risk in ["High", "Critical"]:
            report_parts.append("- 즉시 컴플라이언스 개선 조치 필요")
            report_parts.append("- 규제 당국과의 사전 협의 검토")
            report_parts.append("- 내부 감사 실시 권장")
        elif overall_risk == "Medium":
            report_parts.append("- 정기적인 컴플라이언스 모니터링 강화")
            report_parts.append("- 발견된 이슈에 대한 개선 계획 수립")
        else:
            report_parts.append("- 현재 컴플라이언스 수준 유지")
            report_parts.append("- 정기적인 점검 지속")
        
        final_report = "\n".join(report_parts)
        
        # 메타데이터
        metadata = {
            "compliance_type": compliance_type,
            "overall_risk": overall_risk,
            "tools_used": [r["tool"] for r in tool_results if r.get("success")],
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "compliance_report": final_report,
            "risk_assessment": {"overall_risk": overall_risk, "risk_factors": risk_factors},
            "messages": [AIMessage(content=final_report)],
            "context": metadata
        }
    
    def should_use_agent(self, state: ComplianceToolState) -> str:
        """Agent 사용 여부 결정"""
        # 복잡한 컴플라이언스 확인인 경우 Agent 사용
        query = state.get("query", "")
        tool_calls = state.get("tool_calls", [])
        
        # 여러 도구가 필요하거나 복잡한 경우
        if len(tool_calls) > 2 or "전체" in query or "종합" in query:
            return "agent_compliance_execution"
        return "execute_compliance_tools"
    
    def _build_graph(self) -> StateGraph:
        """Subgraph 구성"""
        workflow = StateGraph(ComplianceToolState)
        
        # 노드 추가
        workflow.add_node("analyze_compliance_query", self.analyze_compliance_query_node)
        workflow.add_node("execute_compliance_tools", self.execute_compliance_tools_node)
        workflow.add_node("agent_compliance_execution", self.agent_compliance_execution_node)
        workflow.add_node("synthesize_compliance_report", self.synthesize_compliance_report_node)
        
        # 시작점
        workflow.add_edge(START, "analyze_compliance_query")
        
        # 조건부 라우팅: Agent 사용 여부
        workflow.add_conditional_edges(
            "analyze_compliance_query",
            self.should_use_agent,
            {
                "execute_compliance_tools": "execute_compliance_tools",
                "agent_compliance_execution": "agent_compliance_execution"
            }
        )
        
        # Tool 실행 후 보고서 합성
        workflow.add_edge("execute_compliance_tools", "synthesize_compliance_report")
        
        # Agent 실행 후 보고서 합성
        workflow.add_edge("agent_compliance_execution", "synthesize_compliance_report")
        
        # 종료
        workflow.add_edge("synthesize_compliance_report", END)
        
        # 그래프 컴파일
        return workflow.compile()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor에서 호출하는 메인 처리 함수"""
        logger.info("Compliance with Tools processing")
        
        # 입력 state를 subgraph state로 변환
        subgraph_state = ComplianceToolState(
            messages=state.get("messages", []),
            query="",
            compliance_type="",
            tool_calls=[],
            tool_results=[],
            risk_assessment={},
            compliance_report="",
            context={},
            error=None
        )
        
        # Subgraph 실행
        try:
            result = await self.graph.ainvoke(subgraph_state)
            
            return {
                "messages": result.get("messages", []),
                "agent_outputs": {
                    "compliance": {
                        "query": result.get("query"),
                        "compliance_type": result.get("compliance_type"),
                        "tools_used": result.get("context", {}).get("tools_used", []),
                        "tool_results": result.get("tool_results", []),
                        "risk_assessment": result.get("risk_assessment", {}),
                        "report": result.get("compliance_report"),
                        "context": result.get("context", {})
                    }
                },
                "next_agent": None
            }
            
        except Exception as e:
            logger.error(f"Compliance with Tools error: {e}")
            return {
                "messages": [AIMessage(content=f"컴플라이언스 확인 중 오류가 발생했습니다: {str(e)}")],
                "agent_outputs": {"compliance": {"error": str(e)}},
                "next_agent": None
            }


# Subgraph 생성 함수
def create_compliance_with_tools():
    """Tool을 사용하는 Compliance Subgraph 생성"""
    return ComplianceWithTools()