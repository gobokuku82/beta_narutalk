"""
Analytics Agent with Tools Integration
Tool을 사용하는 데이터분석 에이전트
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
from app.tools.analysis_tools import (
    DataAnalysisTool,
    TrendAnalysisTool,
    StatisticalAnalysisTool,
    ComparativeAnalysisTool
)


class AnalyticsToolState(TypedDict):
    """Tool을 사용하는 데이터분석 State"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    analysis_type: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    analysis_results: Dict[str, Any]
    insights: List[str]
    visualization_data: Dict[str, Any]
    final_report: str
    context: Dict[str, Any]
    error: Optional[str]


class AnalyticsWithTools:
    """Tool을 사용하는 데이터분석 Subgraph"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.3,  # 분석의 일관성을 위해 낮은 temperature
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Tools 초기화
        self.tools = [
            DataAnalysisTool(),
            TrendAnalysisTool(),
            StatisticalAnalysisTool(),
            ComparativeAnalysisTool()
        ]
        
        # Tool 이름 매핑
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # Agent 프롬프트
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 제약 산업의 데이터 분석 전문가 AI 어시스턴트입니다.
            사용 가능한 도구들을 활용하여 데이터를 분석하고 인사이트를 도출하세요.
            
            도구 사용 가이드:
            - data_analysis: 매출, 성과, 고객 데이터 분석
            - trend_analysis: 시계열 트렌드 분석 및 예측
            - statistical_analysis: 통계적 분석 수행
            - comparative_analysis: 비교 분석
            
            항상 데이터 기반의 정확한 분석과 실행 가능한 인사이트를 제공하세요."""),
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
    
    async def analyze_data_query_node(self, state: AnalyticsToolState) -> Dict:
        """데이터 분석 쿼리 분석 및 Tool 선택"""
        logger.info("Analyzing data analytics query")
        
        query = state.get("query", "")
        if not query and state.get("messages"):
            last_message = state["messages"][-1]
            query = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else str(last_message)
        
        # LLM으로 필요한 도구 결정
        tool_selection_prompt = f"""
        사용자 쿼리: {query}
        
        이 데이터 분석 요청을 처리하기 위해 필요한 도구를 선택하세요.
        사용 가능한 도구:
        - data_analysis: 일반적인 데이터 분석
        - trend_analysis: 트렌드 및 시계열 분석
        - statistical_analysis: 통계 분석
        - comparative_analysis: 비교 분석
        
        JSON 형식으로 응답하세요:
        {{
            "analysis_type": "sales/performance/market/customer/trend",
            "tools": ["tool1", "tool2"],
            "data_type": "type of data",
            "period": "analysis period",
            "metrics": ["metric1", "metric2"]
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
            for tool_name in analysis.get("tools", ["data_analysis"]):
                if tool_name in self.tool_map:
                    params = {
                        "query": query,
                        "analysis_type": analysis.get("analysis_type", "sales"),
                        "period": analysis.get("period", datetime.now().strftime("%Y-%m"))
                    }
                    
                    # 도구별 특수 파라미터
                    if tool_name == "data_analysis":
                        params["data_type"] = analysis.get("analysis_type", "sales")
                        params["metrics"] = analysis.get("metrics", ["total", "average"])
                    elif tool_name == "trend_analysis":
                        params["metric"] = analysis.get("metrics", ["revenue"])[0] if analysis.get("metrics") else "revenue"
                        params["periods"] = 6
                        params["forecast"] = True
                    elif tool_name == "statistical_analysis":
                        params["dataset"] = analysis.get("data_type", "sales_data")
                        params["methods"] = ["mean", "median", "std"]
                    
                    tool_calls.append({
                        "tool": tool_name,
                        "params": params,
                        "status": "pending"
                    })
            
            return {
                "query": query,
                "analysis_type": analysis.get("analysis_type", "sales"),
                "tool_calls": tool_calls,
                "context": {"analysis": analysis}
            }
            
        except Exception as e:
            logger.error(f"Tool selection failed: {e}")
            # Fallback
            return {
                "query": query,
                "analysis_type": "sales",
                "tool_calls": [{
                    "tool": "data_analysis",
                    "params": {
                        "data_type": "sales",
                        "period": datetime.now().strftime("%Y-%m"),
                        "metrics": ["total", "average", "growth"]
                    },
                    "status": "pending"
                }]
            }
    
    async def execute_analytics_tools_node(self, state: AnalyticsToolState) -> Dict:
        """분석 도구 실행"""
        logger.info("Executing analytics tools")
        
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
                if tool_name == "data_analysis":
                    result = await tool._arun(
                        data_type=params.get("data_type", "sales"),
                        period=params.get("period", datetime.now().strftime("%Y-%m")),
                        metrics=params.get("metrics", None)
                    )
                elif tool_name == "trend_analysis":
                    result = await tool._arun(
                        metric=params.get("metric", "revenue"),
                        periods=params.get("periods", 6),
                        forecast=params.get("forecast", False)
                    )
                elif tool_name == "statistical_analysis":
                    result = await tool._arun(
                        dataset=params.get("dataset", "sales_data"),
                        methods=params.get("methods", None),
                        confidence_level=0.95
                    )
                elif tool_name == "comparative_analysis":
                    result = await tool._arun(
                        query=params.get("query", "")
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
    
    async def agent_analytics_execution_node(self, state: AnalyticsToolState) -> Dict:
        """LangChain Agent 실행 (대안)"""
        logger.info("Executing LangChain agent for analytics")
        
        query = state.get("query", "")
        
        try:
            # Agent Executor 실행
            result = await self.agent_executor.ainvoke({
                "input": query,
                "messages": state.get("messages", [])
            })
            
            # 중간 단계 추출
            tool_results = []
            analysis_results = {}
            
            for action, observation in result.get("intermediate_steps", []):
                tool_results.append({
                    "tool": action.tool,
                    "input": action.tool_input,
                    "output": observation,
                    "success": True
                })
                
                # 분석 결과 수집
                if isinstance(observation, dict):
                    if action.tool == "data_analysis":
                        analysis_results["data_analysis"] = observation
                    elif action.tool == "trend_analysis":
                        analysis_results["trend_analysis"] = observation
                    elif action.tool == "statistical_analysis":
                        analysis_results["statistical_analysis"] = observation
            
            return {
                "tool_results": tool_results,
                "analysis_results": analysis_results,
                "final_report": result.get("output", ""),
                "context": {"agent_execution": "completed"}
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "error": str(e),
                "final_report": f"데이터 분석 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def generate_insights_node(self, state: AnalyticsToolState) -> Dict:
        """분석 결과에서 인사이트 도출"""
        logger.info("Generating insights from analysis")
        
        tool_results = state.get("tool_results", [])
        insights = []
        visualization_data = {}
        
        for result in tool_results:
            if not result.get("success"):
                continue
            
            tool_name = result.get("tool", "unknown")
            data = result.get("data", {})
            
            if tool_name == "data_analysis" and data:
                # 데이터 분석 인사이트
                summary = data.get("summarize", {})
                if summary.get("key_findings"):
                    insights.extend(summary["key_findings"])
                if summary.get("recommendations"):
                    insights.extend(summary["recommendations"])
                
                # 시각화 데이터
                if "analyze" in data:
                    visualization_data["metrics"] = data["analyze"]
            
            elif tool_name == "trend_analysis" and data:
                # 트렌드 분석 인사이트
                trend = data.get("trend", "")
                growth_rate = data.get("growth_rate", 0)
                
                if trend:
                    insights.append(f"트렌드: {trend} (성장률: {growth_rate}%)")
                
                if "forecast" in data:
                    insights.append("예측: 향후 3개월간 지속적인 성장 예상")
                
                # 시각화 데이터
                visualization_data["trend_data"] = data.get("historical_data", [])
                visualization_data["forecast_data"] = data.get("forecast", [])
            
            elif tool_name == "statistical_analysis" and data:
                # 통계 분석 인사이트
                if "hypothesis_test" in data:
                    test_result = data["hypothesis_test"]
                    insights.append(f"통계적 검증: {test_result.get('conclusion', '')}")
                
                if "correlation" in data:
                    correlations = data["correlation"]
                    for key, value in correlations.items():
                        if value > 0.7:
                            insights.append(f"강한 상관관계: {key} ({value:.2f})")
                
                # 시각화 데이터
                visualization_data["statistics"] = {
                    "mean": data.get("mean"),
                    "median": data.get("median"),
                    "std_dev": data.get("std_dev")
                }
            
            elif tool_name == "comparative_analysis" and data:
                # 비교 분석 인사이트
                if "key_findings" in data:
                    insights.extend(data["key_findings"])
                
                # 시각화 데이터
                visualization_data["comparison"] = data.get("metrics", {})
        
        # 인사이트가 없는 경우 기본 인사이트 생성
        if not insights:
            insights = [
                "데이터 분석 완료",
                "추가 데이터가 필요할 수 있습니다",
                "정기적인 모니터링을 권장합니다"
            ]
        
        return {
            "insights": insights,
            "visualization_data": visualization_data
        }
    
    async def synthesize_analytics_report_node(self, state: AnalyticsToolState) -> Dict:
        """도구 결과 통합 및 최종 분석 보고서 생성"""
        logger.info("Synthesizing analytics report")
        
        query = state.get("query", "")
        tool_results = state.get("tool_results", [])
        analysis_type = state.get("analysis_type", "sales")
        insights = state.get("insights", [])
        visualization_data = state.get("visualization_data", {})
        
        # Agent가 이미 보고서를 생성한 경우
        if state.get("final_report"):
            return {
                "messages": [AIMessage(content=state["final_report"])]
            }
        
        # 보고서 생성
        current_datetime = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')
        report_parts = [f"## 데이터 분석 보고서\n"]
        report_parts.append(f"**분석 요청**: {query[:100]}")
        report_parts.append(f"**분석 유형**: {analysis_type}")
        report_parts.append(f"**분석 일시**: {current_datetime}\n")
        
        # 주요 지표
        if visualization_data.get("metrics"):
            report_parts.append("### 주요 지표")
            metrics = visualization_data["metrics"]
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    report_parts.append(f"- {key}: {value:,}" if isinstance(value, int) else f"- {key}: {value:.2f}")
                else:
                    report_parts.append(f"- {key}: {value}")
            report_parts.append("")
        
        # 트렌드 분석
        if visualization_data.get("trend_data"):
            report_parts.append("### 트렌드 분석")
            trend_data = visualization_data["trend_data"]
            if trend_data:
                # 최근 3개 데이터 포인트
                for data_point in trend_data[-3:]:
                    report_parts.append(f"- {data_point.get('period', 'N/A')}: {data_point.get('value', 0):,}")
            
            if visualization_data.get("forecast_data"):
                report_parts.append("\n**예측 (향후 3개월)**")
                for forecast in visualization_data["forecast_data"][:3]:
                    report_parts.append(f"- {forecast.get('period', 'N/A')}: {forecast.get('predicted_value', 0):,}")
            report_parts.append("")
        
        # 통계 분석
        if visualization_data.get("statistics"):
            report_parts.append("### 통계 분석")
            stats = visualization_data["statistics"]
            if stats.get("mean"):
                report_parts.append(f"- 평균: {stats['mean']:,.2f}")
            if stats.get("median"):
                report_parts.append(f"- 중앙값: {stats['median']:,.2f}")
            if stats.get("std_dev"):
                report_parts.append(f"- 표준편차: {stats['std_dev']:,.2f}")
            report_parts.append("")
        
        # 비교 분석
        if visualization_data.get("comparison"):
            report_parts.append("### 비교 분석")
            comparison = visualization_data["comparison"]
            for key, value in comparison.items():
                if isinstance(value, dict):
                    report_parts.append(f"\n**{key}**")
                    for sub_key, sub_value in value.items():
                        report_parts.append(f"- {sub_key}: {sub_value}")
                else:
                    report_parts.append(f"- {key}: {value}")
            report_parts.append("")
        
        # 인사이트
        if insights:
            report_parts.append("### 주요 인사이트")
            for i, insight in enumerate(insights[:10], 1):  # 상위 10개
                report_parts.append(f"{i}. {insight}")
            report_parts.append("")
        
        # 권고사항
        report_parts.append("### 권고사항")
        if analysis_type == "sales":
            report_parts.append("- 매출 성과가 높은 제품/지역에 집중 투자")
            report_parts.append("- 저조한 영역에 대한 개선 전략 수립")
        elif analysis_type == "performance":
            report_parts.append("- 우수 성과자에 대한 인센티브 제공")
            report_parts.append("- 성과 개선이 필요한 영역에 교육 강화")
        else:
            report_parts.append("- 지속적인 데이터 모니터링 실시")
            report_parts.append("- 데이터 기반 의사결정 프로세스 강화")
        
        final_report = "\n".join(report_parts)
        
        # 메타데이터
        metadata = {
            "analysis_type": analysis_type,
            "tools_used": [r["tool"] for r in tool_results if r.get("success")],
            "insights_count": len(insights),
            "has_visualization": bool(visualization_data),
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "final_report": final_report,
            "analysis_results": {"insights": insights, "visualization": visualization_data},
            "messages": [AIMessage(content=final_report)],
            "context": metadata
        }
    
    def should_use_agent(self, state: AnalyticsToolState) -> str:
        """Agent 사용 여부 결정"""
        # 복잡한 분석인 경우 Agent 사용
        query = state.get("query", "")
        tool_calls = state.get("tool_calls", [])
        
        # 여러 도구가 필요하거나 복잡한 경우
        if len(tool_calls) > 2 or "종합" in query or "전체" in query:
            return "agent_analytics_execution"
        return "execute_analytics_tools"
    
    def _build_graph(self) -> StateGraph:
        """Subgraph 구성"""
        workflow = StateGraph(AnalyticsToolState)
        
        # 노드 추가
        workflow.add_node("analyze_data_query", self.analyze_data_query_node)
        workflow.add_node("execute_analytics_tools", self.execute_analytics_tools_node)
        workflow.add_node("agent_analytics_execution", self.agent_analytics_execution_node)
        workflow.add_node("generate_insights", self.generate_insights_node)
        workflow.add_node("synthesize_analytics_report", self.synthesize_analytics_report_node)
        
        # 시작점
        workflow.add_edge(START, "analyze_data_query")
        
        # 조건부 라우팅: Agent 사용 여부
        workflow.add_conditional_edges(
            "analyze_data_query",
            self.should_use_agent,
            {
                "execute_analytics_tools": "execute_analytics_tools",
                "agent_analytics_execution": "agent_analytics_execution"
            }
        )
        
        # Tool 실행 후 인사이트 생성
        workflow.add_edge("execute_analytics_tools", "generate_insights")
        
        # Agent 실행 후 바로 보고서 생성 (Agent가 인사이트도 생성)
        workflow.add_edge("agent_analytics_execution", "synthesize_analytics_report")
        
        # 인사이트 생성 후 보고서 합성
        workflow.add_edge("generate_insights", "synthesize_analytics_report")
        
        # 종료
        workflow.add_edge("synthesize_analytics_report", END)
        
        # 그래프 컴파일
        return workflow.compile()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor에서 호출하는 메인 처리 함수"""
        logger.info("Analytics with Tools processing")
        
        # 입력 state를 subgraph state로 변환
        subgraph_state = AnalyticsToolState(
            messages=state.get("messages", []),
            query="",
            analysis_type="",
            tool_calls=[],
            tool_results=[],
            analysis_results={},
            insights=[],
            visualization_data={},
            final_report="",
            context={},
            error=None
        )
        
        # Subgraph 실행
        try:
            result = await self.graph.ainvoke(subgraph_state)
            
            return {
                "messages": result.get("messages", []),
                "agent_outputs": {
                    "analytics": {
                        "query": result.get("query"),
                        "analysis_type": result.get("analysis_type"),
                        "tools_used": result.get("context", {}).get("tools_used", []),
                        "tool_results": result.get("tool_results", []),
                        "analysis_results": result.get("analysis_results", {}),
                        "insights": result.get("insights", []),
                        "visualization_data": result.get("visualization_data", {}),
                        "report": result.get("final_report"),
                        "context": result.get("context", {})
                    }
                },
                "next_agent": None
            }
            
        except Exception as e:
            logger.error(f"Analytics with Tools error: {e}")
            return {
                "messages": [AIMessage(content=f"데이터 분석 중 오류가 발생했습니다: {str(e)}")],
                "agent_outputs": {"analytics": {"error": str(e)}},
                "next_agent": None
            }


# Subgraph 생성 함수
def create_analytics_with_tools():
    """Tool을 사용하는 Analytics Subgraph 생성"""
    return AnalyticsWithTools()