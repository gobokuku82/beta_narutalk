# 📊 Backend vs Microservices 폴더 구조 분석 리포트

## 📋 개요

현재 프로젝트에는 **2개의 서로 다른 아키텍처**가 공존하고 있습니다:
- `backend/` - 기존 단일 FastAPI 시스템 (복잡한 구조, 의존성 오류)
- `microservices_narutalk/` - 새로운 마이크로서비스 아키텍처 (완전 독립적)

## 🔍 상세 구조 분석

### 1️⃣ Backend 폴더 (기존 시스템)

#### 📁 폴더 구조
```
backend/
├── main.py                     # FastAPI 진입점
└── app/
    ├── agents/                 # ❌ 에이전트 폴더 (빈 폴더들)
    │   ├── document_search/    # 빈 폴더
    │   ├── document_draft/     # 빈 폴더
    │   ├── performance_analysis/  # 빈 폴더
    │   ├── client_analysis/    # 빈 폴더
    │   └── __init__.py         # ❌ 깨진 import 참조
    ├── api/
    │   ├── router.py           # 메인 라우터 (85줄)
    │   └── routers/            # API 엔드포인트
    │       ├── tool_calling.py # Tool Calling 라우터 (108줄)
    │       ├── simple.py       # 간단한 라우터 (90줄)
    │       └── document.py     # 문서 라우터 (157줄)
    └── services/
        ├── tool_calling_router.py    # Tool Calling 로직 (273줄)
        ├── simple_router.py          # 간단한 라우터 로직 (134줄)
        ├── embedding_service.py      # 임베딩 서비스 (274줄)
        ├── database_service.py       # 데이터베이스 서비스 (260줄)
        └── routers/                  # ❌ Legacy 라우터들
            ├── document_search_router.py    # 문서검색 (160줄)
            ├── report_generator_router.py   # 리포트 생성 (99줄)
            ├── analysis_router.py           # 분석 (96줄)
            ├── employee_info_router.py      # 직원정보 (116줄)
            ├── general_chat_router.py       # 일반대화 (177줄)
            ├── qa_router.py                 # Q&A (135줄)
            └── base_router.py               # 기본 라우터 (193줄)
```

#### ⚠️ 문제점
1. **깨진 의존성**: `base_agent` 모듈 삭제로 import 오류
2. **중복 구조**: 3개의 서로 다른 라우터 시스템이 공존
3. **빈 에이전트 폴더**: agents/ 하위 폴더들이 실제로는 빈 폴더
4. **복잡한 의존성**: 여러 서비스가 서로 복잡하게 연결됨

#### 📊 코드 분석
- **총 파일 수**: 약 15개
- **총 코드량**: 약 2,000줄
- **실행 상태**: ❌ 의존성 오류로 불안정
- **아키텍처**: 단일 FastAPI 애플리케이션

### 2️⃣ Microservices 폴더 (새 시스템)

#### 📁 폴더 구조
```
microservices_narutalk/
├── django_manager/             # Django 관리 시스템 (포트: 8000)
│   ├── narutalk_manager/       # Django 프로젝트 설정
│   ├── services/               # 서비스 관리 앱
│   └── monitoring/             # 모니터링 앱
├── agents/                     # ✅ 5개 독립 FastAPI 에이전트
│   ├── router_agent/           # 라우터 에이전트 (포트: 8001)
│   ├── document_agent/         # 문서 검색 에이전트 (포트: 8002)
│   ├── employee_agent/         # 직원 분석 에이전트 (포트: 8003)
│   ├── client_agent/           # 고객 정보 에이전트 (포트: 8004)
│   └── general_agent/          # 일반 대화 에이전트 (포트: 8005)
├── run_all_services.py         # 통합 실행 스크립트
├── requirements.txt            # 의존성 목록
└── README.md                   # 사용 설명서
```

#### ✅ 장점
1. **완전한 독립성**: 각 에이전트가 독립적인 서비스
2. **명확한 책임**: 각 서비스의 역할이 명확하게 분리
3. **확장성**: 개별 서비스 스케일링 가능
4. **안정성**: 한 서비스 장애가 전체에 영향 안 줌

#### 📊 코드 분석
- **총 파일 수**: 25개
- **총 코드량**: 약 1,500줄
- **실행 상태**: ✅ 정상 작동
- **아키텍처**: Django + 5개 독립 FastAPI 서비스

## 🔄 두 시스템의 관계

### 📈 진화 과정
```
단계 1: 단일 FastAPI 시스템 (backend/)
        ↓
단계 2: 복잡한 라우터 시스템 추가
        ↓
단계 3: Agent 시스템 시도 (실패)
        ↓
단계 4: 마이크로서비스 아키텍처 (microservices/)
```

### 🎯 핵심 차이점

| 구분 | Backend 폴더 | Microservices 폴더 |
|------|-------------|-------------------|
| **아키텍처** | 단일 FastAPI 앱 | Django + 5개 FastAPI |
| **에이전트** | 빈 폴더 (실제 구현 없음) | 실제 구현된 5개 에이전트 |
| **의존성** | 복잡하고 깨진 구조 | 명확하고 독립적 |
| **확장성** | 제한적 | 무한 확장 가능 |
| **유지보수** | 어려움 | 쉬움 |
| **실행 상태** | 불안정 | 안정적 |

### 🔗 관계 맵핑

#### Backend → Microservices 변환
```
backend/app/agents/document_search/     → microservices/agents/document_agent/
backend/app/agents/performance_analysis/ → microservices/agents/employee_agent/
backend/app/agents/client_analysis/     → microservices/agents/client_agent/
backend/app/agents/document_draft/      → (일반대화 에이전트로 통합)
backend/app/services/routers/           → (각 에이전트 내부 로직으로 분산)
```

## 🎯 라우터 에이전트 고도화 계획

### 🚀 목표
**OpenAI GPT-4o를 사용한 지능형 라우터 에이전트 구현**

### 📋 구현 계획

#### 1단계: 환경 설정
```bash
# .env 파일 생성 (microservices_narutalk/.env)
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o
```

#### 2단계: Tool Calling 구조 설계
```python
# 4개 에이전트 Tool 정의
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "좋은제약 내부 문서, 정책, 규정, 윤리강령 등을 검색합니다. 문서 관련 질문이나 회사 정책에 대한 문의시 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 키워드나 질문"},
                    "document_type": {"type": "string", "enum": ["policy", "regulation", "ethics", "all"]}
                }
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "analyze_employee_data",
            "description": "직원 정보, 성과 분석, 출근 현황, 부서별 통계 등을 분석합니다. 인사 관련 질문이나 직원 데이터 분석이 필요할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_type": {"type": "string", "enum": ["performance", "attendance", "general", "department"]},
                    "employee_id": {"type": "string", "description": "특정 직원 ID (선택적)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_client_information", 
            "description": "고객사 정보, 거래 내역, 계약 현황, 매출 분석 등을 조회합니다. 고객 관련 문의나 영업 데이터 분석시 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "info_type": {"type": "string", "enum": ["basic", "transactions", "contracts", "analytics"]},
                    "client_id": {"type": "string", "description": "특정 고객 ID (선택적)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "general_conversation",
            "description": "일반적인 대화, 인사말, 간단한 질문 답변을 처리합니다. 위의 전문 영역에 해당하지 않는 일반적인 대화시 사용합니다.",
            "parameters": {
                "type": "object", 
                "properties": {
                    "message": {"type": "string", "description": "사용자 메시지"},
                    "conversation_context": {"type": "string", "description": "대화 맥락 (선택적)"}
                }
            }
        }
    }
]
```

#### 3단계: 라우터 에이전트 구현
```python
# microservices_narutalk/agents/router_agent/enhanced_main.py
import openai
from typing import Dict, Any
import json
import os
from dotenv import load_dotenv

class EnhancedRouterAgent:
    def __init__(self):
        load_dotenv()
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.tools = tools  # 위에서 정의한 tools
        
    async def route_with_gpt4o(self, user_message: str) -> Dict[str, Any]:
        """GPT-4o를 사용한 지능형 라우팅"""
        
        system_prompt = """
        당신은 좋은제약 AI 어시스턴트의 라우터입니다. 
        사용자의 질문을 분석하여 적절한 전문 에이전트에게 전달해야 합니다.
        
        4개의 전문 에이전트:
        1. 문서검색 에이전트 - 회사 정책, 규정, 문서 검색
        2. 직원분석 에이전트 - 인사 데이터, 성과 분석  
        3. 고객정보 에이전트 - 고객사 정보, 거래 분석
        4. 일반대화 에이전트 - 기타 일반적인 대화
        
        사용자 질문에 가장 적합한 에이전트의 function을 호출하세요.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            tools=self.tools,
            tool_choice="auto"
        )
        
        return response
```

#### 4단계: 구현 순서
1. **환경 설정**: `.env` 파일 생성 및 OpenAI API 키 설정
2. **라우터 에이전트 업그레이드**: GPT-4o 기반 라우팅 로직 구현
3. **Tool Calling 연동**: 각 에이전트별 Function 정의
4. **테스트 및 최적화**: 라우팅 정확도 향상

## 🔮 권장사항

### 즉시 수행할 작업
1. **Backend 폴더 정리**: 사용하지 않는 legacy 코드 제거
2. **Microservices 중심 개발**: 새로운 기능은 microservices에서 구현
3. **라우터 에이전트 우선 완성**: GPT-4o 기반 지능형 라우팅 구현

### 장기 계획
1. Backend 폴더 완전 폐기
2. Microservices 아키텍처로 통합
3. 각 에이전트별 고도화 순차 진행

---

**결론**: 현재 Backend 폴더는 복잡하고 불안정한 구조로, Microservices 폴더의 새로운 아키텍처가 훨씬 우수합니다. 라우터 에이전트 고도화를 통해 GPT-4o 기반의 지능형 라우팅 시스템을 구축하는 것이 최적의 방향입니다. 