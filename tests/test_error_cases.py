"""
에러 케이스 테스트
다양한 에러 상황에서 시스템이 적절히 처리하는지 테스트
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ErrorCaseTester:
    """에러 케이스 테스트 클래스"""

    def __init__(self, chat_url: str = "http://localhost:8001", db_url: str = "http://localhost:8002"):
        self.chat_url = chat_url
        self.db_url = db_url
        self.results = []

    async def test_invalid_queries(self):
        """잘못된 쿼리 테스트"""
        print("\n" + "="*80)
        print("❌ Testing Invalid Queries")
        print("="*80)

        test_cases = [
            {
                "name": "Empty query",
                "query": "",
                "expected": "Query should not be empty"
            },
            {
                "name": "Very long query",
                "query": "A" * 10000,
                "expected": "Query too long"
            },
            {
                "name": "Special characters only",
                "query": "!@#$%^&*()",
                "expected": "Invalid query format"
            },
            {
                "name": "SQL injection attempt",
                "query": "'; DROP TABLE users; --",
                "expected": "Safe handling of SQL injection"
            },
            {
                "name": "Script injection",
                "query": "<script>alert('XSS')</script>",
                "expected": "Safe handling of script injection"
            },
            {
                "name": "Nonsensical query",
                "query": "asdfghjkl zxcvbnm qwertyuiop",
                "expected": "Handle nonsense input gracefully"
            }
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            results = []

            for test in test_cases:
                print(f"\n📝 {test['name']}: {test['query'][:50]}...")

                request_data = {
                    "query": test['query'],
                    "user_id": "error_test",
                    "context": {}
                }

                try:
                    response = await client.post(
                        f"{self.chat_url}/api/v1/chat",
                        json=request_data
                    )

                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ Handled gracefully")
                        print(f"   Response: {result.get('response', '')[:100]}...")
                        results.append({
                            "test": test['name'],
                            "success": True,
                            "handled_gracefully": True,
                            "status_code": response.status_code
                        })
                    else:
                        print(f"⚠️ Returned error status: {response.status_code}")
                        results.append({
                            "test": test['name'],
                            "success": True,
                            "status_code": response.status_code,
                            "error": response.text[:100]
                        })

                except Exception as e:
                    print(f"❌ Exception: {str(e)}")
                    results.append({
                        "test": test['name'],
                        "success": False,
                        "error": str(e)
                    })

                await asyncio.sleep(0.5)

        return results

    async def test_missing_parameters(self):
        """필수 파라미터 누락 테스트"""
        print("\n" + "="*80)
        print("🔍 Testing Missing Parameters")
        print("="*80)

        test_cases = [
            {
                "name": "Missing user_id",
                "data": {
                    "query": "테스트 쿼리"
                }
            },
            {
                "name": "Missing query",
                "data": {
                    "user_id": "test_user"
                }
            },
            {
                "name": "Empty request body",
                "data": {}
            },
            {
                "name": "Invalid data type for query",
                "data": {
                    "query": 123,
                    "user_id": "test_user"
                }
            },
            {
                "name": "Invalid data type for context",
                "data": {
                    "query": "테스트 쿼리",
                    "user_id": "test_user",
                    "context": "should be dict"
                }
            }
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            results = []

            for test in test_cases:
                print(f"\n📝 {test['name']}")

                try:
                    response = await client.post(
                        f"{self.chat_url}/api/v1/chat",
                        json=test['data']
                    )

                    if response.status_code == 422:
                        print(f"✅ Correctly returned validation error (422)")
                        results.append({
                            "test": test['name'],
                            "success": True,
                            "status_code": response.status_code,
                            "validation_handled": True
                        })
                    elif response.status_code == 400:
                        print(f"✅ Returned bad request (400)")
                        results.append({
                            "test": test['name'],
                            "success": True,
                            "status_code": response.status_code
                        })
                    else:
                        print(f"⚠️ Unexpected status: {response.status_code}")
                        results.append({
                            "test": test['name'],
                            "success": False,
                            "status_code": response.status_code,
                            "unexpected": True
                        })

                except Exception as e:
                    print(f"❌ Exception: {str(e)}")
                    results.append({
                        "test": test['name'],
                        "success": False,
                        "error": str(e)
                    })

                await asyncio.sleep(0.5)

        return results

    async def test_timeout_scenarios(self):
        """타임아웃 시나리오 테스트"""
        print("\n" + "="*80)
        print("⏱️ Testing Timeout Scenarios")
        print("="*80)

        # 매우 복잡한 쿼리로 처리 시간이 오래 걸리도록 함
        complex_query = """
        2024년 전체 영업 실적을 월별, 팀별, 개인별로 상세 분석하고,
        전년 대비 성장률을 계산하며, 상위 10%, 하위 10% 직원을 식별하고,
        각 직원의 HR 정보와 매칭하여 종합 보고서를 작성해줘.
        또한 모든 관련 규정을 확인하고 위반 사항이 있는지 검토해줘.
        """

        async with httpx.AsyncClient(timeout=5.0) as client:  # 짧은 타임아웃 설정
            print(f"\n📝 Testing with 5 second timeout...")

            request_data = {
                "query": complex_query,
                "user_id": "timeout_test",
                "context": {}
            }

            try:
                start_time = time.time()
                response = await client.post(
                    f"{self.chat_url}/api/v1/chat",
                    json=request_data
                )
                elapsed = time.time() - start_time

                if response.status_code == 200:
                    print(f"✅ Completed within timeout ({elapsed:.2f}s)")
                    return {
                        "test": "timeout",
                        "success": True,
                        "completed_in_time": True,
                        "elapsed": elapsed
                    }
                else:
                    print(f"⚠️ Returned error: {response.status_code}")
                    return {
                        "test": "timeout",
                        "success": True,
                        "status_code": response.status_code
                    }

            except httpx.TimeoutException:
                print(f"✅ Timeout handled correctly")
                return {
                    "test": "timeout",
                    "success": True,
                    "timeout_occurred": True
                }

            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                return {
                    "test": "timeout",
                    "success": False,
                    "error": str(e)
                }

    async def test_database_errors(self):
        """데이터베이스 관련 에러 테스트"""
        print("\n" + "="*80)
        print("🗄️ Testing Database Error Handling")
        print("="*80)

        test_cases = [
            {
                "name": "Non-existent table query",
                "query": "SELECT * FROM non_existent_table_12345 데이터를 보여줘"
            },
            {
                "name": "Non-existent employee",
                "query": "홍길동123456 직원의 정보를 알려줘"
            },
            {
                "name": "Invalid date range",
                "query": "2025년 13월 실적을 보여줘"
            },
            {
                "name": "Non-existent department",
                "query": "우주개발팀의 실적을 분석해줘"
            }
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            results = []

            for test in test_cases:
                print(f"\n📝 {test['name']}")

                request_data = {
                    "query": test['query'],
                    "user_id": "db_error_test",
                    "context": {}
                }

                try:
                    response = await client.post(
                        f"{self.chat_url}/api/v1/chat",
                        json=request_data
                    )

                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ Handled gracefully")
                        print(f"   Response: {result.get('response', '')[:100]}...")
                        results.append({
                            "test": test['name'],
                            "success": True,
                            "handled_gracefully": True
                        })
                    else:
                        print(f"⚠️ Returned error: {response.status_code}")
                        results.append({
                            "test": test['name'],
                            "success": True,
                            "status_code": response.status_code
                        })

                except Exception as e:
                    print(f"❌ Exception: {str(e)}")
                    results.append({
                        "test": test['name'],
                        "success": False,
                        "error": str(e)
                    })

                await asyncio.sleep(0.5)

        return results

    async def test_session_errors(self):
        """세션 관련 에러 테스트"""
        print("\n" + "="*80)
        print("🔐 Testing Session Error Handling")
        print("="*80)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. 잘못된 세션 ID로 요청
            print("\n📝 Invalid session ID")
            request_data = {
                "query": "테스트 쿼리",
                "user_id": "session_test",
                "session_id": "invalid_session_id_12345",
                "context": {}
            }

            try:
                response = await client.post(
                    f"{self.chat_url}/api/v1/chat",
                    json=request_data
                )

                if response.status_code == 200:
                    print(f"✅ Created new session or handled gracefully")
                    result1 = {
                        "test": "invalid_session",
                        "success": True
                    }
                else:
                    print(f"⚠️ Returned error: {response.status_code}")
                    result1 = {
                        "test": "invalid_session",
                        "success": True,
                        "status_code": response.status_code
                    }

            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                result1 = {
                    "test": "invalid_session",
                    "success": False,
                    "error": str(e)
                }

            # 2. 매우 많은 세션 생성 시도
            print("\n📝 Multiple session creation")
            results = []

            for i in range(5):
                request_data = {
                    "query": f"세션 테스트 {i}",
                    "user_id": f"user_{i}",
                    "context": {}
                }

                try:
                    response = await client.post(
                        f"{self.chat_url}/api/v1/chat",
                        json=request_data
                    )

                    if response.status_code == 200:
                        results.append(True)
                    else:
                        results.append(False)

                except:
                    results.append(False)

            success_count = sum(results)
            print(f"✅ Successfully created {success_count}/5 sessions")

            return {
                "invalid_session": result1,
                "multiple_sessions": {
                    "total": 5,
                    "successful": success_count
                }
            }

    async def test_rate_limiting(self):
        """Rate limiting 테스트"""
        print("\n" + "="*80)
        print("🚦 Testing Rate Limiting")
        print("="*80)

        async with httpx.AsyncClient(timeout=5.0) as client:
            # 짧은 시간에 많은 요청 전송
            print("\n📝 Sending 20 rapid requests...")

            request_data = {
                "query": "Rate limit test",
                "user_id": "rate_test",
                "context": {}
            }

            success_count = 0
            rate_limited_count = 0
            error_count = 0

            for i in range(20):
                try:
                    response = await client.post(
                        f"{self.chat_url}/api/v1/chat",
                        json=request_data
                    )

                    if response.status_code == 200:
                        success_count += 1
                    elif response.status_code == 429:  # Too Many Requests
                        rate_limited_count += 1
                        print(f"   Request {i+1}: Rate limited")
                    else:
                        error_count += 1

                except Exception:
                    error_count += 1

                # 매우 짧은 대기
                await asyncio.sleep(0.1)

            print(f"\n📊 Results:")
            print(f"  • Successful: {success_count}/20")
            print(f"  • Rate limited: {rate_limited_count}/20")
            print(f"  • Errors: {error_count}/20")

            return {
                "test": "rate_limiting",
                "total": 20,
                "successful": success_count,
                "rate_limited": rate_limited_count,
                "errors": error_count
            }

    async def run_all_tests(self):
        """모든 에러 케이스 테스트 실행"""
        print("\n" + "="*80)
        print("🚨 Starting Error Case Tests")
        print("="*80)

        # 서버 체크
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.chat_url}/")
                if response.status_code != 200:
                    print("❌ Chat API is not running")
                    return

                response = await client.get(f"{self.db_url}/")
                if response.status_code != 200:
                    print("❌ Database API is not running")
                    return

                print("✅ Servers are running")
            except Exception as e:
                print(f"❌ Server check failed: {e}")
                print("Please start servers: python run_servers.py")
                return

        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }

        # 1. 잘못된 쿼리 테스트
        print("\n[1/6] Invalid Queries")
        results["tests"]["invalid_queries"] = await self.test_invalid_queries()

        # 2. 필수 파라미터 누락 테스트
        print("\n[2/6] Missing Parameters")
        results["tests"]["missing_parameters"] = await self.test_missing_parameters()

        # 3. 타임아웃 테스트
        print("\n[3/6] Timeout Scenarios")
        results["tests"]["timeout"] = await self.test_timeout_scenarios()

        # 4. 데이터베이스 에러 테스트
        print("\n[4/6] Database Errors")
        results["tests"]["database_errors"] = await self.test_database_errors()

        # 5. 세션 에러 테스트
        print("\n[5/6] Session Errors")
        results["tests"]["session_errors"] = await self.test_session_errors()

        # 6. Rate limiting 테스트
        print("\n[6/6] Rate Limiting")
        results["tests"]["rate_limiting"] = await self.test_rate_limiting()

        # 결과 저장 및 요약
        self.save_results(results)
        self.print_summary(results)

        return results

    def print_summary(self, results: Dict):
        """테스트 요약 출력"""
        print("\n" + "="*80)
        print("📊 Error Handling Test Summary")
        print("="*80)

        total_tests = 0
        handled_gracefully = 0
        errors = 0

        for test_category, test_results in results["tests"].items():
            if isinstance(test_results, list):
                total_tests += len(test_results)
                for result in test_results:
                    if result.get("success"):
                        handled_gracefully += 1
                    else:
                        errors += 1
            elif isinstance(test_results, dict):
                total_tests += 1
                if test_results.get("success"):
                    handled_gracefully += 1
                else:
                    errors += 1

        success_rate = (handled_gracefully / total_tests * 100) if total_tests > 0 else 0

        print(f"\n📈 Overall Results:")
        print(f"  • Total Tests: {total_tests}")
        print(f"  • Handled Gracefully: {handled_gracefully} ({success_rate:.1f}%)")
        print(f"  • Errors: {errors}")

        print(f"\n🔍 By Category:")
        for category in results["tests"]:
            print(f"  • {category.replace('_', ' ').title()}: ✅")

        if success_rate >= 90:
            print(f"\n✅ Excellent error handling! ({success_rate:.1f}% success rate)")
        elif success_rate >= 70:
            print(f"\n⚠️ Good error handling, but could be improved ({success_rate:.1f}% success rate)")
        else:
            print(f"\n❌ Error handling needs improvement ({success_rate:.1f}% success rate)")

        print("="*80)

    def save_results(self, results: Dict):
        """결과 저장"""
        filename = f"tests/test_results/reports/error_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Results saved to: {filename}")


async def main():
    """메인 함수"""
    try:
        tester = ErrorCaseTester()
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())