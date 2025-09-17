"""
Supervisor Service Layer
FastAPI와 LangGraph Supervisor를 통합하는 서비스 레이어
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import json
import hashlib

from backend.service.supervisor.main_supervisor_v2 import MedicalSupervisorV2, create_medical_supervisor_v2
from backend.api.services.cache_manager import SQLiteMemoryCache, get_cache

logger = logging.getLogger(__name__)


class SupervisorService:
    """
    Supervisor 통합 서비스
    - FastAPI와 Supervisor 연결
    - 캐싱 관리
    - 세션 관리
    - 에러 처리
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: Optional[str] = None,
        checkpoint_path: str = "database/checkpointer/checkpoint.db",
        enable_cache: bool = True,
        cache_ttl: int = 300
    ):
        """
        Initialize Supervisor Service

        Args:
            llm_provider: LLM 제공자 (openai, anthropic)
            model_name: 모델명
            checkpoint_path: 체크포인트 저장 경로
            enable_cache: 캐시 활성화 여부
            cache_ttl: 캐시 TTL (초)
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.checkpoint_path = checkpoint_path
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl

        # Supervisor 인스턴스
        self.supervisor = None
        self.supervisor_lock = asyncio.Lock()

        # 캐시 매니저
        self.cache = get_cache() if enable_cache else None

        # 세션 관리
        self.active_sessions = {}
        self.session_timeout = 3600  # 1시간

        # 요청 로그
        self.request_history = []
        self.max_history = 100

        # 통계
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "average_response_time": 0
        }

    async def initialize(self):
        """서비스 초기화"""
        # 체크포인트 디렉토리 생성
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)

        # Supervisor 초기화
        await self._get_or_create_supervisor()

        logger.info("SupervisorService initialized")

    async def _get_or_create_supervisor(self) -> MedicalSupervisorV2:
        """Supervisor 인스턴스 가져오기 또는 생성"""
        async with self.supervisor_lock:
            if self.supervisor is None:
                self.supervisor = await create_medical_supervisor_v2(
                    llm_provider=self.llm_provider,
                    model_name=self.model_name,
                    checkpoint_db_path=self.checkpoint_path,
                    database_api_url="http://localhost:8000/api/v1"
                )
            return self.supervisor

    def _generate_cache_key(self, query: str, user_context: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        # 쿼리와 주요 컨텍스트로 키 생성
        key_data = {
            "query": query,
            "user_id": user_context.get("user_id"),
            "role": user_context.get("role"),
            "department": user_context.get("department")
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"chat:{hashlib.md5(key_str.encode()).hexdigest()}"

    async def process_chat(
        self,
        query: str,
        user_context: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        대화 요청 처리

        Args:
            query: 사용자 질의
            user_context: 사용자 컨텍스트
            use_cache: 캐시 사용 여부

        Returns:
            처리 결과
        """
        start_time = datetime.now()
        self.stats["total_requests"] += 1

        # 세션 관리
        session_id = user_context.get("session_id", "default")
        self._update_session(session_id, user_context)

        try:
            # 캐시 확인
            if use_cache and self.cache and self.enable_cache:
                cache_key = self._generate_cache_key(query, user_context)
                cached_result = await self.cache.get(cache_key)

                if cached_result:
                    self.stats["cache_hits"] += 1
                    logger.info(f"Cache hit for query: {query[:50]}...")

                    return {
                        "status": "success",
                        "result": cached_result,
                        "cached": True,
                        "session_id": session_id,
                        "response_time": 0.001  # 캐시는 매우 빠름
                    }

            # Supervisor 실행
            supervisor = await self._get_or_create_supervisor()

            # 대화 히스토리 가져오기
            conversation_history = self._get_conversation_history(session_id)

            # Supervisor 실행
            result = await supervisor.execute_with_context(
                query=query,
                user_context=user_context,
                conversation_history=conversation_history
            )

            # 성공 처리
            if result.get("status") == "success":
                self.stats["successful_requests"] += 1

                # 캐시 저장
                if use_cache and self.cache and self.enable_cache:
                    await self.cache.set(
                        cache_key,
                        result.get("result"),
                        ttl=self.cache_ttl
                    )

                # 히스토리 업데이트
                self._add_to_history(session_id, query, result.get("result"))

                # 응답 시간 계산
                response_time = (datetime.now() - start_time).total_seconds()
                self._update_stats(response_time)

                return {
                    "status": "success",
                    "result": result.get("result"),
                    "context": result.get("context"),
                    "cached": False,
                    "session_id": session_id,
                    "response_time": response_time
                }
            else:
                # 에러 처리
                self.stats["failed_requests"] += 1
                error_message = result.get("error", "Unknown error")
                logger.error(f"Supervisor execution failed: {error_message}")

                return {
                    "status": "error",
                    "error": error_message,
                    "session_id": session_id,
                    "response_time": (datetime.now() - start_time).total_seconds()
                }

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Chat processing failed: {e}", exc_info=True)

            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id,
                "response_time": (datetime.now() - start_time).total_seconds()
            }

    async def stream_response(
        self,
        query: str,
        user_context: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        스트리밍 응답 생성

        Args:
            query: 사용자 질의
            user_context: 사용자 컨텍스트

        Yields:
            SSE 형식의 스트림 데이터
        """
        session_id = user_context.get("session_id", "default")
        self._update_session(session_id, user_context)

        try:
            supervisor = await self._get_or_create_supervisor()

            # 스트리밍 실행
            async for chunk in supervisor.stream_execution(query, user_context):
                # SSE 형식으로 변환
                if chunk["type"] == "stream":
                    data = {
                        "type": "content",
                        "data": chunk["data"],
                        "timestamp": chunk["timestamp"]
                    }
                    yield f"data: {json.dumps(data)}\n\n"

                elif chunk["type"] == "error":
                    data = {
                        "type": "error",
                        "error": chunk["error"],
                        "timestamp": chunk["timestamp"]
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    break

            # 완료 신호
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_data = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    def _update_session(self, session_id: str, user_context: Dict[str, Any]):
        """세션 정보 업데이트"""
        self.active_sessions[session_id] = {
            "user_context": user_context,
            "last_activity": datetime.now(),
            "history": self.active_sessions.get(session_id, {}).get("history", [])
        }

        # 오래된 세션 정리
        self._cleanup_sessions()

    def _cleanup_sessions(self):
        """비활성 세션 정리"""
        current_time = datetime.now()
        expired = []

        for session_id, session_data in self.active_sessions.items():
            last_activity = session_data["last_activity"]
            if (current_time - last_activity).total_seconds() > self.session_timeout:
                expired.append(session_id)

        for session_id in expired:
            del self.active_sessions[session_id]
            logger.info(f"Session {session_id} expired and removed")

    def _get_conversation_history(self, session_id: str) -> List[Dict]:
        """대화 히스토리 조회"""
        session = self.active_sessions.get(session_id, {})
        return session.get("history", [])

    def _add_to_history(self, session_id: str, query: str, response: Any):
        """대화 히스토리에 추가"""
        if session_id in self.active_sessions:
            history_entry = {
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            self.active_sessions[session_id]["history"].append(history_entry)

            # 히스토리 크기 제한 (최근 20개)
            if len(self.active_sessions[session_id]["history"]) > 20:
                self.active_sessions[session_id]["history"] = \
                    self.active_sessions[session_id]["history"][-20:]

    def _update_stats(self, response_time: float):
        """통계 업데이트"""
        # 평균 응답 시간 계산 (이동 평균)
        current_avg = self.stats["average_response_time"]
        total_requests = self.stats["successful_requests"]

        if total_requests > 0:
            self.stats["average_response_time"] = \
                (current_avg * (total_requests - 1) + response_time) / total_requests
        else:
            self.stats["average_response_time"] = response_time

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 조회"""
        session = self.active_sessions.get(session_id)
        if session:
            return {
                "session_id": session_id,
                "user_context": session["user_context"],
                "last_activity": session["last_activity"].isoformat(),
                "history_count": len(session["history"])
            }
        return None

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """활성 세션 목록 조회"""
        sessions = []
        for session_id, session_data in self.active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "user_id": session_data["user_context"].get("user_id"),
                "last_activity": session_data["last_activity"].isoformat(),
                "history_count": len(session_data["history"])
            })
        return sessions

    def get_statistics(self) -> Dict[str, Any]:
        """서비스 통계 조회"""
        cache_stats = {}
        if self.cache:
            cache_stats = self.cache.get_stats()

        return {
            "service_stats": self.stats,
            "cache_stats": cache_stats,
            "active_sessions": len(self.active_sessions),
            "checkpoint_path": self.checkpoint_path
        }

    async def clear_cache(self):
        """캐시 초기화"""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")

    async def invalidate_cache(self, pattern: str):
        """패턴별 캐시 무효화"""
        if self.cache:
            count = await self.cache.invalidate(pattern)
            logger.info(f"Invalidated {count} cache entries with pattern: {pattern}")
            return count
        return 0

    async def shutdown(self):
        """서비스 종료"""
        logger.info("Shutting down SupervisorService...")

        # Supervisor 종료
        if self.supervisor:
            await self.supervisor.shutdown()

        # 캐시 종료
        if self.cache:
            self.cache.close()

        logger.info("SupervisorService shutdown complete")


# 싱글톤 인스턴스
_service_instance = None


async def get_supervisor_service() -> SupervisorService:
    """Supervisor Service 인스턴스 반환 (싱글톤)"""
    global _service_instance
    if _service_instance is None:
        _service_instance = SupervisorService()
        await _service_instance.initialize()
    return _service_instance