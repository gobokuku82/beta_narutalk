"""
문서 검색 에이전트 - 문서 검색 및 임베딩 처리
포트: 8002
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Document Agent",
    description="문서 검색 및 임베딩 처리 에이전트",
    version="1.0.0"
)

# 요청/응답 모델
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_results: int
    processing_time: float
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


# 모의 문서 데이터 (실제로는 ChromaDB 사용)
MOCK_DOCUMENTS = [
    {
        "id": "doc1",
        "title": "좋은제약 윤리강령",
        "content": "좋은제약은 윤리적 경영을 통해 사회적 책임을 다하겠습니다.",
        "type": "policy",
        "relevance": 0.9
    },
    {
        "id": "doc2",
        "title": "좋은제약 복리후생 규정",
        "content": "직원들의 복리후생을 위한 다양한 제도를 운영하고 있습니다.",
        "type": "benefit",
        "relevance": 0.8
    },
    {
        "id": "doc3",
        "title": "좋은제약 행동강령",
        "content": "모든 직원이 준수해야 할 행동 기준을 정의합니다.",
        "type": "conduct",
        "relevance": 0.7
    },
    {
        "id": "doc4",
        "title": "좋은제약 자율준수 관리규정",
        "content": "법규 준수를 위한 자율적인 관리 체계를 구축합니다.",
        "type": "compliance",
        "relevance": 0.85
    }
]


def search_documents(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """문서 검색 함수"""
    query_lower = query.lower()
    
    # 간단한 키워드 매칭 (실제로는 벡터 유사도 검색)
    results = []
    for doc in MOCK_DOCUMENTS:
        score = 0.0
        
        # 제목에서 키워드 검색
        if any(keyword in doc['title'].lower() for keyword in query_lower.split()):
            score += 0.3
        
        # 내용에서 키워드 검색
        if any(keyword in doc['content'].lower() for keyword in query_lower.split()):
            score += 0.2
        
        # 기본 관련성 점수
        score += doc['relevance'] * 0.5
        
        if score > 0:
            result = doc.copy()
            result['score'] = score
            results.append(result)
    
    # 점수 기준으로 정렬
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results[:top_k]


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """문서 검색"""
    try:
        logger.info(f"Searching documents for: {request.query}")
        
        start_time = datetime.now()
        
        # 문서 검색
        results = search_documents(request.query, request.top_k)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = SearchResponse(
            results=results,
            total_results=len(results),
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Search completed: {len(results)} results found")
        return response
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents():
    """문서 목록 조회"""
    return {
        "documents": MOCK_DOCUMENTS,
        "total": len(MOCK_DOCUMENTS),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크"""
    return HealthResponse(
        status="healthy",
        service="document_agent",
        timestamp=datetime.now().isoformat(),
        details={
            "port": 8002,
            "version": "1.0.0",
            "capabilities": ["document_search", "text_embedding"],
            "document_count": len(MOCK_DOCUMENTS)
        }
    )


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "document_agent",
        "description": "문서 검색 및 임베딩 처리 에이전트",
        "version": "1.0.0",
        "endpoints": {
            "search": "/search",
            "documents": "/documents",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) 