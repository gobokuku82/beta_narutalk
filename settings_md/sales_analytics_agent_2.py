"""
Sales Analytics Agent - Complete implementation with LangGraph 0.6.x Context API
Full compliance with Context API patterns and best practices
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

# Import our state and context definitions
from .states_final import (
    AgentContext,
    SalesState,
    SubgraphContext,
    create_agent_context,
    create_sales_initial_state,
    filter_context_for_subgraph,
)

logger = logging.getLogger(__name__)


class SalesAnalyticsAgent:
    """
    Sales Analytics Agent following LangGraph 0.6.x Context API patterns
    
    Architecture:
    - Receives context from supervisor/orchestrator
    - Manages SalesState for workflow
    - Orchestrates subgraphs without direct tool usage
    - Returns partial state updates from all nodes
    """
    
    def __init__(self):
        """Initialize the Sales Analytics Agent"""
        self.agent_name = "sales_analytics_agent"
        
        # Initialize LLM for planning (if available)
        self._init_llm()
        
        # Build the workflow graph
        self._build_graph()
        
        # Initialize subgraphs (lazy loading)
        self.data_collection_subgraph = None
        self.analysis_subgraph = None
        
        logger.info(f"Initialized {self.agent_name}")
    
    def _init_llm(self):
        """Initialize LLM for planning"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.planner_llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=api_key
            )
            self.use_llm_planning = True
            logger.info("LLM planning enabled")
        else:
            self.planner_llm = None
            self.use_llm_planning = False
            logger.info("LLM planning disabled - using rule-based planning")
    
    def _build_graph(self):
        """
        Build the workflow graph with Context API compliance
        """
        # Create StateGraph with both state and context schemas
        self.workflow = StateGraph(
            state_schema=SalesState,
            context_schema=AgentContext
        )
        
        # Add nodes - all follow (state: SalesState, runtime: Runtime[AgentContext]) signature
        if self.use_llm_planning:
            # LLM-based planning flow
            self.workflow.add_node("plan", self.plan_execution)
            self.workflow.add_node("execute", self.execute_plan)
            self.workflow.add_node("format", self.format_results)
            
            # Define edges
            self.workflow.add_edge(START, "plan")
            self.workflow.add_edge("plan", "execute")
            self.workflow.add_edge("execute", "format")
            self.workflow.add_edge("format", END)
        else:
            # Rule-based flow (fallback)
            self.workflow.add_node("parse", self.parse_query)
            self.workflow.add_node("process", self.process_query)
            self.workflow.add_node("format", self.format_results)
            
            # Define edges
            self.workflow.add_edge(START, "parse")
            self.workflow.add_edge("parse", "process")
            self.workflow.add_edge("process", "format")
            self.workflow.add_edge("format", END)
        
        logger.info("Workflow graph built successfully")
    
    # ================ Core Node Functions ================
    # All nodes follow the pattern: (state: SalesState, runtime: Runtime[AgentContext]) -> Dict
    
    async def plan_execution(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Plan execution using LLM
        
        Args:
            state: Current workflow state
            runtime: Runtime with context
            
        Returns:
            Partial state update with execution plan
        """
        try:
            # Get query from state (it should be set in initial state)
            query = state.get("query", "")
            
            # Get optional original query from context
            original_query = runtime.context.get("original_query", query)
            
            # Access required context fields safely
            user_id = runtime.context["user_id"]  # Required field
            
            logger.info(f"Planning execution for user {user_id}: {original_query}")
            
            # Build planning prompt
            prompt = self._build_planning_prompt(original_query, state)
            
            # Get LLM response
            response = await self.planner_llm.ainvoke([
                SystemMessage(content="You are an intelligent execution planner for sales analytics."),
                HumanMessage(content=prompt)
            ])
            
            # Parse plan
            plan = self._parse_llm_response(response.content)
            
            logger.info(f"Execution plan created: {plan}")
            
            # Return partial update (only what changed)
            return {
                "execution_plan": plan,
                "execution_step": "planned"
            }
            
        except KeyError as e:
            logger.error(f"Missing required context: {e}")
            return {
                "status": "failed",
                "execution_step": "planning_error",
                "errors": [f"Missing required context: {str(e)}"]
            }
        except Exception as e:
            logger.error(f"Planning error: {e}")
            return {
                "status": "failed",
                "execution_step": "planning_error",
                "execution_plan": {"use_sql": True, "reasoning": str(e)},
                "errors": [str(e)]
            }
    
    async def execute_plan(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Execute the planned operations
        
        Args:
            state: Current workflow state with plan
            runtime: Runtime with context
            
        Returns:
            Partial state update with results
        """
        try:
            plan = state.get("execution_plan", {})
            
            # Access context
            session_id = runtime.context["session_id"]
            logger.info(f"Executing plan for session {session_id}")
            
            results = {}
            
            # Execute based on plan
            if plan.get("use_sql"):
                # Direct SQL execution
                sql_result = await self._execute_sql(state, runtime)
                results["sql"] = sql_result
            
            if "data_collection" in plan.get("use_subgraphs", []):
                # Invoke data collection subgraph
                collection_result = await self._invoke_data_collection(state, runtime)
                results["collection"] = collection_result
            
            if "analysis" in plan.get("use_subgraphs", []):
                # Invoke analysis subgraph
                analysis_result = await self._invoke_analysis(state, runtime, plan)
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
    
    async def parse_query(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Parse query for rule-based processing
        
        Args:
            state: Current workflow state
            runtime: Runtime with context
            
        Returns:
            Partial state update with parsed query
        """
        try:
            query = state.get("query", "")
            
            # Simple parsing logic
            parsed = {
                "action": "query",
                "target": "sales_data"
            }
            
            # Extract employee name if present
            if "김" in query or "이" in query or "박" in query:
                for word in query.split():
                    if any(surname in word for surname in ["김", "이", "박"]):
                        parsed["employee_name"] = word
                        break
            
            # Extract period
            if "월" in query:
                parsed["period"] = "monthly"
            elif "주" in query:
                parsed["period"] = "weekly"
            elif "일" in query:
                parsed["period"] = "daily"
            
            logger.info(f"Parsed query: {parsed}")
            
            return {
                "parsed_query": parsed,
                "execution_step": "parsed"
            }
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return {
                "status": "failed",
                "execution_step": "parse_error",
                "errors": [str(e)]
            }
    
    async def process_query(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Process parsed query (rule-based)
        
        Args:
            state: Current workflow state
            runtime: Runtime with context
            
        Returns:
            Partial state update with results
        """
        try:
            parsed = state.get("parsed_query", {})
            
            # Simple SQL generation
            sql = self._generate_sql_from_parsed(parsed)
            
            # Mock execution for demonstration
            results = [
                {"employee": parsed.get("employee_name", "Unknown"), 
                 "sales": 1000000,
                 "achievement": 95.5}
            ]
            
            return {
                "generated_sql": sql,
                "sql_result": results,
                "execution_step": "processed"
            }
            
        except Exception as e:
            logger.error(f"Process error: {e}")
            return {
                "status": "failed",
                "execution_step": "process_error",
                "errors": [str(e)]
            }
    
    async def format_results(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Format results for presentation
        
        Args:
            state: Current workflow state
            runtime: Runtime with context
            
        Returns:
            Partial state update with formatted results
        """
        try:
            # Get language preference from context
            language = runtime.context.get("language", "ko")
            
            # Format based on available results
            execution_results = state.get("execution_results", {})
            sql_result = state.get("sql_result", [])
            
            formatted = self._format_output(execution_results, sql_result, language)
            
            # Create final report
            report = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "query": state.get("query", ""),
                "results_count": len(sql_result),
                "formatted_output": formatted
            }
            
            return {
                "status": "completed",
                "execution_step": "formatted",
                "formatted_result": formatted,
                "final_report": report
            }
            
        except Exception as e:
            logger.error(f"Format error: {e}")
            return {
                "status": "failed",
                "execution_step": "format_error",
                "errors": [str(e)]
            }
    
    # ================ Subgraph Integration ================
    
    async def _invoke_data_collection(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Invoke data collection subgraph"""
        try:
            # Lazy load subgraph
            if not self.data_collection_subgraph:
                from .subgraphs import DataCollectionSubgraph
                self.data_collection_subgraph = DataCollectionSubgraph()
            
            # Create subgraph context (filtered)
            subgraph_context = filter_context_for_subgraph(
                dict(runtime.context),
                self.agent_name
            )
            
            # Add specific paths
            subgraph_context["db_paths"] = {
                "performance": "sales_performance.db",
                "targets": "sales_targets.db",
                "clients": "clients.db"
            }
            
            # Prepare subgraph state
            subgraph_state = {
                "query_params": state.get("parsed_query", {}),
                "status": "pending"
            }
            
            # Compile and execute subgraph
            graph = self.data_collection_subgraph.build_graph()
            app = graph.compile()
            
            result = await app.ainvoke(
                subgraph_state,
                context=subgraph_context
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Data collection error: {e}")
            return {"error": str(e)}
    
    async def _invoke_analysis(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext],
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke analysis subgraph"""
        try:
            # Lazy load subgraph
            if not self.analysis_subgraph:
                from .subgraphs import AnalysisSubgraph
                self.analysis_subgraph = AnalysisSubgraph()
            
            # Create subgraph context
            subgraph_context = filter_context_for_subgraph(
                dict(runtime.context),
                self.agent_name
            )
            
            # Add analysis hints
            subgraph_context["suggested_tools"] = plan.get("use_tools", [])
            subgraph_context["analysis_depth"] = plan.get("analysis_depth", "normal")
            
            # Prepare subgraph state
            subgraph_state = {
                "input_data": state.get("collected_data", {}),
                "status": "pending"
            }
            
            # Compile and execute
            graph = self.analysis_subgraph.build_graph()
            app = graph.compile()
            
            result = await app.ainvoke(
                subgraph_state,
                context=subgraph_context
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {"error": str(e)}
    
    # ================ Helper Methods ================
    
    def _build_planning_prompt(self, query: str, state: SalesState) -> str:
        """Build prompt for LLM planning"""
        return f"""
Plan execution for this sales analytics query: {query}

Available components:
1. Direct SQL: Simple database queries
2. Data Collection Subgraph: Multi-source data gathering
3. Analysis Subgraph: Advanced analytics with tools

Return JSON:
{{
    "use_sql": true/false,
    "use_subgraphs": ["data_collection", "analysis"],
    "use_tools": ["calculation", "trend"],
    "analysis_depth": "shallow/normal/deep",
    "reasoning": "explanation"
}}
"""
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response to extract plan"""
        try:
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
        except:
            # Fallback plan
            return {
                "use_sql": True,
                "use_subgraphs": [],
                "reasoning": "Failed to parse LLM response"
            }
    
    def _generate_sql_from_parsed(self, parsed: Dict[str, Any]) -> str:
        """Generate SQL from parsed query"""
        employee = parsed.get("employee_name", "%")
        period = parsed.get("period", "monthly")
        
        return f"""
        SELECT employee_name, SUM(sales_amount) as total_sales, 
               AVG(achievement_rate) as avg_achievement
        FROM sales_performance
        WHERE employee_name LIKE '{employee}'
        GROUP BY employee_name
        """
    
    async def _execute_sql(self, state: SalesState, runtime: Runtime[AgentContext]) -> Dict[str, Any]:
        """Execute SQL query"""
        # This would connect to actual database
        # For now, return mock data
        return {
            "rows": [
                {"employee": "김철수", "sales": 1500000, "achievement": 98.5}
            ],
            "count": 1
        }
    
    def _format_output(
        self,
        execution_results: Dict[str, Any],
        sql_result: List[Dict[str, Any]],
        language: str
    ) -> str:
        """Format output for user"""
        lines = []
        
        if language == "ko":
            lines.append("=== 판매 분석 결과 ===")
            
            if sql_result:
                lines.append("\n[직접 조회 결과]")
                for row in sql_result[:5]:
                    lines.append(f"- 직원: {row.get('employee', 'N/A')}")
                    lines.append(f"  매출: {row.get('sales', 0):,}원")
                    lines.append(f"  달성률: {row.get('achievement', 0)}%")
            
            if execution_results:
                if "analysis" in execution_results:
                    lines.append("\n[분석 결과]")
                    analysis = execution_results["analysis"]
                    if "insights" in analysis:
                        for insight in analysis["insights"][:3]:
                            lines.append(f"• {insight}")
        else:
            lines.append("=== Sales Analysis Results ===")
            # English formatting...
        
        return "\n".join(lines)
    
    # ================ Public Interface ================
    
    async def run(
        self,
        query: str,
        user_id: str,
        session_id: str,
        **context_kwargs
    ) -> Dict[str, Any]:
        """
        Run the sales analytics agent
        
        Args:
            query: User query
            user_id: User identifier
            session_id: Session identifier
            **context_kwargs: Additional context fields
            
        Returns:
            Execution result with final report
        """
        # Create context
        context = create_agent_context(
            user_id=user_id,
            session_id=session_id,
            original_query=query,
            **context_kwargs
        )
        
        # Create initial state
        initial_state = create_sales_initial_state(query=query)
        
        # Compile workflow with checkpointer
        async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
            app = self.workflow.compile(checkpointer=checkpointer)
            
            # Execute workflow
            result = await app.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": f"{session_id}_sales"}},
                context=context
            )
            
            return result
    
    async def run_from_supervisor(
        self,
        supervisor_state: Dict[str, Any],
        supervisor_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run agent when called by supervisor
        
        Args:
            supervisor_state: State from supervisor
            supervisor_context: Context from supervisor
            
        Returns:
            Agent execution result
        """
        # Extract query from supervisor state
        query = supervisor_state.get("user_query", "")
        
        # Create agent context from supervisor context
        context = create_agent_context(
            user_id=supervisor_context["user_id"],
            session_id=supervisor_context["session_id"],
            original_query=query,
            intent_result=supervisor_state.get("intent_result"),
            supervisor_context=supervisor_context
        )
        
        # Create initial state
        initial_state = create_sales_initial_state(
            query=query,
            employee_name=supervisor_state.get("extracted_employee"),
            period=supervisor_state.get("extracted_period", "monthly")
        )
        
        # Compile and run
        app = self.workflow.compile()
        
        result = await app.ainvoke(
            initial_state,
            context=context
        )
        
        return result


# ================ Example Usage ================

async def main():
    """Example usage of SalesAnalyticsAgent"""
    
    # Create agent
    agent = SalesAnalyticsAgent()
    
    # Run with query
    result = await agent.run(
        query="김철수의 이번달 판매 실적을 분석해주세요",
        user_id="user123",
        session_id="session456",
        language="ko",
        api_keys={"openai": os.getenv("OPENAI_API_KEY")},
        feature_flags={"use_advanced_analytics": True}
    )
    
    # Print results
    print("Status:", result.get("status"))
    print("Result:", result.get("formatted_result"))
    print("Report:", result.get("final_report"))


if __name__ == "__main__":
    asyncio.run(main())
