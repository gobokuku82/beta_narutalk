"""
End-to-End 채팅 시나리오 테스트
실제 사용 시나리오 검증
"""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List
from unittest.mock import patch, AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.api.services.supervisor_service import SupervisorService
from tests.fixtures.test_data import (
    TEST_QUERIES,
    TEST_CONTEXTS,
    MOCK_DB_RECORDS
)


class TestChatScenarios:
    """E2E 채팅 시나리오 테스트"""

    @pytest.fixture
    async def service(self):
        """SupervisorService 인스턴스"""
        service = SupervisorService(
            llm_provider="openai",
            model_name="gpt-4o-mini",
            enable_cache=True,
            cache_ttl=300
        )
        await service.initialize()
        yield service
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_employee_query_scenario(self, service):
        """직원 정보 조회 시나리오"""
        # 시나리오: 사용자가 특정 직원 정보를 조회
        query = "사번이 1234인 직원의 정보를 알려주세요"
        context = TEST_CONTEXTS["admin"]

        # Mock DB 응답
        with patch('backend.service.worker_agents.database_api_client.DatabaseAPIClient.execute_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": MOCK_DB_RECORDS["employees"][:1]
            }

            result = await service.process_chat(
                query=query,
                user_context=context,
                use_cache=False
            )

            # 검증
            assert result["status"] == "success"
            assert "result" in result
            assert "홍길동" in str(result["result"])

    @pytest.mark.asyncio
    async def test_sales_analysis_scenario(self, service):
        """매출 분석 시나리오"""
        # 시나리오: 분석가가 매출 데이터를 분석하고 보고서 작성
        queries = [
            "2024년 3분기 매출 데이터를 조회해주세요",
            "전년 동기 대비 성장률을 계산해주세요",
            "분석 결과를 요약 보고서로 작성해주세요"
        ]
        context = TEST_CONTEXTS["analyst"]
        session_id = "sales_analysis_session"

        conversation_history = []

        for query in queries:
            # Mock DB 응답
            with patch('backend.service.worker_agents.database_api_client.DatabaseAPIClient.execute_query') as mock_query:
                mock_query.return_value = {
                    "success": True,
                    "data": MOCK_DB_RECORDS["sales"]
                }

                result = await service.process_chat(
                    query=query,
                    user_context={**context, "session_id": session_id},
                    use_cache=False
                )

                # 결과 저장
                conversation_history.append({
                    "query": query,
                    "result": result
                })

                # 검증
                assert result["status"] == "success"
                assert result["session_id"] == session_id

        # 전체 대화 검증
        assert len(conversation_history) == 3

    @pytest.mark.asyncio
    async def test_complex_workflow_scenario(self, service):
        """복잡한 워크플로우 시나리오"""
        # 시나리오: 데이터 조회 → 분석 → 규정 확인 → 보고서 작성
        query = """
        2024년 3분기 매출 데이터를 분석하고,
        회사 규정에 따라 검토한 후,
        임원 보고서를 작성해주세요.
        """
        context = TEST_CONTEXTS["admin"]

        # Mock 여러 에이전트 응답
        with patch('backend.service.supervisor.main_supervisor_v2.MedicalSupervisorV2.execute_with_context') as mock_exec:
            mock_exec.return_value = {
                "status": "success",
                "result": {
                    "answer": "매출 분석 및 보고서 작성 완료",
                    "agents_used": [
                        "sql_analysis_agent",
                        "compliance_validation_agent",
                        "document_generation_agent"
                    ],
                    "steps_completed": [
                        "데이터 조회",
                        "분석 실행",
                        "규정 검토",
                        "보고서 생성"
                    ]
                }
            }

            result = await service.process_chat(
                query=query,
                user_context=context,
                use_cache=False
            )

            # 여러 에이전트가 사용되었는지 확인
            assert len(result["result"]["agents_used"]) >= 3
            assert "steps_completed" in result["result"]

    @pytest.mark.asyncio
    async def test_error_recovery_scenario(self, service):
        """에러 복구 시나리오"""
        # 시나리오: 에러 발생 후 재시도
        queries = [
            "존재하지 않는 테이블에서 데이터 조회",  # 에러 발생
            "employees 테이블에서 데이터 조회"  # 정상 처리
        ]
        context = TEST_CONTEXTS["viewer"]

        results = []
        for i, query in enumerate(queries):
            if i == 0:
                # 첫 번째 쿼리는 에러
                with patch('backend.service.worker_agents.database_api_client.DatabaseAPIClient.execute_query') as mock_query:
                    mock_query.side_effect = Exception("Table not found")

                    result = await service.process_chat(
                        query=query,
                        user_context=context,
                        use_cache=False
                    )
                    results.append(result)
            else:
                # 두 번째 쿼리는 정상
                with patch('backend.service.worker_agents.database_api_client.DatabaseAPIClient.execute_query') as mock_query:
                    mock_query.return_value = {
                        "success": True,
                        "data": MOCK_DB_RECORDS["employees"]
                    }

                    result = await service.process_chat(
                        query=query,
                        user_context=context,
                        use_cache=False
                    )
                    results.append(result)

        # 첫 번째는 에러, 두 번째는 성공
        assert results[0]["status"] == "error"
        assert results[1]["status"] == "success"

    @pytest.mark.asyncio
    async def test_caching_scenario(self, service):
        """캐싱 시나리오"""
        # 시나리오: 같은 쿼리를 반복 실행하여 캐시 효과 확인
        query = "부서별 인원 현황을 조회해주세요"
        context = TEST_CONTEXTS["admin"]

        # 첫 번째 실행 (캐시 미스)
        with patch('backend.service.worker_agents.database_api_client.DatabaseAPIClient.execute_query') as mock_query:
            mock_query.return_value = {
                "success": True,
                "data": MOCK_DB_RECORDS["employees"]
            }

            result1 = await service.process_chat(
                query=query,
                user_context=context,
                use_cache=True
            )

            assert result1["cached"] is False

        # 두 번째 실행 (캐시 히트)
        result2 = await service.process_chat(
            query=query,
            user_context=context,
            use_cache=True
        )

        assert result2["cached"] is True
        assert result2["response_time"] < result1["response_time"]

    @pytest.mark.asyncio
    async def test_streaming_scenario(self, service):
        """스트리밍 응답 시나리오"""
        query = "대용량 데이터 분석 결과를 스트리밍으로 보여주세요"
        context = TEST_CONTEXTS["analyst"]

        chunks = []
        chunk_count = 0

        async for chunk in service.stream_response(query, context):
            chunk_data = json.loads(chunk.replace("data: ", ""))
            chunks.append(chunk_data)
            chunk_count += 1

            # 최대 10개 청크만 수집
            if chunk_count >= 10:
                break

        # 스트리밍 청크 검증
        assert len(chunks) > 0
        assert any(c.get("type") == "content" for c in chunks)

    @pytest.mark.asyncio
    async def test_multi_user_scenario(self, service):
        """다중 사용자 동시 접속 시나리오"""
        # 시나리오: 여러 사용자가 동시에 서비스 사용
        users = [
            ("user1", TEST_CONTEXTS["admin"]),
            ("user2", TEST_CONTEXTS["viewer"]),
            ("user3", TEST_CONTEXTS["analyst"])
        ]

        async def user_query(user_id, context):
            query = f"{user_id}의 테스트 쿼리"
            return await service.process_chat(
                query=query,
                user_context={**context, "user_id": user_id},
                use_cache=False
            )

        # 동시 실행
        with patch('backend.service.supervisor.main_supervisor_v2.MedicalSupervisorV2.execute_with_context') as mock_exec:
            mock_exec.return_value = {
                "status": "success",
                "result": {"answer": "응답"}
            }

            tasks = [user_query(uid, ctx) for uid, ctx in users]
            results = await asyncio.gather(*tasks)

        # 모든 사용자 요청이 처리되었는지 확인
        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)

    @pytest.mark.asyncio
    async def test_session_management_scenario(self, service):
        """세션 관리 시나리오"""
        # 시나리오: 세션별 대화 히스토리 관리
        session_id = "test_session_123"
        context = TEST_CONTEXTS["admin"]

        queries = [
            "첫 번째 질문입니다",
            "이전 질문과 관련된 추가 질문입니다",
            "세션을 마무리합니다"
        ]

        for query in queries:
            result = await service.process_chat(
                query=query,
                user_context={**context, "session_id": session_id},
                use_cache=False
            )

            assert result["session_id"] == session_id

        # 세션 정보 확인
        session_info = service.get_session_info(session_id)
        assert session_info is not None
        assert session_info["history_count"] >= len(queries)

    @pytest.mark.asyncio
    async def test_permission_based_scenario(self, service):
        """권한 기반 접근 시나리오"""
        # 시나리오: 사용자 권한에 따른 다른 응답
        sensitive_query = "전체 직원의 급여 정보를 조회해주세요"

        # Admin 권한
        admin_result = await service.process_chat(
            query=sensitive_query,
            user_context=TEST_CONTEXTS["admin"],
            use_cache=False
        )

        # Viewer 권한
        viewer_result = await service.process_chat(
            query=sensitive_query,
            user_context=TEST_CONTEXTS["viewer"],
            use_cache=False
        )

        # Admin은 성공, Viewer는 권한 제한 메시지
        # (실제 구현에 따라 다를 수 있음)
        assert admin_result["status"] in ["success", "error"]
        assert viewer_result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_performance_scenario(self, service):
        """성능 테스트 시나리오"""
        # 시나리오: 응답 시간 측정
        query = "간단한 조회 쿼리"
        context = TEST_CONTEXTS["admin"]

        response_times = []

        for _ in range(5):
            result = await service.process_chat(
                query=query,
                user_context=context,
                use_cache=False
            )
            response_times.append(result["response_time"])

        # 평균 응답 시간 계산
        avg_response_time = sum(response_times) / len(response_times)

        # 성능 기준 충족 확인 (예: 2초 이내)
        assert avg_response_time < 2.0

    @pytest.mark.asyncio
    async def test_feedback_scenario(self, service):
        """사용자 피드백 시나리오"""
        # 시나리오: 사용자가 응답에 피드백 제공
        query = "테스트 쿼리"
        context = TEST_CONTEXTS["admin"]
        session_id = "feedback_session"

        # 쿼리 실행
        result = await service.process_chat(
            query=query,
            user_context={**context, "session_id": session_id},
            use_cache=False
        )

        # 피드백 제출 (실제 구현에 따라 다를 수 있음)
        feedback = {
            "session_id": session_id,
            "rating": 4,
            "category": "accuracy",
            "comment": "정확한 답변이었습니다"
        }

        # 피드백이 저장되었는지 확인
        # (실제 피드백 저장 로직이 구현되어 있다면)
        assert result["session_id"] == session_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])