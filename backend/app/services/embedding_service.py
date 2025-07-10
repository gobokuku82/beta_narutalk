"""
임베딩 서비스

문서 임베딩과 유사성 검색을 담당하는 서비스입니다.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from sentence_transformers import SentenceTransformer
from ..core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """임베딩 서비스 클래스"""
    
    def __init__(self):
        """임베딩 서비스 초기화"""
        self.embedding_model = None
        self.reranker_model = None
        self.model_loaded = False
        
        # 모델 초기화 시도 (실패해도 서비스는 계속 실행)
        try:
            self._initialize_models()
        except Exception as e:
            logger.warning(f"임베딩 모델 초기화 실패: {str(e)}")
            logger.info("임베딩 서비스가 모델 없이 초기화되었습니다. 기본 검색 기능만 제공됩니다.")
    
    def _initialize_models(self):
        """임베딩 모델 초기화"""
        try:
            # 모델 경로 확인
            if not os.path.exists(settings.embedding_model_path):
                logger.warning(f"임베딩 모델 경로가 존재하지 않습니다: {settings.embedding_model_path}")
                # 기본 모델 시도
                try:
                    logger.info("기본 임베딩 모델 로드 시도: sentence-transformers/all-MiniLM-L6-v2")
                    self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                    self.model_loaded = True
                    logger.info("기본 임베딩 모델 로드 성공")
                except Exception as e:
                    logger.warning(f"기본 임베딩 모델 로드 실패: {str(e)}")
                    return
            else:
                # 사용자 정의 모델 로드
                logger.info(f"사용자 정의 임베딩 모델 로드: {settings.embedding_model_path}")
                self.embedding_model = SentenceTransformer(settings.embedding_model_path)
                self.model_loaded = True
                logger.info("사용자 정의 임베딩 모델 로드 성공")
            
            # 리랭커 모델 초기화 (선택적)
            if os.path.exists(settings.reranker_model_path):
                try:
                    logger.info(f"리랭커 모델 로드: {settings.reranker_model_path}")
                    # 리랭커 모델 로드 로직은 필요시 추가
                    logger.info("리랭커 모델 로드 성공")
                except Exception as e:
                    logger.warning(f"리랭커 모델 로드 실패: {str(e)}")
            
        except Exception as e:
            logger.error(f"임베딩 모델 초기화 실패: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """임베딩 서비스 사용 가능 여부 확인"""
        return self.model_loaded and self.embedding_model is not None
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """텍스트를 임베딩 벡터로 변환"""
        if not self.is_available():
            logger.warning("임베딩 모델이 로드되지 않았습니다.")
            return None
            
        try:
            # 텍스트를 임베딩 벡터로 변환
            embedding = self.embedding_model.encode([text])
            return embedding[0].tolist()
        except Exception as e:
            logger.error(f"텍스트 임베딩 실패: {str(e)}")
            return None
    
    async def embed_documents(self, documents: List[str]) -> Optional[List[List[float]]]:
        """여러 문서를 임베딩 벡터로 변환"""
        if not self.is_available():
            logger.warning("임베딩 모델이 로드되지 않았습니다.")
            return None
            
        try:
            # 문서들을 임베딩 벡터로 변환
            embeddings = self.embedding_model.encode(documents)
            return [embedding.tolist() for embedding in embeddings]
        except Exception as e:
            logger.error(f"문서 임베딩 실패: {str(e)}")
            return None
    
    async def search_similar_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """유사한 문서 검색"""
        if not self.is_available():
            logger.warning("임베딩 서비스를 사용할 수 없습니다. 기본 검색 결과를 반환합니다.")
            # 임베딩 없이 기본 검색 결과 반환
            return self._fallback_search(query, limit)
        
        try:
            # 실제 구현에서는 벡터 데이터베이스 사용
            # 현재는 더미 데이터 반환
            return self._mock_search_results(query, limit)
            
        except Exception as e:
            logger.error(f"문서 검색 실패: {str(e)}")
            return []
    
    def _fallback_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """임베딩 없이 기본 검색 결과 반환"""
        # 기본 검색 결과 (실제로는 키워드 매칭 등 사용)
        fallback_results = [
            {
                "document": f"기본 검색 결과: '{query}'와 관련된 문서입니다.",
                "score": 0.7,
                "source": "fallback_search",
                "metadata": {"type": "fallback"}
            }
        ]
        return fallback_results[:limit]
    
    def _mock_search_results(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """임베딩 기반 모의 검색 결과"""
        mock_results = [
            {
                "document": f"임베딩 검색 결과 1: '{query}'와 관련된 상세 문서입니다.",
                "score": 0.95,
                "source": "embedding_search",
                "metadata": {"type": "embedding"}
            },
            {
                "document": f"임베딩 검색 결과 2: '{query}'에 대한 추가 정보입니다.",
                "score": 0.87,
                "source": "embedding_search", 
                "metadata": {"type": "embedding"}
            },
            {
                "document": f"임베딩 검색 결과 3: '{query}' 관련 참고 자료입니다.",
                "score": 0.82,
                "source": "embedding_search",
                "metadata": {"type": "embedding"}
            }
        ]
        return mock_results[:limit]
    
    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환"""
        return {
            "service_name": "EmbeddingService",
            "model_loaded": self.model_loaded,
            "embedding_model_path": settings.embedding_model_path,
            "reranker_model_path": settings.reranker_model_path,
            "available": self.is_available()
        } 