"""
인터랙티브 에이전트 테스트
사용자가 직접 쿼리를 입력하고 결과를 확인할 수 있는 테스트
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.agents import (
    SearchAgent,
    SalesAnalyticsAgent,
    ComplianceCheckAgent,
    DocumentGenerationAgent
)
from backend.service.utils import get_llm_manager

# 로깅 설정
logging.basicConfig(
    level=logging.WARNING,  # INFO -> WARNING으로 변경하여 로그 줄임
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class InteractiveOrchestrator:
    """인터랙티브 테스트를 위한 간단한 오케스트레이터"""

    def __init__(self):
        print("시스템 초기화 중...")
        self.llm_manager = get_llm_manager()
        self.agents = {
            "search_agent": SearchAgent(),
            "sales_analytics": SalesAnalyticsAgent(),
            "compliance_check": ComplianceCheckAgent(),
            "document_generation": DocumentGenerationAgent()
        }
        self.agent_results = {}  # 에이전트 실행 결과 저장
        print("✓ 시스템 준비 완료\n")

    async def process_query(self, query: str) -> Dict[str, Any]:
        """사용자 쿼리 처리"""
        session_id = f"session_{datetime.now().timestamp()}"
        self.agent_results = {}  # 결과 초기화

        print("\n" + "="*60)
        print(" 쿼리 처리 시작 ")
        print("="*60)
        print(f"입력: {query}")
        print("-"*60)

        # 1. 의도 분석
        print("\n[1단계] 의도 분석 (Intent Analysis)")
        print("-"*40)
        intent_result = await self.llm_manager.analyze_intent(query)

        print(f"✓ 의도: {intent_result.get('intent', 'unknown')}")
        print(f"✓ 신뢰도: {intent_result.get('confidence', 0):.1%}")
        print(f"✓ 필요 에이전트: {', '.join(intent_result.get('agents', []))}")

        if intent_result.get('entities'):
            print(f"✓ 추출된 정보:")
            for key, value in intent_result.get('entities', {}).items():
                if value:
                    print(f"  - {key}: {value}")

        # 2. 실행 계획 수립
        print("\n[2단계] 실행 계획 수립 (Planning)")
        print("-"*40)
        plan = await self.llm_manager.create_execution_plan(intent_result)

        steps = plan.get("steps", [])
        if steps:
            print(f"✓ 총 {len(steps)}개 작업 계획됨:")
            for step in steps:
                print(f"  {step['order']}. [{step['agent']}] {step['action']}")
        else:
            print("✗ 실행 계획 생성 실패")
            return {"error": "계획 수립 실패"}

        # 3. 에이전트 실행
        print("\n[3단계] 에이전트 실행 (Execution)")
        print("-"*40)

        for step in steps:
            agent_name = step.get("agent")
            if agent_name not in self.agents:
                print(f"✗ 알 수 없는 에이전트: {agent_name}")
                continue

            print(f"\n실행 중: {agent_name}")

            # 에이전트별 입력 준비
            agent_input = self._prepare_agent_input(
                agent_name, query, intent_result, step, "user", session_id
            )

            # 에이전트 실행
            try:
                agent = self.agents[agent_name]
                result = await agent.execute(agent_input)

                if result["status"] == "success":
                    self.agent_results[agent_name] = result.get("data", {})
                    print(f"  ✓ {agent_name} 실행 완료")

                    # 주요 결과 미리보기
                    self._print_agent_result_preview(agent_name, result.get("data", {}))
                else:
                    print(f"  ✗ {agent_name} 실행 실패: {result.get('error')}")
                    self.agent_results[agent_name] = {"error": result.get("error")}

            except Exception as e:
                print(f"  ✗ {agent_name} 오류: {e}")
                self.agent_results[agent_name] = {"error": str(e)}

        # 4. 응답 생성
        print("\n[4단계] 응답 생성 (Response Generation)")
        print("-"*40)
        response = await self.llm_manager.generate_response(query, self.agent_results)

        print("\n" + "="*60)
        print(" 최종 응답 ")
        print("="*60)
        print(response)
        print("="*60)

        return {
            "query": query,
            "intent": intent_result,
            "plan": plan,
            "results": self.agent_results,
            "response": response
        }

    def _prepare_agent_input(
        self, agent_name: str, query: str, intent_result: Dict,
        step: Dict, user_id: str, session_id: str
    ) -> Dict[str, Any]:
        """에이전트별 입력 데이터 준비"""
        base_input = {
            "user_id": user_id,
            "session_id": session_id,
            "original_query": query,  # 원본 쿼리 추가
            "intent_result": intent_result  # 의도분석 결과 추가
        }

        entities = intent_result.get("entities", {})

        if agent_name == "search_agent":
            return {
                **base_input,
                "query": query,
                "search_type": "both"
            }

        elif agent_name == "sales_analytics":
            person = entities.get("person", "")
            if not person:
                # 쿼리에서 이름 추출 시도
                for word in query.split():
                    if len(word) >= 2 and len(word) <= 4:  # 한국 이름은 보통 2-4글자
                        person = word
                        break
            return {
                **base_input,
                "employee_name": person or "최시우",  # 기본값
                "period": entities.get("period", "monthly")
            }

        elif agent_name == "compliance_check":
            check_type = "general"
            if "hr" in query.lower() or "인사" in query:
                check_type = "hr"
            elif "financial" in query.lower() or "재무" in query or "경비" in query:
                check_type = "financial"

            return {
                **base_input,
                "check_type": check_type,
                "check_target": entities.get("target", query[:20])
            }

        elif agent_name == "document_generation":
            # 이전 에이전트 결과 활용
            doc_data = {}
            doc_type = "general"

            if "sales_analytics" in self.agent_results:
                sales_data = self.agent_results["sales_analytics"]
                if "final_report" in sales_data:
                    doc_data = sales_data["final_report"]
                    doc_type = "sales_report"

            elif "compliance_check" in self.agent_results:
                compliance_data = self.agent_results["compliance_check"]
                if "compliance_report" in compliance_data:
                    doc_data = compliance_data["compliance_report"]
                    doc_type = "compliance_report"

            return {
                **base_input,
                "doc_type": doc_type,
                "title": f"{query[:30]} 보고서",
                "data": doc_data
            }

        return base_input

    def _print_agent_result_preview(self, agent_name: str, data: Dict):
        """에이전트 결과 미리보기 출력"""
        if agent_name == "search_agent":
            final = data.get("final_results", {})
            if final:
                print(f"    → 검색 결과: {final.get('total_results', 0)}건")

        elif agent_name == "sales_analytics":
            report = data.get("final_report", {})
            if report and "statistics" in report:
                stats = report["statistics"]
                print(f"    → 총 매출: {stats.get('total_sales', 0):,.0f}원")
                print(f"    → 거래 건수: {stats.get('transaction_count', 0)}건")

        elif agent_name == "compliance_check":
            report = data.get("compliance_report", {})
            if report and "summary" in report:
                summary = report["summary"]
                print(f"    → 규정 검토: {summary.get('total_policies', 0)}개")
                print(f"    → 준수율: {summary.get('compliance_rate', 0)}%")

        elif agent_name == "document_generation":
            doc = data.get("final_document", {})
            if doc:
                print(f"    → 문서 생성: {doc.get('title', '제목없음')}")
                print(f"    → 섹션 수: {len(doc.get('sections', []))}개")


async def run_single_query():
    """단일 쿼리 실행"""
    print("\n" + "="*60)
    print(" 단일 쿼리 테스트 ")
    print("="*60)

    orchestrator = InteractiveOrchestrator()

    # 예시 쿼리 목록
    example_queries = [
        "최시우 실적 분석해줘",
        "김철수 직원 정보 찾아줘",
        "휴가 규정 확인해줘",
        "3월 실적 보고서 만들어줘",
        "경비 처리 규정 준수 확인"
    ]

    print("\n예시 쿼리:")
    for i, q in enumerate(example_queries, 1):
        print(f"  {i}. {q}")

    user_input = input("\n쿼리 입력 (1-5 선택 또는 직접 입력, Enter로 1번 사용): ").strip()

    # 번호 선택 처리
    if user_input in ['1', '2', '3', '4', '5']:
        query = example_queries[int(user_input) - 1]
        print(f"→ 예시 {user_input}번 선택: {query}")
    elif not user_input:
        query = example_queries[0]
        print(f"→ 예시 1번 사용: {query}")
    else:
        query = user_input
        print(f"→ 직접 입력: {query}")

    await orchestrator.process_query(query)


async def run_interactive_loop():
    """연속 대화형 테스트"""
    print("\n" + "="*60)
    print(" 대화형 테스트 모드 ")
    print("="*60)
    print("종료하려면 'exit', 'quit', 또는 '종료'를 입력하세요.")

    orchestrator = InteractiveOrchestrator()

    while True:
        query = input("\n질문 > ").strip()

        if query.lower() in ['exit', 'quit', '종료', 'q']:
            print("\n테스트를 종료합니다.")
            break

        if not query:
            print("쿼리를 입력해주세요.")
            continue

        try:
            await orchestrator.process_query(query)
        except Exception as e:
            print(f"\n오류 발생: {e}")
            print("다시 시도해주세요.")


async def run_batch_test():
    """미리 정의된 쿼리 배치 테스트"""
    print("\n" + "="*60)
    print(" 배치 테스트 ")
    print("="*60)

    test_queries = [
        "최시우 실적 분석해줘",
        "김철수 직원 정보 찾아줘",
        "연차 사용 규정 확인해줘",
        "이영희 3월 실적 보고서 작성해줘",
        "경비 처리 규정 준수 여부 확인"
    ]

    orchestrator = InteractiveOrchestrator()

    for i, query in enumerate(test_queries, 1):
        print(f"\n\n[테스트 {i}/{len(test_queries)}]")
        await orchestrator.process_query(query)

        if i < len(test_queries):
            input("\nEnter를 눌러 다음 테스트 진행...")


async def main():
    """메인 실행 함수"""
    print("\n" + "="*70)
    print(" NaruTalk 에이전트 인터랙티브 테스트 ".center(70))
    print("="*70)

    while True:
        print("\n테스트 모드 선택:")
        print("  1. 단일 쿼리 테스트")
        print("  2. 대화형 테스트 (연속 질문)")
        print("  3. 배치 테스트 (미리 정의된 쿼리)")
        print("  0. 종료")

        choice = input("\n선택 (0-3): ").strip()

        if choice == "1":
            await run_single_query()
        elif choice == "2":
            await run_interactive_loop()
        elif choice == "3":
            await run_batch_test()
        elif choice == "0":
            print("\n프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다. 다시 선택해주세요.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n프로그램이 중단되었습니다.")