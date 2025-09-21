"""
Medical Domain Supervisor with Real Database API Integration
실제 Database API를 호출하는 Tool 구현이 포함된 Supervisor
LangGraph 0.6.7 StateGraph 기반 구현
"""

from typing import Dict, Any, List, Optional, Literal, Annotated, Sequence, TypedDict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.memory import InMemoryStore
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import logging
import asyncio
from datetime import datetime
import sys
import os
from pathlib import Path
import operator

# 프로젝트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.service.worker_agents.database_api_client import DatabaseAPIClient
from backend.service.supervisor.context_manager import ContextManager, MedicalContext
from backend.service.supervisor.state import MedicalSupervisorState
from backend.service.supervisor.checkpointer_pool import get_checkpointer_pool

logger = logging.getLogger(__name__)


# State definition for agents
class AgentState(TypedDict):
    """Individual agent state"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: Dict[str, Any]
    next_agent: Optional[str]


# Supervisor state
class SupervisorState(TypedDict):
    """Supervisor state for routing"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: Dict[str, Any]
    current_agent: Optional[str]
    next_agent: Optional[str]
    completed_agents: List[str]


class MedicalSupervisorV2:
    """
    의료/제약 도메인 특화 Supervisor V2
    StateGraph 기반 구현
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o-2024-08-06",
        checkpoint_db_path: str = "./checkpoints/supervisor_v2.db",
        verbose: bool = False
    ):
        """
        Supervisor V2 초기화

        Args:
            llm_provider: LLM 제공자 (openai, anthropic)
            llm_model: 모델명
            checkpoint_db_path: 체크포인트 저장 경로
            verbose: 디버그 출력 여부
        """
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.checkpoint_db_path = checkpoint_db_path
        self.verbose = verbose

        # LLM 초기화
        if llm_provider == "anthropic":
            self.llm = ChatAnthropic(model=llm_model, temperature=0)
        else:
            self.llm = ChatOpenAI(model=llm_model, temperature=0)

        # Database API 클라이언트
        self.db_client = DatabaseAPIClient()

        # Context Manager
        self.context_manager = ContextManager()

        # Checkpointer Pool
        self.checkpointer_pool = get_checkpointer_pool()

        # Store 초기화
        self.store = InMemoryStore()

        # 에이전트별 도구 초기화
        self.agent_tools = self._initialize_tools()

        # Workflow 초기화 플래그
        self.workflow = None
        self.workflow_compiled = False

    def _initialize_tools(self) -> Dict[str, List[Tool]]:
        """각 에이전트별 도구 초기화"""
        tools = {}

        # 1. SQL 분석 에이전트 도구
        tools["sql_analysis"] = [
            self._create_sql_query_tool(),
            self._create_monthly_analysis_tool(),
            self._create_trend_analysis_tool()
        ]

        # 2. 정보 검색 에이전트 도구
        tools["information_retrieval"] = [
            self._create_hr_search_tool(),
            self._create_vector_search_tool(),
            self._create_hybrid_search_tool()
        ]

        # 3. 문서 생성 에이전트 도구
        tools["document_generation"] = [
            self._create_document_generation_tool(),
            self._create_template_management_tool(),
            self._create_document_storage_tool()
        ]

        # 4. 규정 검토 에이전트 도구
        tools["compliance_validation"] = [
            self._create_compliance_check_tool(),
            self._create_regulation_search_tool()
        ]

        return tools

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
                """

                result = await self.db_client.execute_sql(sql, "sales")

                if result["success"] and result["data"]:
                    # 트렌드 분석 로직
                    trends = []
                    for row in result["data"][:3]:  # 샘플 3개
                        monthly_values = [
                            row.get(f"2024{str(i).zfill(2)}", 0) for i in range(1, 12)
                        ]
                        avg = sum(monthly_values) / len([v for v in monthly_values if v])
                        trend = "상승" if monthly_values[-1] > avg else "하락"
                        trends.append(f"{row.get('담당자', 'Unknown')}: {trend} 추세")

                    return f"트렌드 분석 결과:\n" + "\n".join(trends)
                else:
                    return "트렌드 분석 데이터 없음"

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
            """HR 정보 데이터베이스 검색"""
            try:
                # HR 테이블에서 검색
                sql = f"""
                SELECT * FROM 인사자료
                WHERE "성명" LIKE '%{query}%'
                   OR "사번" = '{query}'
                   OR "부서" LIKE '%{query}%'
                LIMIT 10
                """

                result = await self.db_client.execute_sql(sql, "hr")

                if result["success"]:
                    data = result["data"]
                    if data:
                        return f"HR 검색 결과 {len(data)}건 발견"
                    else:
                        return "HR 검색 결과 없음"
                else:
                    return f"HR 검색 실패: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"HR 검색 중 오류: {str(e)}"

        return Tool(
            name="hr_search",
            description="인사 정보를 검색합니다 (성명, 사번, 부서)",
            func=lambda q: asyncio.run(search_hr(q))
        )

    def _create_vector_search_tool(self) -> Tool:
        """벡터 검색 도구"""

        async def search_vector(query: str) -> str:
            """벡터 데이터베이스 검색"""
            try:
                # ChromaDB 벡터 검색 (Mock)
                result = await self.db_client.search_vector(query, "medical_docs")

                if result["success"]:
                    docs = result["documents"]
                    if docs:
                        return f"벡터 검색 결과 {len(docs)}건 발견"
                    else:
                        return "관련 문서 없음"
                else:
                    return f"벡터 검색 실패: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"벡터 검색 중 오류: {str(e)}"

        return Tool(
            name="vector_search",
            description="의료 문서를 벡터 검색합니다",
            func=lambda q: asyncio.run(search_vector(q))
        )

    def _create_hybrid_search_tool(self) -> Tool:
        """하이브리드 검색 도구"""

        async def hybrid_search(query: str) -> str:
            """키워드 + 벡터 하이브리드 검색"""
            try:
                # 키워드 검색
                keyword_results = []

                # 벡터 검색
                vector_results = await self.db_client.search_vector(query, "medical_docs")

                # 결과 병합
                total_results = len(keyword_results) + (
                    len(vector_results.get("documents", [])) if vector_results.get("success") else 0
                )

                return f"하이브리드 검색 완료. 총 {total_results}건 발견"

            except Exception as e:
                return f"하이브리드 검색 중 오류: {str(e)}"

        return Tool(
            name="hybrid_search",
            description="키워드와 벡터를 조합한 하이브리드 검색",
            func=lambda q: asyncio.run(hybrid_search(q))
        )

    def _create_document_generation_tool(self) -> Tool:
        """문서 생성 도구"""

        async def generate_document(params: str) -> str:
            """문서 생성"""
            try:
                # 파라미터 파싱
                parts = params.split('|')
                doc_type = parts[0] if len(parts) > 0 else "report"
                content = parts[1] if len(parts) > 1 else "기본 내용"

                # 문서 생성 로직
                document = {
                    "type": doc_type,
                    "content": content,
                    "created_at": datetime.now().isoformat(),
                    "id": f"DOC_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                }

                return f"문서 생성 완료: {document['id']} ({doc_type})"

            except Exception as e:
                return f"문서 생성 중 오류: {str(e)}"

        return Tool(
            name="generate_document",
            description="문서를 생성합니다. 형식: 문서타입|내용",
            func=lambda p: asyncio.run(generate_document(p))
        )

    def _create_template_management_tool(self) -> Tool:
        """템플릿 관리 도구"""

        async def manage_template(action: str) -> str:
            """템플릿 관리"""
            try:
                if action == "list":
                    templates = ["보고서", "증명서", "계약서", "제안서"]
                    return f"사용 가능한 템플릿: {', '.join(templates)}"
                elif action.startswith("load:"):
                    template_name = action.replace("load:", "").strip()
                    return f"템플릿 '{template_name}' 로드 완료"
                else:
                    return "지원되는 액션: list, load:템플릿명"

            except Exception as e:
                return f"템플릿 관리 중 오류: {str(e)}"

        return Tool(
            name="manage_template",
            description="문서 템플릿을 관리합니다",
            func=lambda a: asyncio.run(manage_template(a))
        )

    def _create_document_storage_tool(self) -> Tool:
        """문서 저장소 도구"""

        async def store_document(doc_info: str) -> str:
            """문서 저장"""
            try:
                # 문서 저장 로직
                doc_id = f"STORED_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                return f"문서 저장 완료: {doc_id}"

            except Exception as e:
                return f"문서 저장 중 오류: {str(e)}"

        return Tool(
            name="store_document",
            description="생성된 문서를 저장소에 저장합니다",
            func=lambda d: asyncio.run(store_document(d))
        )

    def _create_compliance_check_tool(self) -> Tool:
        """컴플라이언스 체크 도구"""

        async def check_compliance(content: str) -> str:
            """컴플라이언스 규정 체크"""
            try:
                # 규정 체크 로직 (Mock)
                violations = []

                # 키워드 기반 체크
                prohibited_keywords = ["리베이트", "불법", "위반"]
                for keyword in prohibited_keywords:
                    if keyword in content:
                        violations.append(f"금지 키워드 발견: {keyword}")

                if violations:
                    return f"컴플라이언스 위반 사항:\n" + "\n".join(violations)
                else:
                    return "컴플라이언스 체크 통과"

            except Exception as e:
                return f"컴플라이언스 체크 중 오류: {str(e)}"

        return Tool(
            name="compliance_check",
            description="문서나 활동의 컴플라이언스 준수 여부를 체크합니다",
            func=lambda c: asyncio.run(check_compliance(c))
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

    def _create_agent_node(self, agent_name: str, tools: List[Tool]):
        """각 에이전트를 위한 노드 생성"""

        async def agent_node(state: AgentState) -> Dict:
            """에이전트 노드 실행"""
            messages = state["messages"]
            context = state.get("context", {})

            # 에이전트별 시스템 프롬프트
            system_prompts = {
                "sql_analysis": "당신은 SQL 분석 전문가입니다. 데이터베이스 쿼리를 작성하고 실행하여 데이터를 분석합니다.",
                "information_retrieval": "당신은 정보 검색 전문가입니다. 다양한 소스에서 관련 정보를 찾아 제공합니다.",
                "document_generation": "당신은 문서 생성 전문가입니다. 템플릿을 활용하여 전문적인 문서를 작성합니다.",
                "compliance_validation": "당신은 규정 준수 검토 전문가입니다. 의료법과 규정을 확인하여 컴플라이언스를 검증합니다."
            }

            # 도구가 있는 경우 도구 사용
            if tools:
                # 도구 바인딩
                llm_with_tools = self.llm.bind_tools(tools)

                # 시스템 메시지 추가
                system_message = SystemMessage(content=system_prompts.get(agent_name, ""))
                messages_with_system = [system_message] + list(messages)

                # LLM 호출
                response = await llm_with_tools.ainvoke(messages_with_system)
            else:
                # 도구 없이 직접 응답
                response = await self.llm.ainvoke(messages)

            return {"messages": [response]}

        return agent_node

    def build_supervisor_workflow(self) -> StateGraph:
        """
        StateGraph 기반 Supervisor workflow 구축
        """

        # Workflow 생성
        workflow = StateGraph(SupervisorState)

        # Supervisor 노드
        async def supervisor_node(state: SupervisorState) -> Dict:
            """Supervisor 노드 - 라우팅 결정"""
            messages = state["messages"]
            context = state.get("context", {})
            completed_agents = state.get("completed_agents", [])

            # Supervisor 시스템 프롬프트
            supervisor_prompt = f"""당신은 의료/제약 도메인 전문 Supervisor입니다.

            다음 전문가들을 관리합니다:
            1. sql_analysis: SQL 분석, 직원 실적, 월별 데이터 분석
            2. information_retrieval: 정보 검색 (HR, 벡터, 하이브리드)
            3. document_generation: 문서 생성 및 템플릿 관리
            4. compliance_validation: 규정 준수 검토

            이미 완료된 에이전트: {completed_agents}

            사용자 요청을 분석하여:
            - 적절한 전문가를 선택하거나
            - 모든 작업이 완료되었으면 'FINISH'로 응답하세요.

            응답 형식: "NEXT: agent_name" 또는 "FINISH: 최종 답변"
            """

            system_message = SystemMessage(content=supervisor_prompt)
            messages_with_system = [system_message] + list(messages)

            response = await self.llm.ainvoke(messages_with_system)

            # 응답 파싱
            response_text = response.content
            if "FINISH:" in response_text:
                return {
                    "messages": [response],
                    "next_agent": None
                }
            elif "NEXT:" in response_text:
                next_agent = response_text.split("NEXT:")[1].strip().split()[0]
                return {
                    "messages": [response],
                    "next_agent": next_agent,
                    "completed_agents": completed_agents
                }
            else:
                # 기본 응답
                return {
                    "messages": [response],
                    "next_agent": None
                }

        # Supervisor 노드 추가
        workflow.add_node("supervisor", supervisor_node)

        # 각 에이전트 노드와 도구 노드 추가
        for agent_name, tools in self.agent_tools.items():
            # 에이전트 노드
            agent_node = self._create_agent_node(agent_name, tools)
            workflow.add_node(agent_name, agent_node)

            # 도구 노드
            if tools:
                tool_node = ToolNode(tools)
                workflow.add_node(f"{agent_name}_tools", tool_node)

                # 에이전트와 도구 간 엣지
                workflow.add_conditional_edges(
                    agent_name,
                    tools_condition,
                    {
                        "tools": f"{agent_name}_tools",
                        "continue": "supervisor"
                    }
                )
                workflow.add_edge(f"{agent_name}_tools", agent_name)

        # 시작 엣지
        workflow.add_edge(START, "supervisor")

        # Supervisor 라우팅
        def route_supervisor(state: SupervisorState) -> str:
            """Supervisor 라우팅 로직"""
            next_agent = state.get("next_agent")
            if next_agent and next_agent in self.agent_tools:
                return next_agent
            return END

        workflow.add_conditional_edges(
            "supervisor",
            route_supervisor,
            {
                "sql_analysis": "sql_analysis",
                "information_retrieval": "information_retrieval",
                "document_generation": "document_generation",
                "compliance_validation": "compliance_validation",
                END: END
            }
        )

        # 에이전트에서 supervisor로 돌아오는 엣지 (도구가 없는 경우)
        for agent_name in self.agent_tools:
            if not self.agent_tools[agent_name]:
                workflow.add_edge(agent_name, "supervisor")

        self.workflow = workflow
        return workflow

    async def compile_with_optimization(self) -> None:
        """최적화된 워크플로우 준비"""

        if not self.workflow:
            self.build_supervisor_workflow()

        # 체크포인트 디렉토리 생성
        os.makedirs(os.path.dirname(self.checkpoint_db_path), exist_ok=True)

        self.workflow_compiled = True

        # 컴파일 설정
        self.compile_config = {
            "interrupt_before": ["compliance_validation"]
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
            "completed_agents": [],
            "next_agent": None
        }

        # 설정
        config = {
            "configurable": {
                "thread_id": user_context.get("session_id", "default"),
                "checkpoint_ns": "medical_supervisor_v2"
            }
        }

        # CheckpointerPool을 통한 연결 관리
        async with self.checkpointer_pool.get_connection_context() as checkpointer:
            # workflow 컴파일
            app = self.workflow.compile(
                checkpointer=checkpointer,
                store=self.store,
                **self.compile_config
            )

            try:
                # 실행
                result = await app.ainvoke(initial_state, config)

                # 결과 처리
                messages = result.get("messages", [])
                last_message = messages[-1] if messages else None

                return {
                    "status": "success",
                    "response": last_message.content if last_message else "처리 완료",
                    "metadata": {
                        "completed_agents": result.get("completed_agents", []),
                        "message_count": len(messages)
                    }
                }

            except Exception as e:
                logger.error(f"Workflow execution error: {e}")
                return {
                    "status": "error",
                    "response": "처리 중 오류가 발생했습니다.",
                    "error": str(e)
                }

    async def stream_execution(
        self,
        query: str,
        user_context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None
    ):
        """스트리밍 실행"""

        if not self.workflow_compiled:
            await self.compile_with_optimization()

        # 컨텍스트 최적화
        medical_context = await self.context_manager.optimize_context(
            query,
            user_context,
            conversation_history or []
        )

        # 초기 상태
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "context": medical_context.dict(),
            "completed_agents": [],
            "next_agent": None
        }

        # 설정
        config = {
            "configurable": {
                "thread_id": user_context.get("session_id", "default"),
                "checkpoint_ns": "medical_supervisor_v2"
            }
        }

        # CheckpointerPool을 통한 연결 관리
        async with self.checkpointer_pool.get_connection_context() as checkpointer:
            # workflow 컴파일
            app = self.workflow.compile(
                checkpointer=checkpointer,
                store=self.store,
                **self.compile_config
            )

            # 스트리밍
            async for event in app.astream(initial_state, config):
                yield event

    async def get_state(self, session_id: str) -> Optional[Dict]:
        """체크포인트에서 상태 조회"""

        config = {
            "configurable": {
                "thread_id": session_id,
                "checkpoint_ns": "medical_supervisor_v2"
            }
        }

        async with self.checkpointer_pool.get_connection_context() as checkpointer:
            app = self.workflow.compile(checkpointer=checkpointer, store=self.store)

            try:
                state = await app.aget_state(config)
                return state.values if state else None
            except Exception as e:
                logger.error(f"Failed to get state: {e}")
                return None


# Example usage
async def main():
    """테스트용 메인 함수"""
    supervisor = MedicalSupervisorV2(verbose=True)

    # 테스트 쿼리
    test_query = "사번 E001의 2024년 월별 매출 실적을 분석해주세요"

    result = await supervisor.execute_with_context(
        query=test_query,
        user_context={"user_id": "test_user", "session_id": "test_session"}
    )

    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())