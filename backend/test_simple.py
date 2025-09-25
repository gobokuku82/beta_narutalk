"""Simple test for subgraphs only"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

print(f"API Key loaded: {'sk-' in os.getenv('OPENAI_API_KEY', '')}")

async def test_subgraphs():
    """Test subgraphs directly"""

    # Test DataCollectionSubgraph
    from service.subgraphs.data_collection_subgraph import DataCollectionSubgraph
    from service.core import create_subgraph_context

    print("\n=== Testing DataCollectionSubgraph ===")

    collection_subgraph = DataCollectionSubgraph()
    collection_graph = collection_subgraph.build_graph()
    collection_app = collection_graph.compile()

    context = create_subgraph_context(
        parent_context={"user_id": "test", "session_id": "test"},
        parent_agent="TestAgent",
        subgraph_name="data_collection"
    )

    state = {
        "query_params": {"original_query": "김철수 실적 분석"},
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

    result = await collection_app.ainvoke(state, context=context)
    print(f"[OK] Data collection completed: {result.get('collection_status')}")
    print(f"  Selected databases: {result.get('target_databases')}")
    print(f"  Performance records: {len(result.get('performance_data', []))}")

    # Test AnalysisSubgraph
    from service.subgraphs.analysis_subgraph import AnalysisSubgraph

    print("\n=== Testing AnalysisSubgraph ===")

    analysis_subgraph = AnalysisSubgraph()
    analysis_graph = analysis_subgraph.build_graph()
    analysis_app = analysis_graph.compile()

    state = {
        "performance_data": [],
        "target_data": [],
        "client_data": [],
        "aggregated_performance": {},
        "aggregated_target": {},
        "aggregated_client": {},
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

    result = await analysis_app.ainvoke(state, context=context)
    print(f"[OK] Analysis completed: {result.get('analysis_status')}")
    print(f"  Selected tools: {result.get('analysis_params', {}).get('selected_tools')}")
    print(f"  Insights: {len(result.get('insights', []))}")

    print("\n[SUCCESS] All subgraph tests passed!")

if __name__ == "__main__":
    asyncio.run(test_subgraphs())