"""
전체 테스트 실행기
모든 테스트를 순차적으로 실행하고 종합 보고서를 생성
"""

import asyncio
import sys
import os
from datetime import datetime
import json
import time
from typing import Dict, Any

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 테스트 모듈 import
from test_scenarios import ScenarioTester
from test_performance import PerformanceTester
from test_error_cases import ErrorCaseTester


class TestRunner:
    """전체 테스트 실행 관리자"""

    def __init__(self, chat_url: str = "http://localhost:8001", db_url: str = "http://localhost:8002"):
        self.chat_url = chat_url
        self.db_url = db_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_suites": {},
            "summary": {}
        }

    async def check_servers(self) -> bool:
        """서버 상태 확인"""
        import httpx

        print("\n" + "="*80)
        print("🔍 Checking Servers")
        print("="*80)

        async with httpx.AsyncClient() as client:
            servers_ready = True

            # Chat API 확인
            try:
                response = await client.get(f"{self.chat_url}/")
                if response.status_code == 200:
                    print(f"✅ Chat API is running on {self.chat_url}")
                else:
                    print(f"❌ Chat API returned status {response.status_code}")
                    servers_ready = False
            except Exception as e:
                print(f"❌ Chat API is not accessible: {e}")
                servers_ready = False

            # Database API 확인
            try:
                response = await client.get(f"{self.db_url}/")
                if response.status_code == 200:
                    print(f"✅ Database API is running on {self.db_url}")
                else:
                    print(f"❌ Database API returned status {response.status_code}")
                    servers_ready = False
            except Exception as e:
                print(f"❌ Database API is not accessible: {e}")
                servers_ready = False

            if not servers_ready:
                print("\n⚠️ Please start the servers first:")
                print("   python run_servers.py")

            return servers_ready

    async def run_scenario_tests(self):
        """시나리오 테스트 실행"""
        print("\n" + "="*80)
        print("📋 [1/3] Running Scenario Tests")
        print("="*80)

        try:
            start_time = time.time()
            tester = ScenarioTester(self.chat_url, self.db_url)

            async with tester:
                results = await tester.run_all_scenarios()

            elapsed = time.time() - start_time
            self.results["test_suites"]["scenarios"] = {
                "status": "completed",
                "elapsed_time": elapsed,
                "results": results
            }

            print(f"\n✅ Scenario tests completed in {elapsed:.1f}s")
            return True

        except Exception as e:
            print(f"\n❌ Scenario tests failed: {e}")
            self.results["test_suites"]["scenarios"] = {
                "status": "failed",
                "error": str(e)
            }
            return False

    async def run_performance_tests(self):
        """성능 테스트 실행"""
        print("\n" + "="*80)
        print("⚡ [2/3] Running Performance Tests")
        print("="*80)

        try:
            start_time = time.time()
            tester = PerformanceTester(self.chat_url, self.db_url)

            results = await tester.run_all_tests()

            elapsed = time.time() - start_time
            self.results["test_suites"]["performance"] = {
                "status": "completed",
                "elapsed_time": elapsed,
                "results": results
            }

            print(f"\n✅ Performance tests completed in {elapsed:.1f}s")
            return True

        except Exception as e:
            print(f"\n❌ Performance tests failed: {e}")
            self.results["test_suites"]["performance"] = {
                "status": "failed",
                "error": str(e)
            }
            return False

    async def run_error_tests(self):
        """에러 케이스 테스트 실행"""
        print("\n" + "="*80)
        print("🚨 [3/3] Running Error Case Tests")
        print("="*80)

        try:
            start_time = time.time()
            tester = ErrorCaseTester(self.chat_url, self.db_url)

            results = await tester.run_all_tests()

            elapsed = time.time() - start_time
            self.results["test_suites"]["error_cases"] = {
                "status": "completed",
                "elapsed_time": elapsed,
                "results": results
            }

            print(f"\n✅ Error case tests completed in {elapsed:.1f}s")
            return True

        except Exception as e:
            print(f"\n❌ Error case tests failed: {e}")
            self.results["test_suites"]["error_cases"] = {
                "status": "failed",
                "error": str(e)
            }
            return False

    def generate_summary(self):
        """테스트 요약 생성"""
        summary = {
            "total_suites": 3,
            "completed": 0,
            "failed": 0,
            "total_time": 0,
            "details": {}
        }

        for suite_name, suite_result in self.results["test_suites"].items():
            if suite_result["status"] == "completed":
                summary["completed"] += 1
                summary["total_time"] += suite_result.get("elapsed_time", 0)

                # 각 테스트 스위트별 세부 통계
                if suite_name == "scenarios" and suite_result.get("results"):
                    scenarios = suite_result["results"]["scenarios"]
                    total_queries = 0
                    successful_queries = 0

                    for category in scenarios.values():
                        for scenario in category:
                            total_queries += scenario["total_queries"]
                            successful_queries += scenario["successful"]

                    summary["details"]["scenarios"] = {
                        "total_queries": total_queries,
                        "successful": successful_queries,
                        "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0
                    }

                elif suite_name == "performance" and suite_result.get("results"):
                    tests = suite_result["results"].get("tests", {})
                    if "response_times" in tests:
                        stats = tests["response_times"].get("statistics", {})
                        summary["details"]["performance"] = {
                            "mean_response_time": stats.get("mean", 0),
                            "median_response_time": stats.get("median", 0)
                        }

                    if "load" in tests:
                        load = tests["load"]
                        summary["details"]["performance"]["rps"] = load.get("actual_rps", 0)
                        summary["details"]["performance"]["success_rate"] = (
                            load["successful"] / load["total_requests"] * 100
                        ) if load.get("total_requests", 0) > 0 else 0

            else:
                summary["failed"] += 1

        self.results["summary"] = summary
        return summary

    def print_final_report(self):
        """최종 보고서 출력"""
        print("\n" + "="*80)
        print("📊 FINAL TEST REPORT")
        print("="*80)

        summary = self.results["summary"]

        print(f"\n🎯 Overall Results:")
        print(f"  • Test Suites: {summary['completed']}/{summary['total_suites']} completed")
        print(f"  • Total Time: {summary['total_time']:.1f}s")

        if summary["completed"] == summary["total_suites"]:
            print(f"  • Status: ✅ All tests passed!")
        elif summary["completed"] > 0:
            print(f"  • Status: ⚠️ Partial success")
        else:
            print(f"  • Status: ❌ All tests failed")

        # 각 테스트별 세부사항
        if "scenarios" in summary["details"]:
            scenarios = summary["details"]["scenarios"]
            print(f"\n📋 Scenario Tests:")
            print(f"  • Queries: {scenarios['successful']}/{scenarios['total_queries']} successful")
            print(f"  • Success Rate: {scenarios['success_rate']:.1f}%")

        if "performance" in summary["details"]:
            perf = summary["details"]["performance"]
            print(f"\n⚡ Performance Tests:")
            if "mean_response_time" in perf:
                print(f"  • Mean Response: {perf['mean_response_time']:.3f}s")
                print(f"  • Median Response: {perf['median_response_time']:.3f}s")
            if "rps" in perf:
                print(f"  • Throughput: {perf['rps']:.2f} req/s")
                print(f"  • Load Test Success: {perf['success_rate']:.1f}%")

        print("\n" + "="*80)

        # 권장사항
        if summary["completed"] == summary["total_suites"]:
            print("\n💡 Recommendations:")

            # 시나리오 테스트 기반 권장사항
            if "scenarios" in summary["details"]:
                if summary["details"]["scenarios"]["success_rate"] < 90:
                    print("  • Consider improving agent reliability for better query handling")

            # 성능 테스트 기반 권장사항
            if "performance" in summary["details"]:
                perf = summary["details"]["performance"]
                if perf.get("mean_response_time", 0) > 5:
                    print("  • Response time is high, consider optimizing query processing")
                if perf.get("rps", 0) < 5:
                    print("  • Throughput is low, consider scaling or optimization")

            print("\n✅ System is ready for frontend integration!")
        else:
            print("\n❌ Please fix failing tests before frontend integration")

        print("="*80)

    def save_report(self):
        """테스트 보고서 저장"""
        filename = f"tests/test_results/reports/full_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Full report saved to: {filename}")

        # 간단한 HTML 보고서도 생성
        html_filename = filename.replace('.json', '.html')
        self.generate_html_report(html_filename)
        print(f"📄 HTML report saved to: {html_filename}")

    def generate_html_report(self, filename: str):
        """HTML 형식의 보고서 생성"""
        summary = self.results["summary"]

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {self.results['timestamp']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>Chat API Test Report</h1>
    <p>Generated: {self.results['timestamp']}</p>

    <div class="summary">
        <h2>Summary</h2>
        <p>Test Suites: {summary['completed']}/{summary['total_suites']} completed</p>
        <p>Total Time: {summary['total_time']:.1f} seconds</p>
        <p>Status: {'<span class="success">✅ All Passed</span>' if summary['completed'] == summary['total_suites'] else '<span class="danger">❌ Some Failed</span>'}</p>
    </div>

    <h2>Test Results</h2>
    <table>
        <tr>
            <th>Test Suite</th>
            <th>Status</th>
            <th>Time (s)</th>
            <th>Details</th>
        </tr>
"""

        for suite_name, suite_result in self.results["test_suites"].items():
            status_class = "success" if suite_result["status"] == "completed" else "danger"
            status_icon = "✅" if suite_result["status"] == "completed" else "❌"

            details = ""
            if suite_name in summary.get("details", {}):
                suite_details = summary["details"][suite_name]
                if "success_rate" in suite_details:
                    details = f"Success Rate: {suite_details['success_rate']:.1f}%"
                elif "mean_response_time" in suite_details:
                    details = f"Mean Response: {suite_details['mean_response_time']:.3f}s"

            html_content += f"""
        <tr>
            <td>{suite_name.replace('_', ' ').title()}</td>
            <td class="{status_class}">{status_icon} {suite_result['status'].title()}</td>
            <td>{suite_result.get('elapsed_time', 0):.1f}</td>
            <td>{details}</td>
        </tr>
"""

        html_content += """
    </table>
</body>
</html>
"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "🚀"*40)
        print("🚀 STARTING COMPREHENSIVE TEST SUITE")
        print("🚀"*40)

        start_time = time.time()

        # 1. 서버 확인
        if not await self.check_servers():
            print("\n❌ Cannot proceed without servers running")
            return False

        # 2. 시나리오 테스트
        await self.run_scenario_tests()

        # 3. 성능 테스트
        await self.run_performance_tests()

        # 4. 에러 케이스 테스트
        await self.run_error_tests()

        # 5. 요약 생성
        self.generate_summary()

        # 6. 최종 보고서
        self.print_final_report()

        # 7. 보고서 저장
        self.save_report()

        total_time = time.time() - start_time
        print(f"\n⏱️ Total test execution time: {total_time:.1f}s")

        return self.results["summary"]["completed"] == self.results["summary"]["total_suites"]


async def main():
    """메인 함수"""
    try:
        runner = TestRunner()
        success = await runner.run_all_tests()

        if success:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️ Some tests failed. Please check the report.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️ Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════╗
║     Chat API Comprehensive Test Suite       ║
║                                              ║
║  This will run:                              ║
║   1. Scenario Tests                          ║
║   2. Performance Tests                       ║
║   3. Error Case Tests                        ║
║                                              ║
║  Estimated time: 5-10 minutes                ║
╚══════════════════════════════════════════════╝
""")

    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm == 'y':
        asyncio.run(main())
    else:
        print("Test cancelled.")