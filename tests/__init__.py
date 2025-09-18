"""
NaruTalk System Test Suite
시스템 종합 테스트 스위트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# 테스트 환경 설정
os.environ["TESTING"] = "true"
os.environ["DATABASE_API_URL"] = "http://localhost:8002/api/v1"
os.environ["API_HOST"] = "localhost"
os.environ["API_PORT"] = "8001"