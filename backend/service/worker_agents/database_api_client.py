"""
Database API Client for Worker Agents
Worker Agent들이 Database API를 직접 호출하기 위한 클라이언트
"""

import httpx
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)


class DatabaseAPIClient:
    """
    Database API 직접 호출 클라이언트
    Agent → Database API (Option B)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000/api/v1",
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize Database API Client

        Args:
            base_url: Database API 서버 URL
            timeout: 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries

        # HTTP 클라이언트
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers={"Content-Type": "application/json"}
        )

        # 한글 컬럼명 목록 (자동 처리용)
        self.korean_columns = {
            "사번", "성명", "본부", "직급", "부서", "지점", "연락처",
            "월평균사용예산", "최근 평가", "기본급(₩)", "성과급(₩)", "책임업무",
            "지점 연락처", "담당자", "거래처ID", "품목", "거래처자료",
            "월방문횟수", "사용 예산", "총환자수", "월", "매출",
            "원장명", "지역구", "병원연락처", "지점별목표", "인사자료",
            "거래처정보", "지점연락처"
        }

        # 월별 컬럼 패턴 (202312 ~ 202411)
        self.monthly_columns = self._generate_monthly_columns()

    def _generate_monthly_columns(self) -> List[str]:
        """월별 컬럼명 생성 (202312 ~ 202411)"""
        columns = []
        # 2023년 12월
        columns.append("202312")
        # 2024년 1월 ~ 11월
        for month in range(1, 12):
            columns.append(f"2024{month:02d}")
        return columns

    def process_korean_query(self, query: str) -> str:
        """
        한글 컬럼명과 테이블명을 큰따옴표로 처리

        Args:
            query: SQL 쿼리

        Returns:
            처리된 SQL 쿼리
        """
        processed = query

        # 한글 컬럼명 처리
        for column in self.korean_columns:
            # 이미 따옴표가 없는 경우만 처리
            if f'"{column}"' not in processed and f"'{column}'" not in processed:
                # 단어 경계를 확인하여 정확한 매칭
                pattern = r'\b' + re.escape(column) + r'\b'
                processed = re.sub(pattern, f'"{column}"', processed)

        # 월별 컬럼 처리
        for month in self.monthly_columns:
            if f'"{month}"' not in processed:
                pattern = r'\b' + month + r'\b'
                processed = re.sub(pattern, f'"{month}"', processed)

        return processed

    async def execute_sql(
        self,
        query: str,
        database: str = "sales",
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        SQL 쿼리 실행

        Args:
            query: SQL 쿼리
            database: 대상 데이터베이스 (hr, sales, rules, hr_rules)
            timeout: 쿼리 타임아웃

        Returns:
            쿼리 실행 결과
        """
        # 한글 컬럼명 처리
        processed_query = self.process_korean_query(query)

        logger.info(f"Executing SQL on {database}: {processed_query[:100]}...")

        request_data = {
            "query": processed_query,
            "database": database,
            "timeout": timeout or self.timeout
        }

        try:
            response = await self._retry_request(
                "POST",
                "/execute_sql",
                json=request_data
            )

            if response.get("status") == "success":
                return {
                    "success": True,
                    "data": response.get("data", []),
                    "rows_affected": response.get("rows_affected", 0),
                    "execution_time": response.get("execution_time", 0)
                }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error"),
                    "data": []
                }

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }

    async def get_schema(
        self,
        table_name: str,
        database: str = "sales"
    ) -> Dict[str, Any]:
        """
        테이블 스키마 조회

        Args:
            table_name: 테이블명
            database: 데이터베이스명

        Returns:
            스키마 정보
        """
        # 한글 테이블명 처리
        if table_name in self.korean_columns:
            table_name = f'"{table_name}"'

        try:
            response = await self._retry_request(
                "GET",
                f"/schema/{table_name}",
                params={"database": database}
            )

            if response.get("status") == "success":
                return {
                    "success": True,
                    "columns": response.get("columns", []),
                    "indexes": response.get("indexes", []),
                    "row_count": response.get("row_count", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"Schema not found for {table_name}",
                    "columns": []
                }

        except Exception as e:
            logger.error(f"Schema retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "columns": []
            }

    async def search_hr(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        HR 정보 검색

        Args:
            query: 검색 쿼리
            filters: 필터 조건
            limit: 결과 제한

        Returns:
            검색 결과
        """
        request_data = {
            "query": query,
            "filters": filters or {},
            "limit": limit
        }

        try:
            response = await self._retry_request(
                "POST",
                "/search/hr",
                json=request_data
            )

            return {
                "success": response.get("status") == "success",
                "data": response.get("data", []),
                "total": response.get("total", 0)
            }

        except Exception as e:
            logger.error(f"HR search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }

    async def search_vector(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        벡터 DB 검색 (ChromaDB)

        Args:
            query: 검색 쿼리
            collection: 컬렉션명 (hr_rules, rules)
            top_k: 상위 K개 결과
            threshold: 유사도 임계값

        Returns:
            벡터 검색 결과
        """
        request_data = {
            "query": query,
            "collection": collection,
            "top_k": top_k,
            "threshold": threshold
        }

        try:
            response = await self._retry_request(
                "POST",
                "/search/vector",
                json=request_data
            )

            return {
                "success": response.get("status") == "success",
                "documents": response.get("documents", []),
                "distances": response.get("distances", [])
            }

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents": []
            }

    async def hybrid_search(
        self,
        query: str,
        databases: List[str],
        vector_collections: List[str],
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        하이브리드 검색 (SQL + Vector)

        Args:
            query: 검색 쿼리
            databases: SQL 데이터베이스 목록
            vector_collections: 벡터 컬렉션 목록
            limit: 결과 제한

        Returns:
            통합 검색 결과
        """
        request_data = {
            "query": query,
            "databases": databases,
            "vector_collections": vector_collections,
            "limit": limit
        }

        try:
            response = await self._retry_request(
                "POST",
                "/hybrid/search",
                json=request_data
            )

            return {
                "success": response.get("status") == "success",
                "sql_results": response.get("sql_results", []),
                "vector_results": response.get("vector_results", []),
                "merged_results": response.get("merged_results", [])
            }

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "sql_results": [],
                "vector_results": []
            }

    async def analyze_monthly_data(
        self,
        employee_id: str,
        start_month: str,
        end_month: str,
        database: str = "sales"
    ) -> Dict[str, Any]:
        """
        월별 데이터 분석 (특화 기능)

        Args:
            employee_id: 직원 ID
            start_month: 시작월 (YYYYMM)
            end_month: 종료월 (YYYYMM)
            database: 데이터베이스

        Returns:
            월별 분석 결과
        """
        # 월별 컬럼 생성
        months = []
        start_year = int(start_month[:4])
        start_mon = int(start_month[4:])
        end_year = int(end_month[:4])
        end_mon = int(end_month[4:])

        current_year = start_year
        current_mon = start_mon

        while (current_year < end_year) or (current_year == end_year and current_mon <= end_mon):
            months.append(f"{current_year}{current_mon:02d}")
            current_mon += 1
            if current_mon > 12:
                current_mon = 1
                current_year += 1

        # 동적 SQL 생성
        month_columns = [f'"{month}"' for month in months if month in self.monthly_columns]

        if not month_columns:
            return {
                "success": False,
                "error": "No valid months in range",
                "data": []
            }

        query = f"""
        SELECT "사번", "담당자", "거래처ID", "품목",
               {', '.join(month_columns)}
        FROM sales_performance
        WHERE "사번" = '{employee_id}'
        """

        result = await self.execute_sql(query, database)

        if result["success"] and result["data"]:
            # 월별 합계 계산
            monthly_totals = {}
            for month in months:
                if month in self.monthly_columns:
                    total = sum(row.get(month, 0) or 0 for row in result["data"])
                    monthly_totals[month] = total

            return {
                "success": True,
                "employee_id": employee_id,
                "monthly_data": result["data"],
                "monthly_totals": monthly_totals,
                "total_sum": sum(monthly_totals.values())
            }

        return result

    async def _retry_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """재시도 로직을 포함한 HTTP 요청"""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(
                    method,
                    endpoint,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    logger.warning(f"Request timeout, retrying... (attempt {attempt + 1})")

            except httpx.HTTPStatusError as e:
                if 400 <= e.response.status_code < 500:
                    # 클라이언트 에러는 재시도하지 않음
                    return {"status": "error", "error": e.response.text}

                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise last_exception

    async def health_check(self) -> bool:
        """API 서버 상태 확인"""
        try:
            response = await self.client.get("/health")
            data = response.json()
            return data.get("status") in ["healthy", "running"]
        except:
            return False

    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()

    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        await self.close()