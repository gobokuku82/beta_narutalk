"""
Import 체크 스크립트
필요한 패키지들이 올바르게 설치되었는지 확인
"""

import sys

def check_imports():
    """필수 import 확인"""

    results = []

    # LangGraph 관련
    try:
        from langgraph.graph import StateGraph, START, END
        results.append(("✓", "langgraph.graph"))
    except ImportError as e:
        results.append(("✗", f"langgraph.graph: {e}"))

    try:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        results.append(("✓", "langgraph.checkpoint.sqlite.aio (AsyncSqliteSaver)"))
    except ImportError as e:
        results.append(("✗", f"AsyncSqliteSaver: {e}"))

    # 대안 경로들 시도
    alternatives = [
        "from langgraph.checkpoint.sqlite import AsyncSqliteSaver",
        "from langgraph_checkpoint_sqlite.aio import AsyncSqliteSaver",
        "from langgraph_checkpoint_sqlite import AsyncSqliteSaver",
    ]

    for alt in alternatives:
        try:
            exec(alt)
            results.append(("✓", f"Alternative: {alt}"))
            break
        except:
            continue

    # ChromaDB
    try:
        import chromadb
        results.append(("✓", "chromadb"))
    except ImportError as e:
        results.append(("✗", f"chromadb: {e}"))

    # SQLite
    try:
        import sqlite3
        results.append(("✓", "sqlite3 (내장)"))
    except ImportError as e:
        results.append(("✗", f"sqlite3: {e}"))

    # 결과 출력
    print("\n=== Import 체크 결과 ===\n")

    for status, msg in results:
        print(f"{status} {msg}")

    # langgraph-checkpoint-sqlite 패키지 정보 확인
    print("\n=== 패키지 정보 ===\n")

    try:
        import langgraph_checkpoint_sqlite
        print(f"langgraph-checkpoint-sqlite 버전: {getattr(langgraph_checkpoint_sqlite, '__version__', 'unknown')}")
        print(f"모듈 경로: {langgraph_checkpoint_sqlite.__file__}")

        # 사용 가능한 속성 확인
        attrs = dir(langgraph_checkpoint_sqlite)
        print(f"\n사용 가능한 클래스/함수:")
        for attr in attrs:
            if not attr.startswith('_'):
                print(f"  - {attr}")

    except ImportError:
        print("langgraph-checkpoint-sqlite 패키지를 찾을 수 없습니다.")
        print("\n설치 명령어:")
        print("  pip install langgraph-checkpoint-sqlite")

if __name__ == "__main__":
    check_imports()