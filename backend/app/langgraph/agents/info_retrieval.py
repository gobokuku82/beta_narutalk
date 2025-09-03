"""
Information Retrieval Agent - 정보검색 에이전트
벡터 DB를 활용한 의약품 정보 및 학술자료 검색
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
from loguru import logger
import json
from pathlib import Path

from app.langgraph.state import AgentState
from app.core.config import settings


class InfoRetrievalAgent:
    """정보검색 전문 에이전트"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,  # gpt-4o
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
        
        # 도구 등록
        self.tools = {
            "vector_search": self.vector_search,
            "drug_database": self.search_drug_database,
            "literature_search": self.search_literature,
            "fda_kfda_search": self.search_regulatory_info
        }
    
    def _initialize_vector_store(self):
        """벡터 스토어 초기화"""
        try:
            # ChromaDB 초기화
            vector_store = Chroma(
                persist_directory=str(settings.VECTOR_DB_DIR),
                embedding_function=self.embeddings,
                collection_name="pharma_knowledge"
            )
            
            # 샘플 데이터 추가 (없는 경우)
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
        
        # 벡터 DB에 추가
        vector_store.add_documents(sample_documents)
        logger.info(f"샘플 문서 {len(sample_documents)}개 추가 완료")
    
    async def vector_search(self, query: str, k: int = 5) -> List[Dict]:
        """벡터 DB 검색"""
        try:
            if not self.vector_store:
                return []
            
            # 유사도 검색
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # 결과 포맷팅
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"벡터 검색 오류: {e}")
            return []
    
    async def search_drug_database(self, drug_name: str) -> Dict:
        """의약품 데이터베이스 검색"""
        # 실제 구현에서는 외부 API 또는 DB 연결
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
        
        return mock_data.get(drug_name, {"error": "약물 정보를 찾을 수 없습니다."})
    
    async def search_literature(self, topic: str) -> List[Dict]:
        """학술 문헌 검색"""
        # PubMed API 연동 예시
        mock_results = [
            {
                "title": f"{topic}에 관한 최신 연구",
                "authors": ["Kim J.", "Lee S."],
                "journal": "Korean Journal of Medicine",
                "year": 2024,
                "abstract": f"{topic}의 효과에 대한 메타분석 결과..."
            }
        ]
        
        return mock_results
    
    async def search_regulatory_info(self, query: str) -> Dict:
        """규제 정보 검색"""
        # FDA/KFDA API 연동 예시
        mock_info = {
            "agency": "KFDA",
            "guidelines": [
                "의약품 임상시험 관리 기준",
                "생물학적 동등성 시험 기준"
            ],
            "recent_updates": [
                "2024년 개정된 GMP 기준"
            ]
        }
        
        return mock_info
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """에이전트 처리 로직"""
        logger.info("정보검색 에이전트 처리 시작")
        
        # 최신 메시지 확인
        last_message = state["messages"][-1]
        user_query = last_message.get("content", "")
        
        # 벡터 검색 수행
        search_results = await self.vector_search(user_query)
        
        # 컨텍스트 생성
        context = "\n".join([r["content"] for r in search_results[:3]])
        
        # LLM으로 응답 생성
        prompt = f"""
        사용자 질문: {user_query}
        
        검색된 정보:
        {context}
        
        위 정보를 바탕으로 사용자 질문에 대해 정확하고 도움이 되는 답변을 작성하세요.
        의약품 정보는 정확해야 하며, 부작용과 주의사항을 반드시 포함하세요.
        """
        
        response = await self.llm.ainvoke(prompt)
        
        # 결과 반환
        return {
            "messages": [{"role": "assistant", "content": response.content}],
            "agent_outputs": {
                "info_retrieval": {
                    "search_results": search_results,
                    "response": response.content
                }
            },
            "next_agent": None  # Supervisor로 돌아감
        }