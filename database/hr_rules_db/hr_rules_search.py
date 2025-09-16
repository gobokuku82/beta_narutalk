"""
좋은제약 내부 규정 검색 시스템
ChromaDB를 사용한 검색 기능만 포함
"""

import chromadb
from chromadb.config import Settings
import sys
import os
from typing import List, Dict, Optional

# Windows 콘솔 UTF-8 설정
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')


class HRRulesSearch:
    """내부 규정 검색 클래스"""

    def __init__(self, db_path: str = "./chromadb"):
        """
        Args:
            db_path: ChromaDB 경로
        """
        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )

        # 컬렉션 가져오기
        try:
            self.collection = self.client.get_collection(name="internal_regulations")
            print(f"[OK] ChromaDB 연결 성공")
            print(f"    문서 수: {self.collection.count()}개")
        except Exception as e:
            print(f"[ERROR] 컬렉션을 찾을 수 없습니다: {e}")
            self.collection = None

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        텍스트 검색

        Args:
            query: 검색어
            top_k: 반환할 결과 수

        Returns:
            검색 결과 리스트
        """
        if not self.collection:
            print("[ERROR] 컬렉션이 초기화되지 않았습니다.")
            return []

        try:
            # ChromaDB 자체 임베딩으로 검색
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )

            # 결과 포맷팅
            formatted_results = []
            if results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    formatted_results.append(result)

            return formatted_results

        except Exception as e:
            print(f"[ERROR] 검색 실패: {e}")
            return []

    def search_by_part(self, part_num: str, query: str = "", top_k: int = 5) -> List[Dict]:
        """
        부별 검색

        Args:
            part_num: 부 번호 (1, 2, 3, 4) 또는 이름
            query: 추가 검색어 (선택)
            top_k: 반환할 결과 수
        """
        part_map = {
            "1": "제1부_취업규칙",
            "2": "제2부_인사관리규정",
            "3": "제3부_복무규정",
            "4": "제4부_윤리강령_CP",
            "취업": "제1부_취업규칙",
            "인사": "제2부_인사관리규정",
            "복무": "제3부_복무규정",
            "윤리": "제4부_윤리강령_CP"
        }

        part_name = part_map.get(part_num, part_num)

        if not query:
            query = "규정"

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k * 2,  # 더 많이 가져와서 필터링
                where={"part": part_name}
            )

            formatted_results = []
            if results['ids'][0]:
                for i in range(min(top_k, len(results['ids'][0]))):
                    result = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    formatted_results.append(result)

            return formatted_results

        except Exception as e:
            print(f"[ERROR] 부별 검색 실패: {e}")
            return []

    def search_by_keyword(self, keyword: str, top_k: int = 5) -> List[Dict]:
        """
        키워드 검색 (메타데이터 활용)

        Args:
            keyword: 검색 키워드
            top_k: 반환할 결과 수
        """
        try:
            # 키워드가 포함된 문서 검색
            results = self.collection.query(
                query_texts=[keyword],
                n_results=top_k,
                where_document={"$contains": keyword}
            )

            formatted_results = []
            if results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    formatted_results.append(result)

            return formatted_results

        except Exception as e:
            print(f"[ERROR] 키워드 검색 실패: {e}")
            return []

    def get_statistics(self) -> Dict:
        """DB 통계 반환"""
        if not self.collection:
            return {"error": "컬렉션이 초기화되지 않았습니다."}

        try:
            total = self.collection.count()

            # 샘플 데이터로 통계 추정
            sample = self.collection.get(limit=min(100, total))

            stats = {
                'total_documents': total,
                'collection_name': 'internal_regulations',
                'parts': {},
                'chunk_types': {}
            }

            # 메타데이터 분석
            for metadata in sample['metadatas']:
                # 부별 통계
                part = metadata.get('part', 'unknown')
                if part:
                    stats['parts'][part] = stats['parts'].get(part, 0) + 1

                # 청크 타입별 통계
                chunk_type = metadata.get('chunk_type', 'unknown')
                stats['chunk_types'][chunk_type] = stats['chunk_types'].get(chunk_type, 0) + 1

            return stats

        except Exception as e:
            return {"error": str(e)}

    def print_result(self, result: Dict, index: int = 1):
        """검색 결과 출력"""
        print(f"\n[{index}] ID: {result['id']}")
        print(f"텍스트: {result['text'][:200]}...")

        metadata = result['metadata']
        print(f"부: {metadata.get('part', 'N/A')}")
        print(f"조항: {metadata.get('article_nums', 'N/A')}")
        print(f"키워드: {metadata.get('keywords', 'N/A')}")
        print(f"중요도: {metadata.get('importance_score', 'N/A')}")

        if result['distance']:
            print(f"거리: {result['distance']:.4f}")


def main():
    """메인 실행 함수"""
    print("="*60)
    print("좋은제약 내부 규정 검색 시스템")
    print("="*60)

    # 검색 시스템 초기화
    searcher = HRRulesSearch(db_path="./chromadb")

    if not searcher.collection:
        print("\n[ERROR] DB 연결 실패. 경로를 확인하세요.")
        return

    # 통계 출력
    stats = searcher.get_statistics()
    print(f"\n총 문서: {stats.get('total_documents', 0)}개")

    print("\n명령어:")
    print("  - 일반 검색: 검색어 입력")
    print("  - 부별 검색: part:1~4 검색어")
    print("  - 키워드 검색: key:키워드")
    print("  - 통계: stats")
    print("  - 종료: quit 또는 exit")

    while True:
        try:
            query = input("\n검색어 입력 > ").strip()

            if query.lower() in ['quit', 'exit', '종료']:
                print("검색 시스템을 종료합니다.")
                break

            elif query.lower() == 'stats':
                stats = searcher.get_statistics()
                print("\n=== DB 통계 ===")
                print(f"총 문서: {stats['total_documents']}개")
                print("\n부별 분포:")
                for part, count in stats.get('parts', {}).items():
                    if part:
                        print(f"  - {part}: {count}개")
                print("\n청크 타입:")
                for ctype, count in stats.get('chunk_types', {}).items():
                    print(f"  - {ctype}: {count}개")

            elif query.startswith('part:'):
                # 부별 검색
                parts = query.split()
                part_num = parts[0].replace('part:', '')
                search_query = ' '.join(parts[1:]) if len(parts) > 1 else ""

                results = searcher.search_by_part(part_num, search_query, top_k=5)

                if results:
                    print(f"\n검색 결과: {len(results)}개")
                    for i, result in enumerate(results, 1):
                        searcher.print_result(result, i)
                else:
                    print("검색 결과가 없습니다.")

            elif query.startswith('key:'):
                # 키워드 검색
                keyword = query.replace('key:', '').strip()
                results = searcher.search_by_keyword(keyword, top_k=5)

                if results:
                    print(f"\n검색 결과: {len(results)}개")
                    for i, result in enumerate(results, 1):
                        searcher.print_result(result, i)
                else:
                    print("검색 결과가 없습니다.")

            else:
                # 일반 검색
                results = searcher.search(query, top_k=5)

                if results:
                    print(f"\n검색 결과: {len(results)}개")
                    for i, result in enumerate(results, 1):
                        searcher.print_result(result, i)
                else:
                    print("검색 결과가 없습니다.")

        except KeyboardInterrupt:
            print("\n\n검색 시스템을 종료합니다.")
            break
        except Exception as e:
            print(f"오류 발생: {e}")


if __name__ == "__main__":
    main()