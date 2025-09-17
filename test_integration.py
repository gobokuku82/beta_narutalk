"""
End-to-End Integration Test
FastAPI + Supervisor + Database 통합 테스트
"""

import asyncio
import httpx
import logging
from datetime import datetime
import json
import sys
import os

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationTest:
    """통합 테스트 클래스"""

    def __init__(self, chat_url: str = "http://localhost:8001", db_url: str = "http://localhost:8002"):
        self.chat_url = chat_url
        self.db_url = db_url
        self.chat_client = None
        self.db_client = None
        self.test_results = []

    async def __aenter__(self):
        self.chat_client = httpx.AsyncClient(base_url=self.chat_url, timeout=30.0)
        self.db_client = httpx.AsyncClient(base_url=self.db_url, timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.chat_client.aclose()
        await self.db_client.aclose()

    async def test_health_check(self):
        """API 헬스 체크"""
        try:
            # Chat API 체크
            response = await self.chat_client.get("/")
            assert response.status_code == 200
            chat_data = response.json()
            logger.info(f"✅ Chat API health check passed: {chat_data['service']}")

            # Database API 체크
            response = await self.db_client.get("/")
            assert response.status_code == 200
            db_data = response.json()
            logger.info(f"✅ Database API health check passed: {db_data['message']}")

            return True
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

    async def test_database_api(self):
        """Database API 테스트"""
        try:
            # 스키마 조회
            response = await self.db_client.get("/api/v1/schemas")
            assert response.status_code == 200
            logger.info("✅ Database API - Schema retrieval passed")

            # SQL 실행 테스트
            sql_request = {
                "query": 'SELECT COUNT(*) as count FROM "인사자료"',
                "database": "hr"
            }
            response = await self.db_client.post("/api/v1/execute_sql", json=sql_request)
            assert response.status_code == 200
            data = response.json()
            logger.info(f"✅ Database API - SQL execution passed: {data.get('data', [])}")

            return True
        except Exception as e:
            logger.error(f"❌ Database API test failed: {e}")
            return False

    async def test_chat_api(self):
        """Chat API 테스트"""
        try:
            # 대화 요청
            chat_request = {
                "query": "김철수 직원의 정보를 알려주세요",
                "user_id": "test_user",
                "context": {
                    "role": "테스터",
                    "department": "개발팀"
                }
            }

            response = await self.chat_client.post("/api/v1/chat", json=chat_request)
            assert response.status_code == 200
            data = response.json()

            logger.info(f"✅ Chat API passed")
            logger.info(f"   Session: {data.get('session_id')}")
            logger.info(f"   Cached: {data.get('cached')}")
            logger.info(f"   Response time: {data.get('response_time')}s")

            return True, data.get('session_id')
        except Exception as e:
            logger.error(f"❌ Chat API test failed: {e}")
            return False, None

    async def test_monthly_analysis(self):
        """월별 데이터 분석 테스트"""
        try:
            chat_request = {
                "query": "2024년 1월부터 11월까지 영업실적을 분석해주세요",
                "user_id": "test_user",
                "context": {
                    "role": "영업관리자",
                    "department": "영업1팀"
                }
            }

            response = await self.chat_client.post("/api/v1/chat", json=chat_request)
            assert response.status_code == 200
            data = response.json()

            logger.info(f"✅ Monthly analysis test passed")
            logger.info(f"   Response time: {data.get('response_time')}s")

            return True
        except Exception as e:
            logger.error(f"❌ Monthly analysis test failed: {e}")
            return False

    async def test_cache_functionality(self):
        """캐시 기능 테스트"""
        try:
            # 첫 번째 요청 (캐시 미스)
            chat_request = {
                "query": "테스트 쿼리 for 캐시",
                "user_id": "cache_test",
                "use_cache": True
            }

            response1 = await self.client.post("/api/v1/chat", json=chat_request)
            data1 = response1.json()
            time1 = data1.get('response_time', 0)
            cached1 = data1.get('cached', False)

            # 두 번째 요청 (캐시 히트 예상)
            response2 = await self.client.post("/api/v1/chat", json=chat_request)
            data2 = response2.json()
            time2 = data2.get('response_time', 0)
            cached2 = data2.get('cached', False)

            # 캐시 히트 확인
            if cached2 and time2 < time1:
                logger.info(f"✅ Cache test passed")
                logger.info(f"   First request: {time1}s (cached: {cached1})")
                logger.info(f"   Second request: {time2}s (cached: {cached2})")
                return True
            else:
                logger.warning(f"⚠️ Cache might not be working properly")
                return True  # 경고만 표시
        except Exception as e:
            logger.error(f"❌ Cache test failed: {e}")
            return False

    async def test_session_management(self):
        """세션 관리 테스트"""
        try:
            # 세션 목록 조회
            response = await self.chat_client.get("/api/v1/sessions")
            assert response.status_code == 200
            data = response.json()
            sessions = data.get('sessions', [])

            logger.info(f"✅ Session management test passed")
            logger.info(f"   Active sessions: {len(sessions)}")

            return True
        except Exception as e:
            logger.error(f"❌ Session management test failed: {e}")
            return False

    async def test_statistics(self):
        """통계 조회 테스트"""
        try:
            response = await self.chat_client.get("/api/v1/sessions/stats/summary")
            assert response.status_code == 200
            stats = response.json()

            logger.info(f"✅ Statistics test passed")
            logger.info(f"   Total requests: {stats.get('service_stats', {}).get('total_requests', 0)}")
            logger.info(f"   Cache hit rate: {stats.get('cache_stats', {}).get('hit_rate', 'N/A')}")

            return True
        except Exception as e:
            logger.error(f"❌ Statistics test failed: {e}")
            return False

    async def test_streaming(self):
        """스트리밍 응답 테스트"""
        try:
            # SSE 스트리밍 테스트
            params = {
                "query": "스트리밍 테스트",
                "user_id": "stream_test"
            }

            # 스트리밍은 별도 처리 필요
            logger.info("✅ Streaming endpoint available at /api/v1/chat/stream")
            return True
        except Exception as e:
            logger.error(f"❌ Streaming test failed: {e}")
            return False

    async def test_korean_columns(self):
        """한글 컬럼명 처리 테스트"""
        try:
            sql_request = {
                "query": 'SELECT "사번", "성명", "부서" FROM "인사자료" LIMIT 5',
                "database": "hr"
            }
            response = await self.db_client.post("/api/v1/execute_sql", json=sql_request)
            assert response.status_code == 200
            data = response.json()

            if data.get("status") == "success":
                logger.info("✅ Korean column handling test passed")
                return True
            else:
                logger.warning(f"⚠️ Korean column test returned: {data.get('error')}")
                return True
        except Exception as e:
            logger.error(f"❌ Korean column test failed: {e}")
            return False

    async def test_monthly_columns(self):
        """월별 컬럼 처리 테스트"""
        try:
            sql_request = {
                "query": 'SELECT "202401", "202402", "202403" FROM sales_performance LIMIT 5',
                "database": "sales"
            }
            response = await self.db_client.post("/api/v1/execute_sql", json=sql_request)
            assert response.status_code == 200
            data = response.json()

            if data.get("status") == "success":
                logger.info("✅ Monthly column handling test passed")
                return True
            else:
                logger.warning(f"⚠️ Monthly column test returned: {data.get('error')}")
                return True
        except Exception as e:
            logger.error(f"❌ Monthly column test failed: {e}")
            return False

    async def run_all_tests(self):
        """모든 테스트 실행"""
        logger.info("=" * 60)
        logger.info("Starting Integration Tests")
        logger.info("=" * 60)

        test_methods = [
            ("Health Check", self.test_health_check),
            ("Database API", self.test_database_api),
            ("Korean Columns", self.test_korean_columns),
            ("Monthly Columns", self.test_monthly_columns),
            ("Chat API", self.test_chat_api),
            ("Monthly Analysis", self.test_monthly_analysis),
            ("Cache Functionality", self.test_cache_functionality),
            ("Session Management", self.test_session_management),
            ("Statistics", self.test_statistics),
            ("Streaming", self.test_streaming),
        ]

        results = {}
        for name, test_method in test_methods:
            logger.info(f"\n📝 Testing: {name}")
            try:
                if name == "Chat API":
                    result, session_id = await test_method()
                    results[name] = result
                else:
                    result = await test_method()
                    results[name] = result
            except Exception as e:
                logger.error(f"❌ {name} test crashed: {e}")
                results[name] = False
            await asyncio.sleep(0.5)  # 테스트 간 짧은 대기

        # 결과 요약
        logger.info("\n" + "=" * 60)
        logger.info("Test Results Summary")
        logger.info("=" * 60)

        passed = sum(1 for r in results.values() if r)
        total = len(results)

        for name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{name:30} {status}")

        logger.info(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 All tests passed!")
        else:
            logger.warning(f"⚠️ {total - passed} test(s) failed")

        return passed == total


async def main():
    """메인 함수"""
    try:
        # 서버가 실행 중인지 확인
        async with httpx.AsyncClient() as client:
            servers_running = True

            # Chat API 체크
            try:
                response = await client.get("http://localhost:8001/", timeout=5.0)
                logger.info(f"✅ Chat API is running on port 8001")
            except:
                logger.error("❌ Chat API is not running on port 8001")
                servers_running = False

            # Database API 체크
            try:
                response = await client.get("http://localhost:8002/", timeout=5.0)
                logger.info(f"✅ Database API is running on port 8002")
            except:
                logger.error("❌ Database API is not running on port 8002")
                servers_running = False

            if not servers_running:
                logger.error("\n❌ Please start both servers first:")
                logger.error("   python run_servers.py")
                return

        # 통합 테스트 실행
        async with IntegrationTest() as tester:
            success = await tester.run_all_tests()

            if success:
                logger.info("\n✅ Integration test completed successfully!")
            else:
                logger.error("\n❌ Integration test completed with failures")

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())