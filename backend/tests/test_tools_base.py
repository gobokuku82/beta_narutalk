"""
Base Tools 테스트
Tool 시스템의 기본 기능을 테스트합니다.
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.tools.base import BaseTool, ToolResult, ToolRegistry
from app.tools.database_tools import DrugSearchTool, CustomerSearchTool
from app.tools.search_tools import VectorSearchTool, WebSearchTool
from app.tools.document_tools import DocumentGeneratorTool, ReportBuilderTool
from app.tools.compliance_tools import ComplianceCheckTool, RiskAssessmentTool
from app.tools.analysis_tools import DataAnalysisTool, TrendAnalysisTool
import logging
logger = logging.getLogger(__name__)


async def test_tool_registry():
    """Tool Registry 테스트"""
    print("\n=== Tool Registry 테스트 ===")
    
    # Registry 인스턴스
    registry = ToolRegistry()
    
    # 도구 등록
    drug_tool = DrugSearchTool()
    registry.register(drug_tool, "database")
    
    # 도구 조회
    retrieved_tool = registry.get_tool("drug_search")
    assert retrieved_tool is not None, "도구를 찾을 수 없습니다"
    assert retrieved_tool.name == "drug_search", "도구 이름이 일치하지 않습니다"
    
    # 카테고리별 도구 조회
    db_tools = registry.get_tools_by_category("database")
    assert len(db_tools) > 0, "데이터베이스 도구를 찾을 수 없습니다"
    
    print(f"✅ Registry에 등록된 도구 수: {len(registry.list_all_tools())}")
    print(f"✅ 카테고리별 도구: {list(registry._categories.keys())}")
    

async def test_drug_search_tool():
    """의약품 검색 도구 테스트"""
    print("\n=== DrugSearchTool 테스트 ===")
    
    tool = DrugSearchTool()
    
    # 도구 실행
    result = await tool._arun(keyword="아스피린")
    
    assert result.success, f"도구 실행 실패: {result.error}"
    assert result.data is not None, "결과 데이터가 없습니다"
    
    print(f"✅ 검색어: 아스피린")
    print(f"✅ 검색 결과: {result.data.get('count', 0)}개")
    print(f"✅ 실행 시간: {result.execution_time:.2f}초")
    

async def test_customer_search_tool():
    """고객 검색 도구 테스트"""
    print("\n=== CustomerSearchTool 테스트 ===")
    
    tool = CustomerSearchTool()
    
    # 도구 실행
    result = await tool._arun(keyword="서울")
    
    assert result.success, f"도구 실행 실패: {result.error}"
    assert result.data is not None, "결과 데이터가 없습니다"
    
    print(f"✅ 검색어: 서울")
    print(f"✅ 검색 결과: {result.data.get('count', 0)}개")
    print(f"✅ 실행 시간: {result.execution_time:.2f}초")


async def test_web_search_tool():
    """웹 검색 도구 테스트"""
    print("\n=== WebSearchTool 테스트 ===")
    
    tool = WebSearchTool()
    
    # 도구 실행
    result = await tool._arun(
        query="COVID-19 vaccine",
        site="fda.gov",
        num_results=5
    )
    
    assert result.success, f"도구 실행 실패: {result.error}"
    assert result.data is not None, "결과 데이터가 없습니다"
    
    print(f"✅ 검색어: COVID-19 vaccine")
    print(f"✅ 사이트: fda.gov")
    print(f"✅ 검색 결과: {result.data.get('count', 0)}개")
    

async def test_document_generator_tool():
    """문서 생성 도구 테스트"""
    print("\n=== DocumentGeneratorTool 테스트 ===")
    
    tool = DocumentGeneratorTool()
    
    # 도구 실행
    result = await tool._arun(
        content="테스트 문서 내용입니다. 이것은 자동 생성된 문서입니다.",
        document_type="report",
        format="markdown"
    )
    
    assert result.success, f"도구 실행 실패: {result.error}"
    assert result.data is not None, "결과 데이터가 없습니다"
    assert "document" in result.data, "문서가 생성되지 않았습니다"
    
    print(f"✅ 문서 유형: {result.data.get('document_type')}")
    print(f"✅ 파일 경로: {result.data.get('filepath')}")
    print(f"✅ 단어 수: {result.data.get('metadata', {}).get('word_count', 0)}")


async def test_compliance_check_tool():
    """컴플라이언스 체크 도구 테스트"""
    print("\n=== ComplianceCheckTool 테스트 ===")
    
    tool = ComplianceCheckTool()
    
    # 도구 실행
    result = await tool._arun(
        check_type="drug_regulation",
        target="신약 A",
        regulations=None
    )
    
    assert result.success, f"도구 실행 실패: {result.error}"
    assert result.data is not None, "결과 데이터가 없습니다"
    
    print(f"✅ 확인 대상: 신약 A")
    print(f"✅ 준수율: {result.data.get('compliance_rate', 0)}%")
    print(f"✅ 리스크 수준: {result.data.get('risk_level')}")


async def test_data_analysis_tool():
    """데이터 분석 도구 테스트"""
    print("\n=== DataAnalysisTool 테스트 ===")
    
    tool = DataAnalysisTool()
    
    # 도구 실행 (MultiStepTool)
    result = await tool._arun(
        data_type="sales",
        period="2024-01",
        metrics=["total", "average", "growth"]
    )
    
    assert result.success, f"도구 실행 실패: {result.error}"
    assert result.data is not None, "결과 데이터가 없습니다"
    
    print(f"✅ 분석 유형: sales")
    print(f"✅ 분석 기간: 2024-01")
    print(f"✅ 실행된 단계: {list(result.data.keys())}")
    

async def test_trend_analysis_tool():
    """트렌드 분석 도구 테스트"""
    print("\n=== TrendAnalysisTool 테스트 ===")
    
    tool = TrendAnalysisTool()
    
    # 도구 실행
    result = await tool._arun(
        metric="revenue",
        periods=6,
        forecast=True
    )
    
    assert result.success, f"도구 실행 실패: {result.error}"
    assert result.data is not None, "결과 데이터가 없습니다"
    
    print(f"✅ 분석 지표: revenue")
    print(f"✅ 트렌드: {result.data.get('trend')}")
    print(f"✅ 성장률: {result.data.get('growth_rate')}%")
    if "forecast" in result.data:
        print(f"✅ 예측 데이터: {len(result.data['forecast'])}개월")


async def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Tool System 테스트 시작")
    print("=" * 60)
    
    test_functions = [
        test_tool_registry,
        test_drug_search_tool,
        test_customer_search_tool,
        test_web_search_tool,
        test_document_generator_tool,
        test_compliance_check_tool,
        test_data_analysis_tool,
        test_trend_analysis_tool
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} 실패: {str(e)}")
            logger.error(f"Test failed: {test_func.__name__}", exc_info=True)
    
    print("\n" + "=" * 60)
    print(f"테스트 완료: 성공 {passed}/{len(test_functions)}, 실패 {failed}/{len(test_functions)}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)