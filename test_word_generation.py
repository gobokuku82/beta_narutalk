"""
Word 문서 생성 테스트
"""

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

        # 파일 크기 확인
        app_size = os.path.getsize(app_path)
        report_size = os.path.getsize(report_path)

        print(f"\n📊 File sizes:")
        print(f"   - Application: {app_size:,} bytes")
        print(f"   - Report: {report_size:,} bytes")

        if app_size == 0 or report_size == 0:
            print("⚠️ Warning: One or more files have zero size!")
            return False

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""

    print("=" * 80)
    print("🔧 Word Document Generation Test")
    print("=" * 80)

    # Word Generator 직접 테스트
    success = test_word_generator_directly()

    if success:
        print("\n✅ Test successful!")
    else:
        print("\n❌ Test failed!")

    # 생성된 문서 위치 안내
    output_dir = Path("./generated_documents")
    if output_dir.exists():
        files = list(output_dir.glob("*.docx"))
        if files:
            print(f"\n📁 Generated documents in: {output_dir.absolute()}")
            for file in files:
                print(f"   - {file.name} ({file.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()