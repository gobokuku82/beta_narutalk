"""
Dynamic Agent Loader for LangGraph 0.6.x
동적 에이전트 로딩 시스템 - 메모리 최적화 및 지연 로딩
"""

import importlib
import inspect
import asyncio
from typing import Dict, Type, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
import sys

logger = logging.getLogger(__name__)

# 프로젝트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))


@dataclass
class AgentMetadata:
    """에이전트 메타데이터"""
    name: str
    module_path: str
    class_name: str
    description: str
    required_tools: List[str]
    dependencies: List[str]
    memory_estimate: int  # 예상 메모리 사용량 (MB)
    load_priority: int  # 로드 우선순위 (낮을수록 우선)
    is_loaded: bool = False
    last_used: Optional[datetime] = None
    usage_count: int = 0
    average_execution_time: float = 0.0


class DynamicAgentLoader:
    """
    동적 에이전트 로더
    - 필요시에만 에이전트 로드 (Lazy Loading)
    - 메모리 효율적 관리
    - 자동 언로드 지원
    """

    def __init__(
        self,
        max_loaded_agents: int = 10,
        memory_limit_mb: int = 500,
        auto_unload: bool = True,
        unload_after_seconds: int = 300  # 5분
    ):
        """
        Initialize DynamicAgentLoader

        Args:
            max_loaded_agents: 동시 로드 가능한 최대 에이전트 수
            memory_limit_mb: 메모리 제한 (MB)
            auto_unload: 자동 언로드 활성화
            unload_after_seconds: 미사용 시 언로드까지 대기 시간
        """
        self.max_loaded_agents = max_loaded_agents
        self.memory_limit_mb = memory_limit_mb
        self.auto_unload = auto_unload
        self.unload_after_seconds = unload_after_seconds

        # 에이전트 레지스트리
        self.agent_registry: Dict[str, AgentMetadata] = {}
        self.loaded_agents: Dict[str, Any] = {}

        # 에이전트 모듈 매핑
        self.agent_modules = {
            "sql_analysis": AgentMetadata(
                name="sql_analysis",
                module_path="backend.service.worker_agents.sql_analysis_agent",
                class_name="SQLAnalysisAgent",
                description="SQL 분석 및 쿼리 생성 에이전트",
                required_tools=["generate_sql", "execute_query"],
                dependencies=["pandas", "numpy"],
                memory_estimate=50,
                load_priority=1
            ),
            "information_retrieval": AgentMetadata(
                name="information_retrieval",
                module_path="backend.service.worker_agents.information_retrieval_agent",
                class_name="InformationRetrievalAgent",
                description="정보 검색 에이전트",
                required_tools=["search_hr", "search_vector"],
                dependencies=["chromadb", "faiss"],
                memory_estimate=100,
                load_priority=2
            ),
            "document_generation": AgentMetadata(
                name="document_generation",
                module_path="backend.service.worker_agents.document_generation_agent",
                class_name="DocumentGenerationAgent",
                description="문서 생성 에이전트",
                required_tools=["generate_template", "export_document"],
                dependencies=["jinja2", "reportlab"],
                memory_estimate=30,
                load_priority=3
            ),
            "compliance_validation": AgentMetadata(
                name="compliance_validation",
                module_path="backend.service.worker_agents.compliance_validation_agent",
                class_name="ComplianceValidationAgent",
                description="규정 준수 검증 에이전트",
                required_tools=["check_compliance", "search_regulation"],
                dependencies=["chromadb"],
                memory_estimate=40,
                load_priority=4
            )
        }

        # 레지스트리 초기화
        for agent_type, metadata in self.agent_modules.items():
            self.agent_registry[agent_type] = metadata

        # 통계
        self.stats = {
            "total_loads": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "auto_unloads": 0,
            "current_memory_usage": 0
        }

        # 자동 언로드 태스크
        self._unload_task = None
        if auto_unload:
            self._start_auto_unload_task()

        logger.info(f"DynamicAgentLoader initialized with {len(self.agent_registry)} agents registered")

    def _start_auto_unload_task(self):
        """자동 언로드 백그라운드 태스크 시작"""
        async def auto_unload_loop():
            while True:
                try:
                    await asyncio.sleep(60)  # 1분마다 체크
                    await self._check_and_unload_unused_agents()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in auto unload loop: {e}")

        self._unload_task = asyncio.create_task(auto_unload_loop())

    async def _check_and_unload_unused_agents(self):
        """미사용 에이전트 체크 및 언로드"""
        now = datetime.now()
        agents_to_unload = []

        for agent_type, metadata in self.agent_registry.items():
            if metadata.is_loaded and metadata.last_used:
                time_since_use = (now - metadata.last_used).total_seconds()
                if time_since_use > self.unload_after_seconds:
                    agents_to_unload.append(agent_type)

        for agent_type in agents_to_unload:
            await self.unload_agent(agent_type)
            self.stats["auto_unloads"] += 1
            logger.info(f"Auto-unloaded agent: {agent_type}")

    async def get_agent(
        self,
        agent_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        에이전트 가져오기 (필요시 로드)

        Args:
            agent_type: 에이전트 타입
            config: 에이전트 설정

        Returns:
            에이전트 인스턴스
        """
        self.stats["total_loads"] += 1

        # 이미 로드된 경우
        if agent_type in self.loaded_agents:
            self.stats["cache_hits"] += 1
            metadata = self.agent_registry[agent_type]
            metadata.last_used = datetime.now()
            metadata.usage_count += 1
            logger.debug(f"Agent cache hit: {agent_type}")
            return self.loaded_agents[agent_type]

        # 새로 로드
        self.stats["cache_misses"] += 1
        agent = await self._load_agent(agent_type, config)
        return agent

    async def _load_agent(
        self,
        agent_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        에이전트 동적 로드

        Args:
            agent_type: 에이전트 타입
            config: 에이전트 설정

        Returns:
            로드된 에이전트 인스턴스
        """
        if agent_type not in self.agent_registry:
            raise ValueError(f"Unknown agent type: {agent_type}")

        metadata = self.agent_registry[agent_type]

        # 메모리 체크
        if await self._check_memory_limit(metadata.memory_estimate):
            # 메모리 부족시 우선순위가 낮은 에이전트 언로드
            await self._make_room_for_agent(metadata.memory_estimate)

        try:
            # 모듈 임포트
            logger.info(f"Loading agent module: {metadata.module_path}")
            module = importlib.import_module(metadata.module_path)

            # 클래스 찾기
            agent_class = None
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and name == metadata.class_name:
                    agent_class = obj
                    break

            if not agent_class:
                raise ImportError(f"Class {metadata.class_name} not found in {metadata.module_path}")

            # 인스턴스 생성
            agent_config = config or {}
            agent = agent_class(**agent_config)

            # 캐시에 저장
            self.loaded_agents[agent_type] = agent

            # 메타데이터 업데이트
            metadata.is_loaded = True
            metadata.last_used = datetime.now()
            metadata.usage_count = 1
            self.stats["current_memory_usage"] += metadata.memory_estimate

            logger.info(f"Successfully loaded agent: {agent_type}")
            return agent

        except Exception as e:
            logger.error(f"Failed to load agent {agent_type}: {e}")
            raise

    async def _check_memory_limit(self, required_memory: int) -> bool:
        """
        메모리 제한 체크

        Args:
            required_memory: 필요한 메모리 (MB)

        Returns:
            메모리 부족 여부
        """
        return (self.stats["current_memory_usage"] + required_memory) > self.memory_limit_mb

    async def _make_room_for_agent(self, required_memory: int):
        """
        새 에이전트를 위한 공간 확보

        Args:
            required_memory: 필요한 메모리 (MB)
        """
        # 우선순위와 사용 빈도를 고려한 언로드 대상 선택
        loaded_agents = [
            (agent_type, metadata)
            for agent_type, metadata in self.agent_registry.items()
            if metadata.is_loaded
        ]

        # 정렬: 우선순위 높음(숫자 큼) + 사용 빈도 낮음
        loaded_agents.sort(
            key=lambda x: (x[1].load_priority, -x[1].usage_count)
        )

        freed_memory = 0
        for agent_type, metadata in loaded_agents:
            if freed_memory >= required_memory:
                break

            await self.unload_agent(agent_type)
            freed_memory += metadata.memory_estimate

    async def unload_agent(self, agent_type: str):
        """
        에이전트 언로드

        Args:
            agent_type: 에이전트 타입
        """
        if agent_type in self.loaded_agents:
            # 정리 메서드 호출 (있는 경우)
            agent = self.loaded_agents[agent_type]
            if hasattr(agent, 'cleanup'):
                try:
                    if asyncio.iscoroutinefunction(agent.cleanup):
                        await agent.cleanup()
                    else:
                        agent.cleanup()
                except Exception as e:
                    logger.error(f"Error during agent cleanup: {e}")

            # 메모리에서 제거
            del self.loaded_agents[agent_type]

            # 메타데이터 업데이트
            metadata = self.agent_registry[agent_type]
            metadata.is_loaded = False
            self.stats["current_memory_usage"] -= metadata.memory_estimate

            logger.info(f"Unloaded agent: {agent_type}")

    async def preload_agents(self, agent_types: List[str]):
        """
        에이전트 사전 로드

        Args:
            agent_types: 사전 로드할 에이전트 타입 목록
        """
        for agent_type in agent_types:
            try:
                await self.get_agent(agent_type)
                logger.info(f"Preloaded agent: {agent_type}")
            except Exception as e:
                logger.error(f"Failed to preload agent {agent_type}: {e}")

    def get_loaded_agents(self) -> List[str]:
        """현재 로드된 에이전트 목록 반환"""
        return list(self.loaded_agents.keys())

    def get_agent_stats(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        에이전트 통계 반환

        Args:
            agent_type: 에이전트 타입

        Returns:
            에이전트 통계 정보
        """
        if agent_type not in self.agent_registry:
            return None

        metadata = self.agent_registry[agent_type]
        return {
            "name": metadata.name,
            "is_loaded": metadata.is_loaded,
            "usage_count": metadata.usage_count,
            "last_used": metadata.last_used.isoformat() if metadata.last_used else None,
            "memory_estimate": metadata.memory_estimate,
            "average_execution_time": metadata.average_execution_time
        }

    def get_loader_stats(self) -> Dict[str, Any]:
        """로더 전체 통계 반환"""
        return {
            **self.stats,
            "loaded_agents_count": len(self.loaded_agents),
            "cache_hit_rate": (
                self.stats["cache_hits"] / self.stats["total_loads"] * 100
                if self.stats["total_loads"] > 0 else 0
            ),
            "memory_usage_percentage": (
                self.stats["current_memory_usage"] / self.memory_limit_mb * 100
            )
        }

    def update_agent_execution_time(
        self,
        agent_type: str,
        execution_time: float
    ):
        """
        에이전트 실행 시간 업데이트

        Args:
            agent_type: 에이전트 타입
            execution_time: 실행 시간 (초)
        """
        if agent_type in self.agent_registry:
            metadata = self.agent_registry[agent_type]
            # 이동 평균 계산
            n = metadata.usage_count
            metadata.average_execution_time = (
                (metadata.average_execution_time * (n - 1) + execution_time) / n
                if n > 0 else execution_time
            )

    async def optimize_loading_strategy(self) -> Dict[str, Any]:
        """
        로딩 전략 최적화
        - 사용 패턴 분석
        - 권장 사전 로드 목록 제공
        """
        # 사용 빈도 기준 정렬
        frequently_used = sorted(
            self.agent_registry.items(),
            key=lambda x: x[1].usage_count,
            reverse=True
        )

        # 권장 사항 생성
        recommendations = {
            "preload_candidates": [],
            "unload_candidates": [],
            "memory_optimization": []
        }

        # 자주 사용되는 에이전트는 사전 로드 권장
        for agent_type, metadata in frequently_used[:3]:
            if not metadata.is_loaded and metadata.usage_count > 5:
                recommendations["preload_candidates"].append({
                    "agent": agent_type,
                    "usage_count": metadata.usage_count,
                    "average_time": metadata.average_execution_time
                })

        # 거의 사용되지 않는 로드된 에이전트는 언로드 권장
        for agent_type, metadata in self.agent_registry.items():
            if metadata.is_loaded and metadata.usage_count < 2:
                recommendations["unload_candidates"].append(agent_type)

        # 메모리 최적화 제안
        if self.stats["current_memory_usage"] > self.memory_limit_mb * 0.8:
            recommendations["memory_optimization"].append(
                "Consider increasing memory limit or unloading unused agents"
            )

        return recommendations

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        # 모든 에이전트 언로드
        for agent_type in list(self.loaded_agents.keys()):
            await self.unload_agent(agent_type)

        # 자동 언로드 태스크 취소
        if self._unload_task:
            self._unload_task.cancel()
            try:
                await self._unload_task
            except asyncio.CancelledError:
                pass


# 전역 로더 인스턴스
_global_loader: Optional[DynamicAgentLoader] = None


def get_agent_loader() -> DynamicAgentLoader:
    """전역 에이전트 로더 인스턴스 반환"""
    global _global_loader
    if _global_loader is None:
        _global_loader = DynamicAgentLoader()
    return _global_loader