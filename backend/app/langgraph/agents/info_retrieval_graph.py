"""
Information Retrieval Agent - Subgraph Implementation
LangGraph 0.6.6 기반 정보검색 에이전트 (Subgraph 구조)
"""

from typing import Dict, Any, List, TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from loguru import logger
import operator
from datetime import datetime

from app.core.config import settings


class InfoRetrievalState(TypedDict):
    """정보검색 에이전트 전용 State"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    search_type: str  # vector, drug, literature, regulatory, all
    vector_results: List[Dict]
    drug_results: Dict
    literature_results: List[Dict]
    regulatory_results: Dict
    final_response: str
    context: str
    iteration: int


class InfoRetrievalSubgraph:
    """정보검색 Subgraph - 멀티 스텝 검색 워크플로우"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # 임베딩 모델
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # 벡터 DB 초기화
        self.vector_store = self._initialize_vector_store()
        
        # Subgraph 생성
        self.graph = self._build_graph()
    
    def _initialize_vector_store(self):
        """벡터 스토어 초기화"""
        try:
            vector_store = Chroma(
                persist_directory=str(settings.VECTOR_DB_DIR),
                embedding_function=self.embeddings,
                collection_name="pharma_knowledge"
            )
            
            # 샘플 데이터 확인 및 추가
            if vector_store._collection.count() == 0:
                self._load_sample_data(vector_store)
            
            return vector_store
        except Exception as e:
            logger.error(f"벡터 스토어 초기화 실패: {e}")
            return None
    
    def _load_sample_data(self, vector_store):
        """샘플 데이터 로드"""
        sample_documents = [
            Document(
                page_content="아스피린은 해열진통제이며 혈전 예방에 사용됩니다. 부작용으로는 위장 장애가 있을 수 있습니다.",
                metadata={"type": "drug_info", "drug_name": "아스피린"}
            ),
            Document(
                page_content="메트포르민은 제2형 당뇨병 치료제입니다. 혈당 조절에 효과적이며 체중 감소 효과도 있습니다.",
                metadata={"type": "drug_info", "drug_name": "메트포르민"}
            ),
            Document(
                page_content="스타틴 계열 약물은 콜레스테롤 수치를 낮추는데 사용됩니다. 심혈관 질환 예방에 효과적입니다.",
                metadata={"type": "drug_info", "drug_name": "스타틴"}
            ),
            Document(
                page_content="최신 임상시험 결과: SGLT2 억제제가 심부전 환자에서 유의미한 개선 효과를 보였습니다.",
                metadata={"type": "clinical_trial", "year": "2024"}
            ),
            Document(
                page_content="FDA 가이드라인: 생물학적 제제의 바이오시밀러 승인 기준이 업데이트되었습니다.",
                metadata={"type": "regulation", "agency": "FDA"}
            )
        ]
        
        vector_store.add_documents(sample_documents)
        logger.info(f"샘플 문서 {len(sample_documents)}개 추가 완료")
    
    async def analyze_query_node(self, state: InfoRetrievalState) -> Dict:
        """쿼리 분석 노드 - 검색 유형 결정"""
        logger.info("쿼리 분석 시작")
        
        query = state.get("query", "")
        if not query and state.get("messages"):
            last_message = state["messages"][-1]
            query = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else str(last_message)
        
        # LLM으로 검색 유형 분석
        prompt = f"""
        사용자 쿼리: {query}
        
        이 쿼리에 필요한 검색 유형을 선택하세요:
        - vector: 일반 의약품 정보 검색
        - drug: 특정 약물 상세 정보
        - literature: 학술 문헌 검색
        - regulatory: 규제/가이드라인 정보
        - all: 모든 유형 검색
        
        가장 적절한 하나를 선택하세요:
        """
        
        response = await self.llm.ainvoke(prompt)
        search_type = response.content.strip().lower()
        
        # 검색 유형 검증
        valid_types = ["vector", "drug", "literature", "regulatory", "all"]
        if search_type not in valid_types:
            search_type = "vector"  # 기본값
        
        return {
            "query": query,
            "search_type": search_type,
            "iteration": state.get("iteration", 0) + 1
        }
    
    async def vector_search_node(self, state: InfoRetrievalState) -> Dict:
        """벡터 검색 노드"""
        logger.info("벡터 검색 수행")
        
        if not self.vector_store:
            return {"vector_results": []}
        
        query = state.get("query", "")
        results = self.vector_store.similarity_search_with_score(query, k=5)
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": float(score)
            })
        
        return {"vector_results": formatted_results}
    
    async def drug_database_node(self, state: InfoRetrievalState) -> Dict:
        """약물 데이터베이스 검색 노드"""
        logger.info("약물 DB 검색 수행")
        
        query = state.get("query", "")
        
        # 실제 구현에서는 외부 API 호출
        mock_data = {
            "아스피린": {
                "generic_name": "Aspirin",
                "brand_names": ["바이엘 아스피린", "아스트릭스"],
                "indication": "해열, 진통, 혈전 예방",
                "dosage": "100-500mg",
                "side_effects": ["위장 장애", "출혈 위험 증가"],
                "contraindications": ["위궤양", "혈우병"]
            },
            "메트포르민": {
                "generic_name": "Metformin",
                "brand_names": ["글루코파지", "다이아벡스"],
                "indication": "제2형 당뇨병",
                "dosage": "500-2000mg",
                "side_effects": ["구역", "설사", "복부 불편감"],
                "contraindications": ["신부전", "간부전"]
            }
        }
        
        # 쿼리에서 약물명 추출
        drug_found = None
        for drug_name in mock_data.keys():
            if drug_name in query:
                drug_found = drug_name
                break
        
        if drug_found:
            return {"drug_results": mock_data[drug_found]}
        else:
            return {"drug_results": {"message": "특정 약물 정보를 찾을 수 없습니다."}}
    
    async def literature_search_node(self, state: InfoRetrievalState) -> Dict:
        """학술 문헌 검색 노드"""
        logger.info("학술 문헌 검색 수행")
        
        query = state.get("query", "")
        
        # PubMed API 연동 시뮬레이션
        mock_results = [
            {
                "title": f"{query}에 관한 최신 연구",
                "authors": ["Kim J.", "Lee S."],
                "journal": "Korean Journal of Medicine",
                "year": 2024,
                "abstract": f"{query}의 효과에 대한 메타분석 결과..."
            },
            {
                "title": "약물 상호작용 연구",
                "authors": ["Park H."],
                "journal": "International Journal of Pharmacy",
                "year": 2024,
                "abstract": "다양한 약물 간 상호작용 분석..."
            }
        ]
        
        return {"literature_results": mock_results}
    
    async def regulatory_search_node(self, state: InfoRetrievalState) -> Dict:
        """규제 정보 검색 노드"""
        logger.info("규제 정보 검색 수행")
        
        # FDA/KFDA 정보 시뮬레이션
        mock_info = {
            "agency": "KFDA",
            "guidelines": [
                "의약품 임상시험 관리 기준 (2024 개정)",
                "생물학적 동등성 시험 기준",
                "의약품 제조 및 품질관리 기준 (GMP)"
            ],
            "recent_updates": [
                "2024년 개정된 GMP 기준",
                "바이오시밀러 승인 절차 간소화"
            ],
            "warnings": [
                "특정 약물 부작용 경고"
            ]
        }
        
        return {"regulatory_results": mock_info}
    
    async def synthesize_node(self, state: InfoRetrievalState) -> Dict:
        """결과 통합 및 응답 생성 노드"""
        logger.info("검색 결과 통합 및 응답 생성")
        
        # 모든 검색 결과 수집
        context_parts = []
        
        # 벡터 검색 결과
        if state.get("vector_results"):
            vector_context = "\n".join([r["content"] for r in state["vector_results"][:3]])
            context_parts.append(f"[일반 정보]\n{vector_context}")
        
        # 약물 DB 결과
        if state.get("drug_results") and "generic_name" in state["drug_results"]:
            drug_info = state["drug_results"]
            drug_context = f"""
            약물명: {drug_info.get('generic_name')}
            적응증: {drug_info.get('indication')}
            용량: {drug_info.get('dosage')}
            부작용: {', '.join(drug_info.get('side_effects', []))}
            """
            context_parts.append(f"[약물 상세 정보]\n{drug_context}")
        
        # 문헌 검색 결과
        if state.get("literature_results"):
            lit_context = "\n".join([f"- {r['title']} ({r['year']})" for r in state["literature_results"][:2]])
            context_parts.append(f"[관련 연구]\n{lit_context}")
        
        # 규제 정보
        if state.get("regulatory_results"):
            reg_info = state["regulatory_results"]
            reg_context = f"기관: {reg_info.get('agency')}\n최근 업데이트: {', '.join(reg_info.get('recent_updates', []))}"
            context_parts.append(f"[규제 정보]\n{reg_context}")
        
        # 전체 컨텍스트 생성
        full_context = "\n\n".join(context_parts) if context_parts else "검색 결과가 없습니다."
        
        # LLM으로 최종 응답 생성
        prompt = f"""
        사용자 질문: {state.get('query', '')}
        
        검색된 정보:
        {full_context}
        
        위 정보를 바탕으로 사용자 질문에 대해 정확하고 전문적인 답변을 작성하세요.
        의약품 정보는 정확해야 하며, 부작용과 주의사항을 반드시 포함하세요.
        답변은 구조화되고 이해하기 쉽게 작성하세요.
        """
        
        response = await self.llm.ainvoke(prompt)
        
        return {
            "final_response": response.content,
            "context": full_context,
            "messages": [AIMessage(content=response.content)]
        }
    
    def should_search_vector(self, state: InfoRetrievalState) -> str:
        """벡터 검색 수행 여부 결정"""
        search_type = state.get("search_type", "")
        if search_type in ["vector", "all"]:
            return "vector_search"
        return "skip"
    
    def should_search_drug(self, state: InfoRetrievalState) -> str:
        """약물 DB 검색 수행 여부 결정"""
        search_type = state.get("search_type", "")
        if search_type in ["drug", "all"]:
            return "drug_database"
        return "skip"
    
    def should_search_literature(self, state: InfoRetrievalState) -> str:
        """문헌 검색 수행 여부 결정"""
        search_type = state.get("search_type", "")
        if search_type in ["literature", "all"]:
            return "literature_search"
        return "skip"
    
    def should_search_regulatory(self, state: InfoRetrievalState) -> str:
        """규제 정보 검색 수행 여부 결정"""
        search_type = state.get("search_type", "")
        if search_type in ["regulatory", "all"]:
            return "regulatory_search"
        return "skip"
    
    def _build_graph(self) -> StateGraph:
        """Subgraph 구성"""
        workflow = StateGraph(InfoRetrievalState)
        
        # 노드 추가
        workflow.add_node("analyze_query", self.analyze_query_node)
        workflow.add_node("vector_search", self.vector_search_node)
        workflow.add_node("drug_database", self.drug_database_node)
        workflow.add_node("literature_search", self.literature_search_node)
        workflow.add_node("regulatory_search", self.regulatory_search_node)
        workflow.add_node("synthesize", self.synthesize_node)
        
        # 시작점 설정
        workflow.add_edge(START, "analyze_query")
        
        # 조건부 검색 라우팅
        workflow.add_conditional_edges(
            "analyze_query",
            self.should_search_vector,
            {
                "vector_search": "vector_search",
                "skip": "synthesize"
            }
        )
        
        # 각 검색 노드에서 다음 검색으로 이동
        workflow.add_edge("vector_search", "synthesize")
        
        # 병렬 검색 가능 (search_type이 "all"인 경우)
        # 실제로는 더 복잡한 라우팅 로직 필요
        
        # 종료 설정
        workflow.add_edge("synthesize", END)
        
        # 그래프 컴파일
        return workflow.compile()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor에서 호출하는 메인 처리 함수"""
        logger.info("InfoRetrieval Subgraph 처리 시작")
        
        # 입력 state를 subgraph state로 변환
        subgraph_state = InfoRetrievalState(
            messages=state.get("messages", []),
            query="",
            search_type="",
            vector_results=[],
            drug_results={},
            literature_results=[],
            regulatory_results={},
            final_response="",
            context="",
            iteration=0
        )
        
        # Subgraph 실행
        try:
            result = await self.graph.ainvoke(subgraph_state)
            
            # 결과를 parent state 형식으로 변환
            return {
                "messages": result.get("messages", []),
                "agent_outputs": {
                    "info_retrieval": {
                        "query": result.get("query"),
                        "search_type": result.get("search_type"),
                        "context": result.get("context"),
                        "response": result.get("final_response"),
                        "vector_results": result.get("vector_results"),
                        "drug_results": result.get("drug_results"),
                        "literature_results": result.get("literature_results"),
                        "regulatory_results": result.get("regulatory_results")
                    }
                },
                "next_agent": None
            }
        except Exception as e:
            logger.error(f"InfoRetrieval Subgraph 실행 오류: {e}")
            return {
                "messages": [AIMessage(content=f"정보 검색 중 오류가 발생했습니다: {str(e)}")],
                "agent_outputs": {"info_retrieval": {"error": str(e)}},
                "next_agent": None
            }


# Subgraph 인스턴스 생성 함수
def create_info_retrieval_subgraph():
    """InfoRetrieval Subgraph 생성"""
    return InfoRetrievalSubgraph()