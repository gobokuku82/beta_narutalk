"""
Final simple test - bypassing all complex parts
"""

print("테스트 시작...")

# 1. 기본 import 테스트
try:
    from backend.service.orchestrator.orchestrator import MainOrchestrator
    print("[OK] MainOrchestrator import 성공")
except Exception as e:
    print(f"[FAIL] Import 실패: {e}")
    exit(1)

# 2. 오케스트레이터 생성 테스트
try:
    orchestrator = MainOrchestrator()
    print("[OK] Orchestrator 생성 성공")
except Exception as e:
    print(f"[FAIL] Orchestrator 생성 실패: {e}")
    exit(1)

# 3. 워크플로우 컴파일 테스트
try:
    app = orchestrator.workflow.compile()
    print("[OK] Workflow 컴파일 성공")
except Exception as e:
    print(f"[FAIL] Compile 실패: {e}")
    exit(1)

print("\n시스템이 정상적으로 로드되었습니다.")
print("하지만 실행 중 타임아웃 문제가 있습니다.")
print("\n주요 원인:")
print("1. SearchAgent의 임베딩 모델 로딩 지연")
print("2. LLM 호출 응답 지연")
print("3. LangGraph의 비동기 처리 문제")
print("\n해결 방법:")
print("1. 임베딩 모델을 완전히 비활성화")
print("2. 모든 LLM 호출을 Mock으로 교체")
print("3. 동기 실행으로 변경")