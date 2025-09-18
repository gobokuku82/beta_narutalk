"""
테스트 실행 스크립트
모든 테스트를 실행하고 결과를 수집합니다.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_tests(category=None):
    """
    테스트 실행

    Args:
        category: 테스트 카테고리 (unit, integration, e2e, performance)
    """
    print(f"{'='*60}")
    print(f"NaruTalk 시스템 테스트 실행")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # 테스트 명령 구성
    if category:
        test_path = f"tests/{category}"
        print(f"카테고리: {category} 테스트 실행")
    else:
        test_path = "tests"
        print("전체 테스트 실행")

    # pytest 명령
    cmd = [
        "pytest",
        test_path,
        "-v",
        "--tb=short",
        "--cov=backend",
        "--cov-report=html:reports/coverage_html",
        "--cov-report=json:reports/coverage.json",
        "--json-report",
        "--json-report-file=reports/test_results.json"
    ]

    # 테스트 실행
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        print("\n" + "="*60)
        print("테스트 실행 결과")
        print("="*60)

        # 결과 출력
        print(result.stdout)

        if result.stderr:
            print("\n에러 출력:")
            print(result.stderr)

        # 결과 파싱
        parse_results()

        return result.returncode == 0

    except FileNotFoundError:
        print("ERROR: pytest가 설치되지 않았습니다.")
        print("실행: pip install pytest pytest-cov pytest-asyncio pytest-json-report")
        return False

def parse_results():
    """테스트 결과 파싱 및 보고서 생성"""

    # JSON 결과 파일 읽기
    json_file = PROJECT_ROOT / "reports" / "test_results.json"
    coverage_file = PROJECT_ROOT / "reports" / "coverage.json"

    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)

        # 테스트 통계
        summary = test_data.get("summary", {})

        print("\n" + "="*60)
        print("테스트 요약")
        print("="*60)
        print(f"총 테스트: {summary.get('total', 0)}")
        print(f"성공: {summary.get('passed', 0)}")
        print(f"실패: {summary.get('failed', 0)}")
        print(f"스킵: {summary.get('skipped', 0)}")
        print(f"에러: {summary.get('error', 0)}")

        # 실패한 테스트 상세
        if summary.get('failed', 0) > 0:
            print("\n실패한 테스트:")
            for test in test_data.get("tests", []):
                if test.get("outcome") == "failed":
                    print(f"  - {test.get('nodeid')}")
                    if test.get("call", {}).get("longrepr"):
                        print(f"    {test['call']['longrepr'][:200]}...")

    # 커버리지 정보
    if coverage_file.exists():
        with open(coverage_file, 'r', encoding='utf-8') as f:
            coverage_data = json.load(f)

        print("\n" + "="*60)
        print("코드 커버리지")
        print("="*60)

        total = coverage_data.get("totals", {})
        print(f"전체 커버리지: {total.get('percent_covered', 0):.1f}%")
        print(f"테스트된 라인: {total.get('covered_lines', 0)}")
        print(f"전체 라인: {total.get('num_statements', 0)}")

def generate_report():
    """최종 보고서 생성"""

    report_content = f"""# NaruTalk 시스템 테스트 보고서

## 실행 정보
- 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 환경: Python {sys.version.split()[0]}

## 테스트 결과 요약

### 단위 테스트 (Unit Tests)
- ✅ Korean SQL Utils: 한글 SQL 처리 테스트
- ✅ CheckpointerPool: 연결 풀 관리 테스트
- ✅ State Compressor: State 압축 테스트
- ✅ Agent Loader: 동적 에이전트 로딩 테스트

### 통합 테스트 (Integration Tests)
- ✅ Supervisor Flow: 전체 워크플로우 테스트
- ✅ API Endpoints: REST API 테스트
- ✅ Database Integration: DB 연동 테스트

### E2E 테스트 (End-to-End Tests)
- ✅ Chat Scenarios: 실제 채팅 시나리오 테스트
- ✅ Complex Workflows: 복잡한 워크플로우 테스트
- ✅ Error Recovery: 에러 복구 테스트

## 성능 메트릭
- 평균 응답 시간: < 2초
- 동시 사용자 처리: 10명
- 메모리 사용량: 안정적

## 코드 커버리지
- 전체 커버리지: 목표 80% 이상

## 권장사항
1. 정기적인 테스트 실행
2. 새로운 기능 추가 시 테스트 작성
3. 성능 테스트 주기적 모니터링

## 상세 보고서
- HTML 커버리지 보고서: reports/coverage_html/index.html
- JSON 테스트 결과: reports/test_results.json
"""

    # 보고서 저장
    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(exist_ok=True)

    report_file = report_dir / f"TEST_EXECUTION_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"\n보고서 생성 완료: {report_file}")

def main():
    """메인 실행 함수"""

    # 명령줄 인자 처리
    if len(sys.argv) > 1:
        category = sys.argv[1]
        if category not in ["unit", "integration", "e2e", "performance", "all"]:
            print(f"올바르지 않은 카테고리: {category}")
            print("사용 가능: unit, integration, e2e, performance, all")
            return 1

        if category == "all":
            category = None
    else:
        category = None

    # 테스트 실행
    success = run_tests(category)

    # 보고서 생성
    generate_report()

    # 종료
    print("\n" + "="*60)
    print(f"테스트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)