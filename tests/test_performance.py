"""
성능 테스트
Chat API의 응답 시간, 동시 요청 처리, 캐시 성능 등을 테스트
"""

import asyncio
import httpx
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any
import json
import os
import sys
import random

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PerformanceTester:
    """성능 테스트 클래스"""

    def __init__(self, chat_url: str = "http://localhost:8001", db_url: str = "http://localhost:8002"):
        self.chat_url = chat_url
        self.db_url = db_url
        self.test_queries = [
            "2024년 11월 영업실적을 분석해줘",
            "김철수 직원의 정보를 알려줘",
            "리베이트 관련 규정을 설명해줘",
            "영업1팀 전체 실적을 보여줘",
            "상위 10명의 영업사원을 조회해줘",
            "공정거래법 위반 사례를 알려줘",
            "서울지점 연락처를 찾아줘",
            "전월 대비 성장률을 계산해줘",
            "HR 규정 중 연차 사용 규칙은?",
            "팀별 실적 비교표를 만들어줘"
        ]

    async def measure_single_request(self, client: httpx.AsyncClient, query: str, use_cache: bool = False) -> Dict:
        """단일 요청 성능 측정"""
        request_data = {
            "query": query,
            "user_id": "perf_test",
            "context": {},
            "use_cache": use_cache
        }

        start_time = time.perf_counter()

        try:
            response = await client.post(
                f"{self.chat_url}/api/v1/chat",
                json=request_data,
                timeout=60.0
            )

            end_time = time.perf_counter()
            elapsed_time = end_time - start_time

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "elapsed_time": elapsed_time,
                    "response_time": result.get('response_time', 0),
                    "cached": result.get('cached', False),
                    "query": query
                }
            else:
                return {
                    "success": False,
                    "elapsed_time": elapsed_time,
                    "error": f"Status {response.status_code}",
                    "query": query
                }

        except Exception as e:
            return {
                "success": False,
                "elapsed_time": time.perf_counter() - start_time,
                "error": str(e),
                "query": query
            }

    async def test_response_times(self, iterations: int = 10):
        """응답 시간 테스트"""
        print("\n" + "="*80)
        print("⏱️  Response Time Test")
        print(f"Running {iterations} iterations...")
        print("="*80)

        async with httpx.AsyncClient() as client:
            results = []

            for i in range(iterations):
                query = random.choice(self.test_queries)
                print(f"\n[{i+1}/{iterations}] Testing: {query[:50]}...")

                result = await self.measure_single_request(client, query, use_cache=False)

                if result["success"]:
                    print(f"✅ Success: {result['elapsed_time']:.3f}s")
                    results.append(result['elapsed_time'])
                else:
                    print(f"❌ Failed: {result.get('error')}")

                # 짧은 대기
                await asyncio.sleep(0.5)

            if results:
                print("\n📊 Response Time Statistics:")
                print(f"  • Min: {min(results):.3f}s")
                print(f"  • Max: {max(results):.3f}s")
                print(f"  • Mean: {statistics.mean(results):.3f}s")
                print(f"  • Median: {statistics.median(results):.3f}s")
                if len(results) > 1:
                    print(f"  • Std Dev: {statistics.stdev(results):.3f}s")

                return {
                    "test": "response_times",
                    "iterations": iterations,
                    "successful": len(results),
                    "failed": iterations - len(results),
                    "times": results,
                    "statistics": {
                        "min": min(results),
                        "max": max(results),
                        "mean": statistics.mean(results),
                        "median": statistics.median(results),
                        "stdev": statistics.stdev(results) if len(results) > 1 else 0
                    }
                }

    async def test_concurrent_requests(self, concurrent: int = 5):
        """동시 요청 처리 테스트"""
        print("\n" + "="*80)
        print("🔄 Concurrent Requests Test")
        print(f"Sending {concurrent} concurrent requests...")
        print("="*80)

        async with httpx.AsyncClient() as client:
            queries = [random.choice(self.test_queries) for _ in range(concurrent)]

            print("\nSending requests...")
            start_time = time.perf_counter()

            # 동시 요청 생성
            tasks = [
                self.measure_single_request(client, query, use_cache=False)
                for query in queries
            ]

            # 모든 요청 완료 대기
            results = await asyncio.gather(*tasks)

            total_time = time.perf_counter() - start_time

            successful = [r for r in results if r["success"]]
            failed = [r for r in results if not r["success"]]

            print(f"\n✅ Completed in {total_time:.3f}s")
            print(f"  • Successful: {len(successful)}/{concurrent}")
            print(f"  • Failed: {len(failed)}/{concurrent}")

            if successful:
                times = [r['elapsed_time'] for r in successful]
                print(f"  • Avg Response Time: {statistics.mean(times):.3f}s")
                print(f"  • Max Response Time: {max(times):.3f}s")

            return {
                "test": "concurrent_requests",
                "concurrent": concurrent,
                "total_time": total_time,
                "successful": len(successful),
                "failed": len(failed),
                "avg_time": statistics.mean(times) if successful else 0
            }

    async def test_cache_performance(self):
        """캐시 성능 테스트"""
        print("\n" + "="*80)
        print("💾 Cache Performance Test")
        print("="*80)

        async with httpx.AsyncClient() as client:
            test_query = "2024년 11월 영업실적 상위 5명을 알려줘"

            # 첫 번째 요청 (캐시 미스)
            print(f"\n1. First request (cache miss): {test_query}")
            first_result = await self.measure_single_request(client, test_query, use_cache=True)

            if not first_result["success"]:
                print(f"❌ First request failed: {first_result.get('error')}")
                return None

            first_time = first_result['elapsed_time']
            print(f"   Time: {first_time:.3f}s")
            print(f"   Cached: {first_result.get('cached', False)}")

            # 짧은 대기
            await asyncio.sleep(1)

            # 두 번째 요청 (캐시 히트 예상)
            print(f"\n2. Second request (cache hit expected):")
            second_result = await self.measure_single_request(client, test_query, use_cache=True)

            if not second_result["success"]:
                print(f"❌ Second request failed: {second_result.get('error')}")
                return None

            second_time = second_result['elapsed_time']
            print(f"   Time: {second_time:.3f}s")
            print(f"   Cached: {second_result.get('cached', False)}")

            # 성능 개선 계산
            if second_result.get('cached'):
                improvement = ((first_time - second_time) / first_time) * 100
                print(f"\n📈 Cache Performance:")
                print(f"   • First request: {first_time:.3f}s")
                print(f"   • Cached request: {second_time:.3f}s")
                print(f"   • Improvement: {improvement:.1f}%")
                print(f"   • Speed up: {first_time/second_time:.1f}x faster")

            return {
                "test": "cache_performance",
                "first_request": {
                    "time": first_time,
                    "cached": first_result.get('cached', False)
                },
                "second_request": {
                    "time": second_time,
                    "cached": second_result.get('cached', False)
                },
                "improvement_percentage": improvement if second_result.get('cached') else 0
            }

    async def test_load_capacity(self, duration_seconds: int = 30, requests_per_second: int = 2):
        """부하 테스트"""
        print("\n" + "="*80)
        print("🏋️ Load Capacity Test")
        print(f"Duration: {duration_seconds}s, Rate: {requests_per_second} req/s")
        print("="*80)

        async with httpx.AsyncClient() as client:
            start_time = time.time()
            end_time = start_time + duration_seconds

            successful_requests = 0
            failed_requests = 0
            response_times = []

            request_count = 0

            while time.time() < end_time:
                # 요청 시작
                batch_start = time.time()

                # 초당 요청 수만큼 동시 요청
                tasks = []
                for _ in range(requests_per_second):
                    query = random.choice(self.test_queries)
                    tasks.append(self.measure_single_request(client, query, use_cache=True))

                results = await asyncio.gather(*tasks)

                for result in results:
                    request_count += 1
                    if result["success"]:
                        successful_requests += 1
                        response_times.append(result['elapsed_time'])
                    else:
                        failed_requests += 1

                # 진행 상황 출력
                elapsed = time.time() - start_time
                print(f"\r⏳ Progress: {elapsed:.0f}s / {duration_seconds}s | "
                      f"Requests: {request_count} | "
                      f"Success: {successful_requests} | "
                      f"Failed: {failed_requests}", end="")

                # 다음 배치까지 대기
                batch_duration = time.time() - batch_start
                if batch_duration < 1.0:
                    await asyncio.sleep(1.0 - batch_duration)

            print()  # 줄바꿈

            # 통계 계산
            actual_duration = time.time() - start_time
            actual_rps = request_count / actual_duration

            print(f"\n📊 Load Test Results:")
            print(f"  • Duration: {actual_duration:.1f}s")
            print(f"  • Total Requests: {request_count}")
            print(f"  • Successful: {successful_requests} ({successful_requests/request_count*100:.1f}%)")
            print(f"  • Failed: {failed_requests}")
            print(f"  • Actual RPS: {actual_rps:.2f}")

            if response_times:
                print(f"\n📈 Response Time Under Load:")
                print(f"  • Min: {min(response_times):.3f}s")
                print(f"  • Max: {max(response_times):.3f}s")
                print(f"  • Mean: {statistics.mean(response_times):.3f}s")
                print(f"  • Median: {statistics.median(response_times):.3f}s")

                # 백분위수 계산
                sorted_times = sorted(response_times)
                p95_index = int(len(sorted_times) * 0.95)
                p99_index = int(len(sorted_times) * 0.99)
                print(f"  • P95: {sorted_times[p95_index]:.3f}s")
                print(f"  • P99: {sorted_times[p99_index]:.3f}s")

            return {
                "test": "load_capacity",
                "duration": actual_duration,
                "target_rps": requests_per_second,
                "actual_rps": actual_rps,
                "total_requests": request_count,
                "successful": successful_requests,
                "failed": failed_requests,
                "response_times": {
                    "min": min(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "mean": statistics.mean(response_times) if response_times else 0,
                    "median": statistics.median(response_times) if response_times else 0,
                    "p95": sorted_times[p95_index] if response_times else 0,
                    "p99": sorted_times[p99_index] if response_times else 0
                }
            }

    async def run_all_tests(self):
        """모든 성능 테스트 실행"""
        print("\n" + "="*80)
        print("🚀 Starting Performance Tests")
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

        # 1. 응답 시간 테스트
        print("\n[1/4] Response Time Test")
        response_time_result = await self.test_response_times(iterations=10)
        if response_time_result:
            results["tests"]["response_times"] = response_time_result

        # 2. 동시 요청 테스트
        print("\n[2/4] Concurrent Requests Test")
        concurrent_result = await self.test_concurrent_requests(concurrent=10)
        if concurrent_result:
            results["tests"]["concurrent"] = concurrent_result

        # 3. 캐시 성능 테스트
        print("\n[3/4] Cache Performance Test")
        cache_result = await self.test_cache_performance()
        if cache_result:
            results["tests"]["cache"] = cache_result

        # 4. 부하 테스트
        print("\n[4/4] Load Capacity Test")
        load_result = await self.test_load_capacity(duration_seconds=20, requests_per_second=3)
        if load_result:
            results["tests"]["load"] = load_result

        # 결과 저장
        self.save_results(results)
        self.print_summary(results)

        return results

    def print_summary(self, results: Dict):
        """테스트 요약 출력"""
        print("\n" + "="*80)
        print("📊 Performance Test Summary")
        print("="*80)

        for test_name, test_result in results["tests"].items():
            if test_name == "response_times":
                print(f"\n⏱️ Response Times:")
                stats = test_result["statistics"]
                print(f"  • Mean: {stats['mean']:.3f}s")
                print(f"  • Median: {stats['median']:.3f}s")
                print(f"  • Min/Max: {stats['min']:.3f}s / {stats['max']:.3f}s")

            elif test_name == "concurrent":
                print(f"\n🔄 Concurrent Handling:")
                print(f"  • {test_result['successful']}/{test_result['concurrent']} successful")
                print(f"  • Avg time: {test_result['avg_time']:.3f}s")

            elif test_name == "cache":
                print(f"\n💾 Cache Performance:")
                print(f"  • Improvement: {test_result.get('improvement_percentage', 0):.1f}%")

            elif test_name == "load":
                print(f"\n🏋️ Load Capacity:")
                print(f"  • RPS: {test_result['actual_rps']:.2f}")
                print(f"  • Success rate: {test_result['successful']/test_result['total_requests']*100:.1f}%")
                print(f"  • P95 latency: {test_result['response_times']['p95']:.3f}s")

        print("\n" + "="*80)

    def save_results(self, results: Dict):
        """결과 저장"""
        filename = f"tests/test_results/performance/perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Results saved to: {filename}")


async def main():
    """메인 함수"""
    try:
        tester = PerformanceTester()
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())