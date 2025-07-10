"""
문서검색 에이전트 데이터베이스

문서 검색을 위한 데이터베이스 접근 로직을 담당합니다.
벡터DB, 정형DB, 비정형DB를 통합 관리합니다.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from .config import DocumentSearchConfig

logger = logging.getLogger(__name__)

class DocumentSearchDatabase:
    """문서검색 전용 데이터베이스 관리 클래스"""
    
    def __init__(self, config: DocumentSearchConfig):
        self.config = config
        self.embedding_service = None
        self.database_service = None
        
    def set_services(self, embedding_service=None, database_service=None, **kwargs):
        """서비스 의존성 주입"""
        self.embedding_service = embedding_service
        self.database_service = database_service
    
    async def search_all_sources(self, query: str, source_type: str = "all") -> List[Dict[str, Any]]:
        """모든 데이터 소스에서 통합 검색"""
        all_results = []
        
        try:
            # 검색 소스별 병렬 검색
            if source_type in ["all", "internal"]:
                internal_results = await self.search_internal_documents(query)
                all_results.extend(internal_results)
            
            if source_type in ["all", "external"]:
                external_results = await self.search_external_documents(query)
                all_results.extend(external_results)
            
            # 결과 정렬 및 중복 제거
            ranked_results = await self.rank_and_deduplicate(all_results, query)
            
            return ranked_results[:self.config.max_search_results]
            
        except Exception as e:
            logger.error(f"통합 검색 실패: {str(e)}")
            return []
    
    async def search_internal_documents(self, query: str) -> List[Dict[str, Any]]:
        """내부 문서 검색"""
        results = []
        
        try:
            # 1. 벡터DB 검색 (의미 기반)
            vector_results = await self.search_vector_documents(query, "internal")
            for result in vector_results:
                result["search_type"] = "vector"
                result["source_category"] = "internal"
                result["weight"] = self.config.vector_search_weight
            results.extend(vector_results)
            
            # 2. 정형DB 검색 (메타데이터)
            structured_results = await self.search_structured_metadata(query, "internal")
            for result in structured_results:
                result["search_type"] = "structured"
                result["source_category"] = "internal"
                result["weight"] = self.config.structured_search_weight
            results.extend(structured_results)
            
            # 3. 비정형DB 검색 (텍스트 매칭)
            unstructured_results = await self.search_unstructured_content(query, "internal")
            for result in unstructured_results:
                result["search_type"] = "unstructured"
                result["source_category"] = "internal"
                result["weight"] = self.config.unstructured_search_weight
            results.extend(unstructured_results)
            
            logger.info(f"내부 문서 검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"내부 문서 검색 실패: {str(e)}")
            return []
    
    async def search_external_documents(self, query: str) -> List[Dict[str, Any]]:
        """외부 문서 검색"""
        results = []
        
        try:
            # 외부 문서 소스별 검색
            for source in self.config.external_document_sources:
                source_results = await self.search_external_source(query, source)
                for result in source_results:
                    result["source_category"] = "external"
                    result["external_source"] = source
                results.extend(source_results)
            
            logger.info(f"외부 문서 검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"외부 문서 검색 실패: {str(e)}")
            return []
    
    async def search_vector_documents(self, query: str, category: str) -> List[Dict[str, Any]]:
        """벡터 데이터베이스 검색"""
        try:
            if not self.embedding_service:
                return []
            
            # 문서 목록 가져오기
            documents = await self.get_category_documents(category)
            if not documents:
                return []
            
            # 임베딩 기반 유사도 검색
            results = await self.embedding_service.search_similar_documents(
                query, documents, limit=self.config.max_search_results
            )
            
            # 결과 포맷팅
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("document", ""),
                    "score": result.get("score", 0.0),
                    "rank": result.get("rank", 0),
                    "source": "vector_db",
                    "metadata": result.get("metadata", {})
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"벡터DB 검색 실패: {str(e)}")
            return []
    
    async def search_structured_metadata(self, query: str, category: str) -> List[Dict[str, Any]]:
        """정형 데이터베이스에서 문서 메타데이터 검색"""
        try:
            if not self.database_service:
                return []
            
            # 문서 메타데이터 테이블 검색
            results = []
            
            # 예시: 문서 정보 테이블에서 검색
            # (실제 구현에서는 문서 메타데이터 테이블 구조에 맞게 수정)
            metadata_results = await self.search_document_metadata(query)
            
            for metadata in metadata_results:
                results.append({
                    "content": metadata.get("title", ""),
                    "score": 0.8,  # 메타데이터 매칭 점수
                    "source": "structured_db",
                    "metadata": metadata
                })
            
            return results
            
        except Exception as e:
            logger.error(f"정형DB 검색 실패: {str(e)}")
            return []
    
    async def search_unstructured_content(self, query: str, category: str) -> List[Dict[str, Any]]:
        """비정형 데이터베이스에서 문서 내용 검색"""
        try:
            if not self.database_service:
                return []
            
            # 회사 문서에서 키워드 검색
            documents = await self.database_service.get_company_documents()
            results = []
            
            for doc in documents:
                if query.lower() in doc.lower():
                    # 간단한 텍스트 매칭 점수 계산
                    score = doc.lower().count(query.lower()) / len(doc.split()) * 10
                    score = min(score, 1.0)  # 최대 1.0으로 제한
                    
                    results.append({
                        "content": doc,
                        "score": score,
                        "source": "unstructured_db",
                        "metadata": {"type": "company_document"}
                    })
            
            # 점수 순으로 정렬
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:self.config.max_search_results]
            
        except Exception as e:
            logger.error(f"비정형DB 검색 실패: {str(e)}")
            return []
    
    async def search_external_source(self, query: str, source: str) -> List[Dict[str, Any]]:
        """특정 외부 소스에서 검색"""
        try:
            # 외부 소스별 검색 로직 (향후 확장)
            results = []
            
            if source == "industry_reports":
                results = await self.search_industry_reports(query)
            elif source == "market_research":
                results = await self.search_market_research(query)
            elif source == "news":
                results = await self.search_news_articles(query)
            elif source == "regulations":
                results = await self.search_regulations(query)
            
            return results
            
        except Exception as e:
            logger.error(f"외부 소스 검색 실패 ({source}): {str(e)}")
            return []
    
    async def get_category_documents(self, category: str) -> List[str]:
        """카테고리별 문서 목록 가져오기"""
        try:
            if category == "internal":
                return await self.database_service.get_company_documents()
            elif category == "external":
                # 외부 문서 목록 (향후 구현)
                return []
            else:
                return []
        except Exception as e:
            logger.error(f"카테고리 문서 조회 실패: {str(e)}")
            return []
    
    async def search_document_metadata(self, query: str) -> List[Dict[str, Any]]:
        """문서 메타데이터 검색 (향후 구현)"""
        return []
    
    async def search_industry_reports(self, query: str) -> List[Dict[str, Any]]:
        """산업 보고서 검색 (향후 구현)"""
        return []
    
    async def search_market_research(self, query: str) -> List[Dict[str, Any]]:
        """시장 조사 자료 검색 (향후 구현)"""
        return []
    
    async def search_news_articles(self, query: str) -> List[Dict[str, Any]]:
        """뉴스 기사 검색 (향후 구현)"""
        return []
    
    async def search_regulations(self, query: str) -> List[Dict[str, Any]]:
        """규정/법규 검색 (향후 구현)"""
        return []
    
    async def rank_and_deduplicate(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """검색 결과 순위 매기기 및 중복 제거"""
        try:
            # 가중치가 적용된 점수 계산
            for result in results:
                original_score = result.get("score", 0.0)
                weight = result.get("weight", 1.0)
                result["final_score"] = original_score * weight
            
            # 최종 점수 순으로 정렬
            results.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
            
            # 중복 제거 (내용 기반)
            seen_content = set()
            unique_results = []
            
            for result in results:
                content_hash = hash(result.get("content", "")[:100])  # 첫 100자로 중복 판단
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append(result)
            
            return unique_results
            
        except Exception as e:
            logger.error(f"결과 순위 매기기 실패: {str(e)}")
            return results 