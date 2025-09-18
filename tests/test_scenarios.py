"""
시나리오 기반 테스트
실제 업무 시나리오별로 Chat API를 테스트
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ScenarioTester:
    """시나리오 기반 테스트 클래스"""

    def __init__(self, chat_url: str = "http://localhost:8001", db_url: str = "http://localhost:8002"):
        self.chat_url = chat_url
        self.db_url = db_url
        self.results = []
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def execute_query(self, query: str, context: Dict[str, Any] = None) -> Tuple[bool, Dict]:
        """단일 쿼리 실행"""
        request_data = {
            "query": query,
            "user_id": "scenario_test",
            "context": context or {},
            "use_cache": False  # 테스트 시 캐시 비활성화
        }

        start_time = time.time()

        try:
            response = await self.client.post(
                f"{self.chat_url}/api/v1/chat",
                json=request_data
            )

            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                return True, {
                    "query": query,
                    "response": result.get('response'),
                    "elapsed_time": elapsed_time,
                    "agents_used": result.get('agents_used', []),
                    "cached": result.get('cached', False)
                }
            else:
                return False, {
                    "query": query,
                    "error": f"Status {response.status_code}",
                    "detail": response.text,
                    "elapsed_time": elapsed_time
                }

        except Exception as e:
            return False, {
                "query": query,
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }

    async def run_scenario(self, name: str, queries: List[str], context: Dict[str, Any] = None) -> Dict:
        """시나리오 실행"""
        print(f"\n{'='*80}")
        print(f"📋 Running Scenario: {name}")
        print(f"{'='*80}")

        scenario_result = {
            "name": name,
            "context": context,
            "total_queries": len(queries),
            "successful": 0,
            "failed": 0,
            "total_time": 0,
            "queries": []
        }

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] {query}")
            print("⏳ Processing...")

            success, result = await self.execute_query(query, context)

            if success:
                scenario_result["successful"] += 1
                print(f"✅ Success ({result['elapsed_time']:.2f}s)")
                if result.get('agents_used'):
                    print(f"   Agents: {', '.join(result['agents_used'])}")
                print(f"   Response: {result['response'][:200]}...")
            else:
                scenario_result["failed"] += 1
                print(f"❌ Failed: {result.get('error')}")

            scenario_result["total_time"] += result.get('elapsed_time', 0)
            scenario_result["queries"].append(result)

            # 짧은 대기
            await asyncio.sleep(0.5)

        # 시나리오 요약
        print(f"\n{'='*80}")
        print(f"📊 Scenario Summary: {name}")
        print(f"  • Total Queries: {scenario_result['total_queries']}")
        print(f"  • Successful: {scenario_result['successful']} ✅")
        print(f"  • Failed: {scenario_result['failed']} ❌")
        print(f"  • Total Time: {scenario_result['total_time']:.2f}s")
        print(f"  • Avg Time: {scenario_result['total_time'] / scenario_result['total_queries']:.2f}s")
        print(f"{'='*80}")

        return scenario_result

    async def test_sales_scenarios(self):
        """영업 실적 분석 시나리오"""
        scenarios = [
            {
                "name": "월별 실적 분석",
                "context": {"role": "영업팀장", "department": "영업1팀"},
                "queries": [
                    "2024년 11월 전체 영업실적을 요약해줘",
                    "전월 대비 성장률이 어떻게 되나요?",
                    "상위 5명의 영업사원과 실적을 알려줘",
                    "하위 실적자들에 대한 개선 방안을 제시해줘"
                ]
            },
            {
                "name": "개인 실적 추적",
                "context": {"role": "매니저", "department": "영업관리팀"},
                "queries": [
                    "김철수 직원의 2024년 연간 실적 추이를 보여줘",
                    "김철수의 목표 달성률은 어떻게 되나요?",
                    "김철수와 팀 평균을 비교해줘",
                    "김철수의 강점과 개선점을 분석해줘"
                ]
            },
            {
                "name": "팀별 비교 분석",
                "context": {"role": "임원", "department": "경영지원팀"},
                "queries": [
                    "영업1팀과 영업2팀의 실적을 비교해줘",
                    "가장 성과가 좋은 팀은 어디인가요?",
                    "팀별 인당 평균 실적을 계산해줘",
                    "팀별 실적 격차의 원인을 분석해줘"
                ]
            }
        ]

        results = []
        for scenario in scenarios:
            result = await self.run_scenario(
                scenario["name"],
                scenario["queries"],
                scenario["context"]
            )
            results.append(result)

        return results

    async def test_hr_scenarios(self):
        """인사 정보 조회 시나리오"""
        scenarios = [
            {
                "name": "직원 정보 조회",
                "context": {"role": "HR담당자", "department": "인사팀"},
                "queries": [
                    "영업1팀의 전체 직원 명단을 보여줘",
                    "서울지점의 연락처를 알려줘",
                    "김영희 매니저의 상세 정보를 조회해줘",
                    "2024년 신입사원 명단을 보여줘"
                ]
            },
            {
                "name": "조직 구조 분석",
                "context": {"role": "경영기획", "department": "전략팀"},
                "queries": [
                    "부서별 인원 현황을 알려줘",
                    "지점별 직원 분포를 보여줘",
                    "매니저급 이상 직원 명단을 조회해줘",
                    "조직도를 간단히 설명해줘"
                ]
            }
        ]

        results = []
        for scenario in scenarios:
            result = await self.run_scenario(
                scenario["name"],
                scenario["queries"],
                scenario["context"]
            )
            results.append(result)

        return results

    async def test_compliance_scenarios(self):
        """규정 준수 확인 시나리오"""
        scenarios = [
            {
                "name": "리베이트 규정 확인",
                "context": {"role": "준법감시인", "department": "준법지원팀"},
                "queries": [
                    "리베이트 제공 관련 규정을 상세히 설명해줘",
                    "허용되는 경제적 이익의 범위는 어떻게 되나요?",
                    "리베이트 위반 시 처벌 규정을 알려줘",
                    "최근 리베이트 관련 법령 개정사항이 있나요?"
                ]
            },
            {
                "name": "공정거래 규정",
                "context": {"role": "영업담당", "department": "영업2팀"},
                "queries": [
                    "의료기기 판매 시 주의사항을 알려줘",
                    "공정거래법 위반 사례를 설명해줘",
                    "담합 행위의 정의와 제재사항을 알려줘",
                    "거래처와의 계약 시 주의사항은?"
                ]
            }
        ]

        results = []
        for scenario in scenarios:
            result = await self.run_scenario(
                scenario["name"],
                scenario["queries"],
                scenario["context"]
            )
            results.append(result)

        return results

    async def test_document_generation_scenarios(self):
        """문서 생성 시나리오"""
        scenarios = [
            {
                "name": "보고서 작성",
                "context": {"role": "팀장", "department": "영업기획팀"},
                "queries": [
                    "11월 영업 실적 보고서를 작성해줘",
                    "전년 동기 대비 분석을 포함해줘",
                    "주요 성과와 개선사항을 정리해줘",
                    "다음 달 전략을 제안해줘"
                ]
            },
            {
                "name": "규정 위반 리스크 평가",
                "context": {"role": "컴플라이언스 매니저", "department": "준법지원팀"},
                "queries": [
                    "현재 영업 활동의 규정 위반 리스크를 평가해줘",
                    "고위험 영역을 식별해줘",
                    "리스크 완화 방안을 제시해줘",
                    "모니터링 체계를 제안해줘"
                ]
            }
        ]

        results = []
        for scenario in scenarios:
            result = await self.run_scenario(
                scenario["name"],
                scenario["queries"],
                scenario["context"]
            )
            results.append(result)

        return results

    async def test_complex_scenarios(self):
        """복합 시나리오 (여러 Agent 협업)"""
        scenarios = [
            {
                "name": "종합 분석 및 전략 수립",
                "context": {"role": "CEO", "department": "경영진"},
                "queries": [
                    "2024년 전체 영업 실적과 HR 현황을 종합 분석해줘",
                    "실적 상위 직원들의 특성을 분석하고 채용 전략을 제안해줘",
                    "규정 준수와 실적 향상을 동시에 달성할 수 있는 방안은?",
                    "내년도 사업 계획을 위한 종합 보고서를 작성해줘"
                ]
            }
        ]

        results = []
        for scenario in scenarios:
            result = await self.run_scenario(
                scenario["name"],
                scenario["queries"],
                scenario["context"]
            )
            results.append(result)

        return results

    async def run_all_scenarios(self):
        """모든 시나리오 실행"""
        print("\n" + "="*80)
        print("🚀 Starting Scenario Tests")
        print("="*80)

        # 서버 체크
        try:
            response = await self.client.get(f"{self.chat_url}/")
            if response.status_code != 200:
                print("❌ Chat API is not running")
                return

            response = await self.client.get(f"{self.db_url}/")
            if response.status_code != 200:
                print("❌ Database API is not running")
                return

            print("✅ Servers are running")
        except Exception as e:
            print(f"❌ Server check failed: {e}")
            print("Please start servers: python run_servers.py")
            return

        all_results = {
            "timestamp": datetime.now().isoformat(),
            "scenarios": {}
        }

        # 각 카테고리별 시나리오 실행
        print("\n📊 Testing Sales Scenarios...")
        all_results["scenarios"]["sales"] = await self.test_sales_scenarios()

        print("\n👥 Testing HR Scenarios...")
        all_results["scenarios"]["hr"] = await self.test_hr_scenarios()

        print("\n📋 Testing Compliance Scenarios...")
        all_results["scenarios"]["compliance"] = await self.test_compliance_scenarios()

        print("\n📄 Testing Document Generation Scenarios...")
        all_results["scenarios"]["documents"] = await self.test_document_generation_scenarios()

        print("\n🔄 Testing Complex Scenarios...")
        all_results["scenarios"]["complex"] = await self.test_complex_scenarios()

        # 전체 통계
        self.print_overall_statistics(all_results)

        # 결과 저장
        self.save_results(all_results)

        return all_results

    def print_overall_statistics(self, results: Dict):
        """전체 통계 출력"""
        print("\n" + "="*80)
        print("📈 Overall Test Statistics")
        print("="*80)

        total_scenarios = 0
        total_queries = 0
        total_successful = 0
        total_failed = 0
        total_time = 0

        for category, scenarios in results["scenarios"].items():
            for scenario in scenarios:
                total_scenarios += 1
                total_queries += scenario["total_queries"]
                total_successful += scenario["successful"]
                total_failed += scenario["failed"]
                total_time += scenario["total_time"]

        success_rate = (total_successful / total_queries * 100) if total_queries > 0 else 0

        print(f"📊 Summary:")
        print(f"  • Total Scenarios: {total_scenarios}")
        print(f"  • Total Queries: {total_queries}")
        print(f"  • Successful: {total_successful} ({success_rate:.1f}%)")
        print(f"  • Failed: {total_failed}")
        print(f"  • Total Time: {total_time:.2f}s")
        print(f"  • Average Time per Query: {total_time/total_queries:.2f}s")

        # 카테고리별 통계
        print(f"\n📂 By Category:")
        for category, scenarios in results["scenarios"].items():
            cat_queries = sum(s["total_queries"] for s in scenarios)
            cat_successful = sum(s["successful"] for s in scenarios)
            cat_rate = (cat_successful / cat_queries * 100) if cat_queries > 0 else 0
            print(f"  • {category.capitalize()}: {cat_successful}/{cat_queries} ({cat_rate:.1f}%)")

        print("="*80)

    def save_results(self, results: Dict):
        """결과 저장"""
        filename = f"tests/test_results/reports/scenarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Results saved to: {filename}")


async def main():
    """메인 함수"""
    try:
        async with ScenarioTester() as tester:
            await tester.run_all_scenarios()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())