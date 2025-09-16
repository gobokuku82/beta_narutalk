현재 LangGraph 0.6.7 기반의 Supervisor 챗봇을 하이브리드 방식으로 리팩토링하려고 합니다.

## 현재 상황
- LangGraph 0.6.7과 supervisor 패턴 사용 중
- backend/agents/에 graph.py, state.py, supervisor.py 파일 존재
- backend/agents/supervisor/ 폴더에 6개 supervisor 컴포넌트 존재
- 현재 Direct Node 방식만 사용 중, Tool-based 코드는 레거시

## 목표
하이브리드 Supervisor 구현:
1. 고정된 메타 플로우 (Intent Analysis → Planning은 순차 진행)
2. 동적 에이전트 선택 (Planning 이후 LLM이 실행할 에이전트 동적 선택)
3. Tool-based와 Direct Node의 장점 결합

## 작업 요청사항

### 1. 새로운 하이브리드 구조 생성
`backend/agents/hybrid_supervisor.py` 파일을 생성해주세요:
- HybridSupervisor 클래스 구현
- 고정 플로우: intent_analysis → planning → dynamic_execution
- dynamic_execution에서 LLM이 Tool로 에이전트 선택
- 병렬 실행 가능한 에이전트는 동시 실행

### 2. Tool 구조 개선
- 각 실행 에이전트(data_analysis, info_retrieval 등)를 StructuredTool로 래핑
- Pydantic 스키마로 입력/출력 검증
- Tool 설명을 LLM이 이해하기 쉽게 상세히 작성

### 3. 동적 라우팅 로직
`dynamic_execution_node`에서:
- 현재 상태와 실행 계획을 분석
- 의존성 없는 에이전트들은 병렬 실행 결정
- 실행 결과를 평가하여 다음 단계 결정
- 에러 발생 시 대체 에이전트 선택

### 4. graph.py 수정
기존 순차 실행 대신:
```python
# 기존: A → B → C → D
# 개선: A → B → Dynamic(C|D|E 중 LLM 선택)
5. 상태 관리 개선
GlobalSessionState에 추가:

dynamic_decisions: LLM의 선택 기록
parallel_executions: 병렬 실행 정보
decision_reasoning: 선택 이유 저장

6. 테스트 케이스
tests/test_hybrid_supervisor.py 생성:

단순 질의 테스트 (단일 에이전트)
복잡한 질의 테스트 (다중 에이전트)
병렬 실행 테스트
에러 복구 테스트

코드 스타일 요구사항

Type hints 필수 사용
Docstring으로 각 메서드 설명
비동기 처리 (async/await) 일관성 유지
로깅 추가 (logger.info, logger.error)
에러 처리 강화 (try-except with specific exceptions)

파일 구조
backend/agents/
├── hybrid_supervisor.py (새로 생성)
├── graph.py (수정)
├── state.py (수정)
├── tools/ (새 폴더)
│   ├── __init__.py
│   ├── agent_tools.py (에이전트를 Tool로 래핑)
│   └── schemas.py (Pydantic 스키마)
└── supervisor/ (기존 유지하되 통합)
구현 예시 시작 코드
pythonfrom typing import List, Dict, Any, Optional
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class AgentSelectionInput(BaseModel):
    """LLM의 에이전트 선택 입력"""
    task_description: str = Field(description="수행할 작업 설명")
    required_data: Dict[str, Any] = Field(description="필요한 데이터")
    constraints: Optional[List[str]] = Field(description="제약 사항")

class HybridSupervisor:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.fixed_nodes = ["intent_analysis", "planning"]
        self.dynamic_tools = self._create_agent_tools()
    
    def _create_agent_tools(self) -> List[StructuredTool]:
        # 각 에이전트를 Tool로 변환
        pass
    
    async def dynamic_execution_node(self, state: GlobalSessionState):
        # LLM이 다음 실행할 에이전트 선택
        pass
주의사항

기존 supervisor/ 폴더의 intent_analyzer.py와 planner.py는 그대로 유지
execution_manager_node부터 새로운 dynamic 방식 적용
백워드 호환성 유지 (기존 API 엔드포인트 동작)
성능 최적화: 불필요한 LLM 호출 최소화
캐싱 정책 유지 및 개선

검증 기준

 기존 순차 실행과 동일한 결과 보장
 병렬 실행 시 성능 향상 확인
 LLM의 선택 이유가 명확히 로깅됨
 에러 발생 시 graceful degradation
 모든 테스트 통과

이 작업을 단계별로 진행해주시고, 각 단계마다 변경사항을 설명해주세요.