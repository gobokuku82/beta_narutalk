"""
Information Retrieval Agent - 정보검색 에이전트 (HuggingFace 버전)
HuggingFace KURE-v1 임베딩과 bge-reranker-v2-m3-ko 사용
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
from loguru import logger
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path

from app.langgraph.state import AgentState
from app.core.config import settings


class InfoRetrievalAgentHF:
    """정보검색 전문 에이전트 - HuggingFace 모델 버전"""
    
    def __init__(self):
        # LLM 초기화 (응답 생성용)
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,  # gpt-4o
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # HuggingFace 임베딩 모델 (KURE-v1)
        logger.info(f"HuggingFace 임베딩 모델 로드 중: {settings.EMBEDDING_MODEL}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Reranker 모델 초기화 (bge-reranker-v2-m3-ko)
        logger.info(f"Reranker 모델 로드 중: {settings.RERANKER_MODEL}")
        self.reranker_tokenizer = AutoTokenizer.from_pretrained(
            settings.RERANKER_MODEL,
            use_auth_token=settings.HUGGINGFACE_TOKEN
        )
        self.reranker_model = AutoModelForSequenceClassification.from_pretrained(
            settings.RERANKER_MODEL,
            use_auth_token=settings.HUGGINGFACE_TOKEN
        )
        
        # GPU 사용 가능하면 GPU로 이동
        if torch.cuda.is_available():
            self.reranker_model = self.reranker_model.cuda()
            logger.info("Reranker 모델 GPU 사용")
        
        # 벡터 DB 초기화
        self.vector_store = self._initialize_vector_store()
        
        # 도구 등록
        self.tools = {
            "vector_search": self.vector_search_with_rerank,
            "drug_database": self.search_drug_database,
            "literature_search": self.search_literature,
            "fda_kfda_search": self.search_regulatory_info
        }
    
    def _initialize_vector_store(self):
        """벡터 스토어 초기화 - HuggingFace 임베딩 사용"""
        try:
            # ChromaDB 초기화 (HuggingFace 임베딩)
            vector_store = Chroma(
                persist_directory=str(settings.VECTOR_DB_DIR),
                embedding_function=self.embeddings,
                collection_name="pharma_knowledge_hf"
            )
            
            # 샘플 데이터 추가 (없는 경우)
            if vector_store._collection.count() == 0:
                self._load_sample_data(vector_store)
            
            logger.info(f"벡터 스토어 초기화 완료 (컬렉션 크기: {vector_store._collection.count()})")
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
                page_content="SGLT2 억제제는 당뇨병 치료제로 심부전 환자에게도 효과적입니다. 신장 보호 효과가 있습니다.",
                metadata={"type": "drug_info", "drug_name": "SGLT2 억제제"}
            ),
            Document(
                page_content="ACE 억제제는 고혈압 치료제로 심부전 치료에도 사용됩니다. 기침이 주요 부작용입니다.",
                metadata={"type": "drug_info", "drug_name": "ACE 억제제"}
            ),
            Document(
                page_content="최신 임상시험: SGLT2 억제제가 심부전 환자에서 입원율을 30% 감소시켰습니다.",
                metadata={"type": "clinical_trial", "year": "2024"}
            ),
            Document(
                page_content="FDA 가이드라인: 생물학적 제제의 바이오시밀러 승인 기준이 업데이트되었습니다.",
                metadata={"type": "regulation", "agency": "FDA"}
            ),
            Document(
                page_content="KFDA 공지: 의약품 임상시험 관리기준(GCP) 개정안이 발표되었습니다.",
                metadata={"type": "regulation", "agency": "KFDA"}
            )
        ]
        
        # 벡터 DB에 추가
        vector_store.add_documents(sample_documents)
        logger.info(f"샘플 문서 {len(sample_documents)}개 추가 완료")
    
    def rerank_results(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        BGE Reranker를 사용한 재순위화
        """
        if not documents:
            return []
        
        try:
            # Reranker 입력 준비
            pairs = [[query, doc["content"]] for doc in documents]
            
            # 토크나이징
            with torch.no_grad():
                inputs = self.reranker_tokenizer(
                    pairs,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors='pt'
                )
                
                # GPU로 이동 (가능한 경우)
                if torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                
                # 점수 계산
                outputs = self.reranker_model(**inputs)
                scores = outputs.logits.squeeze(-1)
                
                # CPU로 이동 및 numpy 변환
                if torch.cuda.is_available():
                    scores = scores.cpu()
                scores = scores.numpy()
            
            # 점수에 따라 정렬
            for i, doc in enumerate(documents):
                doc["rerank_score"] = float(scores[i])
            
            # 재순위화된 결과 정렬
            reranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
            
            logger.info(f"재순위화 완료: {len(documents)}개 문서 -> 상위 {min(top_k, len(reranked))}개 반환")
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"재순위화 오류: {e}")
            # 오류 시 원본 반환
            return documents[:top_k]
    
    async def vector_search_with_rerank(self, query: str, k: int = 10, rerank_k: int = 5) -> List[Dict]:
        """벡터 검색 후 재순위화"""
        try:
            if not self.vector_store:
                return []
            
            # 1단계: 벡터 유사도 검색 (더 많은 후보 검색)
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # 결과 포맷팅
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })
            
            # 2단계: Reranker로 재순위화
            reranked_results = self.rerank_results(query, formatted_results, top_k=rerank_k)
            
            return reranked_results
        except Exception as e:
            logger.error(f"벡터 검색 오류: {e}")
            return []
    
    async def search_drug_database(self, drug_name: str) -> Dict:
        """의약품 데이터베이스 검색"""
        # 기존 구현과 동일
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
        logger.info("정보검색 에이전트 (HF) 처리 시작")
        
        # 최신 메시지 확인
        last_message = state["messages"][-1]
        user_query = last_message.get("content", "")
        
        # 벡터 검색 + 재순위화 수행
        search_results = await self.vector_search_with_rerank(
            query=user_query,
            k=10,  # 초기 검색 개수
            rerank_k=3  # 재순위화 후 상위 개수
        )
        
        # 컨텍스트 생성 (재순위화된 상위 결과 사용)
        context = "\n\n".join([
            f"[관련도: {r.get('rerank_score', 0):.2f}]\n{r['content']}"
            for r in search_results
        ])
        
        # LLM으로 응답 생성
        prompt = f"""
        사용자 질문: {user_query}
        
        검색된 정보 (관련도 순):
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
                    "embedding_model": settings.EMBEDDING_MODEL,
                    "reranker_model": settings.RERANKER_MODEL,
                    "response": response.content
                }
            },
            "next_agent": None  # Supervisor로 돌아감
        }