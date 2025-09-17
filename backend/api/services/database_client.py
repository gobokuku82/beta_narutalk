"""
Database API Client
Database API 서버와 통신하는 클라이언트
"""

import httpx
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseAPIClient:
    """
    Database API와 통신하는 HTTP 클라이언트
    Chat API -> Database API 통신용
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8002/api/v1",
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

        logger.info(f"Database API Client initialized: {self.base_url}")

    async def execute_sql(
        self,
        query: str,
        database: str = "sales"
    ) -> Dict[str, Any]:
        """
        SQL 쿼리 실행

        Args:
            query: SQL 쿼리
            database: 대상 데이터베이스

        Returns:
            쿼리 실행 결과
        """
        request_data = {
            "query": query,
            "database": database,
            "timeout": self.timeout
        }

        try:
            response = await self._retry_request(
                "POST",
                "/execute_sql",
                json=request_data
            )

            return response

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {
                "status": "error",
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
        try:
            response = await self._retry_request(
                "GET",
                f"/schema/{table_name}",
                params={"database": database}
            )

            return response

        except Exception as e:
            logger.error(f"Schema retrieval failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "columns": []
            }

    async def get_all_schemas(self) -> Dict[str, Any]:
        """
        모든 데이터베이스 스키마 조회

        Returns:
            전체 스키마 정보
        """
        try:
            response = await self._retry_request(
                "GET",
                "/schemas"
            )

            return response

        except Exception as e:
            logger.error(f"All schemas retrieval failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "schemas": {}
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

            return response

        except Exception as e:
            logger.error(f"HR search failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "data": []
            }

    async def search_regulations(
        self,
        query: str,
        rule_type: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        규정 검색

        Args:
            query: 검색 쿼리
            rule_type: 규정 타입
            keywords: 키워드 목록

        Returns:
            검색 결과
        """
        request_data = {
            "query": query,
            "rule_type": rule_type,
            "keywords": keywords or []
        }

        try:
            response = await self._retry_request(
                "POST",
                "/search/regulations",
                json=request_data
            )

            return response

        except Exception as e:
            logger.error(f"Regulations search failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "data": []
            }

    async def health_check(self) -> bool:
        """
        Database API 서버 상태 확인

        Returns:
            서버 상태 (True/False)
        """
        try:
            response = await self.client.get("/health")
            data = response.json()

            is_healthy = data.get("status") in ["healthy", "running"]

            if is_healthy:
                logger.debug("Database API is healthy")
            else:
                logger.warning(f"Database API health check failed: {data}")

            return is_healthy

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def _retry_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        재시도 로직을 포함한 HTTP 요청

        Args:
            method: HTTP 메서드
            endpoint: API 엔드포인트
            **kwargs: 추가 요청 파라미터

        Returns:
            API 응답
        """
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
                    logger.warning(
                        f"Request timeout for {method} {endpoint}, "
                        f"retrying... (attempt {attempt + 1})"
                    )

            except httpx.HTTPStatusError as e:
                if 400 <= e.response.status_code < 500:
                    # 클라이언트 에러는 재시도하지 않음
                    return {
                        "status": "error",
                        "error": e.response.text,
                        "status_code": e.response.status_code
                    }

                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    logger.warning(
                        f"Server error {e.response.status_code} for {method} {endpoint}, "
                        f"retrying... (attempt {attempt + 1})"
                    )

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    logger.warning(
                        f"Request failed for {method} {endpoint}: {e}, "
                        f"retrying... (attempt {attempt + 1})"
                    )

        # 모든 재시도 실패
        logger.error(
            f"All retry attempts failed for {method} {endpoint}: {last_exception}"
        )
        raise last_exception

    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()
        logger.debug("Database API Client closed")

    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        await self.close()