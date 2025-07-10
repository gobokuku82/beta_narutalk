"""
문서검색 에이전트 설정

문서 검색과 관련된 모든 설정을 관리합니다.
"""

from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class DocumentSearchConfig:
    """문서검색 에이전트 설정"""
    
    # 기본 설정
    agent_name: str = "document_search_agent"
    max_search_results: int = 10
    confidence_threshold: float = 0.6
    
    # 검색 소스 우선순위
    search_priority: List[str] = None
    
    # 지원하는 문서 유형
    supported_document_types: List[str] = None
    
    # 검색 가중치
    vector_search_weight: float = 0.5
    structured_search_weight: float = 0.3
    unstructured_search_weight: float = 0.2
    
    # 내부/외부 문서 설정
    internal_document_sources: List[str] = None
    external_document_sources: List[str] = None
    
    def __post_init__(self):
        if self.search_priority is None:
            self.search_priority = ["vector_db", "structured_db", "unstructured_db"]
        
        if self.supported_document_types is None:
            self.supported_document_types = [
                "pdf", "docx", "txt", "md", "html", 
                "excel", "ppt", "hwp", "json", "xml"
            ]
        
        if self.internal_document_sources is None:
            self.internal_document_sources = [
                "company_documents", "policies", "procedures", 
                "regulations", "manuals", "reports"
            ]
        
        if self.external_document_sources is None:
            self.external_document_sources = [
                "industry_reports", "market_research", "news", 
                "regulations", "patents", "academic_papers"
            ]

# 기본 설정 인스턴스
default_config = DocumentSearchConfig() 