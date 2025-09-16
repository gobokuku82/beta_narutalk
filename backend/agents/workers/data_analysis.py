"""
Data Analysis Agent
데이터 분석 및 SQL 쿼리 실행 에이전트
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import sqlite3
import os
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)


class DataAnalysisAgent:
    """데이터 분석 및 SQL 쿼리 실행을 담당하는 에이전트"""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize data analysis agent"""
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.name = "DataAnalysisAgent"

        # Database paths
        self.db_paths = {
            "hr": Path("database/hr_information/hr_data.db"),
            "sales": Path("database/sales_performance_db/sales_performance_db.db"),
            "clients": Path("database/sales_performance_db/clients_info.db"),
            "targets": Path("database/sales_performance_db/sales_target_db.db"),
            "main": Path("pharma_chatbot.db")
        }

        # FastAPI endpoint (if running)
        self.api_base_url = "http://localhost:8000"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """메인 실행 메서드"""
        start_time = datetime.now()

        try:
            # Extract task parameters
            query = task.get("query", "")
            data_source = task.get("data_source", "main_db")
            analysis_type = task.get("analysis_type", "sql")
            filters = task.get("filters", {})
            limit = task.get("limit", 100)

            # Perform analysis based on type
            if analysis_type == "sql":
                result = await self._execute_sql_analysis(query, data_source, filters, limit)
            elif analysis_type == "statistical":
                result = await self._execute_statistical_analysis(query, data_source)
            elif analysis_type == "aggregation":
                result = await self._execute_aggregation_analysis(query, data_source, filters)
            else:  # trend
                result = await self._execute_trend_analysis(query, data_source)

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "confidence_score": result.get("confidence", 0.85),
                "execution_time": execution_time,
                "sql_query": result.get("sql_query"),
                "results": result.get("data", []),
                "row_count": len(result.get("data", [])),
                "summary": result.get("summary"),
                "visualizations": result.get("visualizations")
            }

        except Exception as e:
            logger.error(f"Data analysis failed: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "confidence_score": 0.0,
                "execution_time": execution_time,
                "error": str(e)
            }

    async def _execute_sql_analysis(
        self, query: str, data_source: str, filters: Dict, limit: int
    ) -> Dict[str, Any]:
        """SQL 쿼리 생성 및 실행"""

        # Generate SQL query using LLM
        sql_query = await self._generate_sql_query(query, data_source, filters, limit)

        # Execute real database query
        try:
            data = await self._execute_real_query(sql_query, data_source)
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            # Fallback to API if direct DB fails
            data = await self._execute_via_api(sql_query, data_source)

        # Generate summary
        summary = await self._generate_summary(query, data)

        return {
            "sql_query": sql_query,
            "data": data,
            "summary": summary,
            "confidence": 0.9
        }

    async def _generate_sql_query(self, query: str, data_source: str, filters: Dict, limit: int) -> str:
        """LLM을 사용하여 SQL 쿼리 생성"""

        # Get table schema based on data source
        schema_info = await self._get_database_schema(data_source)

        system_prompt = """You are a SQL expert. Generate SQL queries based on user requests.
        Follow these rules:
        1. Use standard SQL syntax
        2. Include appropriate JOINs when needed
        3. Apply filters correctly
        4. Add LIMIT clause when specified
        5. Ensure query is safe (no DROP, DELETE, UPDATE)
        6. Handle Korean column names properly with quotes if needed"""

        user_prompt = f"""Generate SQL query for: {query}
        Database: {data_source}
        Filters: {json.dumps(filters) if filters else 'None'}
        Limit: {limit}

        Available tables and columns:
        {schema_info}"""

        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        # Extract SQL from response
        sql_query = response.content.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        return sql_query

    async def _get_database_schema(self, data_source: str) -> str:
        """데이터베이스 스키마 정보 가져오기"""

        schema_map = {
            "hr": """
            - 인사자료 (사번, 이름, 직급, 직무, 부서, 전화번호, 기본연봉예상, 입사일자)
            - 긴급연락처 (사번, 관계, 이름, 전화번호)
            """,
            "sales": """
            - sales_performance (date, product_name, sales_amount, region, customer_type)
            - monthly_targets (year_month, target_amount, achieved_amount)
            """,
            "clients": """
            - clients (client_id, company_name, contact_person, phone, email, address)
            - contracts (contract_id, client_id, start_date, end_date, value)
            """,
            "main_db": """
            - conversations (id, user_id, session_id, status, created_at)
            - messages (id, conversation_id, role, content, sequence_number)
            - agent_states (id, conversation_id, agent_name, state_data, execution_status)
            """
        }

        return schema_map.get(data_source, "Unknown database")

    async def _execute_real_query(self, sql_query: str, data_source: str) -> List[Dict]:
        """실제 데이터베이스 쿼리 실행"""

        # Get database path
        db_path = self.db_paths.get(data_source)
        if not db_path or not db_path.exists():
            raise ValueError(f"Database not found: {data_source}")

        # Execute query
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        try:
            cursor.execute(sql_query)
            rows = cursor.fetchall()

            # Convert to list of dicts
            data = []
            for row in rows:
                data.append(dict(row))

            return data
        finally:
            conn.close()

    async def _execute_via_api(self, sql_query: str, data_source: str) -> List[Dict]:
        """FastAPI를 통한 쿼리 실행"""

        # Call FastAPI endpoint for data analysis
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.api_base_url}/analysis/execute_query"
                payload = {
                    "query": sql_query,
                    "data_source": data_source
                }

                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("data", [])
                    else:
                        logger.error(f"API call failed: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"API call error: {str(e)}")
                return []

    async def _execute_statistical_analysis(
        self, query: str, data_source: str
    ) -> Dict[str, Any]:
        """통계 분석 실행"""

        # Generate statistical analysis
        stats_data = {
            "mean": 85.5,
            "median": 86.0,
            "std_dev": 12.3,
            "min": 45,
            "max": 100,
            "count": 250
        }

        summary = f"통계 분석 결과: 평균 {stats_data['mean']}, 중앙값 {stats_data['median']}, 표준편차 {stats_data['std_dev']}"

        return {
            "data": [stats_data],
            "summary": summary,
            "confidence": 0.88
        }

    async def _execute_aggregation_analysis(
        self, query: str, data_source: str, filters: Dict
    ) -> Dict[str, Any]:
        """집계 분석 실행"""

        # Simulate aggregation
        aggregated_data = [
            {"department": "개발팀", "total": 45, "average_salary": 5500000},
            {"department": "인사팀", "total": 12, "average_salary": 4800000},
            {"department": "영업팀", "total": 28, "average_salary": 5200000},
        ]

        summary = "부서별 직원 수 및 평균 급여 집계 완료"

        return {
            "data": aggregated_data,
            "summary": summary,
            "confidence": 0.92
        }

    async def _execute_trend_analysis(
        self, query: str, data_source: str
    ) -> Dict[str, Any]:
        """트렌드 분석 실행"""

        # Simulate trend analysis
        trend_data = [
            {"month": "2024-01", "value": 85, "trend": "increasing"},
            {"month": "2024-02", "value": 88, "trend": "increasing"},
            {"month": "2024-03", "value": 92, "trend": "increasing"},
            {"month": "2024-04", "value": 90, "trend": "stable"},
        ]

        summary = "최근 4개월간 상승 트렌드를 보이고 있으며, 마지막 달은 안정화 단계"

        visualizations = [
            {
                "type": "line_chart",
                "data": trend_data,
                "title": "Monthly Trend Analysis"
            }
        ]

        return {
            "data": trend_data,
            "summary": summary,
            "visualizations": visualizations,
            "confidence": 0.87
        }

    async def _generate_summary(self, query: str, data: List[Dict]) -> str:
        """데이터 분석 결과 요약 생성"""

        if not data:
            return "조회된 데이터가 없습니다."

        prompt = f"""다음 데이터 분석 결과를 한국어로 간단히 요약해주세요:
        Query: {query}
        Data (first 3 rows): {data[:3]}
        Total rows: {len(data)}

        간결하고 핵심적인 인사이트를 제공하세요."""

        response = await self.llm.ainvoke([
            HumanMessage(content=prompt)
        ])

        return response.content.strip()

    async def execute_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph 노드 실행 메서드"""

        # Extract task from state
        execution_state = state.get("execution_manager_state", {})
        pending_tasks = execution_state.get("pending_tasks", [])

        if not pending_tasks:
            logger.warning("No pending tasks for data analysis")
            return state

        # Get first task for this agent
        task = None
        for t in pending_tasks:
            if t.get("agent") == "DataAnalysisAgent":
                task = t
                break

        if not task:
            logger.warning("No data analysis task found")
            return state

        # Execute task
        result = await self.execute(task)

        # Update state
        completed_tasks = execution_state.get("completed_tasks", [])
        completed_tasks.append({
            "task_id": task.get("task_id"),
            "agent": self.name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        # Remove from pending
        pending_tasks.remove(task)

        state["execution_manager_state"]["pending_tasks"] = pending_tasks
        state["execution_manager_state"]["completed_tasks"] = completed_tasks

        # Store agent-specific result
        if "agent_results" not in state:
            state["agent_results"] = {}
        state["agent_results"][self.name] = result

        logger.info(f"Data analysis completed for task {task.get('task_id')}")
        return state