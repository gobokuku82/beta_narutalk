"""
제약 영업 규제 준수 시스템 - GPT-4o 통합 검색 엔진
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI

from search_engine import ComplianceSearchEngine, SearchQuery, SearchResult
from conflict_resolver import ConflictResolver

# 환경 변수 로드
load_dotenv()


@dataclass
class GPTEnhancedResult:
    query: str
    search_results: List[SearchResult]
    gpt_answer: str
    confidence: float
    sources: List[str]


class GPTEnhancedSearchEngine:
    """GPT-4o를 활용한 향상된 검색 엔진"""

    def __init__(self, chunks_file: str = "chunked_data.json"):
        """
        GPT 통합 검색 엔진 초기화

        Args:
            chunks_file: 청킹 데이터 파일 경로
        """
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # 기본 검색 엔진 초기화
        self.search_engine = ComplianceSearchEngine(chunks_file=chunks_file)
        self.conflict_resolver = ConflictResolver()

        # GPT 설정
        self.model = "gpt-4o"
        self.temperature = 0.1  # 일관성 있는 답변을 위해 낮은 temperature

    def search_and_answer(self, query: str, top_k: int = 5) -> GPTEnhancedResult:
        """
        검색 수행 후 GPT-4o로 답변 생성

        Args:
            query: 사용자 질문
            top_k: 검색할 결과 수

        Returns:
            GPT 향상 검색 결과
        """
        # 1. 기본 검색 수행
        search_query = SearchQuery(text=query, top_k=top_k)
        search_results = self.search_engine.search(search_query)

        # 2. 검색 결과가 없으면 기본 답변
        if not search_results:
            return GPTEnhancedResult(
                query=query,
                search_results=[],
                gpt_answer="관련 규정을 찾을 수 없습니다. 질문을 다시 확인해 주세요.",
                confidence=0.0,
                sources=[]
            )

        # 3. 충돌 해결
        primary_result = self._resolve_conflicts(search_results)

        # 4. GPT-4o로 답변 생성
        gpt_answer, confidence = self._generate_gpt_answer(query, search_results, primary_result)

        # 5. 출처 정리
        sources = self._extract_sources(search_results)

        return GPTEnhancedResult(
            query=query,
            search_results=search_results,
            gpt_answer=gpt_answer,
            confidence=confidence,
            sources=sources
        )

    def _resolve_conflicts(self, results: List[SearchResult]) -> SearchResult:
        """법령 간 충돌 해결"""
        if len(results) <= 1:
            return results[0] if results else None

        # 검색 결과를 충돌 해결기에 전달할 형식으로 변환
        regulations = []
        for result in results:
            regulations.append({
                'chunk_id': result.chunk_id,
                'text': result.text,
                'metadata': result.metadata
            })

        resolution = self.conflict_resolver.resolve_conflicts(regulations)
        if resolution:
            # 가장 엄격한 규정 찾기
            for result in results:
                if result.chunk_id == resolution.applied_regulation.chunk_id:
                    return result

        return results[0]

    def _generate_gpt_answer(self,
                           query: str,
                           search_results: List[SearchResult],
                           primary_result: SearchResult) -> Tuple[str, float]:
        """
        GPT-4o를 사용하여 자연스러운 답변 생성

        Args:
            query: 원본 질문
            search_results: 검색 결과
            primary_result: 주요 결과 (충돌 해결 후)

        Returns:
            (답변, 신뢰도)
        """
        # 컨텍스트 구성
        context = self._build_context(search_results, primary_result)

        # 프롬프트 구성
        system_prompt = """당신은 제약회사 규제 준수 전문가입니다.
        제공된 법령과 규정을 바탕으로 정확하고 실무적인 답변을 제공해야 합니다.

        답변 원칙:
        1. 가장 엄격한 기준을 우선 적용
        2. 구체적인 금액과 횟수 명시
        3. 실무 적용 시 주의사항 포함
        4. 근거 법령 명확히 제시
        5. 불확실한 경우 보수적으로 해석
        """

        user_prompt = f"""
        질문: {query}

        관련 규정:
        {context}

        위 규정을 바탕으로 다음 형식으로 답변해주세요:

        [답변]
        가능/불가능/조건부 가능 여부를 명확히 밝히고 이유 설명

        [적용 조건]
        - 구체적인 제한사항 (금액, 횟수, 대상 등)

        [근거]
        - 적용 법령 및 조항

        [실무 TIP]
        - 실제 업무 시 주의사항
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=1000
            )

            answer = response.choices[0].message.content

            # 신뢰도 계산 (검색 결과 수와 매칭 정도 기반)
            confidence = min(len(search_results) * 0.2, 1.0)
            if primary_result and primary_result.score:
                confidence = confidence * 0.5 + primary_result.score * 0.5

            return answer, confidence

        except Exception as e:
            print(f"GPT API 오류: {e}")
            # 폴백: 기본 검색 엔진 답변 사용
            fallback_answer = self.search_engine.generate_answer(query, search_results)
            return fallback_answer, 0.5

    def _build_context(self, search_results: List[SearchResult], primary_result: SearchResult) -> str:
        """검색 결과로부터 컨텍스트 구성"""
        context_parts = []

        # 주요 결과
        if primary_result:
            context_parts.append(f"[주요 규정 - {primary_result.source_law}]")
            context_parts.append(f"내용: {primary_result.text}")

            # 메타데이터 정보
            if primary_result.metadata.get('limit_value'):
                context_parts.append(f"금액 한도: {primary_result.metadata['limit_value']:,}원")
            if primary_result.metadata.get('frequency_count'):
                context_parts.append(f"빈도 제한: {primary_result.metadata.get('frequency_period', '')} {primary_result.metadata['frequency_count']}회")
            context_parts.append("")

        # 추가 관련 규정
        for i, result in enumerate(search_results[:3], 1):
            if result != primary_result:
                context_parts.append(f"[관련 규정 {i} - {result.source_law}]")
                context_parts.append(f"내용: {result.text[:200]}...")
                context_parts.append("")

        return '\n'.join(context_parts)

    def _extract_sources(self, search_results: List[SearchResult]) -> List[str]:
        """검색 결과에서 출처 추출"""
        sources = []
        seen = set()

        for result in search_results:
            source = f"{result.source_law}"
            if result.metadata.get('article'):
                source += f" {result.metadata['article']}"

            if source not in seen:
                sources.append(source)
                seen.add(source)

        return sources

    def batch_search(self, queries: List[str]) -> List[GPTEnhancedResult]:
        """여러 질문 일괄 처리"""
        results = []
        for query in queries:
            print(f"처리 중: {query}")
            result = self.search_and_answer(query)
            results.append(result)
        return results

    def interactive_mode(self):
        """대화형 모드"""
        print("=== 제약 영업 규제 준수 시스템 (GPT-4o Enhanced) ===")
        print("질문을 입력하세요. 종료하려면 'quit' 입력")
        print("-" * 50)

        while True:
            query = input("\n질문: ").strip()
            if query.lower() in ['quit', 'exit', '종료']:
                print("시스템을 종료합니다.")
                break

            if not query:
                continue

            result = self.search_and_answer(query)

            print("\n" + "=" * 50)
            print(result.gpt_answer)
            print("\n[출처]")
            for source in result.sources:
                print(f"  - {source}")
            print(f"\n[신뢰도: {result.confidence:.1%}]")
            print("=" * 50)


def main():
    """테스트 실행"""
    print("GPT-4o 통합 검색 엔진 테스트")
    print("-" * 50)

    # 테스트 질문
    test_queries = [
        "대학병원 교수님께 10만원 식사 대접 가능한가요?",
        "해외 학술대회 참가 지원 방법과 한도는?",
        "제품 설명회 개최 시 주의사항은?",
        "의료진에게 선물 제공이 가능한가요?",
        "강연료 지급 기준과 연간 한도는?"
    ]

    # 엔진 초기화
    engine = GPTEnhancedSearchEngine()

    # 각 질문 테스트
    for query in test_queries[:2]:  # 처음 2개만 테스트
        print(f"\n질문: {query}")
        result = engine.search_and_answer(query)

        print("\n[GPT-4o 답변]")
        print(result.gpt_answer)

        print("\n[검색된 규정]")
        for sr in result.search_results[:2]:
            print(f"  - {sr.source_law}: {sr.text[:50]}...")

        print(f"\n[신뢰도: {result.confidence:.1%}]")
        print("-" * 50)


if __name__ == "__main__":
    main()