#!/usr/bin/env python3
"""
NaruTalk AI 챗봇 서버 실행 스크립트
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path

# 경로 설정
project_root = Path(__file__).parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

def check_requirements():
    """필요한 의존성 확인"""
    # 패키지 이름: (pip 이름, import 이름)
    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('langchain', 'langchain'),
        ('langchain-core', 'langchain_core'),
        ('langchain-community', 'langchain_community'),
        ('langgraph', 'langgraph'),
        ('sentence-transformers', 'sentence_transformers'),
        ('chromadb', 'chromadb'),
        ('transformers', 'transformers'),
        ('torch', 'torch'),
        ('pytest', 'pytest')
    ]
    
    missing_packages = []
    for pip_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("❌ 다음 패키지가 설치되지 않았습니다:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n설치 명령어:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_directories():
    """필요한 디렉토리 확인"""
    essential_dirs = [
        "backend",
        "frontend",
        "database"
    ]
    optional_dirs = [
        "models",  # 허깅페이스 모델 사용 시 선택사항
        "tests"
    ]
    
    missing_essential = []
    missing_optional = []
    
    for dir_name in essential_dirs:
        if not (project_root / dir_name).exists():
            missing_essential.append(dir_name)
    
    for dir_name in optional_dirs:
        if not (project_root / dir_name).exists():
            missing_optional.append(dir_name)
    
    if missing_essential:
        print("❌ 다음 필수 디렉토리가 없습니다:")
        for dir_name in missing_essential:
            print(f"  - {dir_name}")
        return False
    
    if missing_optional:
        print("⚠️  다음 선택 디렉토리가 없습니다:")
        for dir_name in missing_optional:
            print(f"  - {dir_name}")
        print("선택 디렉토리는 시스템 작동에 필수가 아닙니다.")
    
    return True

def check_models():
    """모델 파일 확인"""
    model_dirs = [
        "models/KURE-V1",
        "models/bge-reranker-v2-m3-ko"
    ]
    
    missing_models = []
    for model_dir in model_dirs:
        if not (project_root / model_dir).exists():
            missing_models.append(model_dir)
    
    if missing_models:
        print("⚠️  다음 모델 디렉토리가 없습니다:")
        for model_dir in missing_models:
            print(f"  - {model_dir}")
        print("임베딩 기능에 제한이 있을 수 있습니다.")
        return False
    
    return True

def setup_environment():
    """환경 설정"""
    # 환경 변수 설정
    os.environ.setdefault('PYTHONPATH', str(backend_path))
    
    # 로그 레벨 설정
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    print("✅ 환경 설정 완료")

def main():
    """메인 함수"""
    print("🚀 NaruTalk AI 챗봇 시스템 시작")
    print("=" * 50)
    
    # 1. 의존성 확인
    print("1. 의존성 확인 중...")
    if not check_requirements():
        sys.exit(1)
    print("✅ 의존성 확인 완료")
    
    # 2. 디렉토리 확인
    print("\n2. 디렉토리 구조 확인 중...")
    if not check_directories():
        sys.exit(1)
    print("✅ 디렉토리 구조 확인 완료")
    
    # 3. 모델 확인
    print("\n3. 모델 파일 확인 중...")
    models_ok = check_models()
    if models_ok:
        print("✅ 모델 파일 확인 완료")
    
    # 4. 환경 설정
    print("\n4. 환경 설정 중...")
    setup_environment()
    
    # 5. 서버 시작
    print("\n5. 서버 시작 중...")
    print("=" * 50)
    print("📌 서버 정보:")
    print("   - 주소: http://localhost:8000")
    print("   - API 문서: http://localhost:8000/docs")
    print("   - 테스트 페이지: http://localhost:8000/tests/test_frontend.html")
    print("   - 중지: Ctrl+C")
    print("=" * 50)
    
    try:
        # FastAPI 서버 시작
        os.chdir(backend_path)
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(backend_path)],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n🛑 서버가 중지되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 시작 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 