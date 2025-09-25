"""
Test script for the complete Sales Analytics Agent pipeline
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(Path(__file__).parent.parent / '.env')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verify API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key == "your-api-key-here":
    logger.error("Valid OpenAI API key not found in environment")
else:
    logger.info("OpenAI API key loaded successfully")


async def test_sales_agent():
    """Test the Sales Analytics Agent with subgraphs"""
    try:
        from service.agents.sales_analytics_agent import SalesAnalyticsAgent

        # Create agent
        agent = SalesAnalyticsAgent()
        logger.info("SalesAnalyticsAgent created successfully")

        # Test queries
        test_queries = [
            {
                "query": "김철수의 2024년 1월 판매 실적을 분석해줘",
                "employee_name": "김철수",
                "period": "202401"
            },
            {
                "query": "2024년 전체 판매 목표 대비 달성률을 계산해줘",
                "period": "2024"
            },
            {
                "query": "모든 직원의 실적을 비교 분석해줘",
                "analysis_type": "comparative"
            }
        ]

        for i, test_case in enumerate(test_queries, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Test Case {i}: {test_case['query']}")
            logger.info(f"{'='*60}")

            # Run agent
            result = await agent.run(
                query=test_case["query"],
                user_id="test_user",
                session_id=f"test_session_{i}",
                **{k: v for k, v in test_case.items() if k != "query"}
            )

            # Check results
            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Execution Step: {result.get('execution_step')}")

            # Check if subgraphs were executed
            if result.get("execution_results"):
                exec_results = result["execution_results"]
                if "collection" in exec_results:
                    logger.info("✓ Data Collection Subgraph executed")
                    collection = exec_results["collection"]
                    if collection.get("status") == "completed":
                        data = collection.get("data_collection_result", {})
                        logger.info(f"  - Performance data: {len(data.get('performance_data', []))} records")
                        logger.info(f"  - Target data: {len(data.get('target_data', []))} records")
                        logger.info(f"  - Client data: {len(data.get('client_data', []))} records")

                if "analysis" in exec_results:
                    logger.info("✓ Analysis Subgraph executed")
                    analysis = exec_results["analysis"]
                    if analysis.get("status") == "completed":
                        data = analysis.get("analysis_result", {})
                        logger.info(f"  - Basic metrics: {len(data.get('basic_metrics', {}))} metrics")
                        logger.info(f"  - Insights: {len(data.get('insights', []))} insights")

                        # Print insights
                        for insight in data.get("insights", [])[:3]:
                            logger.info(f"    • {insight}")

            # Check formatted result
            if result.get("formatted_result"):
                logger.info("\nFormatted Result:")
                logger.info(result["formatted_result"][:500])  # First 500 chars

            # Check errors
            if result.get("errors"):
                logger.error(f"Errors: {result['errors']}")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


async def test_subgraphs_directly():
    """Test subgraphs directly without the agent"""
    try:
        logger.info("\n" + "="*60)
        logger.info("Testing Subgraphs Directly")
        logger.info("="*60)

        # Test DataCollectionSubgraph
        from service.subgraphs.data_collection_subgraph import DataCollectionSubgraph
        from service.core import create_subgraph_context

        logger.info("\n1. Testing DataCollectionSubgraph...")

        # Create subgraph
        collection_subgraph = DataCollectionSubgraph()
        collection_graph = collection_subgraph.build_graph()
        collection_app = collection_graph.compile()

        # Create context
        context = create_subgraph_context(
            parent_context={"user_id": "test", "session_id": "test"},
            parent_agent="TestAgent",
            subgraph_name="data_collection"
        )

        # Create initial state
        collection_state = {
            "query_params": {
                "original_query": "김철수 실적",
                "person_name": "김철수"
            },
            "target_databases": [],
            "performance_data": [],
            "target_data": [],
            "client_data": [],
            "aggregated_performance": {},
            "aggregated_target": {},
            "aggregated_client": {},
            "collection_status": "pending",
            "errors": []
        }

        # Run subgraph
        collection_result = await collection_app.ainvoke(collection_state, context=context)
        logger.info(f"Collection Status: {collection_result.get('collection_status')}")
        logger.info(f"Selected databases: {collection_result.get('target_databases')}")

        # Test AnalysisSubgraph
        from service.subgraphs.analysis_subgraph import AnalysisSubgraph

        logger.info("\n2. Testing AnalysisSubgraph...")

        # Create subgraph
        analysis_subgraph = AnalysisSubgraph()
        analysis_graph = analysis_subgraph.build_graph()
        analysis_app = analysis_graph.compile()

        # Create initial state with collected data
        analysis_state = {
            "performance_data": collection_result.get("performance_data", []),
            "target_data": collection_result.get("target_data", []),
            "client_data": collection_result.get("client_data", []),
            "aggregated_performance": collection_result.get("aggregated_performance", {}),
            "aggregated_target": collection_result.get("aggregated_target", {}),
            "aggregated_client": collection_result.get("aggregated_client", {}),
            "analysis_type": "comprehensive",
            "analysis_params": {},
            "basic_metrics": {},
            "trend_analysis": {},
            "comparative_analysis": {},
            "insights": [],
            "analysis_report": {},
            "analysis_status": "pending",
            "errors": []
        }

        # Run subgraph
        analysis_result = await analysis_app.ainvoke(analysis_state, context=context)
        logger.info(f"Analysis Status: {analysis_result.get('analysis_status')}")
        logger.info(f"Selected tools: {analysis_result.get('analysis_params', {}).get('selected_tools')}")
        logger.info(f"Insights generated: {len(analysis_result.get('insights', []))}")

    except Exception as e:
        logger.error(f"Subgraph test failed: {e}", exc_info=True)


async def main():
    """Main test function"""
    logger.info("Starting Sales Analytics Agent Pipeline Test")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")

    # Test subgraphs directly first
    await test_subgraphs_directly()

    # Then test the complete agent
    await test_sales_agent()

    logger.info("\nAll tests completed!")


if __name__ == "__main__":
    asyncio.run(main())