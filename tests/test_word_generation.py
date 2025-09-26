"""
Word 문서 생성 테스트
"""

import asyncio
import sys
import os
import io
from datetime import datetime
from pathlib import Path

# Windows 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv(Path('.env'))

from backend.service.tools.word_generator import WordGenerator
from backend.service.agents.document_generation_agent import DocumentGenerationAgent


def test_word_generator_directly():
    """Word Generator 직접 테스트"""

    print("=" * 80)
    print("📝 Direct Word Generator Test")
    print("=" * 80)

    generator = WordGenerator()

    # 제품설명회 신청서 데이터
    application_data = {
        "seminar_type": "단일",
        "pm_attendance": "참석",
        "date": "2024-12-15 14:00",
        "location": "서울 강남구 테헤란로 123 회의실",
        "product_name": "신약 A",
        "expected_attendees": "20명",
        "purpose": "신제품 효능 및 사용법 소개",
        "main_content": "1. 제품 소개\n2. 임상 데이터 발표\n3. Q&A 세션",
        "staff_list": [
            {"no": "1", "team": "영업1팀", "name": "김영희", "signature": ""},
            {"no": "2", "team": "영업2팀", "name": "이철수", "signature": ""},
            {"no": "3", "team": "마케팅팀", "name": "박민수", "signature": ""}
        ],
        "hcp_list": [
            {"no": "1", "hospital": "서울대병원", "name": "정의사", "signature": ""},
            {"no": "2", "hospital": "삼성병원", "name": "김약사", "signature": ""},
            {"no": "3", "hospital": "아산병원", "name": "이간호", "signature": ""}
        ]
    }

    try:
        # 신청서 생성
        print("\n📄 Generating Product Seminar Application...")
        app_path = generator.create_product_seminar_application(application_data)
        print(f"✅ Created: {app_path}")

        # 결과보고서 데이터 (신청서 데이터 + 추가 필드)
        report_data = application_data.copy()
        report_data.update({
            "actual_attendees": "18명",
            "result": "성공적으로 진행됨. 참석자 만족도 높음.",
            "payment_details": "강의료: 500,000원\n다과비: 200,000원",
            "budget_usage": "총 예산: 1,000,000원\n사용액: 700,000원\n잔액: 300,000원"
        })

        # 결과보고서 생성
        print("\n📄 Generating Product Seminar Report...")
        report_path = generator.create_product_seminar_report(report_data)
        print(f"✅ Created: {report_path}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_document_generation_agent():
    """Document Generation Agent를 통한 테스트"""

    print("\n" + "=" * 80)
    print("🤖 Document Generation Agent Test")
    print("=" * 80)

    agent = DocumentGenerationAgent()

    # 테스트 데이터
    test_cases = [
        {
            "name": "Product Seminar Application",
            "input": {
                "doc_type": "product_seminar_application",
                "doc_format": "word",
                "data": {
                    "seminar_type": "복수",
                    "pm_attendance": "미참석",
                    "date": "2024-12-20 10:00",
                    "location": "부산 해운대구 센텀시티 컨벤션센터",
                    "product_name": "신약 B, 신약 C",
                    "expected_attendees": "50명",
                    "purpose": "신제품 라인업 종합 소개",
                    "main_content": "1. 회사 비전 발표\n2. 신제품 라인업 소개\n3. 네트워킹 시간",
                    "staff_list": [
                        {"no": "1", "team": "본사", "name": "최대표", "signature": ""},
                        {"no": "2", "team": "연구소", "name": "김연구", "signature": ""}
                    ],
                    "hcp_list": [
                        {"no": "1", "hospital": "부산대병원", "name": "박의사", "signature": ""},
                        {"no": "2", "hospital": "동아대병원", "name": "최약사", "signature": ""}
                    ]
                }
            }
        },
        {
            "name": "Product Seminar Report",
            "input": {
                "doc_type": "product_seminar_report",
                "doc_format": "word",
                "data": {
                    "seminar_type": "단일",
                    "pm_attendance": "참석",
                    "date": "2024-11-30 15:00",
                    "location": "대전 유성구 대덕연구단지",
                    "product_name": "바이오신약 D",
                    "actual_attendees": "30명",
                    "result": "목표 인원 달성. 활발한 질의응답 진행.",
                    "main_content": "1. 바이오 기술 소개\n2. 임상 3상 결과 발표\n3. 향후 계획 공유",
                    "payment_details": "강의료: 1,000,000원\n장소대여: 300,000원\n식사: 450,000원",
                    "budget_usage": "총 예산: 2,000,000원\n사용액: 1,750,000원\n잔액: 250,000원",
                    "staff_list": [
                        {"no": "1", "team": "임상팀", "name": "정임상", "signature": ""}
                    ],
                    "hcp_list": [
                        {"no": "1", "hospital": "충남대병원", "name": "강의사", "signature": ""}
                    ]
                }
            }
        }
    ]

    for test_case in test_cases:
        print(f"\n📋 Test Case: {test_case['name']}")
        print("-" * 60)

        try:
            # 에이전트 실행
            result = await agent.run(
                **test_case["input"],
                user_id="test_user",
                session_id=f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                language="ko"
            )

            # 결과 출력
            if result.get("status") == "completed":
                print(f"✅ Success!")
                final_doc = result.get("final_document", {})
                print(f"   - Document Type: {final_doc.get('doc_type')}")
                print(f"   - Format: {final_doc.get('format')}")
                print(f"   - Content: {final_doc.get('content', '')[:100]}...")
            else:
                print(f"❌ Failed: {result.get('status')}")
                print(f"   Error: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """메인 함수"""

    print("=" * 80)
    print("🔧 Word Document Generation Test Suite")
    print("=" * 80)

    # 1. Word Generator 직접 테스트
    success = test_word_generator_directly()

    if success:
        # 2. Document Generation Agent 테스트
        await test_document_generation_agent()

    print("\n" + "=" * 80)
    print("✅ Test Complete")
    print("=" * 80)

    # 생성된 문서 위치 안내
    output_dir = Path("./generated_documents")
    if output_dir.exists():
        files = list(output_dir.glob("*.docx"))
        if files:
            print(f"\n📁 Generated documents in: {output_dir.absolute()}")
            for file in files[-5:]:  # 최근 5개만
                print(f"   - {file.name}")


if __name__ == "__main__":
    asyncio.run(main())