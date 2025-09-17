"""
SQL Analysis Agent
SQL 분석 에이전트 - Text2SQL 활용
"""

from typing import Dict, Any, List, Optional, Literal, Union
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import httpx
import pandas as pd
import json
import asyncio

logger = logging.getLogger(__name__)


class SQLQueryRequest(BaseModel):
    """SQL 쿼리 요청"""
    
    natural_language_query: str
    target_tables: List[str] = Field(default_factory=list)
    time_range: Optional[Dict[str, str]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    aggregation_type: Optional[str] = None
    analysis_type: Literal["simple", "trend", "comparison", "complex"] = "simple"


class ColumnMetadata(BaseModel):
    """칼럼 메타데이터"""
    
    column_name: str
    data_type: str
    description: str
    is_nullable: bool = True
    is_primary_key: bool = False
    foreign_key_reference: Optional[str] = None
    business_meaning: str = ""
    calculation_formula: Optional[str] = None


class AnalysisResult(BaseModel):
    """분석 결과"""
    
    query_id: str
    original_query: str
    generated_sql: str
    execution_status: str
    data: Optional[List[Dict]] = None
    statistics: Optional[Dict[str, Any]] = None
    visualizations: Optional[List[Dict]] = None
    insights: List[str] = Field(default_factory=list)
    errors: Optional[str] = None


class SQLAnalysisAgent:
    """
    SQL 분석 에이전트
    - Text2SQL을 활용한 자연어 쿼리 변환
    - 복잡한 칼럼 메타데이터 관리
    - 다양한 분석 도구 제공
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Initialize SQL Analysis Agent
        
        Args:
            api_base_url: FastAPI 서버 URL
        """
        
        self.api_base_url = api_base_url
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # 분석 도구 초기화
        self.tools = self._initialize_analysis_tools()
        
        # 테이블 스키마 캐시
        self.schema_cache = {}
        
        # 복잡한 칼럼 메타데이터
        self.column_metadata = self._initialize_column_metadata()
    
    def _initialize_analysis_tools(self) -> Dict[str, Tool]:
        """분석 도구 초기화"""
        
        tools = {
            "generate_sql": Tool(
                name="generate_sql",
                description="자연어를 SQL로 변환",
                func=self._generate_sql_query
            ),
            "execute_query": Tool(
                name="execute_query",
                description="SQL 쿼리 실행",
                func=self._execute_sql_query
            ),
            "calculate_statistics": Tool(
                name="calculate_statistics",
                description="통계 계산",
                func=self._calculate_statistics
            ),
            "trend_analysis": Tool(
                name="trend_analysis",
                description="트렌드 분석",
                func=self._perform_trend_analysis
            ),
            "comparative_analysis": Tool(
                name="comparative_analysis",
                description="비교 분석",
                func=self._perform_comparative_analysis
            ),
            "generate_visualization": Tool(
                name="generate_visualization",
                description="시각화 생성",
                func=self._generate_visualization
            )
        }
        
        return tools
    
    def _initialize_column_metadata(self) -> Dict[str, Dict[str, ColumnMetadata]]:
        """복잡한 칼럼 메타데이터 초기화"""
        
        # 실제로는 DB에서 로드해야 함
        metadata = {
            "sales_performance": {
                "sales_amount": ColumnMetadata(
                    column_name="sales_amount",
                    data_type="decimal",
                    description="매출액",
                    business_meaning="제품 판매로 인한 수익",
                    calculation_formula="unit_price * quantity * (1 - discount_rate)"
                ),
                "achievement_rate": ColumnMetadata(
                    column_name="achievement_rate",
                    data_type="float",
                    description="목표 달성률",
                    business_meaning="설정된 목표 대비 실제 달성 비율",
                    calculation_formula="(actual_sales / target_sales) * 100"
                ),
                "product_mix_json": ColumnMetadata(
                    column_name="product_mix_json",
                    data_type="json",
                    description="제품 구성 JSON",
                    business_meaning="판매된 제품들의 구성 비율과 상세 정보"
                )
            },
            "client_trends": {
                "visit_frequency": ColumnMetadata(
                    column_name="visit_frequency",
                    data_type="int",
                    description="방문 빈도",
                    business_meaning="특정 기간 내 고객 방문 횟수"
                ),
                "prescription_trend": ColumnMetadata(
                    column_name="prescription_trend",
                    data_type="json",
                    description="처방 트렌드",
                    business_meaning="시간에 따른 처방 패턴 변화"
                ),
                "loyalty_score": ColumnMetadata(
                    column_name="loyalty_score",
                    data_type="float",
                    description="충성도 점수",
                    business_meaning="고객 충성도를 나타내는 복합 지표",
                    calculation_formula="weighted_avg(visit_freq, purchase_amount, retention_period)"
                )
            }
        }
        
        return metadata
    
    async def analyze_query(self, request: SQLQueryRequest) -> AnalysisResult:
        """
        쿼리 분석 메인 메서드
        """
        
        logger.info(f"Analyzing query: {request.natural_language_query}")
        
        # 1. 스키마 정보 조회
        schema_info = await self._fetch_schema_info(request.target_tables)
        
        # 2. SQL 생성
        generated_sql = await self._generate_sql_with_metadata(
            request.natural_language_query,
            schema_info,
            request
        )
        
        # 3. SQL 실행
        query_result = await self._execute_query_via_api(generated_sql)
        
        if query_result.get("error"):
            # SQL 수정 및 재시도
            generated_sql = await self._fix_and_retry_sql(
                generated_sql,
                query_result["error"],
                schema_info
            )
            query_result = await self._execute_query_via_api(generated_sql)
        
        # 4. 분석 유형에 따른 추가 처리
        analysis_results = await self._perform_analysis(
            request.analysis_type,
            query_result.get("data", []),
            request
        )
        
        # 5. 인사이트 생성
        insights = await self._generate_insights(
            query_result.get("data", []),
            request
        )
        
        # 결과 구성
        result = AnalysisResult(
            query_id=self._generate_query_id(),
            original_query=request.natural_language_query,
            generated_sql=generated_sql,
            execution_status="success" if query_result.get("data") else "failed",
            data=query_result.get("data"),
            statistics=analysis_results.get("statistics"),
            visualizations=analysis_results.get("visualizations"),
            insights=insights,
            errors=query_result.get("error")
        )
        
        return result
    
    async def _fetch_schema_info(self, tables: List[str]) -> Dict[str, Any]:
        """테이블 스키마 정보 조회"""
        
        if not tables:
            # 기본 테이블 추론
            tables = self._infer_tables_from_context()
        
        schema_info = {}
        
        async with httpx.AsyncClient() as client:
            for table in tables:
                # 캐시 확인
                if table in self.schema_cache:
                    schema_info[table] = self.schema_cache[table]
                    continue
                
                try:
                    response = await client.get(
                        f"{self.api_base_url}/schema/{table}",
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        schema = response.json()
                        self.schema_cache[table] = schema
                        schema_info[table] = schema
                        
                except Exception as e:
                    logger.error(f"Error fetching schema for {table}: {e}")
        
        return schema_info
    
    async def _generate_sql_with_metadata(
        self,
        natural_query: str,
        schema_info: Dict[str, Any],
        request: SQLQueryRequest
    ) -> str:
        """메타데이터를 활용한 SQL 생성"""
        
        # 관련 칼럼 메타데이터 추출
        relevant_metadata = self._get_relevant_metadata(natural_query)
        
        system_prompt = """당신은 SQL 전문가입니다.
        자연어 쿼리를 정확한 SQL로 변환하세요.
        
        다음 정보를 활용하세요:
        1. 테이블 스키마
        2. 칼럼 메타데이터 (비즈니스 의미, 계산식)
        3. 필터 조건
        4. 시간 범위
        
        복잡한 칼럼의 경우 제공된 계산식을 사용하세요.
        JSON 칼럼은 적절한 JSON 함수를 사용하세요.
        
        SQL만 반환하고 다른 설명은 하지 마세요.
        """
        
        # 컨텍스트 구성
        context = f"""
        테이블 스키마:
        {json.dumps(schema_info, ensure_ascii=False, indent=2)}
        
        칼럼 메타데이터:
        {json.dumps(self._serialize_metadata(relevant_metadata), ensure_ascii=False, indent=2)}
        
        필터: {request.filters}
        시간 범위: {request.time_range}
        집계 유형: {request.aggregation_type}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"자연어 쿼리: {natural_query}\n\n컨텍스트:\n{context}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # SQL 추출
        sql = response.content
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        
        return sql
    
    async def _execute_query_via_api(self, sql: str) -> Dict[str, Any]:
        """FastAPI를 통한 쿼리 실행"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/execute_sql",
                    json={"query": sql},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Query execution failed: {response.text}"}
                    
            except Exception as e:
                logger.error(f"Error executing query: {e}")
                return {"error": str(e)}
    
    async def _fix_and_retry_sql(
        self,
        sql: str,
        error: str,
        schema_info: Dict[str, Any]
    ) -> str:
        """SQL 오류 수정 및 재생성"""
        
        system_prompt = """SQL 쿼리에 오류가 있습니다.
        오류를 수정하여 올바른 SQL을 생성하세요.
        
        일반적인 오류 유형:
        1. 칼럼명 오타
        2. 테이블명 오류
        3. 조인 조건 누락
        4. 집계 함수 오류
        5. 문법 오류
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
            원본 SQL:
            {sql}
            
            오류 메시지:
            {error}
            
            스키마 정보:
            {json.dumps(schema_info, ensure_ascii=False, indent=2)}
            
            수정된 SQL을 제공하세요.
            """)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # SQL 추출
        fixed_sql = response.content
        if "```sql" in fixed_sql:
            fixed_sql = fixed_sql.split("```sql")[1].split("```")[0].strip()
        
        return fixed_sql
    
    async def _perform_analysis(
        self,
        analysis_type: str,
        data: List[Dict],
        request: SQLQueryRequest
    ) -> Dict[str, Any]:
        """분석 유형별 처리"""
        
        if not data:
            return {}
        
        results = {}
        
        if analysis_type == "simple":
            # 기본 통계
            results["statistics"] = await self._calculate_basic_stats(data)
            
        elif analysis_type == "trend":
            # 트렌드 분석
            trend_result = await self._perform_trend_analysis(data)
            results["statistics"] = trend_result.get("statistics")
            results["visualizations"] = [trend_result.get("chart")]
            
        elif analysis_type == "comparison":
            # 비교 분석
            comparison_result = await self._perform_comparative_analysis(data)
            results["statistics"] = comparison_result.get("comparison_stats")
            results["visualizations"] = [comparison_result.get("chart")]
            
        elif analysis_type == "complex":
            # 복합 분석
            # 여러 분석 기법 조합
            results["statistics"] = await self._calculate_advanced_stats(data)
            results["visualizations"] = await self._generate_multiple_visualizations(data)
        
        return results
    
    async def _calculate_basic_stats(self, data: List[Dict]) -> Dict[str, Any]:
        """기본 통계 계산"""
        
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        stats = {}
        
        # 숫자형 칼럼 통계
        numeric_columns = df.select_dtypes(include=['number']).columns
        
        for col in numeric_columns:
            stats[col] = {
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "count": int(df[col].count())
            }
        
        # 카테고리형 칼럼 통계
        categorical_columns = df.select_dtypes(include=['object']).columns
        
        for col in categorical_columns:
            value_counts = df[col].value_counts().to_dict()
            stats[col] = {
                "unique_count": df[col].nunique(),
                "top_values": dict(list(value_counts.items())[:5])
            }
        
        return stats
    
    async def _calculate_advanced_stats(self, data: List[Dict]) -> Dict[str, Any]:
        """고급 통계 계산"""
        
        df = pd.DataFrame(data)
        
        stats = await self._calculate_basic_stats(data)
        
        # 상관관계 분석
        numeric_df = df.select_dtypes(include=['number'])
        if len(numeric_df.columns) > 1:
            correlation_matrix = numeric_df.corr().to_dict()
            stats["correlations"] = correlation_matrix
        
        # 분위수 계산
        for col in numeric_df.columns:
            stats[col]["quartiles"] = {
                "q1": float(df[col].quantile(0.25)),
                "q2": float(df[col].quantile(0.5)),
                "q3": float(df[col].quantile(0.75))
            }
        
        return stats
    
    async def _perform_trend_analysis(self, data: List[Dict]) -> Dict[str, Any]:
        """트렌드 분석"""
        
        df = pd.DataFrame(data)
        
        # 시간 칼럼 찾기
        date_columns = []
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                date_columns.append(col)
        
        if not date_columns:
            return {"error": "No date column found for trend analysis"}
        
        date_col = date_columns[0]
        
        # 트렌드 계산
        trend_stats = {}
        numeric_columns = df.select_dtypes(include=['number']).columns
        
        for col in numeric_columns:
            # 이동 평균
            df[f'{col}_ma7'] = df[col].rolling(window=7, min_periods=1).mean()
            df[f'{col}_ma30'] = df[col].rolling(window=30, min_periods=1).mean()
            
            # 성장률
            df[f'{col}_growth'] = df[col].pct_change()
            
            trend_stats[col] = {
                "overall_trend": self._calculate_trend_direction(df[col].values),
                "average_growth_rate": float(df[f'{col}_growth'].mean()),
                "volatility": float(df[col].std())
            }
        
        # 시각화 데이터
        chart_data = {
            "type": "line",
            "data": df.to_dict('records'),
            "x_axis": date_col,
            "y_axis": list(numeric_columns)
        }
        
        return {
            "statistics": trend_stats,
            "chart": chart_data
        }
    
    async def _perform_comparative_analysis(self, data: List[Dict]) -> Dict[str, Any]:
        """비교 분석"""
        
        df = pd.DataFrame(data)
        
        # 그룹별 비교 (첫 번째 문자열 칼럼을 그룹 기준으로)
        categorical_columns = df.select_dtypes(include=['object']).columns
        
        if len(categorical_columns) == 0:
            return {"error": "No categorical column for comparison"}
        
        group_col = categorical_columns[0]
        numeric_columns = df.select_dtypes(include=['number']).columns
        
        comparison_stats = {}
        
        for num_col in numeric_columns:
            grouped = df.groupby(group_col)[num_col].agg([
                'mean', 'median', 'std', 'count'
            ]).to_dict()
            
            comparison_stats[num_col] = grouped
        
        # 시각화 데이터
        chart_data = {
            "type": "bar",
            "data": df.groupby(group_col)[list(numeric_columns)].mean().reset_index().to_dict('records'),
            "x_axis": group_col,
            "y_axis": list(numeric_columns)
        }
        
        return {
            "comparison_stats": comparison_stats,
            "chart": chart_data
        }
    
    async def _generate_visualization(self, data: List[Dict], viz_type: str = "auto") -> Dict[str, Any]:
        """시각화 생성"""
        
        df = pd.DataFrame(data)
        
        if viz_type == "auto":
            # 데이터 특성에 따라 자동 선택
            viz_type = self._determine_best_visualization(df)
        
        visualization = {
            "type": viz_type,
            "data": data,
            "config": self._get_visualization_config(viz_type, df)
        }
        
        return visualization
    
    async def _generate_multiple_visualizations(self, data: List[Dict]) -> List[Dict]:
        """여러 시각화 생성"""
        
        visualizations = []
        
        # 다양한 시각화 타입 생성
        viz_types = ["bar", "line", "pie", "scatter"]
        
        for viz_type in viz_types:
            try:
                viz = await self._generate_visualization(data, viz_type)
                if viz:
                    visualizations.append(viz)
            except:
                continue
        
        return visualizations[:3]  # 최대 3개
    
    async def _generate_insights(
        self,
        data: List[Dict],
        request: SQLQueryRequest
    ) -> List[str]:
        """데이터 인사이트 생성"""
        
        if not data:
            return ["데이터가 없습니다."]
        
        df = pd.DataFrame(data)
        insights = []
        
        # 기본 인사이트
        insights.append(f"총 {len(data)}개의 레코드가 조회되었습니다.")
        
        # LLM 기반 인사이트
        system_prompt = """데이터를 분석하여 비즈니스 인사이트를 제공하세요.
        
        다음 관점에서 분석하세요:
        1. 주요 발견사항
        2. 특이사항
        3. 개선 기회
        4. 주의가 필요한 부분
        
        각 인사이트는 한 문장으로 작성하세요.
        """
        
        # 데이터 요약
        data_summary = df.describe().to_string() if len(df) > 0 else ""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
            원본 쿼리: {request.natural_language_query}
            데이터 요약:
            {data_summary}
            
            샘플 데이터 (상위 5개):
            {df.head().to_string() if len(df) > 0 else ""}
            """)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # 인사이트 파싱
        llm_insights = response.content.split("\n")
        insights.extend([i.strip() for i in llm_insights if i.strip()][:5])
        
        return insights
    
    def _infer_tables_from_context(self) -> List[str]:
        """컨텍스트에서 테이블 추론"""
        # 기본 테이블 목록
        return ["sales_performance", "client_trends"]
    
    def _get_relevant_metadata(self, query: str) -> Dict[str, ColumnMetadata]:
        """관련 칼럼 메타데이터 추출"""
        
        relevant = {}
        query_lower = query.lower()
        
        for table, columns in self.column_metadata.items():
            for col_name, metadata in columns.items():
                # 쿼리에 칼럼명이나 설명이 포함되어 있는지 확인
                if (col_name.lower() in query_lower or 
                    metadata.description.lower() in query_lower or
                    metadata.business_meaning.lower() in query_lower):
                    relevant[f"{table}.{col_name}"] = metadata
        
        return relevant
    
    def _serialize_metadata(self, metadata: Dict[str, ColumnMetadata]) -> Dict[str, Dict]:
        """메타데이터 직렬화"""
        
        serialized = {}
        for key, meta in metadata.items():
            serialized[key] = {
                "type": meta.data_type,
                "description": meta.description,
                "business_meaning": meta.business_meaning,
                "formula": meta.calculation_formula
            }
        
        return serialized
    
    def _calculate_trend_direction(self, values: List[float]) -> str:
        """트렌드 방향 계산"""
        
        if len(values) < 2:
            return "insufficient_data"
        
        # 선형 회귀를 통한 트렌드 계산
        import numpy as np
        x = np.arange(len(values))
        coefficients = np.polyfit(x, values, 1)
        slope = coefficients[0]
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _determine_best_visualization(self, df: pd.DataFrame) -> str:
        """최적 시각화 타입 결정"""
        
        numeric_cols = len(df.select_dtypes(include=['number']).columns)
        categorical_cols = len(df.select_dtypes(include=['object']).columns)
        
        if numeric_cols >= 2 and categorical_cols == 0:
            return "scatter"
        elif categorical_cols >= 1 and numeric_cols >= 1:
            return "bar"
        elif 'date' in str(df.columns).lower():
            return "line"
        else:
            return "table"
    
    def _get_visualization_config(self, viz_type: str, df: pd.DataFrame) -> Dict[str, Any]:
        """시각화 설정"""
        
        config = {
            "title": "Data Visualization",
            "width": 800,
            "height": 400
        }
        
        if viz_type == "bar":
            config["orientation"] = "vertical"
        elif viz_type == "line":
            config["smooth"] = True
        elif viz_type == "pie":
            config["show_percentage"] = True
        
        return config
    
    def _generate_query_id(self) -> str:
        """쿼리 ID 생성"""
        
        from uuid import uuid4
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"QUERY_{timestamp}_{str(uuid4())[:8]}"


# === Graph Node Function ===

async def sql_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Graph node for SQL analysis
    """
    
    agent = SQLAnalysisAgent()
    
    # 요청 구성
    request = SQLQueryRequest(
        natural_language_query=state.get("query", ""),
        target_tables=state.get("target_tables", []),
        time_range=state.get("time_range"),
        filters=state.get("filters", {}),
        analysis_type=state.get("analysis_type", "simple")
    )
    
    # 분석 실행
    result = await agent.analyze_query(request)
    
    # 상태 업데이트
    return {
        "query_results": result.dict(),
        "analysis_complete": True,
        "insights": result.insights,
        "next_step": "complete" if result.execution_status == "success" else "retry"
    }
