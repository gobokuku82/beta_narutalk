"""
Sales Analytics Agent - Sales performance analysis
Fully compliant with LangGraph 0.6.x Context API with consistent context access
Refactored for clean architecture with proper separation of concerns
"""

from typing import Dict, Any, List, Type, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
import sqlite3
import asyncio
from pathlib import Path
import logging
from datetime import datetime, timedelta
import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..core.base_agent import BaseAgent
from ..core.states import SalesState
from ..core.context import AgentContext
from ..core.config import Config
from ..tools import SQLGenerator, SQLExecutor
from ..subgraphs import DataCollectionSubgraph, AnalysisSubgraph

logger = logging.getLogger(__name__)


class SalesAnalyticsAgent(BaseAgent):
    """
    Agent for analyzing sales performance
    Architecture:
    - Agent: Orchestration only (no direct tool usage)
    - DataCollectionSubgraph: Pure data collection (no tools)
    - AnalysisSubgraph: Autonomous tool usage based on hints
    
    Context Access Pattern:
    - Use bracket notation [] for required fields (TypedDict guarantee)
    - Use .get() for optional fields with defaults
    - Never use direct attribute access (runtime.context.field)
    """

    def __init__(self):
        # Set LLM planning flag BEFORE calling super().__init__
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.planner_llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=api_key
            )
            self.use_llm_planning = True
        else:
            self.planner_llm = None
            self.use_llm_planning = False
            logger.warning("No OpenAI API key found, falling back to rule-based planning")

        # Now call super().__init__ which will call _build_graph
        super().__init__("sales_analytics_agent")
        self.sales_db_path = Config.get_database_path("sales")
        self.sql_generator = SQLGenerator()
        self.sql_executor = SQLExecutor()

        # Initialize Subgraphs (Tools are managed by subgraphs)
        self.data_collection_subgraph = DataCollectionSubgraph()
        self.analysis_subgraph = AnalysisSubgraph()

        # Execution logger for learning
        self.execution_logs = []

    def _get_state_schema(self) -> Type:
        """Get the state schema for this agent"""
        return SalesState

    def _build_graph(self):
        """Build the sales analytics workflow with LLM planning"""
        # StateGraph with context_schema following LangGraph 0.6.x Context API
        self.workflow = StateGraph(SalesState, context_schema=AgentContext)

        # Add nodes - LLM planning workflow
        self.workflow.add_node("llm_planning", self.llm_planning)
        self.workflow.add_node("execute_plan", self.execute_plan)
        self.workflow.add_node("format_result", self.format_result)

        # Legacy nodes (kept for fallback)
        self.workflow.add_node("parse_query", self.parse_query)
        self.workflow.add_node("generate_sql", self.generate_sql)
        self.workflow.add_node("execute_sql", self.execute_sql)

        # Conditional routing based on LLM availability
        if self.use_llm_planning:
            # LLM planning flow
            self.workflow.add_edge(START, "llm_planning")
            self.workflow.add_edge("llm_planning", "execute_plan")
            self.workflow.add_edge("execute_plan", "format_result")
            self.workflow.add_edge("format_result", END)
        else:
            # Legacy flow (fallback)
            self.workflow.add_edge(START, "parse_query")
            self.workflow.add_edge("parse_query", "generate_sql")
            self.workflow.add_edge("generate_sql", "execute_sql")
            self.workflow.add_edge("execute_sql", "format_result")
            self.workflow.add_edge("format_result", END)

    # ==================== Helper Methods for Context Access ====================
    
    def _get_context_value(self, runtime: Runtime[AgentContext], key: str, default: Any = None) -> Any:
        """
        Safely get value from context with consistent pattern
        
        Args:
            runtime: Runtime object with context
            key: Key to retrieve
            default: Default value if key doesn't exist or is None
            
        Returns:
            Value from context or default
        """
        if hasattr(runtime, 'context') and runtime.context:
            # For TypedDict, use dictionary-style access
            if isinstance(runtime.context, dict):
                return runtime.context.get(key, default)
            # Fallback for other types (shouldn't happen with TypedDict)
            return getattr(runtime.context, key, default)
        return default

    def _get_required_context(self, runtime: Runtime[AgentContext], key: str) -> Any:
        """
        Get required context value (raises KeyError if missing)
        
        Args:
            runtime: Runtime object with context
            key: Required key
            
        Returns:
            Value from context
            
        Raises:
            KeyError: If required key is missing
        """
        if hasattr(runtime, 'context') and runtime.context:
            # TypedDict guarantees these keys exist
            return runtime.context[key]
        raise KeyError(f"Required context key '{key}' is missing")

    # ==================== Text2SQL Node Functions ====================
    # All nodes now receive Runtime[AgentContext] and return partial updates

    async def parse_query(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Parse the user query to extract key information

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with parsed query
        """
        try:
            # Get original query - optional field with fallback to state
            original_query = self._get_context_value(
                runtime, 
                'original_query', 
                state.get("query", "")
            )
            
            # Get required user_id
            user_id = self._get_required_context(runtime, 'user_id')
            
            self.logger.info(f"Parsing query for user {user_id}: {original_query}")

            # Use the SQL generator to parse the query
            parsed = self.sql_generator.parse_query(original_query)
            self.logger.info(f"Parsed query components: {parsed}")

            # Return partial update (LangGraph 0.6.x pattern)
            return {
                "status": "processing",
                "execution_step": "query_parsed",
                "parsed_query": parsed
            }

        except KeyError as e:
            self.logger.error(f"Missing required context: {e}")
            return {
                "status": "failed",
                "execution_step": "context_error",
                "parsed_query": {}
            }
        except Exception as e:
            self.logger.error(f"Error parsing query: {e}")
            return {
                "status": "failed",
                "execution_step": "parsing_failed",
                "parsed_query": {}
            }

    async def generate_sql(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Generate SQL query from parsed components using LLM or rule-based approach

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with generated SQL
        """
        try:
            # Get required session_id
            session_id = self._get_required_context(runtime, 'session_id')
            
            # Get optional original query
            original_query = self._get_context_value(
                runtime,
                'original_query',
                state.get("query", "")
            )
            
            self.logger.info(f"Generating SQL for session: {session_id}")

            parsed_query = state.get("parsed_query", {})

            # Try LLM-based SQL generation first if available
            if self.sql_generator.use_llm:
                try:
                    # Get optional intent result from context
                    intent_result = self._get_context_value(runtime, "intent_result", None)

                    # Use LLM to generate SQL
                    sql, explanation = await self.sql_generator.generate_sql_with_llm(
                        original_query,
                        parsed_query,
                        intent_result
                    )

                    self.logger.info("Using LLM-generated SQL")
                except Exception as llm_error:
                    self.logger.warning(f"LLM SQL generation failed, falling back to rule-based: {llm_error}")
                    sql, explanation = self.sql_generator.generate_sql(parsed_query)
            else:
                sql, explanation = self.sql_generator.generate_sql(parsed_query)

            # Validate SQL for safety
            if not self.sql_generator.validate_sql(sql):
                return {
                    "status": "failed",
                    "execution_step": "sql_validation_failed",
                    "generated_sql": sql
                }

            self.logger.info(f"Generated SQL: {sql}")
            self.logger.info(f"Explanation: {explanation}")

            # Return partial update
            return {
                "execution_step": "sql_generated",
                "generated_sql": sql
            }

        except KeyError as e:
            self.logger.error(f"Missing required context: {e}")
            return {
                "status": "failed",
                "execution_step": "context_error",
                "generated_sql": ""
            }
        except Exception as e:
            self.logger.error(f"Error generating SQL: {e}")
            return {
                "execution_step": "sql_generation_failed",
                "generated_sql": ""
            }

    async def execute_sql(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Execute SQL query against the database

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with query results
        """
        try:
            # Get required user_id
            user_id = self._get_required_context(runtime, 'user_id')
            self.logger.info(f"Executing SQL for user: {user_id}")

            generated_sql = state.get("generated_sql", "")

            if not generated_sql:
                return {
                    "status": "failed",
                    "execution_step": "no_sql_to_execute",
                    "sql_result": []
                }

            # Execute SQL using the executor tool
            results, error = self.sql_executor.execute_query(generated_sql)

            if error:
                self.logger.error(f"SQL execution error: {error}")
                return {
                    "status": "failed",
                    "execution_step": "sql_execution_failed",
                    "sql_result": [],
                    "formatted_result": f"SQL 실행 오류: {error}"
                }

            self.logger.info(f"SQL executed successfully, got {len(results)} rows")

            # Return partial update
            return {
                "execution_step": "sql_executed",
                "sql_result": results
            }

        except KeyError as e:
            self.logger.error(f"Missing required context: {e}")
            return {
                "status": "failed",
                "execution_step": "context_error",
                "sql_result": []
            }
        except Exception as e:
            self.logger.error(f"Error executing SQL: {e}")
            return {
                "status": "failed",
                "execution_step": "sql_execution_error",
                "sql_result": []
            }

    async def format_result(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Format SQL results for user presentation

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with formatted result
        """
        try:
            # Get required session_id
            session_id = self._get_required_context(runtime, 'session_id')
            
            # Get optional original query
            original_query = self._get_context_value(
                runtime,
                'original_query',
                state.get("query", "")
            )
            
            self.logger.info(f"Formatting results for session: {session_id}")

            sql_result = state.get("sql_result", [])
            parsed_query = state.get("parsed_query", {})
            execution_results = state.get("execution_results", {})

            # Format based on what was executed
            if execution_results:
                formatted = self.format_execution_results(execution_results)
            else:
                # Legacy SQL formatting
                formatted = self.sql_executor.format_results(sql_result)
                if parsed_query.get("name"):
                    name = parsed_query["name"]
                    formatted = f"{name}님의 조회 결과:\n\n{formatted}"

            # Create final report structure
            final_report = {
                "status": "success",
                "query": original_query,
                "parsed": parsed_query,
                "results_count": len(sql_result),
                "formatted_output": formatted,
                "execution_plan": state.get("execution_plan", {}),
                "raw_results": sql_result[:5] if sql_result else []
            }

            self.logger.info("Results formatted successfully")

            # Return partial update
            return {
                "status": "completed",
                "execution_step": "result_formatted",
                "formatted_result": formatted,
                "final_report": final_report
            }

        except KeyError as e:
            self.logger.error(f"Missing required context: {e}")
            return {
                "status": "failed",
                "execution_step": "context_error",
                "formatted_result": "컨텍스트 오류",
                "final_report": {"status": "error", "error": str(e)}
            }
        except Exception as e:
            self.logger.error(f"Error formatting result: {e}")
            return {
                "status": "failed",
                "execution_step": "formatting_failed",
                "formatted_result": "결과 포맷팅 실패",
                "final_report": {"status": "error", "error": str(e)}
            }

    # ==================== LLM Planning Methods ====================

    async def llm_planning(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        LLM-based execution planning for the agent
        Agent only decides orchestration, not tool usage

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with execution plan
        """
        try:
            # Get query from optional context or state
            query = self._get_context_value(
                runtime,
                'original_query',
                state.get("query", "")
            )
            
            self.logger.info(f"LLM planning for query: {query}")

            # Build prompt for LLM
            prompt = f"""You are planning execution for SalesAnalyticsAgent.
Query: {query}

Available components:
1. Subgraphs:
   - data_collection: Collect data from multiple databases (performance_db, target_db, clients_db)
   - analysis: Analyze collected data (the subgraph will autonomously use tools)

2. Tools that analysis subgraph can use (provide as hints only):
   - calculation: Calculate achievement rate, growth rate, market share
   - trend: Analyze trends, make predictions, detect seasonality
   - cross_db: Cross-database analysis for comprehensive insights

3. Direct SQL: For simple queries that need single table access

Decision needed:
- Which subgraphs should be used?
- What tool hints should be given to analysis subgraph?
- Is simple SQL sufficient?
- What analysis depth is needed?

Consider:
- Use data_collection when multiple data sources are needed
- Use analysis for complex analytics (it will choose tools autonomously)
- Suggest tools that might be helpful, but the subgraph decides
- Use SQL for simple direct queries

Return JSON format:
{{
    "use_subgraphs": ["data_collection", "analysis"],
    "use_tools": ["calculation", "trend"],  // Hints for analysis subgraph
    "use_sql": false,
    "analysis_depth": "normal",  // shallow, normal, or deep
    "reasoning": "Brief explanation of why this plan was chosen"
}}"""

            # Get LLM response
            response = await self.planner_llm.ainvoke([
                SystemMessage(content="You are an intelligent execution planner for sales analytics. Create an efficient execution plan."),
                HumanMessage(content=prompt)
            ])

            # Parse response
            try:
                content = response.content.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                plan = json.loads(content)
                self.logger.info(f"Execution plan created: {plan}")

                # Log execution for learning
                self.log_execution(query, plan)

                # Return partial update
                return {
                    "execution_plan": plan,
                    "execution_step": "plan_created"
                }

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {e}")
                return {
                    "execution_plan": {
                        "use_sql": True,
                        "use_subgraphs": [],
                        "use_tools": [],
                        "reasoning": "Failed to parse LLM response, falling back to SQL"
                    },
                    "execution_step": "plan_fallback"
                }

        except Exception as e:
            self.logger.error(f"Error in LLM planning: {e}")
            return {
                "execution_plan": {
                    "use_sql": True,
                    "use_subgraphs": [],
                    "use_tools": [],
                    "reasoning": f"Planning error: {str(e)}"
                },
                "execution_step": "plan_error"
            }

    async def execute_plan(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Execute the plan created by LLM
        Agent orchestrates subgraphs without directly using tools

        Args:
            state: Current workflow state with execution plan
            runtime: Runtime with context access

        Returns:
            Partial state update with execution results
        """
        try:
            plan = state.get("execution_plan", {})
            
            # Get query from optional context or state
            query = self._get_context_value(
                runtime,
                'original_query',
                state.get("query", "")
            )
            
            self.logger.info(f"Executing plan for query: {query}")

            results = {}

            # 1. Execute Data Collection Subgraph if needed (Tool-free)
            if "data_collection" in plan.get("use_subgraphs", []):
                self.logger.info("Executing data_collection subgraph")
                collection_result = await self.invoke_data_collection_subgraph(state, runtime)
                results["collected_data"] = collection_result
                # Update state for next subgraph
                state["collected_data"] = collection_result

            # 2. Execute Analysis Subgraph if needed (with tool hints)
            if "analysis" in plan.get("use_subgraphs", []):
                self.logger.info("Executing analysis subgraph with tool hints")

                # Pass tool hints and depth to the subgraph
                analysis_params = {
                    "suggested_tools": plan.get("use_tools", []),
                    "analysis_depth": plan.get("analysis_depth", "normal")
                }

                analysis_result = await self.invoke_analysis_subgraph_with_params(
                    state, runtime, analysis_params
                )
                results["analysis_result"] = analysis_result

            # 3. Execute SQL if needed (for simple direct queries)
            if plan.get("use_sql", False):
                self.logger.info("Executing SQL query")
                parsed = self.sql_generator.parse_query(query)
                state["parsed_query"] = parsed

                sql, explanation = self.sql_generator.generate_sql(parsed)
                state["generated_sql"] = sql

                sql_results, error = self.sql_executor.execute_query(sql)
                if not error:
                    results["sql_result"] = sql_results
                else:
                    results["sql_error"] = error

            # Return partial update with results
            return {
                "execution_results": results,
                "execution_step": "execution_completed",
                "sql_result": results.get("sql_result", [])
            }

        except Exception as e:
            self.logger.error(f"Error executing plan: {e}")
            return {
                "execution_results": {},
                "execution_step": "execution_error"
            }

    # ==================== Subgraph Integration Methods ====================

    async def invoke_data_collection_subgraph(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Invoke data collection subgraph (pure data collection, no tools)"""
        try:
            # Build subgraph
            collection_graph = self.data_collection_subgraph.build_graph()

            # Prepare state for subgraph
            parsed_query = state.get("parsed_query", {})
            collection_state = {
                "query_params": {
                    "person_name": parsed_query.get("person_name") or parsed_query.get("name"),
                    "period": parsed_query.get("month") or parsed_query.get("period"),
                    "client_id": parsed_query.get("client_id"),
                    "team": parsed_query.get("team")
                },
                "performance_data": [],
                "target_data": [],
                "client_data": [],
                "aggregated_performance": {},
                "aggregated_target": {},
                "aggregated_client": {},
                "collection_status": "pending",
                "errors": [],
                "execution_time": 0
            }

            # Compile subgraph
            compiled_graph = collection_graph.compile()

            # Create context for subgraph from runtime context (consistent pattern)
            subgraph_context = {
                "user_id": self._get_required_context(runtime, 'user_id'),
                "session_id": self._get_required_context(runtime, 'session_id'),
                "request_id": self._get_context_value(runtime, 'request_id', "unknown"),
                "db_paths": {
                    "performance": "database/storage/sales_performance/sales_performance_db.db",
                    "target": "database/storage/sales_performance/sales_target_db.db",
                    "clients": "database/storage/sales_performance/clients_db.db"
                },
                "timeout": 30,
                "parallel_execution": True
            }

            # Execute subgraph with context
            result = await compiled_graph.ainvoke(
                collection_state,
                context=subgraph_context
            )

            self.logger.info(f"Data collection completed with status: {result.get('collection_status')}")
            return result

        except KeyError as e:
            self.logger.error(f"Missing required context for subgraph: {e}")
            return {"error": f"Context error: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error invoking data collection subgraph: {e}")
            return {"error": str(e)}

    async def invoke_analysis_subgraph(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Invoke analysis subgraph (legacy method for backward compatibility)"""
        return await self.invoke_analysis_subgraph_with_params(state, runtime, {})

    async def invoke_analysis_subgraph_with_params(
        self,
        state: SalesState,
        runtime: Runtime[AgentContext],
        analysis_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke analysis subgraph with parameters (autonomous tool usage)"""
        try:
            # Build subgraph
            analysis_graph = self.analysis_subgraph.build_graph()

            # Get collected data from state
            collected_data = state.get("collected_data", {})

            # Prepare state for analysis
            analysis_state = {
                "performance_data": collected_data.get("performance_data", []),
                "target_data": collected_data.get("target_data", []),
                "client_data": collected_data.get("client_data", []),
                "aggregated_performance": collected_data.get("aggregated_performance", {}),
                "aggregated_target": collected_data.get("aggregated_target", {}),
                "aggregated_client": collected_data.get("aggregated_client", {}),
                "analysis_type": "comprehensive",
                "analysis_params": {
                    "suggested_tools": analysis_params.get("suggested_tools", []),
                    "analysis_depth": analysis_params.get("analysis_depth", "normal")
                },
                "basic_metrics": {},
                "trend_analysis": {},
                "comparative_analysis": {},
                "predictions": {},
                "insights": [],
                "analysis_report": {},
                "analysis_status": "pending",
                "errors": [],
                "execution_time": 0
            }

            # Compile subgraph
            compiled_graph = analysis_graph.compile()

            # Create context for subgraph with tool suggestions (consistent pattern)
            subgraph_context = {
                "user_id": self._get_required_context(runtime, 'user_id'),
                "session_id": self._get_required_context(runtime, 'session_id'),
                "request_id": self._get_context_value(runtime, 'request_id', "unknown"),
                "analysis_depth": analysis_params.get("analysis_depth", "normal"),
                "include_predictions": True,
                "language": self._get_context_value(runtime, 'language', "ko"),
                "timeout": 30,
                "suggested_tools": analysis_params.get("suggested_tools", [])
            }

            # Execute subgraph with context
            result = await compiled_graph.ainvoke(
                analysis_state,
                context=subgraph_context
            )

            self.logger.info(f"Analysis completed with status: {result.get('analysis_status')}")
            return result

        except KeyError as e:
            self.logger.error(f"Missing required context for subgraph: {e}")
            return {"error": f"Context error: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error invoking analysis subgraph: {e}")
            return {"error": str(e)}

    # ==================== Public Run Method ====================
    
    async def run(
        self, 
        query: str, 
        user_id: str, 
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Public method to run the agent
        
        Args:
            query: User query
            user_id: User identifier (required)
            session_id: Session identifier (optional, generated if not provided)
            request_id: Request identifier (optional, generated if not provided)
            **kwargs: Additional context parameters
            
        Returns:
            Execution result
        """
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        import uuid
        
        # Generate IDs if not provided
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        # Prepare context following AgentContext schema
        context = {
            "user_id": user_id,
            "session_id": session_id,
            "request_id": request_id,
            "original_query": query,
            # Optional fields from kwargs
            "api_keys": kwargs.get("api_keys", {}),
            "permissions": kwargs.get("permissions", []),
            "language": kwargs.get("language", "ko"),
            "debug_mode": kwargs.get("debug_mode", False),
            "feature_flags": kwargs.get("feature_flags", {}),
            # Additional fields that might be passed from supervisor
            "intent_result": kwargs.get("intent_result"),
            "supervisor_context": kwargs.get("supervisor_context", {})
        }
        
        # Create initial state
        initial_state = self._create_initial_state({"query": query})
        
        # Compile and run with checkpointer
        async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
            app = self.workflow.compile(checkpointer=checkpointer)
            
            result = await app.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": f"sales_{session_id}"}},
                context=context
            )
            
            return result

    # ==================== Helper Methods ====================

    def format_execution_results(self, results: Dict[str, Any]) -> str:
        """Format execution results for presentation"""
        formatted = []

        # Format SQL results if present
        if "sql_result" in results and results["sql_result"]:
            formatted.append("SQL 조회 결과:")
            formatted.append(self.sql_executor.format_results(results["sql_result"]))

        # Format collected data if present
        if "collected_data" in results:
            data = results["collected_data"]
            if data.get("aggregated_performance"):
                formatted.append("\n실적 데이터:")
                perf = data["aggregated_performance"]
                if "monthly_totals" in perf:
                    formatted.append(f"  월별 실적: {perf['monthly_totals']}")

        # Format analysis results if present
        if "analysis_result" in results:
            analysis = results["analysis_result"]

            if analysis.get("basic_metrics"):
                metrics = analysis["basic_metrics"]
                if "average_achievement" in metrics:
                    formatted.append(f"\n평균 달성률: {metrics['average_achievement']:.1f}%")

            if analysis.get("trend_analysis"):
                trend = analysis["trend_analysis"]
                if "performance_trend" in trend:
                    formatted.append(f"\n트렌드 분석 완료")

            if analysis.get("insights"):
                formatted.append("\n인사이트:")
                for insight in analysis["insights"][:3]:
                    formatted.append(f"  - {insight}")

        return "\n".join(formatted) if formatted else "결과 없음"

    def log_execution(self, query: str, plan: Dict[str, Any]):
        """Log execution for learning"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "plan": plan
        }
        self.execution_logs.append(log_entry)

        # Save to file for persistence
        try:
            with open("agent_execution_logs.jsonl", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.warning(f"Failed to save execution log: {e}")
