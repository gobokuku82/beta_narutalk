"""
Sales Analytics Agent
Complete implementation following LangGraph 0.6.x Context API patterns
Clean separation of Config, Context, and State
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

# Import from clean architecture
from ..core.config import Config
from ..core.context import (
    create_agent_context,
    create_subgraph_context,
    extract_api_keys_from_env,
    merge_with_config_defaults
)
from ..core.states import (
    SalesState,
    create_sales_initial_state,
    merge_state_updates,
    get_state_summary
)

logger = logging.getLogger(__name__)


class SalesAnalyticsAgent:
    """
    Sales Analytics Agent with clean architecture
    - Config: System settings (static)
    - Context: Runtime metadata (read-only)
    - State: Workflow data (mutable)
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize agent with optional config override
        
        Args:
            config: Optional Config instance (uses default if None)
        """
        self.agent_name = "sales_analytics_agent"
        self.config = config or Config()
        
        # Initialize LLM based on config
        self._init_llm()
        
        # Build workflow
        self._build_graph()
        
        # Lazy load subgraphs
        self.subgraphs = {}
        
        logger.info(f"Initialized {self.agent_name}")
    
    def _init_llm(self):
        """Initialize LLM based on config and environment"""
        # Check if LLM planning is enabled in config
        if not self.config.FEATURES.get("enable_llm_planning", True):
            self.planner_llm = None
            self.use_llm_planning = False
            logger.info("LLM planning disabled by config")
            return
        
        # Get API key from environment (will be passed via context at runtime)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.planner_llm = None
            self.use_llm_planning = False
            logger.warning("No OpenAI API key in environment, LLM planning disabled")
            return
        
        # Get model config
        model_config = self.config.get_model_config("planning")
        
        # Initialize LLM
        self.planner_llm = ChatOpenAI(
            api_key=api_key,  # Will be overridden by context at runtime
            **model_config
        )
        self.use_llm_planning = True
        logger.info(f"LLM planning enabled with model: {model_config['model']}")
    
    def _build_graph(self):
        """Build workflow graph"""
        # Import context type here to avoid circular import
        from ..core.context import AgentContext
        
        # Create graph with State and Context schemas
        self.workflow = StateGraph(
            state_schema=SalesState,
            context_schema=AgentContext
        )
        
        # Add nodes based on planning mode
        if self.use_llm_planning:
            self.workflow.add_node("plan", self.plan_execution)
            self.workflow.add_node("execute", self.execute_plan)
            self.workflow.add_node("format", self.format_results)
            
            self.workflow.add_edge(START, "plan")
            self.workflow.add_edge("plan", "execute")
            self.workflow.add_edge("execute", "format")
            self.workflow.add_edge("format", END)
        else:
            self.workflow.add_node("analyze", self.analyze_query)
            self.workflow.add_node("collect", self.collect_data)
            self.workflow.add_node("process", self.process_data)
            self.workflow.add_node("format", self.format_results)
            
            self.workflow.add_edge(START, "analyze")
            self.workflow.add_edge("analyze", "collect")
            self.workflow.add_edge("collect", "process")
            self.workflow.add_edge("process", "format")
            self.workflow.add_edge("format", END)
        
        logger.info("Workflow graph built")
    
    # ================ Node Functions ================
    # All nodes: (state: SalesState, runtime: Runtime[AgentContext]) -> Dict

    async def plan_execution(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Plan execution using LLM"""
        try:
            # Get query from state
            query = state.get("query", "")

            # Access context - required fields with []
            user_id = runtime.context["user_id"]

            # Optional fields with .get()
            api_key = runtime.context.get("api_keys", {}).get("openai_api_key")
            language = runtime.context.get("language", "ko")
            
            logger.info(f"Planning for user {user_id}: {query}")
            
            # Update LLM API key if provided in context
            if api_key and self.planner_llm:
                self.planner_llm.api_key = api_key
            
            # Build prompt
            prompt = self._build_planning_prompt(query, language)
            
            # Get LLM response with timeout from config
            timeout = runtime.context.get("timeout_overrides", {}).get(
                "llm",
                self.config.TIMEOUTS["llm"]
            )
            
            response = await asyncio.wait_for(
                self.planner_llm.ainvoke([
                    SystemMessage(content="You are a sales analytics planner."),
                    HumanMessage(content=prompt)
                ]),
                timeout=timeout
            )
            
            # Parse plan
            plan = self._parse_llm_response(response.content)
            
            # Return partial state update
            return {
                "execution_plan": plan,
                "execution_step": "planned"
            }
            
        except asyncio.TimeoutError:
            logger.error("Planning timeout")
            return {
                "status": "failed",
                "execution_step": "planning_timeout",
                "errors": ["Planning timeout exceeded"]
            }
        except Exception as e:
            logger.error(f"Planning error: {e}")
            return {
                "status": "failed",
                "execution_step": "planning_error",
                "errors": [str(e)]
            }
    
    async def execute_plan(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Execute the plan"""
        try:
            plan = state.get("execution_plan", {})
            session_id = runtime.context["session_id"]
            
            logger.info(f"Executing plan for session {session_id}")
            
            results = {}
            
            # Execute based on plan
            if plan.get("use_sql"):
                sql_result = await self._execute_sql(state, runtime)
                results["sql"] = sql_result

            if "data_collection" in plan.get("use_subgraphs", []):
                collection_result = await self._invoke_subgraph(
                    "data_collection", state, runtime
                )
                results["collection"] = collection_result

            if "analysis" in plan.get("use_subgraphs", []):
                analysis_result = await self._invoke_subgraph(
                    "analysis", state, runtime, plan
                )
                results["analysis"] = analysis_result
            
            # Return partial update
            return {
                "execution_results": results,
                "execution_step": "executed",
                "status": "processing"
            }
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {
                "status": "failed",
                "execution_step": "execution_error",
                "errors": [str(e)]
            }
    
    async def analyze_query(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Analyze query (rule-based)"""
        try:
            query = state.get("query", "")
            
            # Simple rule-based analysis
            parsed = {"action": "query", "target": "sales"}
            
            # Extract entities
            if "월" in query:
                parsed["period"] = "monthly"
            elif "주" in query:
                parsed["period"] = "weekly"
            elif "일" in query:
                parsed["period"] = "daily"
            else:
                parsed["period"] = state.get("period", "monthly")
            
            # Extract employee name
            for word in query.split():
                if any(surname in word for surname in ["김", "이", "박", "최", "정"]):
                    parsed["employee_name"] = word
                    break
            
            return {
                "parsed_query": parsed,
                "execution_step": "analyzed"
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {
                "status": "failed",
                "execution_step": "analysis_error",
                "errors": [str(e)]
            }
    
    async def collect_data(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Collect data from databases"""
        try:
            parsed = state.get("parsed_query", {})
            
            # Get database paths from config
            db_paths = {
                "performance": str(self.config.get_database_path("sales_performance")),
                "targets": str(self.config.get_database_path("sales_targets")),
                "clients": str(self.config.get_database_path("clients"))
            }
            
            # Mock data collection
            collected = {
                "performance": [
                    {"employee": parsed.get("employee_name", "Unknown"),
                     "sales": 1500000,
                     "date": "2024-01"}
                ],
                "targets": [
                    {"employee": parsed.get("employee_name", "Unknown"),
                     "target": 2000000,
                     "date": "2024-01"}
                ]
            }
            
            return {
                "collected_data": collected,
                "execution_step": "collected"
            }
            
        except Exception as e:
            logger.error(f"Collection error: {e}")
            return {
                "status": "failed",
                "execution_step": "collection_error",
                "errors": [str(e)]
            }
    
    async def process_data(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Process collected data"""
        try:
            collected = state.get("collected_data", {})
            
            # Calculate statistics
            stats = {}
            if collected.get("performance") and collected.get("targets"):
                perf = collected["performance"][0]
                target = collected["targets"][0]
                
                stats["achievement_rate"] = (perf["sales"] / target["target"]) * 100
                stats["gap"] = target["target"] - perf["sales"]
            
            # Generate insights
            insights = []
            if stats.get("achievement_rate", 0) > 90:
                insights.append("목표 달성률이 우수합니다")
            elif stats.get("achievement_rate", 0) > 70:
                insights.append("목표 달성률이 양호합니다")
            else:
                insights.append("목표 달성률 개선이 필요합니다")
            
            return {
                "statistics": stats,
                "insights": insights,
                "execution_step": "processed"
            }
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {
                "status": "failed",
                "execution_step": "processing_error",
                "errors": [str(e)]
            }
    
    async def format_results(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Format final results"""
        try:
            # Get language from context
            language = runtime.context.get("language", "ko")
            
            # Get all results
            execution_results = state.get("execution_results", {})
            statistics = state.get("statistics", {})
            insights = state.get("insights", [])
            
            # Format output
            if language == "ko":
                formatted = self._format_korean(
                    execution_results, statistics, insights
                )
            else:
                formatted = self._format_english(
                    execution_results, statistics, insights
                )
            
            # Create final report
            report = {
                "status": "success",
                "query": state.get("query", ""),
                "timestamp": datetime.now().isoformat(),
                "statistics": statistics,
                "insights": insights,
                "formatted_output": formatted
            }
            
            # Mark as complete
            return {
                "status": "completed",
                "execution_step": "formatted",
                "formatted_result": formatted,
                "final_report": report,
                "end_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Formatting error: {e}")
            return {
                "status": "failed",
                "execution_step": "formatting_error",
                "errors": [str(e)]
            }
    
    # ================ Helper Methods ================
    
    def _build_planning_prompt(self, query: str, language: str) -> str:
        """Build planning prompt"""
        if language == "ko":
            return f"""
다음 판매 분석 질의를 위한 실행 계획을 수립하세요: {query}

사용 가능한 구성 요소:
1. SQL: 직접 데이터베이스 조회
2. 데이터 수집: 여러 소스에서 데이터 수집
3. 분석: 고급 분석 도구 사용

JSON 형식으로 반환:
{{
    "use_sql": true/false,
    "use_subgraphs": ["data_collection", "analysis"],
    "reasoning": "설명"
}}
"""
        else:
            return f"""
Plan execution for this sales query: {query}

Available components:
1. SQL: Direct database query
2. Data Collection: Gather from multiple sources
3. Analysis: Advanced analytics

Return JSON:
{{
    "use_sql": true/false,
    "use_subgraphs": ["data_collection", "analysis"],
    "reasoning": "explanation"
}}
"""
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response"""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except:
            return {"use_sql": True, "use_subgraphs": [], "reasoning": "Parse failed"}
    
    def _format_korean(
        self,
        execution_results: Dict,
        statistics: Dict,
        insights: List[str]
    ) -> str:
        """Format results in Korean"""
        lines = ["=== 판매 분석 결과 ===\n"]
        
        if statistics:
            lines.append("[통계]")
            for key, value in statistics.items():
                if key == "achievement_rate":
                    lines.append(f"• 달성률: {value:.1f}%")
                elif key == "gap":
                    lines.append(f"• 목표 차이: {value:,.0f}원")
        
        if insights:
            lines.append("\n[인사이트]")
            for insight in insights:
                lines.append(f"• {insight}")
        
        return "\n".join(lines)
    
    def _format_english(
        self,
        execution_results: Dict,
        statistics: Dict,
        insights: List[str]
    ) -> str:
        """Format results in English"""
        lines = ["=== Sales Analysis Results ===\n"]
        
        if statistics:
            lines.append("[Statistics]")
            for key, value in statistics.items():
                if key == "achievement_rate":
                    lines.append(f"• Achievement Rate: {value:.1f}%")
                elif key == "gap":
                    lines.append(f"• Target Gap: ${value:,.0f}")
        
        if insights:
            lines.append("\n[Insights]")
            for insight in insights:
                lines.append(f"• {insight}")
        
        return "\n".join(lines)
    
    async def _execute_sql(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Execute SQL query"""
        # Mock implementation
        return {
            "rows": [{"employee": "김철수", "sales": 1500000}],
            "count": 1
        }
    
    async def _invoke_subgraph(
        self,
        subgraph_name: str,
        state: SalesState,
        runtime: Runtime[AgentContext],
        plan: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Invoke a subgraph"""
        # Create subgraph context
        subgraph_context = create_subgraph_context(
            parent_context=dict(runtime.context),
            parent_agent=self.agent_name,
            subgraph_name=subgraph_name
        )
        
        # Add specific parameters
        if plan:
            subgraph_context["suggested_tools"] = plan.get("use_tools", [])
            subgraph_context["analysis_depth"] = plan.get("analysis_depth", "normal")
        
        # Mock subgraph execution
        return {"status": "completed", "data": {}}
    
    # ================ Public Interface ================
    
    async def run(
        self,
        query: str,
        user_id: str,
        session_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run the agent
        
        Args:
            query: User query
            user_id: User identifier
            session_id: Session identifier
            **kwargs: Additional context fields
            
        Returns:
            Final state with results
        """
        # Extract API keys from environment if not provided
        if "api_keys" not in kwargs:
            kwargs["api_keys"] = extract_api_keys_from_env()
        
        # Create context
        context = create_agent_context(
            user_id=user_id,
            session_id=session_id,
            original_query=query,
            **kwargs
        )
        
        # Merge with config defaults
        context = merge_with_config_defaults(context, self.config)
        
        # Create initial state
        initial_state = create_sales_initial_state(
            query=query,
            employee_name=kwargs.get("employee_name"),
            period=kwargs.get("period", "monthly")
        )
        
        # Get checkpoint path from config
        checkpoint_path = self.config.get_checkpoint_path(
            self.agent_name, session_id
        )
        
        # Compile and run
        async with AsyncSqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
            app = self.workflow.compile(checkpointer=checkpointer)
            
            result = await app.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": f"{session_id}_sales"}},
                context=context
            )
            
            # Log summary
            summary = get_state_summary(result)
            logger.info(f"Execution complete: {summary}")
            
            return result


# ================ Example Usage ================

async def main():
    """Example usage"""
    
    # Create agent with default config
    agent = SalesAnalyticsAgent()
    
    # Run query
    result = await agent.run(
        query="김철수의 이번달 판매 실적 분석",
        user_id="user123",
        session_id="session456",
        language="ko"
    )
    
    # Print results
    print("Status:", result.get("status"))
    print("Results:", result.get("formatted_result"))


if __name__ == "__main__":
    asyncio.run(main())
