"""
허깅페이스 모델 기반 임베딩 서비스

문서 임베딩과 유사성 검색을 담당하는 서비스입니다.
허깅페이스 모델을 직접 사용하여 더 나은 성능을 제공합니다.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from huggingface_hub import login
from ..core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """허깅페이스 모델 기반 임베딩 서비스 클래스"""
    
    def __init__(self):
        """임베딩 서비스 초기화"""
        self.embedding_model = None
        self.reranker_model = None
        self.model_loaded = False
        self.reranker_loaded = False
        
        # 허깅페이스 토큰 설정
        self._setup_huggingface_token()
        
        # 모델 초기화는 지연 로딩으로 변경 (서버 시작 속도 향상)
        logger.info("임베딩 서비스 초기화 완료 (모델은 첫 사용 시 로드됩니다)")
    
    def _setup_huggingface_token(self):
        """허깅페이스 토큰 설정"""
        try:
            if settings.huggingface_token:
                login(token=settings.huggingface_token)
                logger.info("허깅페이스 토큰으로 로그인 완료")
            else:
                logger.warning("허깅페이스 토큰이 설정되지 않았습니다. 퍼블릭 모델만 사용 가능합니다.")
        except Exception as e:
            logger.warning(f"허깅페이스 토큰 설정 실패: {str(e)}")
    
    def _initialize_models(self):
        """허깅페이스 임베딩 모델 초기화"""
        try:
            # 임베딩 모델 로드
            logger.info(f"허깅페이스 임베딩 모델 로드: {settings.embedding_model_id}")
            self.embedding_model = SentenceTransformer(
                settings.embedding_model_id,
                trust_remote_code=True
            )
            self.model_loaded = True
            logger.info("허깅페이스 임베딩 모델 로드 성공")
            
            # 리랭커 모델 로드 (선택적)
            try:
                logger.info(f"허깅페이스 리랭커 모델 로드: {settings.reranker_model_id}")
                self.reranker_model = CrossEncoder(
                    settings.reranker_model_id,
                    trust_remote_code=True
                )
                self.reranker_loaded = True
                logger.info("허깅페이스 리랭커 모델 로드 성공")
            except Exception as e:
                logger.warning(f"리랭커 모델 로드 실패: {str(e)}")
                
        except Exception as e:
            logger.error(f"허깅페이스 임베딩 모델 초기화 실패: {str(e)}")
            
            # 폴백: 기본 모델 시도
            try:
                logger.info("기본 임베딩 모델 로드 시도: sentence-transformers/all-MiniLM-L6-v2")
                self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                self.model_loaded = True
                logger.info("기본 임베딩 모델 로드 성공")
            except Exception as fallback_e:
                logger.error(f"기본 임베딩 모델 로드도 실패: {str(fallback_e)}")
                raise
    
    def is_available(self) -> bool:
        """임베딩 서비스 사용 가능 여부 확인"""
        # 지연 로딩: 모델이 로드되지 않았어도 사용 가능으로 간주
        return True
    
    def is_reranker_available(self) -> bool:
        """리랭커 서비스 사용 가능 여부 확인"""
        return self.reranker_loaded and self.reranker_model is not None
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """텍스트를 임베딩 벡터로 변환"""
        # 지연 로딩: 첫 사용 시 모델 로드
        if not self.model_loaded:
            try:
                logger.info("첫 사용 시 임베딩 모델을 로드합니다...")
                self._initialize_models()
            except Exception as e:
                logger.error(f"임베딩 모델 로드 실패: {str(e)}")
                return None
        
        if not self.model_loaded or not self.embedding_model:
            logger.warning("임베딩 모델이 로드되지 않았습니다.")
            return None
            
        try:
            # 텍스트를 임베딩 벡터로 변환
            embedding = self.embedding_model.encode([text], normalize_embeddings=True)
            return embedding[0].tolist()
        except Exception as e:
            logger.error(f"텍스트 임베딩 실패: {str(e)}")
            return None
    
    async def embed_documents(self, documents: List[str]) -> Optional[List[List[float]]]:
        """여러 문서를 임베딩 벡터로 변환"""
        # 지연 로딩: 첫 사용 시 모델 로드
        if not self.model_loaded:
            try:
                logger.info("첫 사용 시 임베딩 모델을 로드합니다...")
                self._initialize_models()
            except Exception as e:
                logger.error(f"임베딩 모델 로드 실패: {str(e)}")
                return None
        
        if not self.model_loaded or not self.embedding_model:
            logger.warning("임베딩 모델이 로드되지 않았습니다.")
            return None
            
        try:
            # 문서들을 임베딩 벡터로 변환 (정규화 적용)
            embeddings = self.embedding_model.encode(documents, normalize_embeddings=True)
            return [embedding.tolist() for embedding in embeddings]
        except Exception as e:
            logger.error(f"문서 임베딩 실패: {str(e)}")
            return None
    
    async def search_similar_documents(self, query: str, documents: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """유사한 문서 검색 (임베딩 + 리랭킹)"""
        if not self.is_available():
            logger.warning("임베딩 서비스를 사용할 수 없습니다. 기본 검색 결과를 반환합니다.")
            return self._fallback_search(query, limit)
        
        try:
            # 1. 임베딩 기반 유사도 검색
            query_embedding = await self.embed_text(query)
            if not query_embedding:
                return self._fallback_search(query, limit)
            
            doc_embeddings = await self.embed_documents(documents)
            if not doc_embeddings:
                return self._fallback_search(query, limit)
            
            # 코사인 유사도 계산
            similarities = []
            query_vec = np.array(query_embedding)
            
            for i, doc_embedding in enumerate(doc_embeddings):
                doc_vec = np.array(doc_embedding)
                similarity = np.dot(query_vec, doc_vec)  # 정규화된 벡터이므로 내적이 코사인 유사도
                similarities.append((i, similarity, documents[i]))
            
            # 유사도 순으로 정렬
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_results = similarities[:min(limit * 2, len(similarities))]  # 리랭킹을 위해 더 많이 선택
            
            # 2. 리랭킹 (사용 가능한 경우)
            if self.is_reranker_available() and len(top_results) > 1:
                reranked_results = await self._rerank_documents(query, top_results)
                final_results = reranked_results[:limit]
            else:
                final_results = top_results[:limit]
            
            # 결과 포맷팅
            formatted_results = []
            for i, (doc_idx, score, document) in enumerate(final_results):
                formatted_results.append({
                    "document": document,
                    "score": float(score),
                    "rank": i + 1,
                    "source": "huggingface_embedding_search",
                    "metadata": {
                        "type": "embedding",
                        "doc_index": doc_idx,
                        "reranked": self.is_reranker_available()
                    }
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"문서 검색 실패: {str(e)}")
            return self._fallback_search(query, limit)
    
    async def _rerank_documents(self, query: str, results: List[Tuple[int, float, str]]) -> List[Tuple[int, float, str]]:
        """리랭커를 사용하여 검색 결과 재정렬"""
        try:
            # 쿼리-문서 쌍 생성
            query_doc_pairs = [(query, result[2]) for result in results]
            
            # 리랭킹 점수 계산
            rerank_scores = self.reranker_model.predict(query_doc_pairs)
            
            # 결과 재정렬
            reranked_results = []
            for i, (doc_idx, _, document) in enumerate(results):
                reranked_results.append((doc_idx, float(rerank_scores[i]), document))
            
            # 리랭킹 점수 순으로 정렬
            reranked_results.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"리랭킹 완료: {len(reranked_results)}개 문서 재정렬")
            return reranked_results
            
        except Exception as e:
            logger.error(f"리랭킹 실패: {str(e)}")
            return results
    
    def _fallback_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """임베딩 없이 기본 검색 결과 반환"""
        fallback_results = [
            {
                "document": f"기본 검색 결과: '{query}'와 관련된 문서입니다.",
                "score": 0.7,
                "rank": 1,
                "source": "fallback_search",
                "metadata": {"type": "fallback"}
            }
        ]
        return fallback_results[:limit]
    
    async def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        embedding_info = {}
        reranker_info = {}
        
        if self.embedding_model:
            try:
                embedding_info = {
                    "model_id": settings.embedding_model_id,
                    "max_seq_length": getattr(self.embedding_model, 'max_seq_length', 'unknown'),
                    "embedding_dimension": self.embedding_model.get_sentence_embedding_dimension()
                }
            except Exception as e:
                embedding_info = {"error": str(e)}
        
        if self.reranker_model:
            try:
                reranker_info = {
                    "model_id": settings.reranker_model_id,
                    "model_type": "CrossEncoder"
                }
            except Exception as e:
                reranker_info = {"error": str(e)}
        
        return {
            "service_name": "HuggingFace EmbeddingService",
            "embedding_model": embedding_info,
            "reranker_model": reranker_info,
            "model_loaded": self.model_loaded,
            "reranker_loaded": self.reranker_loaded,
            "available": self.is_available()
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환 (호환성 유지)"""
        return {
            "service_name": "HuggingFace EmbeddingService",
            "model_loaded": self.model_loaded,
            "reranker_loaded": self.reranker_loaded,
            "embedding_model_id": settings.embedding_model_id,
            "reranker_model_id": settings.reranker_model_id,
            "available": self.is_available()
        } 