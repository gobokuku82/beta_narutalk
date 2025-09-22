from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any, Optional
import sqlite3
import pandas as pd
import json
import logging
from pathlib import Path
from ..utils import LLMManager, PromptTemplates

logger = logging.getLogger(__name__)

class SalesAnalyticsState(TypedDict):
    query: str
    sql_query: str
    query_results: List[Dict]
    analysis: Dict[str, Any]
    visualization: Dict[str, Any]

class SalesAnalyticsAgent:
    def __init__(self):
        self.workflow = StateGraph(SalesAnalyticsState)
        self.llm_manager = LLMManager()
        self.prompt_templates = PromptTemplates()

        # 데이터베이스 경로 설정
        import os
        from dotenv import load_dotenv
        load_dotenv()

        self.db_paths = {
            "clients": os.getenv("CLIENTS_DB_PATH", "./database/storage/sales_performance/clients_db.db"),
            "clients_info": os.getenv("CLIENTS_INFO_PATH", "./database/storage/sales_performance/clients_info.db"),
            "sales_performance": os.getenv("SALES_PERFORMANCE_PATH", "./database/storage/sales_performance/sales_performance_db.db"),
            "sales_target": os.getenv("SALES_TARGET_PATH", "./database/storage/sales_performance/sales_target_db.db")
        }

        self._build_graph()

    def _build_graph(self):
        self.workflow.add_node("parse_query", self.parse_sales_query)
        self.workflow.add_node("generate_sql", self.text_to_sql)
        self.workflow.add_node("execute_query", self.execute_sql_query)
        self.workflow.add_node("analyze_data", self.perform_analysis)
        self.workflow.add_node("visualize", self.create_visualization)

        # 엔트리 포인트 정의 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "parse_query")
        self.workflow.add_edge("parse_query", "generate_sql")
        self.workflow.add_edge("generate_sql", "execute_query")
        self.workflow.add_edge("execute_query", "analyze_data")

        self.workflow.add_conditional_edges(
            "analyze_data",
            self.check_visualization_need,
            {
                "need_viz": "visualize",
                "text_only": END
            }
        )
        self.workflow.add_edge("visualize", END)

    async def parse_sales_query(self, state):
        """매출 관련 쿼리 파싱"""
        # 쿼리에서 기간, 지역 등 추출
        query = state['query'].lower()

        # 기간 추출
        if "지난달" in query:
            state['period'] = "last_month"
        elif "지난 분기" in query:
            state['period'] = "last_quarter"
        elif "올해" in query:
            state['period'] = "this_year"

        # 지역 추출
        regions = ["서울", "경기", "부산", "대구"]
        for region in regions:
            if region in state['query']:
                state['region'] = region
                break

        return state

    async def text_to_sql(self, state):
        """Text2SQL 변환"""
        try:
            # 스키마 정보 로드
            schema_info = await self.load_schema_info()

            # 프롬프트 생성
            prompt = self.prompt_templates.get_prompt(
                category="text_to_sql",
                subcategory="sales_performance",
                user_query=state['query'],
                period=state.get('period', ''),
                region=state.get('region', '')
            )

            # 시스템 프롬프트
            system_prompt = f"""
            You are a SQL expert for pharmaceutical sales data analysis.

            Database Schema:
            {schema_info}

            Important Rules:
            1. Only generate SELECT queries
            2. Always use proper JOINs when accessing multiple tables
            3. Include date filters when time period is mentioned
            4. Limit results to 1000 rows
            5. Return only the SQL query without any explanation
            """

            # LLM 호출 (정확한 SQL을 위해 strict 모델 사용)
            response = await self.llm_manager.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model="openai_strict",
                category="text_to_sql",
                temperature=0
            )

            # SQL 추출 및 검증
            sql_query = response['content'].strip()

            # SQL 주입 방지 기본 검증
            if not self._validate_sql(sql_query):
                logger.error("Generated SQL failed validation")
                sql_query = "SELECT 'Error: Invalid SQL generated' as error"

            state["sql_query"] = sql_query
            logger.info(f"Generated SQL: {sql_query[:100]}...")

        except Exception as e:
            logger.error(f"Text2SQL failed: {e}")
            state["sql_query"] = f"SELECT 'Error: {str(e)}' as error"

        return state

    async def execute_sql_query(self, state):
        """SQL 쿼리 실행"""
        try:
            sql_query = state.get('sql_query', '')

            if not sql_query or 'error' in sql_query.lower():
                state['query_results'] = []
                return state

            # 적절한 데이터베이스 선택
            db_path = self._select_database(sql_query)

            # 쿼리 실행
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(sql_query, conn)
            conn.close()

            # 결과를 딕셔너리 리스트로 변환
            state['query_results'] = df.to_dict('records')
            logger.info(f"Query returned {len(df)} rows")

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            state['query_results'] = []
            state['error'] = str(e)

        return state

    async def perform_analysis(self, state):
        """데이터 분석 수행"""
        try:
            results = state.get('query_results', [])

            if not results:
                state['analysis'] = {"error": "No data available for analysis"}
                return state

            # 데이터프레임으로 변환
            df = pd.DataFrame(results)

            # 기본 통계 분석
            analysis = {
                "row_count": len(df),
                "columns": df.columns.tolist(),
                "summary": {}
            }

            # 숫자 컬럼에 대한 통계
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                analysis["summary"][col] = {
                    "mean": float(df[col].mean()),
                    "sum": float(df[col].sum()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max())
                }

            state['analysis'] = analysis

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            state['analysis'] = {"error": str(e)}

        return state

    async def create_visualization(self, state):
        """시각화 생성 (차트 설정 정보)"""
        try:
            analysis = state.get('analysis', {})

            if 'error' in analysis:
                state['visualization'] = {}
                return state

            # 시각화 설정 생성 (실제 차트는 프론트엔드에서 렌더링)
            viz_config = {
                "type": "bar",  # 기본 차트 타입
                "data": state.get('query_results', [])[:20],  # 상위 20개만
                "options": {
                    "title": "Sales Analysis Results",
                    "responsive": True
                }
            }

            state['visualization'] = viz_config

        except Exception as e:
            logger.error(f"Visualization creation failed: {e}")
            state['visualization'] = {}

        return state

    def check_visualization_need(self, state: SalesAnalyticsState) -> str:
        """시각화 필요 여부 확인"""
        # 결과가 있고 에러가 없으면 시각화
        if state.get("query_results") and len(state.get("query_results", [])) > 0:
            return "need_viz"
        return "text_only"

    async def load_schema_info(self):
        """데이터베이스 스키마 정보 로드"""
        schema_info = """
        Tables:
        1. clients_db: client_id, client_name, region, type, status
        2. clients_info: client_id, address, contact, manager, notes
        3. sales_performance_db: date, client_id, product_id, amount, quantity
        4. sales_target_db: year, quarter, client_id, target_amount
        """
        return schema_info

    def _validate_sql(self, sql: str) -> bool:
        """SQL 쿼리 기본 검증"""
        sql_upper = sql.upper()

        # 위험한 명령어 체크
        dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE']
        for keyword in dangerous:
            if keyword in sql_upper:
                return False

        # SELECT 쿼리인지 확인
        if not sql_upper.strip().startswith('SELECT'):
            return False

        return True

    def _select_database(self, sql: str) -> str:
        """SQL에 따라 적절한 데이터베이스 선택"""
        sql_lower = sql.lower()

        if 'sales_performance' in sql_lower:
            return self.db_paths['sales_performance']
        elif 'sales_target' in sql_lower:
            return self.db_paths['sales_target']
        elif 'clients_info' in sql_lower:
            return self.db_paths['clients_info']
        else:
            return self.db_paths['clients']

    async def execute(self, input_data: Dict) -> Dict:
        """에이전트 실행 메서드 (agent_execution에서 호출)"""
        try:
            # 초기 상태 설정
            initial_state = {
                "query": input_data.get("query", ""),
                "sql_query": "",
                "query_results": [],
                "analysis": {},
                "visualization": {}
            }

            # 워크플로우 컴파일 및 실행
            app = self.workflow.compile()
            result = await app.ainvoke(initial_state)

            return {
                "status": "success",
                "data": {
                    "sql_query": result.get("sql_query"),
                    "results": result.get("query_results"),
                    "analysis": result.get("analysis"),
                    "visualization": result.get("visualization")
                }
            }

        except Exception as e:
            logger.error(f"Sales analytics agent execution failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }