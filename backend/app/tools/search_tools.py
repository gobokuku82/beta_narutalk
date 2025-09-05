"""
Search Tools
검색 관련 도구들
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import logging
logger = logging.getLogger(__name__)
import time
import random

from app.core.config import settings
from .base import BaseTool, ToolResult, StructuredTool, CachedTool


class VectorSearchInput(BaseModel):
    """벡터 검색 입력"""
    query: str = Field(description="검색 쿼리")
    k: int = Field(default=5, description="반환할 결과 개수")
    filter: Optional[Dict] = Field(None, description="메타데이터 필터")


class LiteratureSearchInput(BaseModel):
    """문헌 검색 입력"""
    topic: str = Field(description="검색할 주제")
    year_from: Optional[int] = Field(None, description="시작 연도")
    year_to: Optional[int] = Field(None, description="종료 연도")
    journal: Optional[str] = Field(None, description="특정 저널명")


class WebSearchInput(BaseModel):
    """웹 검색 입력"""
    query: str = Field(description="검색 쿼리")
    site: Optional[str] = Field(None, description="특정 사이트 제한")
    num_results: int = Field(default=10, description="결과 개수")


class VectorSearchTool(StructuredTool, CachedTool):
    """벡터 데이터베이스 검색 도구"""
    
    name: str = "vector_search"
    description: str = "벡터 데이터베이스에서 유사한 문서를 검색합니다."
    args_schema: type[BaseModel] = VectorSearchInput
    cache_ttl: int = 600  # 10분 캐싱
    
    def __init__(self):
        super().__init__()
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.vector_store = self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """벡터 스토어 초기화"""
        try:
            vector_store = Chroma(
                persist_directory=str(settings.VECTOR_DB_DIR),
                embedding_function=self.embeddings,
                collection_name="pharma_knowledge"
            )
            
            # 샘플 데이터 확인
            if vector_store._collection.count() == 0:
                self._load_sample_documents(vector_store)
            
            return vector_store
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            return None
    
    def _load_sample_documents(self, vector_store):
        """샘플 문서 로드"""
        sample_docs = [
            Document(
                page_content="SGLT2 억제제는 제2형 당뇨병 치료제로 심혈관 및 신장 보호 효과가 입증되었습니다.",
                metadata={"type": "clinical", "year": 2024}
            ),
            Document(
                page_content="GLP-1 수용체 작용제는 체중 감소와 혈당 조절에 효과적입니다.",
                metadata={"type": "clinical", "year": 2024}
            ),
            Document(
                page_content="면역항암제 병용요법이 진행성 암 환자의 생존율을 향상시켰습니다.",
                metadata={"type": "oncology", "year": 2024}
            ),
            Document(
                page_content="새로운 알츠하이머 치료제가 FDA 승인을 받았습니다.",
                metadata={"type": "neurology", "year": 2024}
            ),
            Document(
                page_content="CAR-T 세포 치료가 혈액암 치료에 혁신을 가져왔습니다.",
                metadata={"type": "oncology", "year": 2023}
            )
        ]
        
        vector_store.add_documents(sample_docs)
        logger.info(f"Added {len(sample_docs)} sample documents to vector store")
    
    async def _execute(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """실제 벡터 검색 실행"""
        start_time = time.time()
        
        try:
            if not self.vector_store:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Vector store not initialized",
                    execution_time=time.time() - start_time,
                    tool_name=self.name
                )
            
            # 유사도 검색
            results = self.vector_store.similarity_search_with_score(query, k=5)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "count": len(formatted_results),
                    "results": formatted_results
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    async def _arun(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """벡터 검색 실행 (캐싱 사용)"""
        # CachedTool의 _arun이 _execute를 호출
        return await super()._arun(query, run_manager)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class LiteratureSearchTool(StructuredTool):
    """학술 문헌 검색 도구"""
    
    name: str = "literature_search"
    description: str = "PubMed, Google Scholar 등에서 학술 문헌을 검색합니다."
    args_schema: type[BaseModel] = LiteratureSearchInput
    
    async def _arun(
        self,
        topic: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        journal: Optional[str] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """문헌 검색 실행"""
        start_time = time.time()
        
        try:
            # Mock 문헌 데이터 생성
            mock_papers = [
                {
                    "title": f"Effects of {topic} on Patient Outcomes: A Systematic Review",
                    "authors": ["Kim J", "Lee S", "Park H"],
                    "journal": journal or "New England Journal of Medicine",
                    "year": year_to or 2024,
                    "abstract": f"This systematic review examines the effects of {topic} on various patient outcomes...",
                    "doi": f"10.1056/NEJMoa{random.randint(100000, 999999)}",
                    "citations": random.randint(10, 500)
                },
                {
                    "title": f"Meta-analysis of {topic} in Clinical Practice",
                    "authors": ["Smith A", "Johnson B"],
                    "journal": journal or "The Lancet",
                    "year": year_to or 2024,
                    "abstract": f"A comprehensive meta-analysis of {topic} studies from the past decade...",
                    "doi": f"10.1016/S0140-6736({random.randint(20, 24)}){random.randint(10000, 99999)}-{random.randint(0, 9)}",
                    "citations": random.randint(50, 300)
                },
                {
                    "title": f"Recent Advances in {topic} Research",
                    "authors": ["Chen L", "Wang M"],
                    "journal": journal or "Nature Medicine",
                    "year": year_from or 2023,
                    "abstract": f"Recent developments in {topic} have shown promising results...",
                    "doi": f"10.1038/nm.{random.randint(1000, 9999)}",
                    "citations": random.randint(20, 150)
                }
            ]
            
            # 연도 필터 적용
            if year_from:
                mock_papers = [p for p in mock_papers if p["year"] >= year_from]
            if year_to:
                mock_papers = [p for p in mock_papers if p["year"] <= year_to]
            
            return ToolResult(
                success=True,
                data={
                    "topic": topic,
                    "count": len(mock_papers),
                    "papers": mock_papers,
                    "search_params": {
                        "year_from": year_from,
                        "year_to": year_to,
                        "journal": journal
                    }
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class WebSearchTool(StructuredTool):
    """웹 검색 도구"""
    
    name: str = "web_search"
    description: str = "웹에서 최신 정보를 검색합니다. 의학 뉴스, FDA 공지, 임상시험 정보 등을 찾을 수 있습니다."
    args_schema: type[BaseModel] = WebSearchInput
    
    async def _arun(
        self,
        query: str,
        site: Optional[str] = None,
        num_results: int = 10,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """웹 검색 실행"""
        start_time = time.time()
        
        try:
            # Mock 웹 검색 결과
            mock_results = []
            
            # 사이트별 템플릿
            site_templates = {
                "fda.gov": {
                    "prefix": "FDA",
                    "type": "regulatory"
                },
                "clinicaltrials.gov": {
                    "prefix": "ClinicalTrials",
                    "type": "clinical_trial"
                },
                "pubmed.ncbi.nlm.nih.gov": {
                    "prefix": "PubMed",
                    "type": "research"
                },
                "who.int": {
                    "prefix": "WHO",
                    "type": "global_health"
                }
            }
            
            # 결과 생성
            for i in range(min(num_results, 10)):
                if site and site in site_templates:
                    template = site_templates[site]
                    title = f"{template['prefix']}: {query} - Result {i+1}"
                    url = f"https://{site}/search?q={query.replace(' ', '+')}&page={i+1}"
                    result_type = template['type']
                else:
                    # 랜덤 사이트 선택
                    random_site = random.choice(list(site_templates.keys()))
                    template = site_templates[random_site]
                    title = f"{template['prefix']}: {query} - Result {i+1}"
                    url = f"https://{random_site}/search?q={query.replace(' ', '+')}"
                    result_type = template['type']
                
                mock_results.append({
                    "title": title,
                    "url": url,
                    "snippet": f"...relevant information about {query}. This result contains important details about the topic including recent updates and guidelines...",
                    "type": result_type,
                    "date": f"2024-0{random.randint(1, 9)}-{random.randint(10, 28)}"
                })
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "site": site,
                    "count": len(mock_results),
                    "results": mock_results
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class SemanticSearchTool(BaseTool):
    """의미 기반 검색 도구"""
    
    name: str = "semantic_search"
    description: str = "자연어 쿼리를 이해하여 가장 관련성 높은 정보를 검색합니다."
    
    def __init__(self):
        super().__init__()
        self.vector_tool = VectorSearchTool()
        self.literature_tool = LiteratureSearchTool()
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """의미 검색 실행"""
        start_time = time.time()
        
        try:
            # 벡터 검색과 문헌 검색 병렬 실행
            import asyncio
            
            vector_task = self.vector_tool._execute(query)
            literature_task = self.literature_tool._arun(query)
            
            vector_result, literature_result = await asyncio.gather(
                vector_task, literature_task
            )
            
            # 결과 통합
            combined_data = {
                "query": query,
                "vector_search": vector_result.data if vector_result.success else None,
                "literature_search": literature_result.data if literature_result.success else None,
                "combined_count": (
                    (vector_result.data.get("count", 0) if vector_result.success else 0) +
                    (literature_result.data.get("count", 0) if literature_result.success else 0)
                )
            }
            
            return ToolResult(
                success=True,
                data=combined_data,
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


# Tool 레지스트리에 등록
def register_search_tools():
    """모든 검색 도구를 레지스트리에 등록"""
    from .base import tool_registry
    
    tools = [
        (VectorSearchTool(), "search"),
        (LiteratureSearchTool(), "search"),
        (WebSearchTool(), "search"),
        (SemanticSearchTool(), "search")
    ]
    
    for tool, category in tools:
        tool_registry.register(tool, category)
    
    logger.info(f"Registered {len(tools)} search tools")