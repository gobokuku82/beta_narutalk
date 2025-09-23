"""
    회사내부정보를 검색하는 sub-graph agent입니다.
        - 회사내부규정 ( chromadb ) : .\database\storage\hr_rules\chromadb\chroma.sqlite3
        - 회사인사정보 ( sqlite ) : .\database\storage\hr_information\hr_data
"""

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
import chromadb
from chromadb.config import Settings
import sqlite3
import asyncio
from pathlib import Path
import logging
from datetime import datetime
import torch

logger = logging.getLogger(__name__)

class SearchState(TypedDict):
    query: str
    search_type: str  # hr_info, hr_rules, both
    filters: Dict[str, Any]
    hr_results: List[Dict[str, Any]]
    rules_results: List[Dict[str, Any]]
    reranked_results: List[Dict[str, Any]]
    relevance_scores: Dict[str, float]
    sources: List[str]
    final_results: Dict[str, Any]
    execution_status: str

class SearchAgent:
    def __init__(self):
        self.workflow = StateGraph(SearchState)
        self._initialize_databases()
        self._build_graph()

    def _initialize_databases(self):
        """데이터베이스 초기화"""
        # ChromaDB 설정 (내부규정)
        self.hr_rules_path = Path("database/storage/hr_rules/chromadb")
        self.hr_rules_client = chromadb.PersistentClient(
            path=str(self.hr_rules_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )

        # SQLite 설정 (인사정보)
        self.hr_info_path = Path("database/storage/hr_information/hr_data.db")

        # 임베딩 모델 초기화 (Lazy loading)
        self.embedding_model = None
        self.embedding_model_path = 'models/kure_v1'

        # 리랭커 모델 초기화 (Lazy loading)
        self.reranker_model = None
        self.reranker_tokenizer = None
        self.reranker_model_path = 'models/bge-reranker-v2-m3-ko'

    def _load_embedding_model(self):
        """임베딩 모델을 lazy load (필요할 때만 로드)"""
        if self.embedding_model is None:
            try:
                logger.info("Loading embedding model (kure_v1)...")
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(self.embedding_model_path)
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
                self.embedding_model = False  # False로 설정하여 재시도 방지
        return self.embedding_model

    def _load_reranker_model(self):
        """리랭커 모델을 lazy load (필요할 때만 로드)"""
        if self.reranker_model is None:
            try:
                logger.info("Loading reranker model (bge-reranker-v2-m3-ko)...")
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                self.reranker_model = AutoModelForSequenceClassification.from_pretrained(
                    self.reranker_model_path
                )
                self.reranker_tokenizer = AutoTokenizer.from_pretrained(
                    self.reranker_model_path
                )
                logger.info("Reranker model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load reranker model: {e}")
                self.reranker_model = False  # False로 설정하여 재시도 방지
                self.reranker_tokenizer = False
        return self.reranker_model

    def _build_graph(self):
        """그래프 구성"""
        # 노드 추가
        self.workflow.add_node("analyze_query", self.analyze_search_query)
        self.workflow.add_node("search_hr_info", self.search_hr_information)
        self.workflow.add_node("search_hr_rules", self.search_hr_rules)
        self.workflow.add_node("merge_results", self.merge_search_results)
        self.workflow.add_node("rerank_results", self.rerank_with_model)
        self.workflow.add_node("format_response", self.format_final_response)

        # 엔트리 포인트 설정 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "analyze_query")

        # 검색 타입에 따른 분기
        self.workflow.add_conditional_edges(
            "analyze_query",
            self.determine_search_targets,
            {
                "hr_info_only": "search_hr_info",
                "hr_rules_only": "search_hr_rules",
                "both": "search_hr_info"
            }
        )

        # HR 정보 검색 후 처리
        def after_hr_info(state):
            if state.get("search_type") == "both":
                return "search_hr_rules"
            else:
                return "merge_results"

        self.workflow.add_conditional_edges(
            "search_hr_info",
            after_hr_info,
            {
                "search_hr_rules": "search_hr_rules",
                "merge_results": "merge_results"
            }
        )

        # HR 규정 검색 후 병합
        self.workflow.add_edge("search_hr_rules", "merge_results")

        # 결과 리랭킹
        self.workflow.add_edge("merge_results", "rerank_results")

        # 최종 포맷팅
        self.workflow.add_edge("rerank_results", "format_response")

        # 종료
        self.workflow.add_edge("format_response", END)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 실행 인터페이스"""
        initial_state = SearchState(
            query=input_data.get("query", ""),
            search_type=input_data.get("search_type", "both"),
            filters=input_data.get("filters", {}),
            hr_results=[],
            rules_results=[],
            reranked_results=[],
            relevance_scores={},
            sources=[],
            final_results={},
            execution_status="initializing"
        )

        # 워크플로우 컴파일 및 실행
        app = self.workflow.compile()
        result = await app.ainvoke(initial_state)

        return result.get("final_results", {})

    async def analyze_search_query(self, state: SearchState) -> SearchState:
        """검색 쿼리 분석"""
        state["execution_status"] = "analyzing_query"

        query = state.get("query", "")

        # 쿼리 분석 및 키워드 추출
        keywords = self._extract_keywords(query)

        # 검색 타입 결정
        if "인사" in query or "직원" in query or "부서" in query:
            if "규정" not in query and "정책" not in query:
                state["search_type"] = "hr_info"
        elif "규정" in query or "정책" in query or "지침" in query:
            if "인사" not in query and "직원" not in query:
                state["search_type"] = "hr_rules"

        state["filters"]["keywords"] = keywords

        logger.info(f"Query analyzed - Type: {state['search_type']}, Keywords: {keywords}")
        return state

    def determine_search_targets(self, state: SearchState) -> str:
        """검색 대상 결정"""
        search_type = state.get("search_type", "both")

        if search_type == "hr_info":
            return "hr_info_only"
        elif search_type == "hr_rules":
            return "hr_rules_only"
        else:
            return "both"

    async def search_hr_information(self, state: SearchState) -> SearchState:
        """인사정보 검색 (SQLite)"""
        state["execution_status"] = "searching_hr_info"

        try:
            conn = sqlite3.connect(str(self.hr_info_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = state.get("query", "")
            filters = state.get("filters", {})

            # SQL 쿼리 구성
            sql_query = self._build_hr_info_query(query, filters)

            # 쿼리 실행
            cursor.execute(sql_query)
            results = cursor.fetchall()

            # 결과 변환
            hr_results = []
            for row in results:
                hr_results.append({
                    key: row[key] for key in row.keys()
                })

            state["hr_results"] = hr_results
            state["sources"].append("HR Information Database")

            conn.close()

            logger.info(f"Found {len(hr_results)} HR information results")

        except Exception as e:
            logger.error(f"Error searching HR information: {e}")
            state["hr_results"] = []

        return state

    async def search_hr_rules(self, state: SearchState) -> SearchState:
        """내부규정 검색 (ChromaDB)"""
        state["execution_status"] = "searching_hr_rules"

        try:
            # ChromaDB 컬렉션 가져오기
            collection = self.hr_rules_client.get_or_create_collection(
                name="hr_rules",
                metadata={"description": "Company HR rules and regulations"}
            )

            query = state.get("query", "")

            # 임베딩 생성 (lazy loading)
            embedding_model = self._load_embedding_model()
            if embedding_model and embedding_model is not False:
                query_embedding = embedding_model.encode(query).tolist()

                # 벡터 검색
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=10,
                    include=["metadatas", "documents", "distances"]
                )
            else:
                # 텍스트 검색 폴백
                results = collection.query(
                    query_texts=[query],
                    n_results=10,
                    include=["metadatas", "documents", "distances"]
                )

            # 결과 변환
            rules_results = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    rules_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 1.0,
                        "relevance_score": 1.0 - (results["distances"][0][i] if results.get("distances") else 0.5)
                    })

            state["rules_results"] = rules_results
            state["sources"].append("HR Rules Database")

            logger.info(f"Found {len(rules_results)} HR rules results")

        except Exception as e:
            logger.error(f"Error searching HR rules: {e}")
            state["rules_results"] = []

        return state

    async def merge_search_results(self, state: SearchState) -> SearchState:
        """검색 결과 병합"""
        state["execution_status"] = "merging_results"

        merged_results = []

        # HR 정보 결과 추가
        for result in state.get("hr_results", []):
            merged_results.append({
                "type": "hr_info",
                "data": result,
                "source": "HR Information Database"
            })

        # HR 규정 결과 추가
        for result in state.get("rules_results", []):
            merged_results.append({
                "type": "hr_rules",
                "data": result,
                "source": "HR Rules Database"
            })

        state["merged_results"] = merged_results

        logger.info(f"Merged {len(merged_results)} total results")
        return state

    async def rerank_with_model(self, state: SearchState) -> SearchState:
        """리랭커 모델을 사용한 결과 재정렬"""
        state["execution_status"] = "reranking"

        merged_results = state.get("merged_results", [])
        query = state.get("query", "")

        if not merged_results:
            state["reranked_results"] = []
            return state

        # 리랭킹 모델 사용 (lazy loading)
        reranker_model = self._load_reranker_model()
        if reranker_model and reranker_model is not False and self.reranker_tokenizer:
            try:
                # 리랭킹 수행
                reranked = []

                for result in merged_results:
                    # 문서 텍스트 추출
                    if result["type"] == "hr_info":
                        doc_text = str(result["data"])
                    else:
                        doc_text = result["data"].get("content", "")

                    # 리랭킹 점수 계산
                    inputs = self.reranker_tokenizer(
                        query,
                        doc_text,
                        return_tensors="pt",
                        max_length=512,
                        truncation=True
                    )

                    with torch.no_grad():
                        scores = reranker_model(**inputs).logits
                        relevance_score = torch.sigmoid(scores).item()

                    result["rerank_score"] = relevance_score
                    reranked.append(result)

                # 점수 기준 정렬
                reranked.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

                # 상위 N개만 선택
                state["reranked_results"] = reranked[:10]

            except Exception as e:
                logger.error(f"Error during reranking: {e}")
                # 폴백: 원본 순서 유지
                state["reranked_results"] = merged_results[:10]
        else:
            # 리랭커 없을 경우 원본 순서 유지
            state["reranked_results"] = merged_results[:10]

        logger.info(f"Reranked to {len(state['reranked_results'])} results")
        return state

    async def format_final_response(self, state: SearchState) -> SearchState:
        """최종 응답 포맷팅"""
        state["execution_status"] = "formatting"

        reranked_results = state.get("reranked_results", [])

        # 최종 결과 구성
        final_results = {
            "query": state.get("query", ""),
            "total_results": len(reranked_results),
            "results": [],
            "sources": list(set(state.get("sources", []))),
            "timestamp": datetime.now().isoformat()
        }

        # 결과 포맷팅
        for i, result in enumerate(reranked_results):
            formatted_result = {
                "rank": i + 1,
                "type": result["type"],
                "source": result["source"],
                "relevance_score": result.get("rerank_score", 0.0)
            }

            if result["type"] == "hr_info":
                formatted_result["content"] = result["data"]
            else:
                formatted_result["content"] = {
                    "text": result["data"].get("content", ""),
                    "metadata": result["data"].get("metadata", {})
                }

            final_results["results"].append(formatted_result)

        # 관련성 점수 요약
        if reranked_results:
            avg_score = sum(r.get("rerank_score", 0) for r in reranked_results) / len(reranked_results)
            final_results["average_relevance"] = avg_score

        state["final_results"] = final_results
        state["execution_status"] = "completed"

        logger.info("Search completed and formatted")
        return state

    def _extract_keywords(self, query: str) -> List[str]:
        """쿼리에서 키워드 추출"""
        # 간단한 키워드 추출 (실제로는 더 정교한 NLP 처리 필요)
        if not query:
            return []
        stopwords = {"을", "를", "이", "가", "은", "는", "의", "에", "와", "과", "도", "로"}
        words = query.split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        return keywords

    def _build_hr_info_query(self, query: str, filters: Dict) -> str:
        """HR 정보 검색을 위한 SQL 쿼리 구성"""
        base_query = "SELECT * FROM 인사자료 WHERE 1=1"

        keywords = filters.get("keywords", [])
        if keywords:
            conditions = []
            for keyword in keywords:
                conditions.append(
                    f"(name LIKE '%{keyword}%' OR department LIKE '%{keyword}%' OR position LIKE '%{keyword}%')"
                )
            if conditions:
                base_query += " AND (" + " OR ".join(conditions) + ")"

        # 추가 필터 적용
        if filters.get("department"):
            base_query += f" AND department = '{filters['department']}'"

        if filters.get("position"):
            base_query += f" AND position = '{filters['position']}'"

        base_query += " LIMIT 50"

        return base_query