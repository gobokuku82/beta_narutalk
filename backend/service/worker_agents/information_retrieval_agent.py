"""
Information Retrieval Agent
정보 검색 에이전트 - 다양한 소스에서 정보 검색
"""

from typing import Dict, Any, List, Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import httpx
import asyncio
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """검색 요청"""
    
    query: str
    search_type: Literal[
        "hr",              # 인사정보
        "regulation",      # 규정
        "region",          # 지역정보
        "web",            # 웹검색
        "paper",          # 논문
        "hira",           # 심평원
        "multi"           # 다중 검색
    ]
    filters: Dict[str, Any] = Field(default_factory=dict)
    max_results: int = 10
    date_range: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """검색 결과"""
    
    source_type: str
    source_name: str
    title: str
    content: str
    relevance_score: float
    metadata: Dict[str, Any]
    url: Optional[str] = None
    timestamp: str


class InformationSearchResponse(BaseModel):
    """정보 검색 응답"""
    
    search_id: str
    query: str
    total_results: int
    results: List[SearchResult]
    aggregated_summary: Optional[str] = None
    search_metadata: Dict[str, Any]


class BaseSearcher(ABC):
    """검색기 베이스 클래스"""
    
    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """검색 실행"""
        pass


class HRSearcher(BaseSearcher):
    """인사정보 검색기"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
    
    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """인사정보 검색"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/search/hr",
                    json={
                        "query": query,
                        "filters": kwargs.get("filters", {})
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("results", []):
                        results.append(SearchResult(
                            source_type="hr",
                            source_name="인사정보DB",
                            title=item.get("name", ""),
                            content=self._format_hr_info(item),
                            relevance_score=item.get("score", 0.5),
                            metadata=item,
                            timestamp=datetime.now().isoformat()
                        ))
                    
                    return results
                    
            except Exception as e:
                logger.error(f"HR search error: {e}")
                return []
    
    def _format_hr_info(self, data: Dict) -> str:
        """인사정보 포맷팅"""
        
        return f"""
        이름: {data.get('name', '')}
        부서: {data.get('department', '')}
        직급: {data.get('position', '')}
        연락처: {data.get('contact', '')}
        담당지역: {data.get('region', '')}
        """


class RegulationSearcher(BaseSearcher):
    """규정 검색기"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
    
    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """규정 검색"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/search/regulations",
                    json={"query": query},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("results", []):
                        results.append(SearchResult(
                            source_type="regulation",
                            source_name=item.get("regulation_type", "내부규정"),
                            title=item.get("title", ""),
                            content=item.get("content", ""),
                            relevance_score=item.get("relevance", 0.5),
                            metadata={
                                "article": item.get("article"),
                                "effective_date": item.get("effective_date"),
                                "category": item.get("category")
                            },
                            timestamp=datetime.now().isoformat()
                        ))
                    
                    return results
                    
            except Exception as e:
                logger.error(f"Regulation search error: {e}")
                return []


class WebSearcher(BaseSearcher):
    """웹 검색기 (네이버, 구글, 다음)"""
    
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
    
    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """웹 검색 (멀티 소스)"""
        
        search_engines = kwargs.get("engines", ["naver", "google"])
        
        tasks = []
        if "naver" in search_engines:
            tasks.append(self._search_naver(query))
        if "google" in search_engines:
            tasks.append(self._search_google(query))
        if "daum" in search_engines:
            tasks.append(self._search_daum(query))
        
        if tasks:
            results_lists = await asyncio.gather(*tasks)
            # 결과 통합
            all_results = []
            for results in results_lists:
                all_results.extend(results)
            
            # 관련도 순으로 정렬
            all_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return all_results[:kwargs.get("max_results", 10)]
        
        return []
    
    async def _search_naver(self, query: str) -> List[SearchResult]:
        """네이버 검색"""
        
        # 실제로는 네이버 API 호출
        # 여기서는 모의 구현
        
        return [
            SearchResult(
                source_type="web",
                source_name="Naver",
                title=f"네이버 검색 결과: {query}",
                content="네이버에서 검색된 내용입니다...",
                relevance_score=0.8,
                metadata={},
                url="https://naver.com",
                timestamp=datetime.now().isoformat()
            )
        ]
    
    async def _search_google(self, query: str) -> List[SearchResult]:
        """구글 검색"""
        
        # 실제로는 Google Custom Search API 호출
        
        return [
            SearchResult(
                source_type="web",
                source_name="Google",
                title=f"Google 검색 결과: {query}",
                content="구글에서 검색된 내용입니다...",
                relevance_score=0.85,
                metadata={},
                url="https://google.com",
                timestamp=datetime.now().isoformat()
            )
        ]
    
    async def _search_daum(self, query: str) -> List[SearchResult]:
        """다음 검색"""
        
        return [
            SearchResult(
                source_type="web",
                source_name="Daum",
                title=f"다음 검색 결과: {query}",
                content="다음에서 검색된 내용입니다...",
                relevance_score=0.75,
                metadata={},
                url="https://daum.net",
                timestamp=datetime.now().isoformat()
            )
        ]


class PaperSearcher(BaseSearcher):
    """논문 검색기"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
    
    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """의료 논문 검색"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/search/papers",
                    json={
                        "query": query,
                        "filters": {
                            "year_from": kwargs.get("year_from", 2020),
                            "peer_reviewed": True
                        }
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for paper in data.get("papers", []):
                        results.append(SearchResult(
                            source_type="paper",
                            source_name="Medical Papers DB",
                            title=paper.get("title", ""),
                            content=paper.get("abstract", ""),
                            relevance_score=paper.get("relevance", 0.5),
                            metadata={
                                "authors": paper.get("authors"),
                                "journal": paper.get("journal"),
                                "year": paper.get("year"),
                                "doi": paper.get("doi")
                            },
                            url=paper.get("url"),
                            timestamp=datetime.now().isoformat()
                        ))
                    
                    return results
                    
            except Exception as e:
                logger.error(f"Paper search error: {e}")
                return []


class HIRASearcher(BaseSearcher):
    """심평원 데이터 검색기"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
    
    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """심평원 데이터 검색"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/search/hira",
                    json={
                        "query": query,
                        "data_type": kwargs.get("data_type", "prescription")
                    },
                    timeout=20.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("results", []):
                        results.append(SearchResult(
                            source_type="hira",
                            source_name="심평원",
                            title=item.get("title", ""),
                            content=self._format_hira_data(item),
                            relevance_score=item.get("relevance", 0.5),
                            metadata=item,
                            url=item.get("reference_url"),
                            timestamp=datetime.now().isoformat()
                        ))
                    
                    return results
                    
            except Exception as e:
                logger.error(f"HIRA search error: {e}")
                return []
    
    def _format_hira_data(self, data: Dict) -> str:
        """심평원 데이터 포맷팅"""
        
        return f"""
        병원: {data.get('hospital', '')}
        처방 트렌드: {data.get('prescription_trend', '')}
        급여 변경사항: {data.get('reimbursement_changes', '')}
        통계 기간: {data.get('period', '')}
        """


class InformationRetrievalAgent:
    """
    정보 검색 에이전트
    여러 소스에서 정보를 검색하고 통합
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Initialize Information Retrieval Agent
        
        Args:
            api_base_url: FastAPI 서버 URL
        """
        
        self.api_base_url = api_base_url
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        
        # 검색기 초기화
        self.searchers = {
            "hr": HRSearcher(api_base_url),
            "regulation": RegulationSearcher(api_base_url),
            "web": WebSearcher({}),  # API 키는 환경변수에서 로드
            "paper": PaperSearcher(api_base_url),
            "hira": HIRASearcher(api_base_url)
        }
        
        # 검색 도구 초기화
        self.tools = self._initialize_search_tools()
    
    def _initialize_search_tools(self) -> Dict[str, Tool]:
        """검색 도구 초기화"""
        
        tools = {}
        
        for search_type, searcher in self.searchers.items():
            tools[search_type] = Tool(
                name=f"search_{search_type}",
                description=f"{search_type} 검색",
                func=searcher.search
            )
        
        # 통합 검색 도구
        tools["multi_search"] = Tool(
            name="multi_search",
            description="여러 소스에서 동시 검색",
            func=self._multi_source_search
        )
        
        # 요약 도구
        tools["summarize"] = Tool(
            name="summarize_results",
            description="검색 결과 요약",
            func=self._summarize_results
        )
        
        return tools
    
    async def search_information(
        self,
        request: SearchRequest
    ) -> InformationSearchResponse:
        """
        정보 검색 메인 메서드
        """
        
        logger.info(f"Searching for: {request.query} (type: {request.search_type})")
        
        # 검색 타입에 따른 처리
        if request.search_type == "multi":
            results = await self._multi_source_search(
                request.query,
                filters=request.filters,
                max_results=request.max_results
            )
        else:
            searcher = self.searchers.get(request.search_type)
            if not searcher:
                raise ValueError(f"Unknown search type: {request.search_type}")
            
            results = await searcher.search(
                request.query,
                filters=request.filters,
                max_results=request.max_results,
                date_range=request.date_range
            )
        
        # 결과 재순위화
        results = await self._rerank_results(results, request.query)
        
        # 요약 생성
        summary = await self._generate_summary(results, request.query)
        
        # 응답 구성
        response = InformationSearchResponse(
            search_id=self._generate_search_id(),
            query=request.query,
            total_results=len(results),
            results=results[:request.max_results],
            aggregated_summary=summary,
            search_metadata={
                "search_type": request.search_type,
                "timestamp": datetime.now().isoformat(),
                "filters": request.filters
            }
        )
        
        return response
    
    async def _multi_source_search(
        self,
        query: str,
        **kwargs
    ) -> List[SearchResult]:
        """다중 소스 검색"""
        
        # 쿼리 분석으로 관련 소스 결정
        relevant_sources = await self._determine_relevant_sources(query)
        
        # 병렬 검색 실행
        tasks = []
        for source in relevant_sources:
            if source in self.searchers:
                tasks.append(
                    self.searchers[source].search(query, **kwargs)
                )
        
        if tasks:
            results_lists = await asyncio.gather(*tasks)
            
            # 결과 통합
            all_results = []
            for results in results_lists:
                all_results.extend(results)
            
            # 중복 제거 및 정렬
            unique_results = self._deduplicate_results(all_results)
            unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return unique_results
        
        return []
    
    async def _determine_relevant_sources(self, query: str) -> List[str]:
        """쿼리에 적합한 소스 결정"""
        
        system_prompt = """쿼리를 분석하여 적합한 검색 소스를 결정하세요.
        
        가능한 소스:
        - hr: 직원, 인사 정보
        - regulation: 규정, 법규, 가이드라인
        - web: 일반 웹 정보, 뉴스, 트렌드
        - paper: 의학 논문, 연구 자료
        - hira: 심평원 데이터, 처방 트렌드, 급여 정보
        
        관련 소스만 JSON 배열로 반환하세요.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"쿼리: {query}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            sources = json.loads(content)
            return sources if isinstance(sources, list) else ["web"]
        except:
            # 기본값
            return ["web", "regulation"]
    
    async def _rerank_results(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """검색 결과 재순위화"""
        
        if len(results) <= 1:
            return results
        
        # LLM을 사용한 관련도 재평가
        system_prompt = """검색 결과의 관련도를 평가하세요.
        
        각 결과에 대해 0.0~1.0 사이의 점수를 부여하세요.
        쿼리와의 직접적인 관련성, 정보의 유용성, 신뢰도를 고려하세요.
        
        JSON 형식으로 점수 배열을 반환하세요.
        """
        
        # 결과 요약
        results_summary = []
        for i, result in enumerate(results[:10]):  # 상위 10개만
            results_summary.append(f"{i}: {result.title[:100]}")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
            쿼리: {query}
            
            검색 결과:
            {chr(10).join(results_summary)}
            """)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            scores = json.loads(content)
            
            # 점수 업데이트
            for i, score in enumerate(scores[:len(results)]):
                results[i].relevance_score = float(score)
            
            # 재정렬
            results.sort(key=lambda x: x.relevance_score, reverse=True)
        except:
            pass
        
        return results
    
    async def _generate_summary(
        self,
        results: List[SearchResult],
        query: str
    ) -> str:
        """검색 결과 요약 생성"""
        
        if not results:
            return "검색 결과가 없습니다."
        
        # 상위 결과 내용 추출
        top_contents = []
        for result in results[:5]:
            top_contents.append(f"[{result.source_name}] {result.content[:200]}")
        
        system_prompt = """검색 결과를 종합하여 핵심 정보를 요약하세요.
        
        요약은 다음을 포함해야 합니다:
        1. 주요 발견사항
        2. 공통적인 정보
        3. 출처별 특이사항
        
        3-5문장으로 작성하세요.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
            원본 쿼리: {query}
            
            검색 결과:
            {chr(10).join(top_contents)}
            """)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        return response.content
    
    async def _summarize_results(
        self,
        results: List[SearchResult]
    ) -> str:
        """결과 요약 도구"""
        
        return await self._generate_summary(results, "")
    
    def _deduplicate_results(
        self,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """중복 결과 제거"""
        
        seen = set()
        unique = []
        
        for result in results:
            # 제목과 소스로 중복 판단
            key = f"{result.title}_{result.source_name}"
            if key not in seen:
                seen.add(key)
                unique.append(result)
        
        return unique
    
    def _generate_search_id(self) -> str:
        """검색 ID 생성"""
        
        from uuid import uuid4
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"SEARCH_{timestamp}_{str(uuid4())[:8]}"


# === Graph Node Function ===

async def information_retrieval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Graph node for information retrieval
    """
    
    agent = InformationRetrievalAgent()
    
    # 검색 타입 결정
    search_type = state.get("search_type", "multi")
    
    # 검색 요청 구성
    request = SearchRequest(
        query=state.get("query", ""),
        search_type=search_type,
        filters=state.get("filters", {}),
        max_results=state.get("max_results", 10),
        date_range=state.get("date_range")
    )
    
    # 검색 실행
    response = await agent.search_information(request)
    
    # 상태 업데이트
    return {
        "search_results": response.dict(),
        "search_complete": True,
        "summary": response.aggregated_summary,
        "next_step": "complete"
    }
