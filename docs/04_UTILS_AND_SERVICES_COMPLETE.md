# Utils 및 Services 완전 상세 문서

## 개요
Utils 모듈은 LLM 관리, 프롬프트 템플릿, 토큰 추적 등의 공통 유틸리티를 제공합니다. Services는 메인 실행 진입점을 포함합니다.

---

## 1. Utils Module Init

### 파일: `backend/service/utils/__init__.py`

#### 파일 목적
Utils 모듈의 공개 API를 정의하고 내보내기

#### 코드
```python
from .llm_manager import LLMManager
from .prompt_templates import PromptTemplates
from .token_tracker import TokenTracker

__all__ = ['LLMManager', 'PromptTemplates', 'TokenTracker']
```

#### 내보낸 클래스
- `LLMManager`: 중앙 집중식 LLM 호출 관리
- `PromptTemplates`: 프롬프트 템플릿 관리
- `TokenTracker`: 토큰 사용량 추적 및 비용 관리

---

## 2. LLM Manager

### 파일: `backend/service/utils/llm_manager.py`

#### 파일 목적
싱글톤 패턴을 사용한 중앙 집중식 LLM 관리. 여러 모델 구성, 캐싱, 토큰 추적을 제공합니다.

#### Imports 및 Dependencies
```python
import os
import hashlib
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
```

#### 환경 변수 로드
```python
load_dotenv()
logger = logging.getLogger(__name__)
```

---

### LLMManager 클래스 (싱글톤)

#### 클래스 정의 및 싱글톤 구현
```python
class LLMManager:
    """
    중앙 집중식 LLM 관리자 (싱글톤 패턴)

    특징:
    - 여러 LLM 클라이언트 구성 지원
    - 응답 캐싱으로 비용 절감
    - 토큰 사용량 추적
    - 배치 처리 지원
    - 에러 처리 및 폴백
    """

    _instance = None
    _initialized = False
```

#### 싱글톤 패턴 구현
```python
def __new__(cls):
    """싱글톤 인스턴스 생성"""
    if cls._instance is None:
        cls._instance = super().__new__(cls)
    return cls._instance

def __init__(self):
    """초기화 (한 번만 실행)"""
    if not self._initialized:
        self._initialize()
        self.__class__._initialized = True
```

#### 초기화 메서드 (_initialize)
```python
def _initialize(self):
    """LLM 클라이언트 및 설정 초기화"""

    # API 키 검증
    self.api_key = os.getenv("OPENAI_API_KEY")
    if not self.api_key:
        logger.error("OPENAI_API_KEY not found in environment")
        raise ValueError("OpenAI API key is required")

    # LLM 클라이언트 구성
    self.clients = {
        # 일반 대화용 (창의적 응답)
        "openai": ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=2000,
            api_key=self.api_key
        ),

        # SQL 생성, 컴플라이언스 검토용 (정확도 중시)
        "openai_strict": ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            max_tokens=1500,
            api_key=self.api_key
        ),

        # 의도 분석, 간단한 작업용 (빠른 응답)
        "openai_mini": ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=1000,
            api_key=self.api_key
        ),

        # 문서 생성용 (균형잡힌 창의성)
        "openai_doc": ChatOpenAI(
            model="gpt-4o",
            temperature=0.5,
            max_tokens=3000,
            api_key=self.api_key
        )
    }

    # 캐시 초기화 (15분 TTL)
    self.cache = {}
    self.cache_ttl = timedelta(minutes=15)

    # 사용량 추적
    self.usage_stats = {
        "total_requests": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
        "by_model": {},
        "by_category": {}
    }

    logger.info("LLMManager initialized with 4 client configurations")
```

---

### 메인 생성 메서드

#### generate(self, prompt: str, model: str = "openai", system_prompt: Optional[str] = None, category: Optional[str] = None, use_cache: bool = True, **kwargs) -> Dict[str, Any]
```python
def generate(self, prompt: str, model: str = "openai",
             system_prompt: Optional[str] = None,
             category: Optional[str] = None,
             use_cache: bool = True,
             **kwargs) -> Dict[str, Any]:
    """
    LLM 응답 생성

    Args:
        prompt: 사용자 프롬프트
        model: 사용할 모델 구성 ('openai', 'openai_strict', 'openai_mini', 'openai_doc')
        system_prompt: 시스템 프롬프트 (선택)
        category: 사용 카테고리 (추적용)
        use_cache: 캐시 사용 여부
        **kwargs: 추가 LLM 파라미터

    Returns:
        {
            "content": "생성된 응답",
            "model": "사용된 모델",
            "usage": {...},
            "category": "카테고리",
            "timestamp": "생성 시간"
        }
    """

    # 캐시 키 생성
    if use_cache:
        cache_key = self._get_cache_key(prompt, model, system_prompt)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Cache hit for {category or 'general'}")
            return cached

    # 클라이언트 선택
    if model not in self.clients:
        logger.warning(f"Unknown model: {model}, using default")
        model = "openai"

    client = self.clients[model]

    # 메시지 구성
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    try:
        # LLM 호출
        response = client.invoke(messages, **kwargs)

        # 응답 파싱
        content = response.content if hasattr(response, 'content') else str(response)

        # 사용량 추출
        usage = {}
        if hasattr(response, 'usage_metadata'):
            usage = {
                "prompt_tokens": response.usage_metadata.get('prompt_tokens', 0),
                "completion_tokens": response.usage_metadata.get('completion_tokens', 0),
                "total_tokens": response.usage_metadata.get('total_tokens', 0)
            }
        elif hasattr(response, 'response_metadata'):
            token_usage = response.response_metadata.get('token_usage', {})
            usage = {
                "prompt_tokens": token_usage.get('prompt_tokens', 0),
                "completion_tokens": token_usage.get('completion_tokens', 0),
                "total_tokens": token_usage.get('total_tokens', 0)
            }

        # 사용량 추적
        self._track_usage(usage, model, category)

        # 결과 구성
        result = {
            "content": content,
            "model": model,
            "usage": usage,
            "category": category or "general",
            "timestamp": datetime.now().isoformat()
        }

        # 캐시 저장
        if use_cache:
            self._save_to_cache(cache_key, result)

        self.usage_stats["total_requests"] += 1

        logger.info(f"Generated response using {model} for {category or 'general'}")
        return result

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return self._handle_error(e, prompt, category)
```

---

### 배치 처리 메서드

#### generate_batch(self, prompts: List[Dict[str, Any]], concurrent_limit: int = 3) -> List[Dict[str, Any]]
```python
async def _generate_async(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """비동기 생성 래퍼"""
    return self.generate(**prompt_data)

async def _batch_generate_async(self, prompts: List[Dict[str, Any]],
                                concurrent_limit: int) -> List[Dict[str, Any]]:
    """비동기 배치 처리"""
    results = []

    # 동시 실행 제한을 위한 세마포어
    semaphore = asyncio.Semaphore(concurrent_limit)

    async def process_with_limit(prompt_data):
        async with semaphore:
            return await self._generate_async(prompt_data)

    # 모든 태스크 생성
    tasks = [process_with_limit(p) for p in prompts]

    # 동시 실행
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 예외 처리
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "content": "",
                "error": str(result),
                "model": prompts[i].get("model", "openai"),
                "category": prompts[i].get("category", "batch")
            })
        else:
            processed_results.append(result)

    return processed_results

def generate_batch(self, prompts: List[Dict[str, Any]],
                  concurrent_limit: int = 3) -> List[Dict[str, Any]]:
    """
    여러 프롬프트 배치 처리

    Args:
        prompts: 프롬프트 딕셔너리 리스트
                 각 딕셔너리는 generate() 메서드의 파라미터 포함
        concurrent_limit: 동시 실행 제한

    Returns:
        응답 리스트

    Example:
        prompts = [
            {"prompt": "질문1", "model": "openai"},
            {"prompt": "질문2", "model": "openai_mini", "category": "intent"}
        ]
        results = llm.generate_batch(prompts)
    """

    # 이벤트 루프 처리
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    results = loop.run_until_complete(
        self._batch_generate_async(prompts, concurrent_limit)
    )

    logger.info(f"Batch processed {len(prompts)} prompts")
    return results
```

---

### 캐시 관리 메서드

#### 캐시 키 생성
```python
def _get_cache_key(self, prompt: str, model: str,
                   system_prompt: Optional[str]) -> str:
    """캐시 키 생성 (MD5 해시)"""
    key_string = f"{model}:{system_prompt or ''}:{prompt}"
    return hashlib.md5(key_string.encode()).hexdigest()
```

#### 캐시 조회
```python
def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
    """캐시에서 조회"""
    if key in self.cache:
        entry = self.cache[key]
        # TTL 확인
        if datetime.now() - entry["cached_at"] < self.cache_ttl:
            return entry["data"]
        else:
            # 만료된 엔트리 삭제
            del self.cache[key]
    return None
```

#### 캐시 저장
```python
def _save_to_cache(self, key: str, data: Dict[str, Any]):
    """캐시에 저장"""
    self.cache[key] = {
        "data": data,
        "cached_at": datetime.now()
    }

    # 캐시 크기 제한 (최대 1000개)
    if len(self.cache) > 1000:
        # 가장 오래된 항목 제거
        oldest_key = min(self.cache.keys(),
                        key=lambda k: self.cache[k]["cached_at"])
        del self.cache[oldest_key]
```

#### 캐시 초기화
```python
def clear_cache(self):
    """캐시 초기화"""
    old_size = len(self.cache)
    self.cache.clear()
    logger.info(f"Cache cleared: {old_size} entries removed")
```

---

### 사용량 추적 메서드

#### 사용량 기록
```python
def _track_usage(self, usage: Dict[str, int], model: str,
                 category: Optional[str]):
    """토큰 사용량 추적"""

    # 전체 사용량
    self.usage_stats["total_tokens"] += usage.get("total_tokens", 0)

    # 모델별 사용량
    if model not in self.usage_stats["by_model"]:
        self.usage_stats["by_model"][model] = {
            "requests": 0,
            "tokens": 0
        }
    self.usage_stats["by_model"][model]["requests"] += 1
    self.usage_stats["by_model"][model]["tokens"] += usage.get("total_tokens", 0)

    # 카테고리별 사용량
    if category:
        if category not in self.usage_stats["by_category"]:
            self.usage_stats["by_category"][category] = {
                "requests": 0,
                "tokens": 0
            }
        self.usage_stats["by_category"][category]["requests"] += 1
        self.usage_stats["by_category"][category]["tokens"] += usage.get("total_tokens", 0)

    # 비용 추정
    cost = self._estimate_cost()
    self.usage_stats["total_cost"] = cost["total"]
```

#### 비용 추정
```python
def _estimate_cost(self) -> Dict[str, float]:
    """토큰 사용량 기반 비용 추정"""

    # 모델별 가격 (1000 토큰당 USD)
    pricing = {
        "gpt-4o": {
            "input": 0.0025,
            "output": 0.01
        },
        "gpt-4o-mini": {
            "input": 0.00015,
            "output": 0.0006
        }
    }

    total_cost = 0.0
    model_costs = {}

    for model, usage in self.usage_stats["by_model"].items():
        tokens = usage["tokens"]

        # 간단한 추정 (입력:출력 = 2:1 가정)
        input_tokens = tokens * 0.67
        output_tokens = tokens * 0.33

        # 모델 매핑
        if "mini" in model:
            price_key = "gpt-4o-mini"
        else:
            price_key = "gpt-4o"

        if price_key in pricing:
            cost = (input_tokens * pricing[price_key]["input"] +
                   output_tokens * pricing[price_key]["output"]) / 1000
            model_costs[model] = cost
            total_cost += cost

    return {
        "total": total_cost,
        "by_model": model_costs
    }
```

#### 사용량 통계 조회
```python
def get_usage_stats(self) -> Dict[str, Any]:
    """사용량 통계 반환"""
    stats = self.usage_stats.copy()
    stats["cost_estimate"] = self._estimate_cost()
    stats["cache_size"] = len(self.cache)
    stats["cache_hit_rate"] = self._calculate_cache_hit_rate()
    return stats

def _calculate_cache_hit_rate(self) -> float:
    """캐시 적중률 계산 (간단한 추정)"""
    # 실제로는 캐시 히트/미스를 추적해야 함
    # 여기서는 캐시 크기 기반 추정
    if self.usage_stats["total_requests"] > 0:
        return min(len(self.cache) / self.usage_stats["total_requests"], 1.0)
    return 0.0
```

---

### 에러 처리 메서드

#### _handle_error(self, error: Exception, prompt: str, category: Optional[str]) -> Dict[str, Any]
```python
def _handle_error(self, error: Exception, prompt: str,
                  category: Optional[str]) -> Dict[str, Any]:
    """에러 처리 및 폴백 응답"""

    error_message = str(error)

    # 에러 타입별 처리
    if "rate_limit" in error_message.lower():
        fallback_content = "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
    elif "api_key" in error_message.lower():
        fallback_content = "API 인증 오류가 발생했습니다."
    elif "timeout" in error_message.lower():
        fallback_content = "응답 시간이 초과되었습니다."
    else:
        fallback_content = "처리 중 오류가 발생했습니다."

    return {
        "content": fallback_content,
        "model": "fallback",
        "error": error_message,
        "category": category or "error",
        "timestamp": datetime.now().isoformat()
    }
```

---

## 3. Prompt Templates

### 파일: `backend/service/utils/prompt_templates.py`

#### 파일 목적
일관된 프롬프트 생성을 위한 템플릿 관리. 버전 관리와 동적 변수 치환을 지원합니다.

#### 클래스 정의
```python
class PromptTemplates:
    """
    프롬프트 템플릿 관리자

    특징:
    - 카테고리별 템플릿 관리
    - 버전 관리 지원
    - 동적 변수 치환
    - 시스템 프롬프트 관리
    """

    def __init__(self):
        self._initialize_templates()
        self._initialize_system_prompts()
```

---

### 템플릿 초기화

#### _initialize_templates(self)
```python
def _initialize_templates(self):
    """모든 프롬프트 템플릿 초기화"""

    self.templates = {
        # ===== 의도 분석 템플릿 =====
        "intent_analysis": {
            "v1": """당신은 제약회사 비즈니스 컨텍스트를 이해하는 의도 분석 전문가입니다.

사용자 쿼리: {query}
추출된 엔티티: {entities}

다음 의도 중에서 사용자의 의도를 분류하세요 (다중 선택 가능):
- sales_analysis: 매출, 실적, 판매 관련 분석
- client_analysis: 거래처, 고객 관련 분석
- hr_search: 직원, 팀, 부서 정보 검색
- rule_search: 규정, 정책, 가이드라인 검색
- doc_generation: 문서, 보고서 생성
- compliance_check: 컴플라이언스, 규정 준수 확인
- general_query: 일반 질의

JSON 형식으로 응답하세요:
{{
    "intents": [
        {{"name": "intent_name", "confidence": 0.9}}
    ],
    "confidence_scores": {{
        "intent_name": 0.9
    }}
}}""",

            "v2": """제약회사 AI 어시스턴트 의도 분석

쿼리: {query}
엔티티: {entities}
이전 대화: {history}

의도를 정확히 분류하고 신뢰도를 평가하세요.
여러 의도가 포함된 경우 모두 식별하세요.

응답 형식:
{{
    "intents": [...],
    "primary_intent": "...",
    "confidence_scores": {{...}},
    "requires_clarification": boolean
}}"""
        },

        # ===== Text-to-SQL 템플릿 =====
        "text_to_sql": {
            "v1": """데이터베이스 스키마:
{schema_info}

사용자 요청: {user_query}

위 요청을 SQL 쿼리로 변환하세요.
규칙:
1. SELECT 문만 사용
2. 안전한 쿼리 작성 (SQL Injection 방지)
3. 적절한 JOIN과 WHERE 절 사용
4. LIMIT를 사용하여 과도한 결과 방지
5. 집계 함수 활용 (SUM, AVG, COUNT 등)

SQL 쿼리:""",

            "sales_performance": """매출 데이터베이스 스키마:
{schema_info}

분석 요청: {user_query}
추출된 정보: {extracted_info}

제약회사 매출 분석을 위한 SQL을 생성하세요.
주요 테이블:
- sales_performance: 매출 실적
- clients: 거래처 정보
- sales_target: 매출 목표

SQL 쿼리 (SELECT만 사용):"""
        },

        # ===== 계획 수립 템플릿 =====
        "planning": {
            "v1": """실행 계획 수립

의도: {intents}
사용 가능한 에이전트: {available_agents}

다음을 고려하여 최적의 실행 계획을 수립하세요:
1. 에이전트 간 의존성
2. 병렬 실행 가능성
3. 리소스 효율성
4. 예상 실행 시간

계획:"""
        },

        # ===== 문서 생성 템플릿 =====
        "document_generation": {
            "sales_report": """매출 보고서 생성

기간: {period}
데이터: {sales_data}
분석: {analysis}

전문적인 매출 보고서를 작성하세요.
포함 내용:
1. 요약
2. 주요 성과 지표
3. 상세 분석
4. 권고사항

보고서:""",

            "compliance_report": """컴플라이언스 검토 보고서

검토일: {check_date}
위반사항: {violations}
권고사항: {recommendations}

KPBMA 규정에 따른 컴플라이언스 보고서를 작성하세요.

보고서:"""
        },

        # ===== 컴플라이언스 템플릿 =====
        "compliance_check": {
            "v1": """컴플라이언스 검토

문서/데이터: {document}
적용 규정: 한국제약바이오협회(KPBMA) 규정

다음 항목을 검토하세요:
1. 리베이트 규정 위반
2. 마케팅 비용 적정성
3. 샘플 제공 규정
4. 학술대회 지원 규정

위반사항 및 권고사항:""",

            "rebate_check": """리베이트 컴플라이언스 검토

거래 정보: {transaction}
할인율: {discount_rate}
금액: {amount}

KPBMA 리베이트 규정 (허용 한도 10%)에 따라 검토하세요.

검토 결과:"""
        },

        # ===== 응답 생성 템플릿 =====
        "response_generation": {
            "v1": """사용자 친화적 응답 생성

원본 데이터: {raw_results}
응답 형식: {format}

제약회사 직원이 이해하기 쉽도록 응답을 작성하세요.
- 전문 용어는 필요시 설명 추가
- 핵심 정보 강조
- 실행 가능한 인사이트 제공

응답:""",

            "error_response": """오류 상황 안내

오류: {error_message}
컨텍스트: {context}

사용자에게 친절하게 오류 상황을 설명하고 대안을 제시하세요.

응답:"""
        },

        # ===== 검색 템플릿 =====
        "search": {
            "hr_search": """HR 정보 검색 최적화

검색어: {query}
필터: {filters}

HR 데이터베이스 검색을 위한 최적화된 쿼리를 생성하세요.

최적화된 검색어:""",

            "rule_search": """규정 검색

검색어: {query}
카테고리: {category}

내부 규정 검색을 위한 시맨틱 쿼리를 생성하세요.

검색 쿼리:"""
        }
    }
```

---

### 시스템 프롬프트 초기화

#### _initialize_system_prompts(self)
```python
def _initialize_system_prompts(self):
    """역할별 시스템 프롬프트 초기화"""

    self.system_prompts = {
        "sql_expert": """당신은 제약회사 데이터베이스 전문가입니다.
매출, 거래처, 재고 데이터에 정통하며 복잡한 비즈니스 쿼리를 SQL로 변환할 수 있습니다.
항상 안전하고 효율적인 쿼리를 작성하며, 데이터 보안을 최우선으로 고려합니다.""",

        "compliance_officer": """당신은 제약산업 컴플라이언스 전문가입니다.
KPBMA 규정, 공정거래법, 약사법 등에 정통하며 위반 사항을 정확히 식별할 수 있습니다.
리베이트, 마케팅 비용, 샘플 제공 등의 규정을 철저히 검토합니다.""",

        "report_writer": """당신은 제약회사 보고서 작성 전문가입니다.
데이터를 명확하고 전문적으로 표현하며, 경영진이 이해하기 쉬운 보고서를 작성합니다.
주요 인사이트를 강조하고 실행 가능한 권고사항을 제시합니다.""",

        "helpful_assistant": """당신은 제약회사 직원을 돕는 AI 어시스턴트입니다.
친절하고 전문적으로 응대하며, 복잡한 정보를 이해하기 쉽게 설명합니다.
항상 정확한 정보를 제공하고, 불확실한 경우 명확히 알립니다.""",

        "data_analyst": """당신은 제약산업 데이터 분석 전문가입니다.
매출 트렌드, 시장 점유율, 경쟁 분석 등을 수행할 수 있습니다.
통계적 인사이트와 비즈니스 인텔리전스를 제공합니다."""
    }
```

---

### 템플릿 관리 메서드

#### get_prompt(self, category: str, subcategory: Optional[str] = None, version: str = "v1", **kwargs) -> str
```python
def get_prompt(self, category: str, subcategory: Optional[str] = None,
               version: str = "v1", **kwargs) -> str:
    """
    프롬프트 템플릿 가져오기 및 변수 치환

    Args:
        category: 템플릿 카테고리
        subcategory: 하위 카테고리 (선택)
        version: 템플릿 버전 (기본 v1)
        **kwargs: 치환할 변수들

    Returns:
        변수가 치환된 프롬프트 문자열

    Example:
        prompt = templates.get_prompt(
            category="intent_analysis",
            version="v1",
            query="지난달 매출 보여줘",
            entities="[...]"
        )
    """

    # 템플릿 찾기
    if category not in self.templates:
        raise ValueError(f"Unknown template category: {category}")

    category_templates = self.templates[category]

    # 하위 카테고리가 있으면 사용
    if subcategory and subcategory in category_templates:
        template = category_templates[subcategory]
    elif version in category_templates:
        template = category_templates[version]
    else:
        # 첫 번째 템플릿 사용
        template = list(category_templates.values())[0]

    # 문자열이 아니면 첫 번째 버전 사용
    if not isinstance(template, str):
        template = template.get(version, template.get("v1", ""))

    # 변수 치환
    try:
        return template.format(**kwargs)
    except KeyError as e:
        missing_var = str(e).strip("'")
        raise ValueError(f"Missing required variable for template: {missing_var}")
```

#### get_system_prompt(self, role: str) -> Optional[str]
```python
def get_system_prompt(self, role: str) -> Optional[str]:
    """
    역할별 시스템 프롬프트 가져오기

    Args:
        role: 역할 이름

    Returns:
        시스템 프롬프트 문자열 또는 None
    """
    return self.system_prompts.get(role)
```

#### add_template(self, category: str, name: str, template: str)
```python
def add_template(self, category: str, name: str, template: str):
    """
    새 템플릿 추가

    Args:
        category: 템플릿 카테고리
        name: 템플릿 이름 (버전 또는 하위 카테고리)
        template: 템플릿 문자열
    """
    if category not in self.templates:
        self.templates[category] = {}

    self.templates[category][name] = template
    logger.info(f"Added template: {category}/{name}")
```

#### list_templates(self) -> Dict[str, list]
```python
def list_templates(self) -> Dict[str, list]:
    """
    사용 가능한 템플릿 목록

    Returns:
        카테고리별 템플릿 이름 목록
    """
    result = {}
    for category, templates in self.templates.items():
        if isinstance(templates, dict):
            result[category] = list(templates.keys())
        else:
            result[category] = ["default"]

    return result
```

#### get_template_variables(self, category: str, name: str = "v1") -> list
```python
def get_template_variables(self, category: str, name: str = "v1") -> list:
    """
    템플릿에 필요한 변수 목록 추출

    Args:
        category: 템플릿 카테고리
        name: 템플릿 이름

    Returns:
        필요한 변수 이름 목록
    """
    import re

    if category not in self.templates:
        return []

    category_templates = self.templates[category]

    if isinstance(category_templates, dict):
        template = category_templates.get(name, "")
    else:
        template = category_templates

    if not isinstance(template, str):
        template = ""

    # {variable} 패턴 찾기
    pattern = r'\{([^}]+)\}'
    variables = re.findall(pattern, template)

    # 중복 제거
    return list(set(variables))
```

---

## 4. Token Tracker

### 파일: `backend/service/utils/token_tracker.py`

#### 파일 목적
토큰 사용량을 실시간으로 추적하고 비용을 관리하며 알림을 제공하는 모듈

#### Imports 및 Dependencies
```python
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import json
import logging
```

---

### TokenTracker 클래스

#### 클래스 초기화
```python
class TokenTracker:
    """
    토큰 사용량 추적 및 비용 관리

    특징:
    - 실시간 사용량 추적
    - 비용 계산 및 예측
    - 임계값 알림
    - 사용량 리포트 생성
    - 히스토리 내보내기
    """

    def __init__(self, alert_threshold: Optional[Dict[str, int]] = None):
        """
        Args:
            alert_threshold: 알림 임계값 설정
                            {"daily": 500000, "hourly": 50000, "per_request": 10000}
        """

        # 가격 정보 (1000 토큰당 USD)
        self.pricing = {
            "gpt-4o": {
                "input": 0.0025,
                "output": 0.01
            },
            "gpt-4o-mini": {
                "input": 0.00015,
                "output": 0.0006
            },
            "gpt-4-turbo": {
                "input": 0.01,
                "output": 0.03
            }
        }

        # 임계값 설정
        self.alert_threshold = alert_threshold or {
            "daily": 500000,      # 일일 50만 토큰
            "hourly": 50000,       # 시간당 5만 토큰
            "per_request": 10000   # 요청당 1만 토큰
        }

        # 사용량 데이터
        self.usage_data = defaultdict(lambda: defaultdict(int))
        self.usage_history = []

        # 알림 기록
        self.alerts_sent = []

        logger.info(f"TokenTracker initialized with thresholds: {self.alert_threshold}")
```

---

### 추적 메서드

#### track(self, model: str, prompt_tokens: int, completion_tokens: int, category: Optional[str] = None, user_id: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]
```python
def track(self, model: str, prompt_tokens: int, completion_tokens: int,
          category: Optional[str] = None, user_id: Optional[str] = None,
          metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    토큰 사용량 추적

    Args:
        model: 사용한 모델
        prompt_tokens: 입력 토큰 수
        completion_tokens: 출력 토큰 수
        category: 사용 카테고리
        user_id: 사용자 ID
        metadata: 추가 메타데이터

    Returns:
        {
            "total_tokens": 총 토큰 수,
            "cost": 예상 비용,
            "alerts": 발생한 알림들
        }
    """

    total_tokens = prompt_tokens + completion_tokens
    timestamp = datetime.now()

    # 사용량 기록 생성
    record = {
        "timestamp": timestamp.isoformat(),
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "category": category or "general",
        "user_id": user_id,
        "metadata": metadata or {}
    }

    # 비용 계산
    cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
    record["cost"] = cost

    # 히스토리에 추가
    self.usage_history.append(record)

    # 집계 데이터 업데이트
    self._update_aggregates(record)

    # 임계값 체크
    alerts = self._check_thresholds(record)

    # 알림 발송
    if alerts:
        self._send_alerts(alerts)

    return {
        "total_tokens": total_tokens,
        "cost": cost,
        "alerts": alerts
    }
```

---

### 비용 계산 메서드

#### _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float
```python
def _calculate_cost(self, model: str, prompt_tokens: int,
                   completion_tokens: int) -> float:
    """비용 계산"""

    # 모델 매핑
    if "mini" in model.lower():
        price_model = "gpt-4o-mini"
    elif "turbo" in model.lower():
        price_model = "gpt-4-turbo"
    else:
        price_model = "gpt-4o"

    if price_model not in self.pricing:
        logger.warning(f"Unknown model for pricing: {model}")
        return 0.0

    prices = self.pricing[price_model]

    # 비용 계산 (USD)
    input_cost = (prompt_tokens / 1000) * prices["input"]
    output_cost = (completion_tokens / 1000) * prices["output"]

    return round(input_cost + output_cost, 6)
```

---

### 집계 데이터 업데이트

#### _update_aggregates(self, record: Dict)
```python
def _update_aggregates(self, record: Dict):
    """집계 데이터 업데이트"""

    timestamp = datetime.fromisoformat(record["timestamp"])
    total_tokens = record["total_tokens"]
    cost = record["cost"]

    # 시간별 집계
    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
    self.usage_data["hourly"][hour_key] += total_tokens

    # 일별 집계
    day_key = timestamp.strftime("%Y-%m-%d")
    self.usage_data["daily"][day_key] += total_tokens

    # 모델별 집계
    model = record["model"]
    self.usage_data["by_model"][model] += total_tokens

    # 카테고리별 집계
    category = record["category"]
    self.usage_data["by_category"][category] += total_tokens

    # 사용자별 집계
    if record.get("user_id"):
        user_id = record["user_id"]
        self.usage_data["by_user"][user_id] += total_tokens

    # 총 비용
    self.usage_data["total"]["tokens"] += total_tokens
    self.usage_data["total"]["cost"] += cost
    self.usage_data["total"]["requests"] += 1
```

---

### 임계값 체크 및 알림

#### _check_thresholds(self, record: Dict) -> List[Dict]
```python
def _check_thresholds(self, record: Dict) -> List[Dict]:
    """임계값 체크"""

    alerts = []
    timestamp = datetime.fromisoformat(record["timestamp"])

    # 요청당 토큰 체크
    if record["total_tokens"] > self.alert_threshold["per_request"]:
        alerts.append({
            "level": "warning",
            "type": "per_request",
            "message": f"Single request used {record['total_tokens']} tokens",
            "threshold": self.alert_threshold["per_request"],
            "value": record["total_tokens"]
        })

    # 시간당 토큰 체크
    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
    hourly_usage = self.usage_data["hourly"][hour_key]
    if hourly_usage > self.alert_threshold["hourly"]:
        alerts.append({
            "level": "warning",
            "type": "hourly",
            "message": f"Hourly usage exceeded: {hourly_usage} tokens",
            "threshold": self.alert_threshold["hourly"],
            "value": hourly_usage
        })

    # 일일 토큰 체크
    day_key = timestamp.strftime("%Y-%m-%d")
    daily_usage = self.usage_data["daily"][day_key]
    if daily_usage > self.alert_threshold["daily"]:
        alerts.append({
            "level": "critical",
            "type": "daily",
            "message": f"Daily usage exceeded: {daily_usage} tokens",
            "threshold": self.alert_threshold["daily"],
            "value": daily_usage
        })

    return alerts
```

#### _send_alerts(self, alerts: List[Dict])
```python
def _send_alerts(self, alerts: List[Dict]):
    """알림 발송"""

    for alert in alerts:
        # 중복 알림 방지
        alert_key = f"{alert['type']}:{alert['value']}"
        recent_alerts = [a for a in self.alerts_sent
                        if datetime.now() - datetime.fromisoformat(a["timestamp"]) < timedelta(hours=1)]

        if not any(a.get("key") == alert_key for a in recent_alerts):
            alert["timestamp"] = datetime.now().isoformat()
            alert["key"] = alert_key

            self.alerts_sent.append(alert)

            # 로그 출력
            if alert["level"] == "critical":
                logger.error(f"CRITICAL ALERT: {alert['message']}")
            else:
                logger.warning(f"ALERT: {alert['message']}")

            # 실제 알림 발송 (이메일, 슬랙 등)
            # self._send_notification(alert)
```

---

### 통계 및 리포트 메서드

#### get_current_stats(self) -> Dict[str, Any]
```python
def get_current_stats(self) -> Dict[str, Any]:
    """현재 통계 조회"""

    now = datetime.now()
    current_hour = now.strftime("%Y-%m-%d %H:00")
    current_day = now.strftime("%Y-%m-%d")

    stats = {
        "current_hour": {
            "tokens": self.usage_data["hourly"].get(current_hour, 0),
            "threshold": self.alert_threshold["hourly"]
        },
        "current_day": {
            "tokens": self.usage_data["daily"].get(current_day, 0),
            "threshold": self.alert_threshold["daily"]
        },
        "total": {
            "tokens": self.usage_data["total"].get("tokens", 0),
            "cost": self.usage_data["total"].get("cost", 0.0),
            "requests": self.usage_data["total"].get("requests", 0)
        },
        "by_model": dict(self.usage_data["by_model"]),
        "by_category": dict(self.usage_data["by_category"]),
        "recent_alerts": self.alerts_sent[-10:]  # 최근 10개 알림
    }

    # 평균 계산
    if stats["total"]["requests"] > 0:
        stats["average_tokens_per_request"] = (
            stats["total"]["tokens"] / stats["total"]["requests"]
        )
    else:
        stats["average_tokens_per_request"] = 0

    return stats
```

#### get_usage_report(self, period: str = "daily") -> Dict[str, Any]
```python
def get_usage_report(self, period: str = "daily") -> Dict[str, Any]:
    """
    사용량 리포트 생성

    Args:
        period: "hourly" 또는 "daily"

    Returns:
        기간별 사용량 리포트
    """

    now = datetime.now()
    report = {
        "period": period,
        "generated_at": now.isoformat(),
        "data": []
    }

    if period == "hourly":
        # 최근 24시간
        for i in range(24):
            hour_time = now - timedelta(hours=i)
            hour_key = hour_time.strftime("%Y-%m-%d %H:00")
            usage = self.usage_data["hourly"].get(hour_key, 0)
            report["data"].append({
                "time": hour_key,
                "tokens": usage
            })

    elif period == "daily":
        # 최근 7일
        for i in range(7):
            day_time = now - timedelta(days=i)
            day_key = day_time.strftime("%Y-%m-%d")
            usage = self.usage_data["daily"].get(day_key, 0)
            report["data"].append({
                "date": day_key,
                "tokens": usage
            })

    # 데이터 정렬 (시간순)
    report["data"].sort(key=lambda x: x.get("time", x.get("date")))

    # 통계 추가
    tokens_list = [d["tokens"] for d in report["data"]]
    if tokens_list:
        report["statistics"] = {
            "total": sum(tokens_list),
            "average": sum(tokens_list) / len(tokens_list),
            "max": max(tokens_list),
            "min": min(tokens_list)
        }

    # Top 사용자/카테고리
    report["top_users"] = sorted(
        [(user, tokens) for user, tokens in self.usage_data["by_user"].items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]

    report["top_categories"] = sorted(
        [(cat, tokens) for cat, tokens in self.usage_data["by_category"].items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return report
```

#### export_history(self, filepath: str)
```python
def export_history(self, filepath: str):
    """
    사용량 히스토리를 파일로 내보내기

    Args:
        filepath: 저장할 파일 경로
    """

    export_data = {
        "exported_at": datetime.now().isoformat(),
        "summary": self.get_current_stats(),
        "history": self.usage_history,
        "aggregates": {
            "hourly": dict(self.usage_data["hourly"]),
            "daily": dict(self.usage_data["daily"]),
            "by_model": dict(self.usage_data["by_model"]),
            "by_category": dict(self.usage_data["by_category"]),
            "by_user": dict(self.usage_data["by_user"])
        }
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Usage history exported to {filepath}")
```

#### reset(self)
```python
def reset(self):
    """사용량 데이터 초기화"""

    self.usage_data.clear()
    self.usage_history.clear()
    self.alerts_sent.clear()

    logger.info("TokenTracker data reset")
```

---

## 5. Supervisor (Main Entry Point)

### 파일: `backend/service/supervisor.py`

#### 파일 목적
오케스트레이터 실행을 위한 메인 진입점. 워크플로우 실행과 체크포인터 관리를 담당합니다.

#### Imports 및 Dependencies
```python
from datetime import datetime
import asyncio
from orchestrator.orchestrator import MainOrchestrator
import logging
```

#### 로깅 설정
```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

---

### 메인 실행 함수

#### async def run_orchestrator(user_query: str, user_id: str = "test_user")
```python
async def run_orchestrator(user_query: str, user_id: str = "test_user"):
    """
    오케스트레이터 실행

    Args:
        user_query: 사용자 쿼리
        user_id: 사용자 ID

    Returns:
        실행 결과
    """

    # 오케스트레이터 초기화
    orchestrator = MainOrchestrator(use_checkpointer=True)

    # 워크플로우 컴파일
    app = orchestrator.app

    # 입력 데이터 준비
    input_data = {
        "user_id": user_id,
        "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "user_query": user_query,
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Starting orchestrator for user: {user_id}")
    logger.info(f"Query: {user_query}")

    # 스트리밍 실행
    config = {"configurable": {"thread_id": f"thread_{user_id}"}}

    try:
        # 스트림 실행
        async for event in app.astream(input_data, config):
            # 각 노드 실행 이벤트 처리
            for node, state in event.items():
                if node != "__end__":
                    logger.info(f"Node executed: {node}")

                    # 주요 상태 업데이트 로그
                    if "intents" in state:
                        logger.info(f"Intents: {state['intents']}")
                    if "active_agents" in state:
                        logger.info(f"Active agents: {state['active_agents']}")
                    if "final_response" in state:
                        logger.info(f"Response generated: {len(state['final_response'])} chars")

        # 최종 상태 가져오기
        final_state = await app.aget_state(config)

        # 결과 반환
        result = {
            "success": True,
            "response": final_state.values.get("final_response", ""),
            "metadata": {
                "session_id": input_data["session_id"],
                "execution_time": final_state.values.get("execution_time", 0),
                "tokens_used": final_state.values.get("tokens_used", 0),
                "agents_used": final_state.values.get("active_agents", []),
                "confidence_score": final_state.values.get("confidence_score", 0)
            }
        }

        return result

    except Exception as e:
        logger.error(f"Orchestrator execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다."
        }
```

---

### 동기 래퍼 함수

#### def run_sync(user_query: str, user_id: str = "test_user")
```python
def run_sync(user_query: str, user_id: str = "test_user"):
    """
    동기 실행 래퍼

    Args:
        user_query: 사용자 쿼리
        user_id: 사용자 ID

    Returns:
        실행 결과
    """

    # 이벤트 루프 처리
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 비동기 함수 실행
    return loop.run_until_complete(run_orchestrator(user_query, user_id))
```

---

### 메인 실행 블록

#### if __name__ == "__main__":
```python
if __name__ == "__main__":
    # 테스트 쿼리
    test_queries = [
        "지난 분기 서울 지역 거래처별 매출 실적을 분석하고 규정 위반 사항이 있는지 검토해줘",
        "김영희 대리의 연락처를 알려줘",
        "리베이트 관련 회사 규정이 뭐야?",
        "이번달 매출 보고서 작성해줘"
    ]

    # 첫 번째 쿼리로 테스트
    result = run_sync(test_queries[0])

    print("\n" + "="*50)
    print("실행 결과")
    print("="*50)

    if result["success"]:
        print(f"\n응답:\n{result['response']}")
        print(f"\n메타데이터:")
        for key, value in result["metadata"].items():
            print(f"  - {key}: {value}")
    else:
        print(f"\n오류: {result.get('error', 'Unknown error')}")
        print(f"응답: {result.get('response', '')}")
```

---

## 6. Test Integration

### 파일: `backend/service/test_integration.py`

#### 파일 목적
LangGraph 0.6.7 통합 테스트. 모든 컴포넌트의 임포트, 컴파일, 실행을 테스트합니다.

#### Imports 및 Dependencies
```python
import sys
import traceback
from typing import Dict, Any
import logging
```

#### 로깅 설정
```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

---

### 테스트 함수들

#### 1. test_imports() -> Dict[str, bool]
```python
def test_imports() -> Dict[str, bool]:
    """모든 모듈 임포트 테스트"""

    results = {}

    # 오케스트레이터 테스트
    orchestrator_modules = [
        "service.orchestrator.orchestrator",
        "service.orchestrator.intent_analysis",
        "service.orchestrator.planning",
        "service.orchestrator.agent_execution",
        "service.orchestrator.result_evaluation",
        "service.orchestrator.response_generation"
    ]

    for module_name in orchestrator_modules:
        try:
            __import__(module_name)
            results[module_name] = True
            logger.info(f"✓ {module_name}")
        except Exception as e:
            results[module_name] = False
            logger.error(f"✗ {module_name}: {e}")

    # 에이전트 테스트
    agent_modules = [
        "service.agents.sales_analytics_agent",
        "service.agents.search_agent",
        "service.agents.document_generation_agent",
        "service.agents.compliance_check_agent"
    ]

    for module_name in agent_modules:
        try:
            __import__(module_name)
            results[module_name] = True
            logger.info(f"✓ {module_name}")
        except Exception as e:
            results[module_name] = False
            logger.error(f"✗ {module_name}: {e}")

    # 유틸리티 테스트
    util_modules = [
        "service.utils.llm_manager",
        "service.utils.prompt_templates",
        "service.utils.token_tracker"
    ]

    for module_name in util_modules:
        try:
            __import__(module_name)
            results[module_name] = True
            logger.info(f"✓ {module_name}")
        except Exception as e:
            results[module_name] = False
            logger.error(f"✗ {module_name}: {e}")

    return results
```

#### 2. test_graph_compilation() -> Dict[str, bool]
```python
def test_graph_compilation() -> Dict[str, bool]:
    """그래프 컴파일 테스트"""

    results = {}

    # 메인 오케스트레이터
    try:
        from service.orchestrator.orchestrator import MainOrchestrator
        orchestrator = MainOrchestrator(use_checkpointer=False)
        results["MainOrchestrator"] = True
        logger.info("✓ MainOrchestrator compiled")
    except Exception as e:
        results["MainOrchestrator"] = False
        logger.error(f"✗ MainOrchestrator: {e}")

    # 서브그래프들
    subgraphs = [
        ("IntentAnalysisSubGraph", "service.orchestrator.intent_analysis"),
        ("PlanningSubGraph", "service.orchestrator.planning"),
        ("AgentExecutionSubGraph", "service.orchestrator.agent_execution"),
        ("ResultEvaluationSubGraph", "service.orchestrator.result_evaluation"),
        ("ResponseGenerationSubGraph", "service.orchestrator.response_generation")
    ]

    for name, module_path in subgraphs:
        try:
            module = __import__(module_path, fromlist=[name])
            graph_class = getattr(module, name)
            instance = graph_class()

            # 그래프가 컴파일되었는지 확인
            if hasattr(instance, 'app'):
                results[name] = True
                logger.info(f"✓ {name} compiled")
            else:
                results[name] = False
                logger.error(f"✗ {name}: No compiled app found")

        except Exception as e:
            results[name] = False
            logger.error(f"✗ {name}: {e}")

    # 에이전트들
    agents = [
        ("SalesAnalyticsAgent", "service.agents.sales_analytics_agent"),
        ("SearchAgent", "service.agents.search_agent"),
        ("DocumentGenerationAgent", "service.agents.document_generation_agent"),
        ("ComplianceCheckAgent", "service.agents.compliance_check_agent")
    ]

    for name, module_path in agents:
        try:
            module = __import__(module_path, fromlist=[name])
            agent_class = getattr(module, name)
            instance = agent_class()

            if hasattr(instance, 'app'):
                results[name] = True
                logger.info(f"✓ {name} compiled")
            else:
                results[name] = False
                logger.error(f"✗ {name}: No compiled app found")

        except Exception as e:
            results[name] = False
            logger.error(f"✗ {name}: {e}")

    return results
```

#### 3. test_simple_execution() -> bool
```python
def test_simple_execution() -> bool:
    """간단한 실행 테스트"""

    try:
        from service.agents.document_generation_agent import DocumentGenerationAgent

        # 에이전트 생성
        agent = DocumentGenerationAgent()

        # 테스트 데이터
        test_input = {
            "document_type": "sales_report",
            "data": {
                "period": "2024년 4분기",
                "sales_data": [
                    {"item": "제품A", "amount": 1000000},
                    {"item": "제품B", "amount": 2000000}
                ],
                "analysis": "매출이 전분기 대비 20% 증가했습니다.",
                "author": "홍길동"
            },
            "format": "html"
        }

        # 실행
        result = agent.execute(test_input)

        # 결과 검증
        if result.get("success"):
            logger.info("✓ DocumentGenerationAgent execution successful")

            # 결과 내용 확인
            if "document" in result:
                logger.info(f"  - Document generated: {len(result['document'].get('content', ''))} chars")
            if "metadata" in result:
                logger.info(f"  - Metadata: {result['metadata']}")

            return True
        else:
            logger.error(f"✗ Execution failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        logger.error(f"✗ Execution test failed: {e}")
        traceback.print_exc()
        return False
```

---

### 메인 테스트 실행

#### def main()
```python
def main():
    """모든 테스트 실행"""

    print("="*60)
    print("LangGraph 0.6.7 Integration Test")
    print("="*60)

    all_results = {}

    # 1. 임포트 테스트
    print("\n1. Testing imports...")
    print("-"*40)
    import_results = test_imports()
    all_results["imports"] = import_results

    import_success = sum(1 for v in import_results.values() if v)
    import_total = len(import_results)
    print(f"\nImport Results: {import_success}/{import_total} successful")

    # 2. 컴파일 테스트
    print("\n2. Testing graph compilation...")
    print("-"*40)
    compile_results = test_graph_compilation()
    all_results["compilation"] = compile_results

    compile_success = sum(1 for v in compile_results.values() if v)
    compile_total = len(compile_results)
    print(f"\nCompilation Results: {compile_success}/{compile_total} successful")

    # 3. 실행 테스트
    print("\n3. Testing simple execution...")
    print("-"*40)
    execution_result = test_simple_execution()
    all_results["execution"] = execution_result

    print(f"\nExecution Result: {'✓ Successful' if execution_result else '✗ Failed'}")

    # 최종 요약
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    # 통계 계산
    total_tests = import_total + compile_total + 1
    successful_tests = import_success + compile_success + (1 if execution_result else 0)

    print(f"\nTotal Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")

    # 실패한 테스트 목록
    failures = []

    for test_name, result in import_results.items():
        if not result:
            failures.append(f"Import: {test_name}")

    for test_name, result in compile_results.items():
        if not result:
            failures.append(f"Compile: {test_name}")

    if not execution_result:
        failures.append("Execution: DocumentGenerationAgent")

    if failures:
        print("\nFailed Tests:")
        for failure in failures:
            print(f"  - {failure}")
    else:
        print("\n✓ All tests passed!")

    return all_results
```

#### if __name__ == "__main__":
```python
if __name__ == "__main__":
    try:
        results = main()

        # 결과를 JSON으로 저장 (옵션)
        import json
        with open("test_results.json", "w") as f:
            # Bool을 문자열로 변환
            json_results = {}
            for category, tests in results.items():
                if isinstance(tests, dict):
                    json_results[category] = {k: str(v) for k, v in tests.items()}
                else:
                    json_results[category] = str(tests)

            json.dump(json_results, f, indent=2)
            print("\nTest results saved to test_results.json")

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        traceback.print_exc()
```

---

이 문서는 Utils 모듈의 3개 파일(LLMManager, PromptTemplates, TokenTracker)과 Service의 2개 파일(supervisor.py, test_integration.py)에 대한 완전한 상세 문서입니다. 모든 클래스, 메서드, 설정, 테스트 코드를 포함하고 있습니다.