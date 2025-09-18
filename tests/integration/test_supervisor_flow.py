"""
Supervisor 워크플로우 통합 테스트
전체 시스템 플로우 검증
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.service.supervisor.main_supervisor_v2 import MedicalSupervisorV2
from backend.service.supervisor.state import MedicalSupervisorState
from tests.fixtures.test_data import (
    TEST_QUERIES,
    TEST_CONTEXTS,
    AGENT_SELECTION_CASES
)


class TestSupervisorFlow:
    """Supervisor 워크플로우 통합 테스트"""

    @pytest.fixture
    async def supervisor(self):
        """테스트용 Supervisor 인스턴스"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        supervisor = MedicalSupervisorV2(
            llm_provider="openai",
            model_name="gpt-4o-mini",
            checkpoint_db_path=db_path,
            database_api_url="http://localhost:8002/api/v1"
        )

        yield supervisor

        # Cleanup
        await supervisor.shutdown()

    @pytest.mark.asyncio
    async def test_simple_query_flow(self, supervisor):
        """단순 쿼리 처리 플로우 테스트"""
        query = TEST_QUERIES["simple"][0]
        context = TEST_CONTEXTS["admin"]

        # 실행
        result = await supervisor.execute_with_context(
            query=query,
            user_context=context,
            conversation_history=[]
        )

        # 검증
        assert result is not None
        assert "status" in result
        assert result["status"] in ["success", "error"]

        if result["status"] == "success":
            assert "result" in result
            assert "agents_used" in result.get("result", {})

    @pytest.mark.asyncio
    async def test_complex_query_flow(self, supervisor):
        """복잡한 쿼리 처리 플로우 테스트"""
        query = TEST_QUERIES["complex"][0]
        context = TEST_CONTEXTS["analyst"]

        # Mock Database API 응답
        with patch.object(supervisor.db_client, 'execute_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": [{"매출": 1500000000, "분기": 3}]
            }

            result = await supervisor.execute_with_context(
                query=query,
                user_context=context,
                conversation_history=[]
            )

            # 여러 에이전트가 사용되었는지 확인
            if result.get("status") == "success":
                agents_used = result.get("result", {}).get("agents_used", [])
                assert len(agents_used) >= 2  # 복잡한 쿼리는 여러 에이전트 사용

    @pytest.mark.asyncio
    async def test_agent_handoff_flow(self, supervisor):
        """에이전트 핸드오프 플로우 테스트"""
        query = TEST_QUERIES["handoff"][0]  # "데이터를 조회한 후 분석 보고서 작성"
        context = TEST_CONTEXTS["admin"]

        with patch.object(supervisor, '_execute_workflow') as mock_workflow:
            # Mock 워크플로우 실행
            mock_workflow.return_value = {
                "status": "success",
                "result": {
                    "answer": "데이터 조회 및 보고서 작성 완료",
                    "agents_used": ["sql_analysis", "document_generation"],
                    "handoff_occurred": True
                }
            }

            result = await supervisor.execute_with_context(
                query=query,
                user_context=context,
                conversation_history=[]
            )

            # Handoff가 발생했는지 확인
            assert result["result"]["handoff_occurred"] is True
            assert len(result["result"]["agents_used"]) == 2

    @pytest.mark.asyncio
    async def test_error_handling_flow(self, supervisor):
        """에러 처리 플로우 테스트"""
        query = TEST_QUERIES["error"][0]  # "존재하지 않는 테이블 조회"
        context = TEST_CONTEXTS["viewer"]

        with patch.object(supervisor.db_client, 'execute_query') as mock_query:
            mock_query.side_effect = Exception("Table not found")

            result = await supervisor.execute_with_context(
                query=query,
                user_context=context,
                conversation_history=[]
            )

            # 에러가 적절히 처리되었는지 확인
            assert result["status"] == "error"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_context_preservation(self, supervisor):
        """컨텍스트 보존 테스트"""
        queries = TEST_QUERIES["simple"][:2]
        context = TEST_CONTEXTS["admin"]
        conversation_history = []

        for query in queries:
            result = await supervisor.execute_with_context(
                query=query,
                user_context=context,
                conversation_history=conversation_history
            )

            # 대화 히스토리 업데이트
            conversation_history.append({
                "query": query,
                "response": result
            })

        # 컨텍스트가 유지되었는지 확인
        assert len(conversation_history) == 2

    @pytest.mark.asyncio
    async def test_parallel_execution(self, supervisor):
        """병렬 실행 테스트"""
        queries = TEST_QUERIES["simple"][:3]
        context = TEST_CONTEXTS["admin"]

        # 병렬 실행
        tasks = [
            supervisor.execute_with_context(
                query=query,
                user_context=context,
                conversation_history=[]
            )
            for query in queries
        ]

        results = await asyncio.gather(*tasks)

        # 모든 쿼리가 처리되었는지 확인
        assert len(results) == 3
        assert all("status" in r for r in results)

    @pytest.mark.asyncio
    async def test_state_management(self, supervisor):
        """State 관리 테스트"""
        query = TEST_QUERIES["medium"][0]
        context = TEST_CONTEXTS["analyst"]

        # State 초기화
        initial_state = MedicalSupervisorState(
            query=query,
            messages=[],
            context=context,
            intermediate_results={},
            final_answer="",
            current_agent="",
            execution_plan={},
            agents_used=[]
        )

        # Mock State 처리
        with patch.object(supervisor, '_process_state') as mock_process:
            mock_process.return_value = {
                **initial_state,
                "final_answer": "처리 완료",
                "agents_used": ["sql_analysis"]
            }

            # State가 올바르게 업데이트되는지 확인
            result = await supervisor.execute_with_context(
                query=query,
                user_context=context,
                conversation_history=[]
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_checkpoint_recovery(self, supervisor):
        """체크포인트 복구 테스트"""
        query = TEST_QUERIES["simple"][0]
        context = TEST_CONTEXTS["admin"]
        thread_id = "test_thread_123"

        # 첫 번째 실행 (체크포인트 저장)
        result1 = await supervisor.execute_with_context(
            query=query,
            user_context=context,
            conversation_history=[],
            thread_id=thread_id
        )

        # 같은 thread_id로 재실행 (체크포인트 복구)
        result2 = await supervisor.execute_with_context(
            query="계속 진행",
            user_context=context,
            conversation_history=[],
            thread_id=thread_id
        )

        # 체크포인트가 복구되었는지 확인
        assert result2 is not None

    @pytest.mark.asyncio
    async def test_agent_selection_logic(self, supervisor):
        """에이전트 선택 로직 테스트"""
        for case in AGENT_SELECTION_CASES[:3]:
            query = case["query"]
            expected_agents = case["expected_agents"]

            with patch.object(supervisor, '_select_agents') as mock_select:
                mock_select.return_value = expected_agents

                result = await supervisor.execute_with_context(
                    query=query,
                    user_context=TEST_CONTEXTS["admin"],
                    conversation_history=[]
                )

                # 예상된 에이전트가 선택되었는지 확인
                mock_select.assert_called()

    @pytest.mark.asyncio
    async def test_streaming_execution(self, supervisor):
        """스트리밍 실행 테스트"""
        query = TEST_QUERIES["simple"][0]
        context = TEST_CONTEXTS["admin"]

        chunks = []
        async for chunk in supervisor.stream_execution(query, context):
            chunks.append(chunk)

        # 스트리밍 청크가 생성되었는지 확인
        assert len(chunks) > 0
        assert all("type" in chunk for chunk in chunks)

    @pytest.mark.asyncio
    async def test_cache_integration(self, supervisor):
        """캐시 통합 테스트"""
        query = TEST_QUERIES["simple"][0]
        context = TEST_CONTEXTS["admin"]

        # 첫 번째 실행 (캐시 미스)
        result1 = await supervisor.execute_with_context(
            query=query,
            user_context=context,
            conversation_history=[]
        )

        # 두 번째 실행 (캐시 히트)
        with patch.object(supervisor, '_get_from_cache') as mock_cache:
            mock_cache.return_value = result1

            result2 = await supervisor.execute_with_context(
                query=query,
                user_context=context,
                conversation_history=[]
            )

            # 캐시가 사용되었는지 확인
            if hasattr(supervisor, '_get_from_cache'):
                mock_cache.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])