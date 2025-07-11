#!/usr/bin/env python3
"""
고도화된 라우터 에이전트 테스트 스크립트
OpenAI GPT-4o 기반 라우팅 기능 검증
"""

import asyncio
import json
import time
from typing import Dict, List
import httpx
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

# 테스트 URL
ROUTER_URL = "http://localhost:8001"

# 테스트 메시지들
TEST_MESSAGES = [
    {
        "category": "문서검색",
        "messages": [
            "좋은제약의 윤리강령에 대해 알려주세요",
            "회사 정책 문서를 찾아주세요",
            "복리후생 제도는 어떻게 되나요?",
            "행동강령 규정을 확인하고 싶습니다"
        ]
    },
    {
        "category": "직원분석", 
        "messages": [
            "우리 회사 직원들의 성과는 어떤가요?",
            "부서별 출근 현황을 분석해주세요",
            "직원 통계 데이터를 보여주세요",
            "인사 평가 결과를 알려주세요"
        ]
    },
    {
        "category": "고객정보",
        "messages": [
            "주요 고객사와의 거래 현황을 보여주세요",
            "매출 분석 데이터를 확인하고 싶습니다",
            "계약 현황은 어떻게 되나요?",
            "고객 관리 정보를 조회해주세요"
        ]
    },
    {
        "category": "일반대화",
        "messages": [
            "안녕하세요",
            "좋은제약은 어떤 회사인가요?",
            "오늘 날씨가 좋네요",
            "반갑습니다"
        ]
    }
]

class RouterTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.successful_tests = 0
        
    async def test_router_health(self) -> bool:
        """라우터 헬스 체크"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ROUTER_URL}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ 라우터 에이전트 상태: {health_data['status']}")
                    print(f"   OpenAI 상태: {health_data['openai_status']}")
                    print(f"   버전: {health_data['details']['version']}")
                    return True
                else:
                    print(f"❌ 라우터 에이전트 연결 실패: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ 라우터 에이전트 연결 오류: {str(e)}")
            return False
    
    async def test_single_message(self, message: str, expected_category: str) -> Dict:
        """단일 메시지 테스트"""
        try:
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                response = await client.post(
                    f"{ROUTER_URL}/analyze",
                    json={"message": message},
                    timeout=30.0
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    self.successful_tests += 1
                    
                    # 결과 분석
                    intent = result.get('intent', 'unknown')
                    confidence = result.get('confidence', 0.0)
                    service = result.get('service', 'unknown')
                    reasoning = result.get('reasoning', 'N/A')
                    
                    # 예상 의도 매핑
                    expected_intents = {
                        "문서검색": "search_documents",
                        "직원분석": "analyze_employee_data", 
                        "고객정보": "get_client_information",
                        "일반대화": "general_conversation"
                    }
                    
                    expected_intent = expected_intents.get(expected_category, 'unknown')
                    is_correct = intent == expected_intent
                    
                    return {
                        "message": message,
                        "expected_category": expected_category,
                        "expected_intent": expected_intent,
                        "actual_intent": intent,
                        "service": service,
                        "confidence": confidence,
                        "is_correct": is_correct,
                        "response_time": response_time,
                        "reasoning": reasoning,
                        "status": "success"
                    }
                else:
                    return {
                        "message": message,
                        "expected_category": expected_category,
                        "status": "error",
                        "error": f"HTTP {response.status_code}",
                        "response_time": response_time
                    }
                    
        except Exception as e:
            return {
                "message": message,
                "expected_category": expected_category,
                "status": "error",
                "error": str(e),
                "response_time": 0
            }
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 고도화된 라우터 에이전트 테스트 시작")
        print("=" * 60)
        
        # 1. 헬스 체크
        print("\n1. 라우터 에이전트 헬스 체크")
        if not await self.test_router_health():
            print("❌ 라우터 에이전트가 실행되지 않았습니다.")
            print("   다음 명령어로 실행하세요: python agents/router_agent/enhanced_main.py")
            return
        
        # 2. OpenAI API 키 확인
        print("\n2. OpenAI API 키 확인")
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️  OpenAI API 키가 설정되지 않았습니다.")
            print("   폴백 라우팅 모드로 테스트합니다.")
        else:
            print("✅ OpenAI API 키가 설정되었습니다.")
        
        # 3. 의도 분석 테스트
        print("\n3. 의도 분석 테스트")
        print("-" * 60)
        
        for test_group in TEST_MESSAGES:
            category = test_group["category"]
            messages = test_group["messages"]
            
            print(f"\n📋 {category} 테스트")
            
            for message in messages:
                self.total_tests += 1
                result = await self.test_single_message(message, category)
                self.results.append(result)
                
                if result["status"] == "success":
                    status_icon = "✅" if result["is_correct"] else "⚠️"
                    print(f"  {status_icon} {message}")
                    print(f"     → {result['actual_intent']} (신뢰도: {result['confidence']:.2f})")
                    print(f"     → 응답시간: {result['response_time']:.2f}초")
                    
                    if not result["is_correct"]:
                        print(f"     → 예상: {result['expected_intent']}, 실제: {result['actual_intent']}")
                else:
                    print(f"  ❌ {message}")
                    print(f"     → 오류: {result['error']}")
                
                # 과도한 API 호출 방지
                await asyncio.sleep(0.5)
        
        # 4. 결과 요약
        self.print_summary()
    
    def print_summary(self):
        """테스트 결과 요약"""
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        
        # 전체 통계
        accuracy = (self.successful_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        correct_predictions = sum(1 for r in self.results if r.get("is_correct", False))
        prediction_accuracy = (correct_predictions / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"총 테스트 수: {self.total_tests}")
        print(f"성공한 테스트: {self.successful_tests}")
        print(f"API 성공률: {accuracy:.1f}%")
        print(f"라우팅 정확도: {prediction_accuracy:.1f}%")
        
        # 카테고리별 통계
        print("\n📈 카테고리별 정확도")
        for test_group in TEST_MESSAGES:
            category = test_group["category"]
            category_results = [r for r in self.results if r.get("expected_category") == category]
            category_correct = sum(1 for r in category_results if r.get("is_correct", False))
            category_accuracy = (category_correct / len(category_results)) * 100 if category_results else 0
            
            print(f"  {category}: {category_accuracy:.1f}% ({category_correct}/{len(category_results)})")
        
        # 응답 시간 통계
        successful_results = [r for r in self.results if r["status"] == "success"]
        if successful_results:
            avg_response_time = sum(r["response_time"] for r in successful_results) / len(successful_results)
            print(f"\n⏱️  평균 응답 시간: {avg_response_time:.2f}초")
        
        # 권장사항
        print("\n💡 권장사항")
        if prediction_accuracy < 80:
            print("  - 라우팅 정확도가 낮습니다. OpenAI API 키를 확인하세요.")
        if accuracy < 100:
            print("  - 일부 API 호출이 실패했습니다. 네트워크 연결을 확인하세요.")
        if not os.getenv('OPENAI_API_KEY'):
            print("  - OpenAI API 키를 설정하면 더 높은 정확도를 얻을 수 있습니다.")
        
        print("\n🎉 테스트 완료!")

async def main():
    """메인 테스트 실행"""
    tester = RouterTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 