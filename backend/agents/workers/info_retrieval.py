"""
Information Retrieval Agent
정보 검색 및 RAG 기반 검색 에이전트
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

logger = logging.getLogger(__name__)


class InformationRetrievalAgent:
    """정보 검색 및 문서 검색을 담당하는 에이전트"""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize information retrieval agent"""
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.name = "InformationRetrievalAgent"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """메인 실행 메서드"""
        start_time = datetime.now()

        try:
            # Extract task parameters
            search_query = task.get("search_query", "")
            search_type = task.get("search_type", "hybrid")
            collections = task.get("collections", ["hr_rules", "policies"])
            top_k = task.get("top_k", 5)
            similarity_threshold = task.get("similarity_threshold", 0.7)
            metadata_filter = task.get("metadata_filter", {})

            # Perform search based on type
            if search_type == "vector":
                result = await self._execute_vector_search(
                    search_query, collections, top_k, similarity_threshold
                )
            elif search_type == "keyword":
                result = await self._execute_keyword_search(
                    search_query, collections, top_k, metadata_filter
                )
            else:  # hybrid
                result = await self._execute_hybrid_search(
                    search_query, collections, top_k, similarity_threshold, metadata_filter
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "confidence_score": result.get("confidence", 0.85),
                "execution_time": execution_time,
                "documents": result.get("documents", []),
                "total_found": result.get("total_found", 0),
                "relevance_scores": result.get("relevance_scores", []),
                "sources": result.get("sources", []),
                "summary": result.get("summary")
            }

        except Exception as e:
            logger.error(f"Information retrieval failed: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "confidence_score": 0.0,
                "execution_time": execution_time,
                "error": str(e)
            }

    async def _execute_vector_search(
        self, query: str, collections: List[str], top_k: int, threshold: float
    ) -> Dict[str, Any]:
        """벡터 유사도 기반 검색 실행"""

        # Simulate ChromaDB vector search
        # 실제 구현 시 ChromaDB 연결 필요
        documents = await self._simulate_vector_search(query, collections, top_k)

        # Filter by threshold
        filtered_docs = [
            doc for doc in documents
            if doc.get("relevance_score", 0) >= threshold
        ]

        # Generate summary
        summary = await self._generate_search_summary(query, filtered_docs)

        return {
            "documents": filtered_docs,
            "total_found": len(filtered_docs),
            "relevance_scores": [doc.get("relevance_score", 0) for doc in filtered_docs],
            "sources": [doc.get("source", "") for doc in filtered_docs],
            "summary": summary,
            "confidence": 0.9
        }

    async def _execute_keyword_search(
        self, query: str, collections: List[str], top_k: int, metadata_filter: Dict
    ) -> Dict[str, Any]:
        """키워드 기반 검색 실행"""

        # Simulate keyword search
        documents = await self._simulate_keyword_search(query, collections, top_k)

        # Apply metadata filters
        if metadata_filter:
            documents = self._apply_metadata_filter(documents, metadata_filter)

        summary = await self._generate_search_summary(query, documents)

        return {
            "documents": documents,
            "total_found": len(documents),
            "relevance_scores": [0.75] * len(documents),  # Default score for keyword search
            "sources": [doc.get("source", "") for doc in documents],
            "summary": summary,
            "confidence": 0.8
        }

    async def _execute_hybrid_search(
        self, query: str, collections: List[str], top_k: int,
        threshold: float, metadata_filter: Dict
    ) -> Dict[str, Any]:
        """하이브리드 검색 (벡터 + 키워드) 실행"""

        # Combine vector and keyword search
        vector_results = await self._simulate_vector_search(query, collections, top_k)
        keyword_results = await self._simulate_keyword_search(query, collections, top_k)

        # Merge and rank results
        merged_documents = self._merge_search_results(vector_results, keyword_results)

        # Apply filters
        if metadata_filter:
            merged_documents = self._apply_metadata_filter(merged_documents, metadata_filter)

        # Filter by threshold
        filtered_docs = [
            doc for doc in merged_documents
            if doc.get("relevance_score", 0) >= threshold
        ][:top_k]

        summary = await self._generate_search_summary(query, filtered_docs)

        return {
            "documents": filtered_docs,
            "total_found": len(filtered_docs),
            "relevance_scores": [doc.get("relevance_score", 0) for doc in filtered_docs],
            "sources": [doc.get("source", "") for doc in filtered_docs],
            "summary": summary,
            "confidence": 0.92
        }

    async def _simulate_vector_search(
        self, query: str, collections: List[str], top_k: int
    ) -> List[Dict]:
        """벡터 검색 시뮬레이션"""

        # 실제 구현 시 ChromaDB 연결
        simulated_docs = [
            {
                "id": "doc1",
                "content": "연차 사용 규정: 직원은 연간 15일의 연차를 사용할 수 있습니다.",
                "source": "hr_rules",
                "relevance_score": 0.95,
                "metadata": {"category": "leave", "year": "2024"}
            },
            {
                "id": "doc2",
                "content": "병가 신청: 의사 소견서를 첨부하여 병가를 신청할 수 있습니다.",
                "source": "hr_rules",
                "relevance_score": 0.88,
                "metadata": {"category": "leave", "year": "2024"}
            },
            {
                "id": "doc3",
                "content": "출장 규정: 국내 출장 시 일비는 5만원이 지급됩니다.",
                "source": "policies",
                "relevance_score": 0.82,
                "metadata": {"category": "travel", "year": "2024"}
            }
        ]

        await asyncio.sleep(0.3)  # Simulate search time
        return simulated_docs[:top_k]

    async def _simulate_keyword_search(
        self, query: str, collections: List[str], top_k: int
    ) -> List[Dict]:
        """키워드 검색 시뮬레이션"""

        simulated_docs = [
            {
                "id": "doc4",
                "content": "휴가 승인 절차: 상급자의 승인을 받아야 합니다.",
                "source": "hr_rules",
                "relevance_score": 0.75,
                "metadata": {"category": "leave", "year": "2024"}
            },
            {
                "id": "doc5",
                "content": "재택근무 정책: 주 2회 재택근무가 가능합니다.",
                "source": "policies",
                "relevance_score": 0.72,
                "metadata": {"category": "work", "year": "2024"}
            }
        ]

        await asyncio.sleep(0.2)  # Simulate search time
        return simulated_docs[:top_k]

    def _merge_search_results(
        self, vector_results: List[Dict], keyword_results: List[Dict]
    ) -> List[Dict]:
        """검색 결과 병합 및 순위 조정"""

        # Combine results with weighted scoring
        all_docs = {}

        # Add vector results with higher weight
        for doc in vector_results:
            doc_id = doc.get("id")
            all_docs[doc_id] = doc
            all_docs[doc_id]["relevance_score"] = doc.get("relevance_score", 0) * 0.7

        # Add keyword results
        for doc in keyword_results:
            doc_id = doc.get("id")
            if doc_id in all_docs:
                # Combine scores if document appears in both
                all_docs[doc_id]["relevance_score"] += doc.get("relevance_score", 0) * 0.3
            else:
                all_docs[doc_id] = doc
                all_docs[doc_id]["relevance_score"] = doc.get("relevance_score", 0) * 0.3

        # Sort by relevance score
        sorted_docs = sorted(
            all_docs.values(),
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )

        return sorted_docs

    def _apply_metadata_filter(
        self, documents: List[Dict], metadata_filter: Dict
    ) -> List[Dict]:
        """메타데이터 필터 적용"""

        filtered = []
        for doc in documents:
            doc_metadata = doc.get("metadata", {})
            match = True

            for key, value in metadata_filter.items():
                if doc_metadata.get(key) != value:
                    match = False
                    break

            if match:
                filtered.append(doc)

        return filtered

    async def _generate_search_summary(self, query: str, documents: List[Dict]) -> str:
        """검색 결과 요약 생성"""

        if not documents:
            return "검색 결과가 없습니다."

        doc_contents = "\n".join([
            f"- {doc.get('content', '')[:100]}..."
            for doc in documents[:3]
        ])

        prompt = f"""다음 검색 결과를 한국어로 요약해주세요:
        검색 쿼리: {query}
        검색된 문서들:
        {doc_contents}

        핵심 정보를 간결하게 요약하세요."""

        response = await self.llm.ainvoke([
            HumanMessage(content=prompt)
        ])

        return response.content.strip()

    async def execute_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph 노드 실행 메서드"""

        # Extract task from state
        execution_state = state.get("execution_manager_state", {})
        pending_tasks = execution_state.get("pending_tasks", [])

        if not pending_tasks:
            logger.warning("No pending tasks for information retrieval")
            return state

        # Get first task for this agent
        task = None
        for t in pending_tasks:
            if t.get("agent") == "InformationRetrievalAgent":
                task = t
                break

        if not task:
            logger.warning("No information retrieval task found")
            return state

        # Execute task
        result = await self.execute(task)

        # Update state
        completed_tasks = execution_state.get("completed_tasks", [])
        completed_tasks.append({
            "task_id": task.get("task_id"),
            "agent": self.name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        # Remove from pending
        pending_tasks.remove(task)

        state["execution_manager_state"]["pending_tasks"] = pending_tasks
        state["execution_manager_state"]["completed_tasks"] = completed_tasks

        # Store agent-specific result
        if "agent_results" not in state:
            state["agent_results"] = {}
        state["agent_results"][self.name] = result

        logger.info(f"Information retrieval completed for task {task.get('task_id')}")
        return state