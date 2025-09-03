#!/usr/bin/env python
"""
경로 테스트 스크립트
실제로 각 데이터베이스 경로가 올바르게 설정되는지 확인
"""

import sys
from pathlib import Path

# backend 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.config import settings

print("=== 경로 확인 ===")
print(f"현재 작업 디렉토리: {Path.cwd()}")
print(f"\nBASE_DIR (backend/app): {settings.BASE_DIR}")
print(f"ROOT_DIR (프로젝트 루트): {settings.ROOT_DIR}")
print(f"\n데이터베이스 디렉토리:")
print(f"DATABASE_DIR: {settings.DATABASE_DIR}")
print(f"  존재 여부: {settings.DATABASE_DIR.exists()}")
print(f"\n하위 디렉토리:")
print(f"VECTOR_DB_DIR: {settings.VECTOR_DB_DIR}")
print(f"  존재 여부: {settings.VECTOR_DB_DIR.exists()}")
print(f"DOCUMENTS_DIR: {settings.DOCUMENTS_DIR}")
print(f"  존재 여부: {settings.DOCUMENTS_DIR.exists()}")
print(f"RULE_DB_DIR: {settings.RULE_DB_DIR}")
print(f"  존재 여부: {settings.RULE_DB_DIR.exists()}")
print(f"RELATION_DB_DIR: {settings.RELATION_DB_DIR}")
print(f"  존재 여부: {settings.RELATION_DB_DIR.exists()}")

print(f"\n.env 파일 경로: {settings.Config.env_file}")
print(f"  존재 여부: {Path(settings.Config.env_file).exists()}")

# 실제 파일 경로 예시
print(f"\n실제 사용 예시:")
print(f"sales.db 경로: {settings.RELATION_DB_DIR / 'sales.db'}")
print(f"templates 디렉토리: {settings.DOCUMENTS_DIR / 'templates'}")
print(f"generated 디렉토리: {settings.DOCUMENTS_DIR / 'generated'}")