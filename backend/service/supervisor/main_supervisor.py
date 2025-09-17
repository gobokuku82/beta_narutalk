"""
Medical Domain Supervisor with langgraph-supervisor library
의료/제약 도메인 특화 Supervisor 구현
"""

from typing import Dict, Any, List, Optional, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command
from langgraph_supervisor import (
    create_supervisor,
    create_handoff_tool,
    create_forward_message_tool
)
from langgraph.prebuilt import create_react_agent, ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.memory import InMemoryStore  # Store는 아직 메모리 사용 가능
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import Tool
import logging
import asyncio
from datetime import datetime

from .context_manager import ContextManager, MedicalContext
from .state import MedicalSupervisorState

logger = logging.getLogger(__name__)


class MedicalSupervisor:
    """
    의료/제약 도메인 특화 Supervisor
    langgraph-supervisor 라이브러리 활용
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: Optional[str] = None,
        checkpoint_db_path: str = "data/checkpoints.db",
        store_db_path: Optional[str] = None  # SQLite Store 경로 (향후 구현)
    ):
        """
        Initialize Medical Supervisor

        Args:
            llm_provider: LLM provider (openai, anthropic)
            model_name: 모델 이름 (기본: gpt-4o or claude-3-opus)
            checkpoint_db_path: SQLite 체크포인트 DB 경로
            store_db_path: SQLite Store DB 경로 (optional)
        """

        # LLM 초기화
        if llm_provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name or "gpt-4o",
                temperature=0.1  # 일관성 있는 응답을 위해 낮은 temperature
            )
        elif llm_provider == "anthropic":
            self.llm = ChatAnthropic(
                model=model_name or "claude-3-opus-20240229",
                temperature=0.1
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

        # Context Manager 초기화
        self.context_manager = ContextManager()

        # 에이전트 초기화
        self.agents = self._initialize_agents()

        # Supervisor workflow 생성
        self.workflow = None
        self.workflow_compiled = False  # 컴파일 상태 추적

        # 메모리 초기화
        self.checkpoint_db_path = checkpoint_db_path
        self.store_db_path = store_db_path
        self.store = InMemoryStore()  # 현재는 InMemoryStore 사용
        
    def _initialize_agents(self) -> Dict[str, Any]:
        """
        하위 에이전트 초기화
        """
        
        agents = {}
        
        # 1. SQL 분석 에이전트 (실적분석, 트렌드 분석)
        agents["sql_analysis"] = create_react_agent(
            self.llm,
            tools=[
                self._create_sql_query_tool(),
                self._create_data_aggregation_tool(),
                self._create_trend_analysis_tool()
            ],
            name="sql_analysis_agent",
            system_message="""당신은 의료/제약 데이터 분석 전문가입니다.
            직원 실적 분석, 거래처 트렌드 분석을 수행합니다.
            복잡한 칼럼에 대한 메타데이터를 활용하여 정확한 분석을 제공합니다."""
        )
        
        # 2. 정보 검색 에이전트
        agents["information_retrieval"] = create_react_agent(
            self.llm,
            tools=[
                self._create_hr_search_tool(),
                self._create_regulation_search_tool(),
                self._create_web_search_tool(),
                self._create_paper_search_tool()
            ],
            name="information_retrieval_agent",
            system_message="""당신은 의료/제약 정보 검색 전문가입니다.
            인사정보, 내부규정, 웹정보, 논문 등 다양한 소스에서 정보를 검색합니다.
            정확하고 관련성 높은 정보만을 제공합니다."""
        )
        
        # 3. 문서 생성 에이전트
        agents["document_generation"] = create_react_agent(
            self.llm,
            tools=[
                self._create_report_generation_tool(),
                self._create_form_filling_tool(),
                self._create_db_storage_tool()
            ],
            name="document_generation_agent",
            system_message="""당신은 의료/제약 문서 작성 전문가입니다.
            방문결과보고서, 제품설명회 신청서, 샘플신청서 등을 작성합니다.
            규정에 맞는 정확한 문서를 생성합니다."""
        )
        
        # 4. 규정 검토 에이전트
        agents["compliance_validation"] = create_react_agent(
            self.llm,
            tools=[
                self._create_compliance_check_tool(),
                self._create_regulation_validation_tool()
            ],
            name="compliance_validation_agent",
            system_message="""당신은 의료/제약 규정 준수 전문가입니다.
            의료법, 리베이트법, 공정거래규약 등을 검토합니다.
            문서와 활동의 규정 위반 여부를 철저히 확인합니다."""
        )
        
        return agents
    
    def _create_sql_query_tool(self) -> Tool:
        """SQL 쿼리 실행 도구"""
        return Tool(
            name="sql_query",
            description="정형 DB에서 SQL 쿼리를 실행하여 데이터를 조회합니다",
            func=lambda query: f"SQL 쿼리 실행: {query}"  # 실제 구현 필요
        )
    
    def _create_data_aggregation_tool(self) -> Tool:
        """데이터 집계 도구"""
        return Tool(
            name="data_aggregation",
            description="데이터를 집계하고 통계를 계산합니다",
            func=lambda data: f"데이터 집계 중: {data}"  # 실제 구현 필요
        )
    
    def _create_trend_analysis_tool(self) -> Tool:
        """트렌드 분석 도구"""
        return Tool(
            name="trend_analysis",
            description="시계열 데이터의 트렌드를 분석합니다",
            func=lambda data: f"트렌드 분석 중: {data}"  # 실제 구현 필요
        )
    
    def _create_hr_search_tool(self) -> Tool:
        """인사정보 검색 도구"""
        return Tool(
            name="hr_search",
            description="인사정보 DB에서 직원 정보를 검색합니다",
            func=lambda query: f"인사정보 검색: {query}"  # 실제 구현 필요
        )
    
    def _create_regulation_search_tool(self) -> Tool:
        """규정 검색 도구"""
        return Tool(
            name="regulation_search",
            description="내부 규정 및 공정거래규약을 검색합니다",
            func=lambda query: f"규정 검색: {query}"  # 실제 구현 필요
        )
    
    def _create_web_search_tool(self) -> Tool:
        """웹 검색 도구"""
        return Tool(
            name="web_search",
            description="네이버, 구글 등 웹에서 정보를 검색합니다",
            func=lambda query: f"웹 검색: {query}"  # 실제 구현 필요
        )
    
    def _create_paper_search_tool(self) -> Tool:
        """논문 검색 도구"""
        return Tool(
            name="paper_search",
            description="의료 관련 논문을 검색합니다",
            func=lambda query: f"논문 검색: {query}"  # 실제 구현 필요
        )
    
    def _create_report_generation_tool(self) -> Tool:
        """보고서 생성 도구"""
        return Tool(
            name="report_generation",
            description="방문결과보고서 등 각종 보고서를 생성합니다",
            func=lambda data: f"보고서 생성 중: {data}"  # 실제 구현 필요
        )
    
    def _create_form_filling_tool(self) -> Tool:
        """양식 작성 도구"""
        return Tool(
            name="form_filling",
            description="제품설명회 신청서, 샘플신청서 등 양식을 작성합니다",
            func=lambda data: f"양식 작성 중: {data}"  # 실제 구현 필요
        )
    
    def _create_db_storage_tool(self) -> Tool:
        """DB 저장 도구"""
        return Tool(
            name="db_storage",
            description="데이터를 정형/비정형 DB에 저장합니다",
            func=lambda data: f"DB 저장 중: {data}"  # 실제 구현 필요
        )
    
    def _create_compliance_check_tool(self) -> Tool:
        """규정 준수 확인 도구"""
        return Tool(
            name="compliance_check",
            description="문서의 규정 위반 여부를 확인합니다",
            func=lambda doc: f"규정 확인 중: {doc}"  # 실제 구현 필요
        )
    
    def _create_regulation_validation_tool(self) -> Tool:
        """규정 검증 도구"""
        return Tool(
            name="regulation_validation",
            description="의료법, 리베이트법 등 법규 위반을 검증합니다",
            func=lambda doc: f"법규 검증 중: {doc}"  # 실제 구현 필요
        )
    
    def build_supervisor_workflow(self) -> StateGraph:
        """
        Supervisor workflow 구축
        langgraph-supervisor 라이브러리 활용
        """
        
        # Supervisor 시스템 프롬프트
        supervisor_prompt = """당신은 의료/제약 도메인 전문 Supervisor입니다.
        
        다음 전문가들을 관리합니다:
        1. sql_analysis_agent: SQL 분석, 직원 실적, 거래처 트렌드 분석
        2. information_retrieval_agent: 정보 검색 (인사, 규정, 웹, 논문)
        3. document_generation_agent: 문서 생성 및 DB 저장
        4. compliance_validation_agent: 규정 준수 검토
        
        사용자 요청을 분석하여 적절한 전문가에게 작업을 할당하세요.
        복잡한 작업은 여러 전문가를 순차적 또는 병렬로 활용하세요.
        
        작업 우선순위:
        1. 규정 준수가 필요한 경우 compliance_validation_agent를 반드시 포함
        2. 데이터 분석이 필요한 경우 sql_analysis_agent 우선
        3. 문서 생성 전에는 필요한 정보를 먼저 수집
        
        모든 작업이 완료되면 FINISH로 응답하세요."""
        
        # Handoff 도구 생성
        handoff_tools = [
            create_handoff_tool(
                agent_name="sql_analysis_agent",
                name="delegate_to_sql_analysis",
                description="SQL 분석 전문가에게 작업 위임"
            ),
            create_handoff_tool(
                agent_name="information_retrieval_agent",
                name="delegate_to_information_retrieval",
                description="정보 검색 전문가에게 작업 위임"
            ),
            create_handoff_tool(
                agent_name="document_generation_agent",
                name="delegate_to_document_generation",
                description="문서 생성 전문가에게 작업 위임"
            ),
            create_handoff_tool(
                agent_name="compliance_validation_agent",
                name="delegate_to_compliance_validation",
                description="규정 검토 전문가에게 작업 위임"
            )
        ]
        
        # Forward 메시지 도구 추가 (직접 전달)
        forward_tool = create_forward_message_tool("supervisor")
        handoff_tools.append(forward_tool)
        
        # Supervisor workflow 생성
        self.workflow = create_supervisor(
            agents=list(self.agents.values()),
            model=self.llm,
            prompt=supervisor_prompt,
            tools=handoff_tools
        )
        
        return self.workflow
    
    async def compile_with_optimization(self) -> None:
        """
        최적화된 워크플로우 준비
        - workflow 빌드만 수행
        - 실제 checkpointer는 실행 시점에 생성
        """

        if not self.workflow:
            self.build_supervisor_workflow()

        # DB 디렉토리 생성
        import os
        os.makedirs(os.path.dirname(self.checkpoint_db_path), exist_ok=True)

        # workflow가 준비되었음을 표시
        self.workflow_compiled = True

        # 컴파일 설정 저장 (실제 컴파일은 실행 시점에)
        self.compile_config = {
            "cache_policy": {
                "sql_analysis_agent": {
                    "ttl": 600,  # 10분
                    "key_func": lambda x: f"sql_{x.get('query', '')}_{x.get('time_range', '')}"
                },
                "information_retrieval_agent": {
                    "ttl": 900,  # 15분
                    "key_func": lambda x: f"info_{x.get('search_query', '')}"
                }
            },
            "node_timeouts": {
                "supervisor": 30,
                "sql_analysis_agent": 60,
                "information_retrieval_agent": 45,
                "document_generation_agent": 90,
                "compliance_validation_agent": 60
            },
            "interrupt_before": ["compliance_validation_agent"]  # 규정 검토 전 확인
        }

        logger.info(f"Supervisor workflow prepared for SQLite checkpointer at {self.checkpoint_db_path}")
    
    async def execute_with_context(
        self,
        query: str,
        user_context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        컨텍스트를 활용한 실행
        AsyncSqliteSaver를 컨텍스트 매니저로 안전하게 사용
        """

        if not self.workflow_compiled:
            await self.compile_with_optimization()

        # 1. 컨텍스트 최적화
        medical_context = await self.context_manager.optimize_context(
            query,
            user_context,
            conversation_history or []
        )

        # 2. 초기 상태 구성
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "context": medical_context.dict(),
            "user_id": user_context.get("user_id"),
            "session_id": user_context.get("session_id"),
            "timestamp": datetime.now().isoformat()
        }

        # 3. 설정
        config = {
            "configurable": {
                "thread_id": user_context.get("session_id", "default"),
                "checkpoint_ns": "medical_supervisor"
            }
        }

        # AsyncSqliteSaver를 컨텍스트 매니저로 사용
        async with AsyncSqliteSaver.from_conn_string(self.checkpoint_db_path) as checkpointer:
            # workflow 컴파일
            app = self.workflow.compile(
                checkpointer=checkpointer,
                store=self.store,
                **self.compile_config  # 저장된 컴파일 설정 사용
            )

            try:
                # 4. 실행 (재시도 로직 포함)
                result = await self._execute_with_retry(
                    lambda: app.ainvoke(initial_state, config)
                )

                # 5. 결과 후처리
                processed_result = await self._post_process_result(result, medical_context)

                return {
                    "status": "success",
                    "result": processed_result,
                    "context": medical_context.dict(),
                    "execution_time": (datetime.now() - datetime.fromisoformat(initial_state["timestamp"])).total_seconds()
                }

            except Exception as e:
                logger.error(f"Execution failed after retries: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "context": medical_context.dict()
                }
        # 컨텍스트 종료 시 자동으로 연결 정리
    
    async def _execute_with_retry(
        self,
        func,
        max_retries: int = 3,
        base_delay: float = 1.0
    ):
        """
        재시도 로직을 포함한 비동기 실행
        지수 백오프 전략 사용
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # 지수 백오프
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {max_retries} attempts failed")

        raise last_exception

    async def check_checkpointer_health(self) -> bool:
        """
        checkpointer 상태 확인
        DB 연결 가능 여부를 테스트
        """
        try:
            async with AsyncSqliteSaver.from_conn_string(self.checkpoint_db_path) as checkpointer:
                # 간단한 테스트 쿼리 실행
                # checkpointer가 제대로 초기화되었는지 확인
                return True
        except Exception as e:
            logger.error(f"Checkpointer health check failed: {e}")
            return False

    async def cleanup(self):
        """
        리소스 정리
        안전한 종료를 위한 정리 작업
        """
        logger.info("Cleaning up resources...")

        # Store 정리 (필요한 경우)
        if hasattr(self, 'store') and self.store:
            # InMemoryStore는 특별한 정리 불필요
            pass

        # 기타 리소스 정리
        self.workflow_compiled = False
        logger.info("Cleanup completed")

    async def shutdown(self):
        """
        Graceful shutdown
        안전한 종료를 위해 모든 리소스 정리
        """
        logger.info("Initiating graceful shutdown...")

        # 진행 중인 작업 대기 (필요한 경우)
        if hasattr(self, '_pending_tasks'):
            await asyncio.gather(*self._pending_tasks, return_exceptions=True)

        # 리소스 정리
        await self.cleanup()

        logger.info("Shutdown completed")

    async def _post_process_result(
        self,
        result: Dict[str, Any],
        context: MedicalContext
    ) -> Dict[str, Any]:
        """
        결과 후처리
        """
        
        processed = {
            "final_answer": result.get("messages", [])[-1].content if result.get("messages") else "",
            "domain": context.domain_type,
            "agents_used": [],
            "data_sources": context.data_sources,
            "compliance_status": "pending"
        }
        
        # 사용된 에이전트 추출
        for msg in result.get("messages", []):
            if hasattr(msg, "name") and msg.name:
                if msg.name not in processed["agents_used"]:
                    processed["agents_used"].append(msg.name)
        
        # 규정 준수 상태 확인
        if "compliance_validation_agent" in processed["agents_used"]:
            processed["compliance_status"] = "reviewed"
        
        return processed
    
    async def stream_execution(
        self,
        query: str,
        user_context: Dict[str, Any]
    ):
        """
        실시간 스트리밍 실행
        AsyncSqliteSaver를 컨텍스트 매니저로 안전하게 사용
        """

        if not self.workflow_compiled:
            await self.compile_with_optimization()

        # 컨텍스트 최적화
        medical_context = await self.context_manager.optimize_context(
            query,
            user_context,
            []
        )

        initial_state = {
            "messages": [HumanMessage(content=query)],
            "context": medical_context.dict(),
            "user_id": user_context.get("user_id"),
            "session_id": user_context.get("session_id"),
            "timestamp": datetime.now().isoformat()
        }

        config = {
            "configurable": {
                "thread_id": user_context.get("session_id", "default"),
                "checkpoint_ns": "medical_supervisor"
            }
        }

        # AsyncSqliteSaver를 컨텍스트 매니저로 사용
        async with AsyncSqliteSaver.from_conn_string(self.checkpoint_db_path) as checkpointer:
            # workflow 컴파일
            app = self.workflow.compile(
                checkpointer=checkpointer,
                store=self.store,
                **self.compile_config  # 저장된 컴파일 설정 사용
            )

            try:
                # 스트리밍
                async for chunk in app.astream(initial_state, config):
                    yield {
                        "type": "stream",
                        "data": chunk,
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Streaming failed: {e}")
                yield {
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        # 컨텍스트 종료 시 자동으로 연결 정리


async def create_medical_supervisor(
    llm_provider: str = "openai",
    model_name: Optional[str] = None,
    checkpoint_db_path: str = "data/checkpoints.db"
) -> MedicalSupervisor:
    """
    의료 Supervisor 생성 헬퍼 함수
    개선된 버전: workflow 준비만 수행
    """

    supervisor = MedicalSupervisor(llm_provider, model_name, checkpoint_db_path)
    await supervisor.compile_with_optimization()

    # checkpointer 상태 확인
    health_check = await supervisor.check_checkpointer_health()
    if not health_check:
        logger.warning("Checkpointer health check failed, but supervisor is ready")

    return supervisor


# 사용 예시
async def main():
    """
    사용 예시
    """
    
    # Supervisor 생성
    supervisor = await create_medical_supervisor()
    
    # 사용자 컨텍스트
    user_context = {
        "user_id": "emp_001",
        "session_id": "session_123",
        "role": "영업사원",
        "department": "영업1팀",
        "region": "서울"
    }
    
    # 쿼리 예시들
    queries = [
        "지난달 A병원 실적 분석해줘",
        "김철수 과장 인사정보 검색",
        "B병원 방문결과보고서 작성",
        "이번 제품설명회 신청서 규정 위반 확인"
    ]
    
    for query in queries:
        print(f"\n처리 중: {query}")
        result = await supervisor.execute_with_context(
            query=query,
            user_context=user_context
        )
        print(f"결과: {result}")


if __name__ == "__main__":
    asyncio.run(main())
