"""
좋은제약 내부 규정 검색 API
다른 모듈에서 import해서 사용할 수 있는 간단한 인터페이스
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional


class HRRulesAPI:
    """내부 규정 검색 API"""

    def __init__(self, db_path: str = "./chromadb"):
        """ChromaDB 초기화"""
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        try:
            self.collection = self.client.get_collection(name="internal_regulations")
            self.is_connected = True
        except:
            self.collection = None
            self.is_connected = False

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        간단한 검색 함수

        사용 예:
            api = HRRulesAPI("./chromadb")
            results = api.search("연차 휴가", top_k=3)
        """
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )

            # 결과 정리
            output = []
            if results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    output.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i]
                    })
            return output

        except:
            return []

    def get_by_article(self, article_num: str) -> List[Dict]:
        """
        조항 번호로 검색

        사용 예:
            api = HRRulesAPI("./chromadb")
            results = api.get_by_article("7")  # 제7조 검색
        """
        if not article_num.startswith('제'):
            article_num = f"제{article_num}조"
        elif not article_num.endswith('조'):
            article_num += '조'

        return self.search(article_num, top_k=3)

    def get_by_topic(self, topic: str) -> List[Dict]:
        """
        주제별 검색

        Args:
            topic: "윤리", "인사", "복무", "휴가", "징계" 등
        """
        topic_keywords = {
            "윤리": "윤리강령 CP 준법 공정거래",
            "인사": "채용 평가 승진 직급",
            "복무": "근무 의무 금지사항",
            "휴가": "연차 휴일 휴직",
            "징계": "제재 처벌 징계"
        }

        query = topic_keywords.get(topic, topic)
        return self.search(query, top_k=5)


# 간단한 함수형 인터페이스
def quick_search(query: str, db_path: str = "./chromadb") -> List[str]:
    """
    가장 간단한 검색 함수

    사용 예:
        from hr_rules_api import quick_search
        results = quick_search("휴가 규정")
        for result in results:
            print(result)
    """
    api = HRRulesAPI(db_path)
    results = api.search(query, top_k=3)

    # 텍스트만 반환
    return [r['text'][:200] + "..." for r in results]


# 사용 예제
if __name__ == "__main__":
    # API 테스트
    api = HRRulesAPI("./chromadb")

    if api.is_connected:
        print("DB 연결 성공\n")

        # 일반 검색
        print("=== 일반 검색: '윤리' ===")
        results = api.search("윤리", top_k=2)
        for r in results:
            print(f"- {r['text'][:100]}...")
            print(f"  부: {r['metadata'].get('part', 'N/A')}\n")

        # 조항 검색
        print("=== 조항 검색: 제7조 ===")
        results = api.get_by_article("7")
        for r in results:
            print(f"- {r['text'][:100]}...")

        # 주제별 검색
        print("\n=== 주제 검색: '휴가' ===")
        results = api.get_by_topic("휴가")
        for r in results:
            print(f"- {r['text'][:100]}...")

    else:
        print("DB 연결 실패")