"""
Test individual agents without LLM
각 에이전트의 독립적인 기능 테스트
"""

import asyncio
import logging
from datetime import datetime
from backend.service.agents import (
    SearchAgent,
    SalesAnalyticsAgent,
    ComplianceCheckAgent,
    DocumentGenerationAgent
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_search_agent():
    """Test SearchAgent independently"""
    print("\n" + "="*60)
    print("Testing SearchAgent")
    print("="*60)

    agent = SearchAgent()

    # Test cases
    test_cases = [
        {
            "name": "HR Search",
            "input": {
                "query": "최시우 직원 정보",
                "search_type": "hr_only",
                "user_id": "test_user",
                "session_id": "test_session_001"
            }
        },
        {
            "name": "Rules Search",
            "input": {
                "query": "연차 사용 규정",
                "search_type": "rules_only",
                "user_id": "test_user",
                "session_id": "test_session_002"
            }
        },
        {
            "name": "Combined Search",
            "input": {
                "query": "김철수 인사 평가",
                "search_type": "both",
                "user_id": "test_user",
                "session_id": "test_session_003"
            }
        }
    ]

    for test in test_cases:
        print(f"\n[Test: {test['name']}]")
        print(f"Query: {test['input']['query']}")

        result = await agent.execute(test['input'])

        if result["status"] == "success":
            state = result.get("data", {})
            final_results = state.get("final_results", {})

            print(f"Status: {state.get('status')}")
            print(f"Results found: {final_results.get('total_results', 0)}")
            print(f"Sources: {final_results.get('sources', [])}")
        else:
            print(f"Error: {result.get('error')}")

    return True


async def test_sales_analytics_agent():
    """Test SalesAnalyticsAgent independently"""
    print("\n" + "="*60)
    print("Testing SalesAnalyticsAgent")
    print("="*60)

    agent = SalesAnalyticsAgent()

    # Test cases
    test_cases = [
        {
            "name": "Monthly Performance",
            "input": {
                "employee_name": "최시우",
                "period": "monthly",
                "user_id": "test_user",
                "session_id": "test_session_004"
            }
        },
        {
            "name": "Quarterly Report",
            "input": {
                "employee_name": "김철수",
                "period": "quarterly",
                "metrics_type": "detailed",
                "user_id": "test_user",
                "session_id": "test_session_005"
            }
        },
        {
            "name": "Yearly Analysis",
            "input": {
                "employee_name": "이영희",
                "period": "yearly",
                "user_id": "test_user",
                "session_id": "test_session_006"
            }
        }
    ]

    for test in test_cases:
        print(f"\n[Test: {test['name']}]")
        print(f"Employee: {test['input']['employee_name']}")
        print(f"Period: {test['input']['period']}")

        result = await agent.execute(test['input'])

        if result["status"] == "success":
            state = result.get("data", {})
            report = state.get("final_report", {})

            print(f"Status: {state.get('status')}")

            if "statistics" in report:
                stats = report["statistics"]
                print(f"Total Sales: {stats.get('total_sales', 0):,.0f}")
                print(f"Avg Sale: {stats.get('average_sale', 0):,.0f}")
                print(f"Transactions: {stats.get('transaction_count', 0)}")

            if "insights" in report:
                print(f"Insights: {len(report['insights'])} generated")
        else:
            print(f"Error: {result.get('error')}")

    return True


async def test_compliance_check_agent():
    """Test ComplianceCheckAgent independently"""
    print("\n" + "="*60)
    print("Testing ComplianceCheckAgent")
    print("="*60)

    agent = ComplianceCheckAgent()

    # Test cases
    test_cases = [
        {
            "name": "HR Compliance",
            "input": {
                "check_type": "hr",
                "check_target": "휴가 사용",
                "user_id": "test_user",
                "session_id": "test_session_007"
            }
        },
        {
            "name": "Financial Compliance",
            "input": {
                "check_type": "financial",
                "check_target": "경비 처리",
                "period": "2024Q1",
                "user_id": "test_user",
                "session_id": "test_session_008"
            }
        },
        {
            "name": "General Compliance",
            "input": {
                "check_type": "general",
                "check_target": "업무 프로세스",
                "user_id": "test_user",
                "session_id": "test_session_009"
            }
        }
    ]

    for test in test_cases:
        print(f"\n[Test: {test['name']}]")
        print(f"Check Type: {test['input']['check_type']}")
        print(f"Target: {test['input']['check_target']}")

        result = await agent.execute(test['input'])

        if result["status"] == "success":
            state = result.get("data", {})
            report = state.get("compliance_report", {})

            print(f"Status: {state.get('status')}")
            print(f"Risk Level: {state.get('risk_level')}")

            if "summary" in report:
                summary = report["summary"]
                print(f"Policies Checked: {summary.get('total_policies', 0)}")
                print(f"Violations: {summary.get('violations_found', 0)}")
                print(f"Compliance Rate: {summary.get('compliance_rate', 0)}%")

            if "recommendations" in report:
                print(f"Recommendations: {len(report['recommendations'])} generated")
        else:
            print(f"Error: {result.get('error')}")

    return True


async def test_document_generation_agent():
    """Test DocumentGenerationAgent independently"""
    print("\n" + "="*60)
    print("Testing DocumentGenerationAgent")
    print("="*60)

    agent = DocumentGenerationAgent()

    # Test cases with data from other agents
    test_cases = [
        {
            "name": "Sales Report Generation",
            "input": {
                "doc_type": "sales_report",
                "title": "2024년 1분기 실적 보고서",
                "data": {
                    "statistics": {
                        "total_sales": 150000000,
                        "average_sale": 1500000,
                        "transaction_count": 100
                    },
                    "insights": [
                        "전월 대비 15% 성장",
                        "신규 고객 20% 증가",
                        "평균 거래액 상승"
                    ],
                    "aggregated_data": {
                        "2024-01": {"amount": 45000000, "count": 30},
                        "2024-02": {"amount": 50000000, "count": 33},
                        "2024-03": {"amount": 55000000, "count": 37}
                    }
                },
                "user_id": "test_user",
                "session_id": "test_session_010"
            }
        },
        {
            "name": "Compliance Report",
            "input": {
                "doc_type": "compliance_report",
                "title": "HR 규정 준수 점검 보고서",
                "data": {
                    "violations": [
                        {"description": "초과근무 승인 절차 미준수"},
                        {"description": "휴가 신청 기한 초과"}
                    ],
                    "compliance_rate": 85.5
                },
                "user_id": "test_user",
                "session_id": "test_session_011"
            }
        },
        {
            "name": "Leave Request",
            "input": {
                "doc_type": "leave_request",
                "doc_format": "text",
                "data": {
                    "employee": "김철수",
                    "department": "영업팀",
                    "leave_type": "연차",
                    "start_date": "2024-04-01",
                    "end_date": "2024-04-05",
                    "reason": "개인 사유"
                },
                "user_id": "test_user",
                "session_id": "test_session_012"
            }
        }
    ]

    for test in test_cases:
        print(f"\n[Test: {test['name']}]")
        print(f"Document Type: {test['input']['doc_type']}")

        result = await agent.execute(test['input'])

        if result["status"] == "success":
            state = result.get("data", {})
            doc = state.get("final_document", {})

            print(f"Status: {state.get('status')}")
            print(f"Title: {doc.get('title')}")
            print(f"Format: {doc.get('format')}")
            print(f"Word Count: {doc.get('word_count', 0)}")
            print(f"Sections: {len(doc.get('sections', []))}")

            # Show first 200 characters of content
            content = doc.get("content", "")
            if content:
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"Content Preview:\n{preview}")
        else:
            print(f"Error: {result.get('error')}")

    return True


async def main():
    """Run all agent tests"""
    print("\n" + "="*70)
    print(" Individual Agent Testing (No LLM) ".center(70))
    print("="*70)
    print(f"Started at: {datetime.now().isoformat()}")

    results = []

    # Test each agent
    try:
        print("\n[1/4] Testing SearchAgent...")
        results.append(await test_search_agent())
    except Exception as e:
        print(f"SearchAgent test failed: {e}")
        results.append(False)

    try:
        print("\n[2/4] Testing SalesAnalyticsAgent...")
        results.append(await test_sales_analytics_agent())
    except Exception as e:
        print(f"SalesAnalyticsAgent test failed: {e}")
        results.append(False)

    try:
        print("\n[3/4] Testing ComplianceCheckAgent...")
        results.append(await test_compliance_check_agent())
    except Exception as e:
        print(f"ComplianceCheckAgent test failed: {e}")
        results.append(False)

    try:
        print("\n[4/4] Testing DocumentGenerationAgent...")
        results.append(await test_document_generation_agent())
    except Exception as e:
        print(f"DocumentGenerationAgent test failed: {e}")
        results.append(False)

    # Summary
    print("\n" + "="*70)
    print(" Test Summary ".center(70))
    print("="*70)

    agents = ["SearchAgent", "SalesAnalyticsAgent", "ComplianceCheckAgent", "DocumentGenerationAgent"]
    for i, (agent, result) in enumerate(zip(agents, results), 1):
        status = "PASS" if result else "FAIL"
        print(f"{i}. {agent}: {status}")

    if all(results):
        print("\n[SUCCESS] All agents tested successfully!")
    else:
        print("\n[WARNING] Some tests failed. Check the logs above.")

    print(f"\nCompleted at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())