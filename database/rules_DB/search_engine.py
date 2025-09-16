"""
제약 영업 규제 준수 시스템 - 하이브리드 검색 엔진
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from pathlib import Path

from embedding_engine import EmbeddingEngine, VectorStore


@dataclass
class SearchQuery:
    text: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 5
    search_type: str = "hybrid"  # 'vector', 'metadata', 'hybrid'
    include_context: bool = True


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any]
    source_law: str
    matched_keywords: List[str] = None
    context: Optional[str] = None


class QueryAnalyzer:
    """쿼리 분석 및 의도 파악"""

    def __init__(self):
        self.intent_patterns = {
            'amount_limit': {
                'patterns': ['얼마', '한도', '금액', '상한', '최대', '몇 원', '몇만원'],
                'metadata_filter': 'limit_value'
            },
            'frequency': {
                'patterns': ['몇 번', '횟수', '빈도', '월', '연간', '일일'],
                'metadata_filter': 'frequency_count'
            },
            'activity': {
                'patterns': {
                    '제품설명회': ['제품설명회', '설명회', '프레젠테이션'],
                    '학술대회': ['학술대회', '학회', '세미나', '심포지엄', '컨퍼런스'],
                    '식음료': ['식사', '점심', '저녁', '다과', '음료', '식음료'],
                    '숙박': ['숙박', '호텔', '숙소', '잠'],
                    '교통': ['교통', '항공', '비행기', '기차', '차량'],
                    '견본품': ['견본품', '샘플', '무료', '시료'],
                    '강연': ['강연', '강의', '발표', '스피치'],
                    '자문': ['자문', '컨설팅', '조언', '상담']
                },
                'metadata_filter': 'activity'
            },
            'target': {
                'patterns': {
                    '의료인': ['의사', '의료인', '의료진', '의료전문가'],
                    '공직자': ['공직자', '공무원', '국공립', '대학병원'],
                    '요양기관': ['병원', '의원', '요양기관', '의료기관'],
                    '약사': ['약사', '약국', '약료']
                },
                'metadata_filter': 'target'
            },
            'permission': {
                'patterns': ['가능', '할 수 있', '허용', '괜찮', '문제없'],
                'intent': 'check_permission'
            },
            'prohibition': {
                'patterns': ['금지', '불가', '안 되', '못 하', '위반'],
                'intent': 'check_prohibition'
            }
        }

        self.scenario_mappings = {
            '병원 방문 식사': ['병원', '방문', '식사'],
            '학술대회 지원': ['학술대회', '참가', '지원', '등록비'],
            '제품 설명회': ['제품', '설명회', '프레젠테이션'],
            '견본품 제공': ['견본품', '샘플', '제공', '무료'],
            '강연료 지급': ['강연', '강연료', '발표', '수당']
        }

    def analyze(self, query: str) -> Dict[str, Any]:
        """
        쿼리 분석 및 메타데이터 추출

        Args:
            query: 검색 쿼리

        Returns:
            분석된 메타데이터
        """
        query_lower = query.lower()
        metadata = {
            'original_query': query,
            'intents': [],
            'filters': {},
            'keywords': [],
            'scenario': None
        }

        # 의도 분석
        for intent_type, config in self.intent_patterns.items():
            if intent_type in ['activity', 'target']:
                # 딕셔너리 패턴 처리
                for key, patterns in config['patterns'].items():
                    if any(pattern in query_lower for pattern in patterns):
                        metadata['filters'][config['metadata_filter']] = key
                        metadata['keywords'].extend(patterns)
            else:
                # 리스트 패턴 처리
                if any(pattern in query_lower for pattern in config['patterns']):
                    metadata['intents'].append(intent_type)
                    if 'metadata_filter' in config:
                        metadata['filters'][config['metadata_filter']] = True

        # 시나리오 매칭
        for scenario, keywords in self.scenario_mappings.items():
            if sum(1 for kw in keywords if kw in query_lower) >= 2:
                metadata['scenario'] = scenario

        # 금액 추출
        amount_match = re.search(r'(\d+)\s*만\s*원', query)
        if amount_match:
            metadata['filters']['limit_value'] = int(amount_match.group(1)) * 10000

        # 빈도 추출
        freq_patterns = [
            (r'월\s*(\d+)회', 'month'),
            (r'연\s*(\d+)회', 'year'),
            (r'일\s*(\d+)회', 'day')
        ]
        for pattern, period in freq_patterns:
            match = re.search(pattern, query)
            if match:
                metadata['filters']['frequency_count'] = int(match.group(1))
                metadata['filters']['frequency_period'] = period

        return metadata


class ComplianceSearchEngine:
    """하이브리드 검색 엔진"""

    def __init__(self,
                 chunks_file: str = None,
                 embeddings_file: str = None,
                 vector_store_type: str = "chromadb"):
        """
        검색 엔진 초기화

        Args:
            chunks_file: 청킹 데이터 파일
            embeddings_file: 임베딩 파일
            vector_store_type: 벡터 스토어 타입
        """
        self.query_analyzer = QueryAnalyzer()
        self.embedding_engine = EmbeddingEngine()
        self.vector_store = VectorStore(store_type=vector_store_type)

        # 청크 데이터 로드
        self.chunks = {}
        self.metadata_index = {}

        if chunks_file:
            self.load_chunks(chunks_file)

        # 임베딩 로드
        if embeddings_file and Path(embeddings_file).exists():
            self.embeddings = self.embedding_engine.load_embeddings(embeddings_file)
        else:
            self.embeddings = {}

    def load_chunks(self, chunks_file: str):
        """청킹 데이터 로드 및 인덱싱"""
        with open(chunks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for chunk in data['chunks']:
            chunk_id = chunk['chunk_id']
            self.chunks[chunk_id] = chunk

            # 메타데이터 인덱싱
            for key, value in chunk['metadata'].items():
                if value is None or isinstance(value, list):
                    continue  # 리스트나 None은 인덱싱하지 않음
                if key not in self.metadata_index:
                    self.metadata_index[key] = {}
                if value not in self.metadata_index[key]:
                    self.metadata_index[key][value] = []
                self.metadata_index[key][value].append(chunk_id)

        print(f"Loaded {len(self.chunks)} chunks")

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        하이브리드 검색 수행

        Args:
            query: 검색 쿼리 객체

        Returns:
            검색 결과 리스트
        """
        # 1. 쿼리 분석
        query_metadata = self.query_analyzer.analyze(query.text)

        # 2. 검색 전략 결정
        if query.search_type == "metadata":
            results = self._metadata_search(query_metadata, query.top_k)
        elif query.search_type == "vector":
            results = self._vector_search(query.text, query.top_k, query_metadata.get('filters'))
        else:  # hybrid
            results = self._hybrid_search(query.text, query_metadata, query.top_k)

        # 3. 결과 후처리
        results = self._postprocess_results(results, query_metadata)

        # 4. 컨텍스트 추가
        if query.include_context:
            results = self._add_context(results)

        return results

    def _vector_search(self, query_text: str, top_k: int, filters: Dict = None) -> List[SearchResult]:
        """벡터 유사도 검색"""
        query_embedding = self.embedding_engine.embed_text(query_text)

        # 벡터 스토어에서 검색
        vector_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # 여유있게 검색
            filters=filters
        )

        results = []
        for vr in vector_results:
            if vr['id'] in self.chunks:
                chunk = self.chunks[vr['id']]
                results.append(SearchResult(
                    chunk_id=vr['id'],
                    text=chunk['text'],
                    score=1 - vr.get('distance', 0) if 'distance' in vr else vr.get('score', 0),
                    metadata=chunk['metadata'],
                    source_law=chunk['metadata'].get('law_name', '알 수 없음')
                ))

        return results[:top_k]

    def _metadata_search(self, query_metadata: Dict, top_k: int) -> List[SearchResult]:
        """메타데이터 기반 검색"""
        candidate_chunks = set()

        # 필터 조건에 맞는 청크 찾기
        for filter_key, filter_value in query_metadata.get('filters', {}).items():
            if filter_key in self.metadata_index:
                if filter_value in self.metadata_index[filter_key]:
                    chunk_ids = self.metadata_index[filter_key][filter_value]
                    if candidate_chunks:
                        candidate_chunks = candidate_chunks.intersection(set(chunk_ids))
                    else:
                        candidate_chunks = set(chunk_ids)

        # 모든 청크를 후보로 (필터가 없는 경우)
        if not candidate_chunks and not query_metadata.get('filters'):
            candidate_chunks = set(self.chunks.keys())

        # 스코어링
        results = []
        for chunk_id in candidate_chunks:
            chunk = self.chunks[chunk_id]
            score = self._calculate_metadata_score(chunk, query_metadata)
            results.append(SearchResult(
                chunk_id=chunk_id,
                text=chunk['text'],
                score=score,
                metadata=chunk['metadata'],
                source_law=chunk['metadata'].get('law_name', '알 수 없음')
            ))

        # 스코어 기준 정렬
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _hybrid_search(self, query_text: str, query_metadata: Dict, top_k: int) -> List[SearchResult]:
        """하이브리드 검색 (벡터 + 메타데이터)"""

        # 벡터 검색 (ChromaDB 필터는 단순화)
        # ChromaDB는 복잡한 필터를 지원하지 않으므로 단일 필터만 사용
        simple_filter = None
        if query_metadata.get('filters'):
            # 가장 중요한 필터 하나만 선택
            if 'activity' in query_metadata['filters']:
                simple_filter = {'activity': query_metadata['filters']['activity']}
            elif 'target' in query_metadata['filters']:
                simple_filter = {'target': query_metadata['filters']['target']}

        vector_results = self._vector_search(
            query_text,
            top_k * 2,
            simple_filter
        )

        # 메타데이터 검색
        metadata_results = self._metadata_search(query_metadata, top_k * 2)

        # 결과 병합 및 스코어 재계산
        combined_results = {}

        for vr in vector_results:
            combined_results[vr.chunk_id] = vr
            combined_results[vr.chunk_id].score *= 0.6  # 벡터 가중치

        for mr in metadata_results:
            if mr.chunk_id in combined_results:
                # 이미 있으면 스코어 합산
                combined_results[mr.chunk_id].score += mr.score * 0.4
            else:
                combined_results[mr.chunk_id] = mr
                combined_results[mr.chunk_id].score *= 0.4  # 메타데이터 가중치

        # 정렬 및 반환
        results = list(combined_results.values())
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    def _calculate_metadata_score(self, chunk: Dict, query_metadata: Dict) -> float:
        """메타데이터 기반 스코어 계산"""
        score = 0.0
        chunk_metadata = chunk['metadata']

        # 필터 일치도
        for filter_key, filter_value in query_metadata.get('filters', {}).items():
            if filter_key in chunk_metadata:
                if chunk_metadata[filter_key] == filter_value:
                    score += 1.0
                elif isinstance(filter_value, (int, float)) and isinstance(chunk_metadata[filter_key], (int, float)):
                    # 수치형 비교
                    diff = abs(filter_value - chunk_metadata[filter_key])
                    score += max(0, 1.0 - diff / max(filter_value, chunk_metadata[filter_key]))

        # 키워드 매칭
        chunk_text_lower = chunk['text'].lower()
        for keyword in query_metadata.get('keywords', []):
            if keyword in chunk_text_lower:
                score += 0.2

        # 시나리오 매칭
        if query_metadata.get('scenario'):
            if query_metadata['scenario'] in chunk_text_lower:
                score += 0.5

        # 법령 우선순위 보정
        law_priority = {
            '청탁금지법': 1.5,
            '약사법': 1.3,
            '공정경쟁규약': 1.0
        }
        law_name = chunk_metadata.get('law_name', '')
        score *= law_priority.get(law_name, 1.0)

        return score

    def _postprocess_results(self, results: List[SearchResult], query_metadata: Dict) -> List[SearchResult]:
        """검색 결과 후처리"""

        # 중복 제거
        seen_texts = set()
        unique_results = []
        for result in results:
            text_key = result.text[:50]  # 앞 50자로 중복 체크
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_results.append(result)

        # 매치된 키워드 표시
        for result in unique_results:
            matched_keywords = []
            for keyword in query_metadata.get('keywords', []):
                if keyword in result.text.lower():
                    matched_keywords.append(keyword)
            result.matched_keywords = matched_keywords

        return unique_results

    def _add_context(self, results: List[SearchResult]) -> List[SearchResult]:
        """검색 결과에 실무 컨텍스트 추가"""
        context_templates = {
            '절대금지': "[금지] 이 행위는 법적으로 금지되어 있습니다.",
            '조건부허용': "[조건부] 특정 조건 하에서만 허용됩니다.",
            '허용': "[허용] 규정된 범위 내에서 허용됩니다."
        }

        for result in results:
            prohibition_type = result.metadata.get('prohibition_type', '')
            result.context = context_templates.get(prohibition_type, '')

            # 구체적 제한사항 추가
            if result.metadata.get('limit_value'):
                amount = result.metadata['limit_value']
                result.context += f" 한도: {amount:,}원"

            if result.metadata.get('frequency_count'):
                count = result.metadata['frequency_count']
                period = result.metadata.get('frequency_period', '')
                result.context += f" 빈도: {period} {count}회"

        return results

    def resolve_conflicts(self, results: List[SearchResult]) -> SearchResult:
        """
        여러 법령 간 충돌 해결

        Args:
            results: 검색 결과 리스트

        Returns:
            가장 엄격한 기준의 결과
        """
        if not results:
            return None

        # 법령 우선순위
        law_priority = {
            '청탁금지법': 1,
            '약사법': 2,
            '공정거래법': 3,
            '공정경쟁규약': 4,
            '가이드라인': 5
        }

        # 우선순위별 정렬
        results.sort(key=lambda x: law_priority.get(x.source_law, 99))

        # 가장 엄격한 제한 찾기
        strictest = results[0]
        for result in results[1:]:
            # 금액 제한 비교
            if result.metadata.get('limit_value', float('inf')) < \
               strictest.metadata.get('limit_value', float('inf')):
                strictest = result

            # 금지 유형 비교
            if result.metadata.get('prohibition_type') == '절대금지':
                strictest = result
                break

        return strictest

    def generate_answer(self, query: str, results: List[SearchResult]) -> str:
        """
        검색 결과를 바탕으로 답변 생성

        Args:
            query: 원본 쿼리
            results: 검색 결과

        Returns:
            구조화된 답변
        """
        if not results:
            return "관련 규정을 찾을 수 없습니다. 질문을 다시 확인해 주세요."

        # 충돌 해결
        primary_result = self.resolve_conflicts(results)

        # 답변 생성
        answer_parts = []

        # 기본 답변
        prohibition_type = primary_result.metadata.get('prohibition_type', '')
        if prohibition_type == '절대금지':
            answer_parts.append("[불가능] **불가능합니다.**")
        elif prohibition_type == '조건부허용':
            answer_parts.append("[조건부] **조건부로 가능합니다.**")
        else:
            answer_parts.append("[가능] **가능합니다.**")

        # 조건 상세
        conditions = []
        if primary_result.metadata.get('limit_value'):
            amount = primary_result.metadata['limit_value']
            conditions.append(f"- 금액 한도: {amount:,}원")

        if primary_result.metadata.get('frequency_count'):
            count = primary_result.metadata['frequency_count']
            period = primary_result.metadata.get('frequency_period', '')
            period_korean = {
                'day': '일',
                'week': '주',
                'month': '월',
                'year': '연'
            }.get(period, period)
            conditions.append(f"- 빈도 제한: {period_korean} {count}회")

        if primary_result.metadata.get('target'):
            conditions.append(f"- 적용 대상: {primary_result.metadata['target']}")

        if conditions:
            answer_parts.append("\n**적용 조건:**")
            answer_parts.extend(conditions)

        # 근거 법령
        answer_parts.append(f"\n**근거:** {primary_result.source_law}")
        if primary_result.metadata.get('article'):
            answer_parts.append(f" {primary_result.metadata['article']}")

        # 추가 주의사항
        if len(results) > 1:
            other_laws = set(r.source_law for r in results[1:3])
            if other_laws:
                answer_parts.append(f"\n**참고:** {', '.join(other_laws)}에도 관련 규정이 있습니다.")

        return '\n'.join(answer_parts)


def main():
    """테스트 실행"""

    # 검색 엔진 초기화 (테스트 모드)
    engine = ComplianceSearchEngine()

    # 테스트 쿼리
    test_queries = [
        "대학병원 교수님께 10만원 식사 대접 가능한가요?",
        "해외 학술대회 숙박비 지원 한도는?",
        "월 몇 번까지 병원 방문 가능한가요?",
        "제품 샘플 제공 시 주의사항은?",
        "강연료 연간 한도가 있나요?"
    ]

    print("=== 제약 영업 규제 검색 엔진 테스트 ===\n")

    # 쿼리 분석 테스트
    analyzer = QueryAnalyzer()
    for query_text in test_queries[:2]:
        print(f"Query: {query_text}")
        analysis = analyzer.analyze(query_text)
        print(f"Analysis: {json.dumps(analysis, ensure_ascii=False, indent=2)}")
        print("-" * 50)

    # 검색 테스트 (더미 데이터로)
    print("\n=== 검색 시뮬레이션 ===")
    for query_text in test_queries:
        query = SearchQuery(text=query_text, top_k=3)
        print(f"\n질문: {query_text}")

        # 더미 결과 생성 (실제로는 검색 수행)
        dummy_result = SearchResult(
            chunk_id="test_001",
            text="제품설명회 목적으로 월 4회, 1회 10만원 이내 식음료 제공 가능",
            score=0.95,
            metadata={
                'law_name': '공정경쟁규약',
                'article': '제10조',
                'prohibition_type': '조건부허용',
                'limit_value': 100000,
                'frequency_count': 4,
                'frequency_period': 'month'
            },
            source_law='공정경쟁규약'
        )

        # 답변 생성
        answer = engine.generate_answer(query_text, [dummy_result])
        print(answer)
        print("=" * 70)


if __name__ == "__main__":
    main()