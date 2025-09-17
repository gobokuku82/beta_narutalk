"""
Medical Domain Supervisor with Real Database API Integration
실제 Database API를 호출하는 Tool 구현이 포함된 Supervisor
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
from langgraph.store.memory import InMemoryStore
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import Tool
import logging
import asyncio
from datetime import datetime
import sys
from pathlib import Path

# 프로젝트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.service.worker_agents.database_api_client import DatabaseAPIClient
from backend.service.supervisor.context_manager import ContextManager, MedicalContext
from backend.service.supervisor.state import MedicalSupervisorState

logger = logging.getLogger(__name__)


class MedicalSupervisorV2:
    """
    의료/제약 도메인 특화 Supervisor V2
    실제 Database API 통합 버전
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: Optional[str] = None,
        checkpoint_db_path: str = "database/checkpointer/checkpoint.db",
        database_api_url: str = "http://localhost:8000/api/v1"
    ):
        """
        Initialize Medical Supervisor V2

        Args:
            llm_provider: LLM provider (openai, anthropic)
            model_name: 모델 이름
            checkpoint_db_path: SQLite 체크포인트 DB 경로
            database_api_url: Database API 서버 URL
        """

        # LLM 초기화
        if llm_provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name or "gpt-4o",
                temperature=0.1
            )
        elif llm_provider == "anthropic":
            self.llm = ChatAnthropic(
                model=model_name or "claude-3-opus-20240229",
                temperature=0.1
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

        # Database API Client
        self.db_client = DatabaseAPIClient(base_url=database_api_url)

        # Context Manager
        self.context_manager = ContextManager()

        # 에이전트 초기화
        self.agents = self._initialize_agents()

        # Supervisor workflow
        self.workflow = None
        self.workflow_compiled = False

        # 메모리 초기화
        self.checkpoint_db_path = checkpoint_db_path
        self.store = InMemoryStore()

    def _initialize_agents(self) -> Dict[str, Any]:
        """
        하위 에이전트 초기화 - 실제 Database API 호출 Tool 포함
        """

        agents = {}

        # 1. SQL 분석 에이전트
        agents["sql_analysis"] = create_react_agent(
            self.llm,
            tools=[
                self._create_sql_query_tool(),
                self._create_monthly_analysis_tool(),
                self._create_trend_analysis_tool()
            ],
            name="sql_analysis_agent",
            system_message="""당신은 의료/제약 데이터 분석 전문가입니다.
            한글 컬럼명과 월별 데이터(202312~202411)를 정확히 처리합니다.
            직원 실적 분석, 거래처 트렌드 분석을 수행합니다."""
        )

        # 2. 정보 검색 에이전트
        agents["information_retrieval"] = create_react_agent(
            self.llm,
            tools=[
                self._create_hr_search_tool(),
                self._create_vector_search_tool(),
                self._create_hybrid_search_tool()
            ],
            name="information_retrieval_agent",
            system_message="""당신은 의료/제약 정보 검색 전문가입니다.
            HR 정보, 규정, ChromaDB 벡터 검색을 수행합니다.
            SQL과 벡터 검색을 조합한 하이브리드 검색도 가능합니다."""
        )

        # 3. 문서 생성 에이전트
        agents["document_generation"] = create_react_agent(
            self.llm,
            tools=[
                self._create_report_generation_tool(),
                self._create_template_tool(),
                self._create_export_tool()
            ],
            name="document_generation_agent",
            system_message="""당신은 의료/제약 문서 작성 전문가입니다.
            방문결과보고서, 제품설명회 신청서 등을 작성합니다.
            템플릿을 활용하여 규정에 맞는 문서를 생성합니다."""
        )

        # 4. 규정 검토 에이전트
        agents["compliance_validation"] = create_react_agent(
            self.llm,
            tools=[
                self._create_compliance_check_tool(),
                self._create_regulation_search_tool()
            ],
            name="compliance_validation_agent",
            system_message="""당신은 의료/제약 규정 준수 전문가입니다.
            의료법, 리베이트법, 공정거래규약을 검토합니다.
            ChromaDB의 규정 데이터베이스를 활용합니다."""
        )

        return agents

    def _create_sql_query_tool(self) -> Tool:
        """SQL 쿼리 실행 도구 - 실제 Database API 호출"""

        async def execute_sql(query: str) -> str:
            """
            SQL 쿼리 실행

            Args:
                query: SQL 쿼리문

            Returns:
                쿼리 실행 결과
            """
            try:
                # 데이터베이스 결정 (쿼리 내용 기반)
                database = "sales"  # 기본값
                if any(keyword in query.lower() for keyword in ["인사자료", "지점연락처", "사번", "성명"]):
                    database = "hr"
                elif any(keyword in query.lower() for keyword in ["rules", "규정", "법규"]):
                    database = "rules"

                # API 호출
                result = await self.db_client.execute_sql(query, database)

                if result["success"]:
                    data = result["data"]
                    if data:
                        # 결과 포맷팅
                        return f"쿼리 실행 성공. {len(data)}개 결과:\n{data[:5]}"  # 처음 5개만
                    else:
                        return "쿼리 실행 성공. 결과 없음."
                else:
                    return f"쿼리 실행 실패: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"SQL 실행 중 오류: {str(e)}"

        return Tool(
            name="sql_query",
            description="정형 DB에서 SQL 쿼리를 실행합니다. 한글 컬럼명과 월별 데이터를 지원합니다.",
            func=lambda q: asyncio.run(execute_sql(q))
        )

    def _create_monthly_analysis_tool(self) -> Tool:
        """월별 데이터 분석 도구"""

        async def analyze_monthly(params: str) -> str:
            """
            월별 데이터 분석

            Args:
                params: "사번,시작월,종료월" 형식 (예: "E001,202401,202411")

            Returns:
                월별 분석 결과
            """
            try:
                parts = params.split(',')
                if len(parts) != 3:
                    return "파라미터 형식: 사번,시작월,종료월"

                employee_id = parts[0].strip()
                start_month = parts[1].strip()
                end_month = parts[2].strip()

                result = await self.db_client.analyze_monthly_data(
                    employee_id, start_month, end_month
                )

                if result["success"]:
                    totals = result.get("monthly_totals", {})
                    total_sum = result.get("total_sum", 0)
                    return f"직원 {employee_id} 월별 실적:\n{totals}\n총합: {total_sum:,}"
                else:
                    return f"분석 실패: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"월별 분석 중 오류: {str(e)}"

        return Tool(
            name="monthly_analysis",
            description="직원의 월별 실적을 분석합니다. 형식: 사번,시작월,종료월",
            func=lambda p: asyncio.run(analyze_monthly(p))
        )

    def _create_trend_analysis_tool(self) -> Tool:
        """트렌드 분석 도구"""

        async def analyze_trend(query: str) -> str:
            """트렌드 분석 - 시계열 데이터 패턴 분석"""
            try:
                # 월별 데이터 조회 SQL 생성
                sql = f"""
                SELECT "담당자", "거래처ID",
                       "202401", "202402", "202403", "202404", "202405", "202406",
                       "202407", "202408", "202409", "202410", "202411"
                FROM sales_performance
                WHERE "담당자" LIKE '%{query}%'
                LIMIT 10
                """

                result = await self.db_client.execute_sql(sql, "sales")

                if result["success"] and result["data"]:
                    # 간단한 트렌드 분석
                    trends = []
                    for row in result["data"][:3]:  # 처음 3개만
                        monthly_values = [row.get(f"2024{i:02d}", 0) for i in range(1, 12)]
                        avg = sum(v for v in monthly_values if v) / len([v for v in monthly_values if v])
                        trend = "상승" if monthly_values[-1] > avg else "하락"
                        trends.append(f"{row.get('담당자', 'Unknown')}: {trend} 추세")

                    return f"트렌드 분석 결과:\n" + "\n".join(trends)
                else:
                    return "트렌드 분석할 데이터 없음"

            except Exception as e:
                return f"트렌드 분석 중 오류: {str(e)}"

        return Tool(
            name="trend_analysis",
            description="시계열 데이터의 트렌드를 분석합니다",
            func=lambda q: asyncio.run(analyze_trend(q))
        )

    def _create_hr_search_tool(self) -> Tool:
        """HR 정보 검색 도구"""

        async def search_hr(query: str) -> str:
            """HR 정보 검색"""
            try:
                result = await self.db_client.search_hr(query)

                if result["success"]:
                    data = result["data"]
                    if data:
                        return f"HR 검색 결과 {len(data)}건:\n{data[:3]}"  # 처음 3개
                    else:
                        return "검색 결과 없음"
                else:
                    return f"HR 검색 실패: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"HR 검색 중 오류: {str(e)}"

        return Tool(
            name="hr_search",
            description="인사정보 DB에서 직원 정보를 검색합니다",
            func=lambda q: asyncio.run(search_hr(q))
        )

    def _create_vector_search_tool(self) -> Tool:
        """벡터 검색 도구 (ChromaDB)"""

        async def search_vector(params: str) -> str:
            """
            벡터 검색

            Args:
                params: "쿼리,컬렉션" 형식 (예: "리베이트,rules")
            """
            try:
                parts = params.split(',')
                query = parts[0].strip()
                collection = parts[1].strip() if len(parts) > 1 else "rules"

                result = await self.db_client.search_vector(query, collection)

                if result["success"]:
                    docs = result["documents"]
                    if docs:
                        return f"벡터 검색 결과 {len(docs)}건:\n{docs[:2]}"  # 처음 2개
                    else:
                        return "검색 결과 없음"
                else:
                    return f"벡터 검색 실패: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"벡터 검색 중 오류: {str(e)}"

        return Tool(
            name="vector_search",
            description="ChromaDB에서 벡터 검색을 수행합니다. 형식: 쿼리,컬렉션",
            func=lambda p: asyncio.run(search_vector(p))
        )

    def _create_hybrid_search_tool(self) -> Tool:
        """하이브리드 검색 도구 (SQL + Vector)"""

        async def hybrid_search(query: str) -> str:
            """SQL과 벡터를 조합한 하이브리드 검색"""
            try:
                result = await self.db_client.hybrid_search(
                    query,
                    databases=["hr", "sales"],
                    vector_collections=["rules", "hr_rules"]
                )

                if result["success"]:
                    sql_count = len(result.get("sql_results", []))
                    vector_count = len(result.get("vector_results", []))
                    return f"하이브리드 검색 완료:\nSQL 결과: {sql_count}건\n벡터 결과: {vector_count}건"
                else:
                    return f"하이브리드 검색 실패: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"하이브리드 검색 중 오류: {str(e)}"

        return Tool(
            name="hybrid_search",
            description="SQL과 벡터 검색을 조합한 하이브리드 검색",
            func=lambda q: asyncio.run(hybrid_search(q))
        )

    def _create_report_generation_tool(self) -> Tool:
        """보고서 생성 도구"""

        def generate_report(data: str) -> str:
            """보고서 생성 (템플릿 기반)"""
            # 실제 구현에서는 템플릿 엔진 사용
            return f"보고서 생성 완료:\n제목: 방문결과보고서\n내용: {data[:100]}..."

        return Tool(
            name="report_generation",
            description="방문결과보고서 등 각종 보고서를 생성합니다",
            func=generate_report
        )

    def _create_template_tool(self) -> Tool:
        """템플릿 관리 도구"""

        def manage_template(action: str) -> str:
            """템플릿 로드/저장"""
            templates = {
                "visit_report": "방문결과보고서 템플릿",
                "product_meeting": "제품설명회 신청서 템플릿",
                "sample_request": "샘플신청서 템플릿"
            }
            return f"사용 가능한 템플릿: {list(templates.keys())}"

        return Tool(
            name="template_manager",
            description="문서 템플릿을 관리합니다",
            func=manage_template
        )

    def _create_export_tool(self) -> Tool:
        """문서 내보내기 도구"""

        def export_document(format: str) -> str:
            """문서를 다양한 형식으로 내보내기"""
            supported = ["PDF", "Excel", "Word", "HTML"]
            if format.upper() in supported:
                return f"{format} 형식으로 내보내기 준비 완료"
            else:
                return f"지원 형식: {supported}"

        return Tool(
            name="export_document",
            description="문서를 PDF, Excel 등으로 내보냅니다",
            func=export_document
        )

    def _create_compliance_check_tool(self) -> Tool:
        """규정 준수 확인 도구"""

        async def check_compliance(document: str) -> str:
            """문서의 규정 위반 여부 확인"""
            try:
                # 규정 키워드 검색
                keywords = ["리베이트", "금품", "향응", "접대", "현금", "상품권"]
                violations = []

                for keyword in keywords:
                    if keyword in document:
                        # ChromaDB에서 관련 규정 검색
                        result = await self.db_client.search_vector(keyword, "rules")
                        if result["success"] and result["documents"]:
                            violations.append(f"'{keyword}' 관련 규정 주의 필요")

                if violations:
                    return f"규정 검토 필요:\n" + "\n".join(violations)
                else:
                    return "규정 위반 사항 없음"

            except Exception as e:
                return f"규정 확인 중 오류: {str(e)}"

        return Tool(
            name="compliance_check",
            description="문서의 규정 위반 여부를 확인합니다",
            func=lambda doc: asyncio.run(check_compliance(doc))
        )

    def _create_regulation_search_tool(self) -> Tool:
        """규정 검색 도구"""

        async def search_regulation(query: str) -> str:
            """규정 데이터베이스 검색"""
            try:
                # ChromaDB에서 규정 검색
                result = await self.db_client.search_vector(query, "rules")

                if result["success"]:
                    docs = result["documents"]
                    if docs:
                        return f"규정 검색 결과 {len(docs)}건 발견"
                    else:
                        return "관련 규정 없음"
                else:
                    return f"규정 검색 실패: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"규정 검색 중 오류: {str(e)}"

        return Tool(
            name="regulation_search",
            description="의료법, 리베이트법 등 규정을 검색합니다",
            func=lambda q: asyncio.run(search_regulation(q))
        )

    def build_supervisor_workflow(self) -> StateGraph:
        """
        Supervisor workflow 구축
        """

        # Supervisor 시스템 프롬프트
        supervisor_prompt = """당신은 의료/제약 도메인 전문 Supervisor입니다.

        다음 전문가들을 관리합니다:
        1. sql_analysis_agent: SQL 분석, 직원 실적, 월별 데이터 분석
        2. information_retrieval_agent: 정보 검색 (HR, 벡터, 하이브리드)
        3. document_generation_agent: 문서 생성 및 템플릿 관리
        4. compliance_validation_agent: 규정 준수 검토

        데이터베이스 정보:
        - HR DB: 인사자료, 지점연락처 (한글 컬럼명)
        - Sales DB: sales_performance (월별 데이터 202312~202411)
        - ChromaDB: rules (규정), hr_rules (HR규정)

        사용자 요청을 분석하여 적절한 전문가에게 작업을 할당하세요.
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

        # Forward 메시지 도구 추가
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
        """최적화된 워크플로우 준비"""

        if not self.workflow:
            self.build_supervisor_workflow()

        # 체크포인트 디렉토리 생성
        os.makedirs(os.path.dirname(self.checkpoint_db_path), exist_ok=True)

        self.workflow_compiled = True

        # 컴파일 설정
        self.compile_config = {
            "interrupt_before": ["compliance_validation_agent"]
        }

        logger.info(f"Supervisor V2 workflow prepared with checkpoint at {self.checkpoint_db_path}")

    async def execute_with_context(
        self,
        query: str,
        user_context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """컨텍스트를 활용한 실행"""

        if not self.workflow_compiled:
            await self.compile_with_optimization()

        # 컨텍스트 최적화
        medical_context = await self.context_manager.optimize_context(
            query,
            user_context,
            conversation_history or []
        )

        # 초기 상태 구성
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "context": medical_context.dict(),
            "user_id": user_context.get("user_id"),
            "session_id": user_context.get("session_id"),
            "timestamp": datetime.now().isoformat()
        }

        # 설정
        config = {
            "configurable": {
                "thread_id": user_context.get("session_id", "default"),
                "checkpoint_ns": "medical_supervisor_v2"
            }
        }

        # AsyncSqliteSaver 사용
        async with AsyncSqliteSaver.from_conn_string(self.checkpoint_db_path) as checkpointer:
            # workflow 컴파일
            app = self.workflow.compile(
                checkpointer=checkpointer,
                store=self.store,
                **self.compile_config
            )

            try:
                # 실행
                result = await app.ainvoke(initial_state, config)

                # 결과 후처리
                processed_result = self._post_process_result(result, medical_context)

                return {
                    "status": "success",
                    "result": processed_result,
                    "context": medical_context.dict(),
                    "execution_time": (datetime.now() - datetime.fromisoformat(initial_state["timestamp"])).total_seconds()
                }

            except Exception as e:
                logger.error(f"Execution failed: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "context": medical_context.dict()
                }

    def _post_process_result(
        self,
        result: Dict[str, Any],
        context: MedicalContext
    ) -> Dict[str, Any]:
        """결과 후처리"""

        processed = {
            "final_answer": result.get("messages", [])[-1].content if result.get("messages") else "",
            "domain": context.domain_type,
            "agents_used": [],
            "data_sources": context.data_sources
        }

        # 사용된 에이전트 추출
        for msg in result.get("messages", []):
            if hasattr(msg, "name") and msg.name:
                if msg.name not in processed["agents_used"]:
                    processed["agents_used"].append(msg.name)

        return processed

    async def stream_execution(
        self,
        query: str,
        user_context: Dict[str, Any]
    ):
        """실시간 스트리밍 실행"""

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
                "checkpoint_ns": "medical_supervisor_v2"
            }
        }

        async with AsyncSqliteSaver.from_conn_string(self.checkpoint_db_path) as checkpointer:
            app = self.workflow.compile(
                checkpointer=checkpointer,
                store=self.store,
                **self.compile_config
            )

            try:
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

    async def shutdown(self):
        """안전한 종료"""
        logger.info("Shutting down Supervisor V2...")

        # Database API 클라이언트 종료
        if self.db_client:
            await self.db_client.close()

        logger.info("Supervisor V2 shutdown complete")


# 생성 헬퍼 함수
async def create_medical_supervisor_v2(
    llm_provider: str = "openai",
    model_name: Optional[str] = None,
    checkpoint_db_path: str = "database/checkpointer/checkpoint.db",
    database_api_url: str = "http://localhost:8000/api/v1"
) -> MedicalSupervisorV2:
    """Medical Supervisor V2 생성"""

    supervisor = MedicalSupervisorV2(
        llm_provider,
        model_name,
        checkpoint_db_path,
        database_api_url
    )
    await supervisor.compile_with_optimization()

    return supervisor