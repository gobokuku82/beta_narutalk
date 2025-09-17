"""
Context Engineering for Medical Domain
컨텍스트 최적화를 통한 에이전트 성능 향상
"""

from typing import Dict, Any, List, Optional, TypedDict, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import json
import logging

logger = logging.getLogger(__name__)


class MedicalContext(BaseModel):
    """의료/제약 도메인 특화 컨텍스트"""
    
    # 사용자 컨텍스트
    user_id: str
    user_role: Literal["영업사원", "매니저", "관리자", "분석가"]
    department: str
    region: str
    
    # 도메인 컨텍스트
    domain_type: Literal["실적분석", "정보검색", "문서생성", "규정검토"]
    target_entity: Optional[str] = None  # 거래처, 제품, 지역 등
    time_range: Optional[Dict[str, str]] = None  # 기간 정보
    
    # 규정 컨텍스트
    compliance_level: Literal["strict", "normal", "relaxed"] = "strict"
    applicable_regulations: List[str] = Field(default_factory=list)
    
    # 데이터 컨텍스트
    data_sources: List[str] = Field(default_factory=list)
    required_columns: List[str] = Field(default_factory=list)
    complex_columns_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # 실행 컨텍스트
    priority: Literal["high", "medium", "low"] = "medium"
    max_execution_time: int = 120  # seconds
    allow_parallel: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "emp_001",
                "user_role": "영업사원",
                "department": "영업1팀",
                "region": "서울",
                "domain_type": "실적분석",
                "target_entity": "A병원",
                "time_range": {"start": "2025-01-01", "end": "2025-01-31"}
            }
        }


class ContextManager:
    """
    Context Engineering 관리자
    - 컨텍스트 최적화
    - 에이전트별 컨텍스트 분리
    - 불필요한 정보 필터링
    """
    
    def __init__(self):
        self.context_cache = {}
        self.context_history = []
        
    async def optimize_context(
        self,
        raw_query: str,
        user_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]]
    ) -> MedicalContext:
        """
        원시 쿼리와 사용자 정보를 최적화된 컨텍스트로 변환
        """
        
        # 1. 도메인 타입 추론
        domain_type = self._infer_domain_type(raw_query)
        
        # 2. 규정 레벨 결정
        compliance_level = self._determine_compliance_level(domain_type, user_context)
        
        # 3. 필요한 데이터 소스 식별
        data_sources = self._identify_data_sources(raw_query, domain_type)
        
        # 4. 복잡한 칼럼 메타데이터 준비
        complex_columns = await self._prepare_column_metadata(domain_type)
        
        # 5. 시간 범위 추출
        time_range = self._extract_time_range(raw_query)
        
        # 6. 대상 엔티티 추출
        target_entity = self._extract_target_entity(raw_query)
        
        context = MedicalContext(
            user_id=user_context.get("user_id", "unknown"),
            user_role=user_context.get("role", "영업사원"),
            department=user_context.get("department", "미지정"),
            region=user_context.get("region", "전국"),
            domain_type=domain_type,
            target_entity=target_entity,
            time_range=time_range,
            compliance_level=compliance_level,
            applicable_regulations=self._get_applicable_regulations(domain_type),
            data_sources=data_sources,
            complex_columns_metadata=complex_columns,
            priority=self._determine_priority(raw_query),
            allow_parallel=self._check_parallel_capability(domain_type)
        )
        
        # 캐시 저장
        cache_key = f"{user_context.get('user_id')}_{domain_type}_{datetime.now().date()}"
        self.context_cache[cache_key] = context
        
        logger.info(f"Optimized context created for domain: {domain_type}")
        return context
    
    def _infer_domain_type(self, query: str) -> str:
        """쿼리에서 도메인 타입 추론"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["실적", "매출", "성과", "트렌드", "분석"]):
            return "실적분석"
        elif any(keyword in query_lower for keyword in ["검색", "찾", "조회", "확인"]):
            return "정보검색"
        elif any(keyword in query_lower for keyword in ["작성", "생성", "만들", "저장"]):
            return "문서생성"
        elif any(keyword in query_lower for keyword in ["규정", "위반", "검토", "확인"]):
            return "규정검토"
        else:
            return "정보검색"  # 기본값
    
    def _determine_compliance_level(self, domain_type: str, user_context: Dict) -> str:
        """규정 준수 레벨 결정"""
        
        if domain_type in ["문서생성", "규정검토"]:
            return "strict"
        elif user_context.get("role") == "관리자":
            return "strict"
        else:
            return "normal"
    
    def _identify_data_sources(self, query: str, domain_type: str) -> List[str]:
        """필요한 데이터 소스 식별"""
        
        sources = []
        query_lower = query.lower()
        
        # 도메인별 기본 소스
        domain_sources = {
            "실적분석": ["sales_db", "performance_db"],
            "정보검색": ["hr_db", "regulation_db", "document_db"],
            "문서생성": ["template_db", "regulation_db"],
            "규정검토": ["regulation_db", "compliance_db"]
        }
        
        sources.extend(domain_sources.get(domain_type, []))
        
        # 쿼리 기반 추가 소스
        if "네이버" in query_lower:
            sources.append("naver_api")
        if "구글" in query_lower:
            sources.append("google_api")
        if "논문" in query_lower:
            sources.append("paper_db")
        if "심평원" in query_lower or "hira" in query_lower:
            sources.append("hira_api")
        
        return list(set(sources))  # 중복 제거
    
    async def _prepare_column_metadata(self, domain_type: str) -> Dict[str, Any]:
        """복잡한 칼럼 메타데이터 준비"""
        
        # 실제 구현에서는 DB에서 가져옴
        metadata = {
            "실적분석": {
                "sales_amount": {
                    "type": "numeric",
                    "unit": "원",
                    "aggregation": ["sum", "avg", "max", "min"],
                    "description": "매출액"
                },
                "visit_count": {
                    "type": "numeric",
                    "aggregation": ["count", "sum"],
                    "description": "방문 횟수"
                },
                "product_mix": {
                    "type": "json",
                    "structure": {"product_id": "string", "quantity": "numeric"},
                    "description": "제품 구성"
                }
            },
            "정보검색": {
                "employee_info": {
                    "type": "structured",
                    "fields": ["name", "department", "position", "region"],
                    "description": "직원 정보"
                },
                "regulation_content": {
                    "type": "text",
                    "searchable": True,
                    "description": "규정 내용"
                }
            }
        }
        
        return metadata.get(domain_type, {})
    
    def _extract_time_range(self, query: str) -> Optional[Dict[str, str]]:
        """쿼리에서 시간 범위 추출"""
        
        # 간단한 구현 (실제로는 더 정교한 날짜 파싱 필요)
        import re
        from datetime import datetime, timedelta
        
        today = datetime.now()
        
        if "이번달" in query or "이번 달" in query:
            return {
                "start": today.replace(day=1).strftime("%Y-%m-%d"),
                "end": today.strftime("%Y-%m-%d")
            }
        elif "지난달" in query or "지난 달" in query:
            last_month = today.replace(day=1) - timedelta(days=1)
            return {
                "start": last_month.replace(day=1).strftime("%Y-%m-%d"),
                "end": last_month.strftime("%Y-%m-%d")
            }
        elif "올해" in query:
            return {
                "start": f"{today.year}-01-01",
                "end": today.strftime("%Y-%m-%d")
            }
        
        # 날짜 패턴 찾기 (YYYY-MM-DD)
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        dates = re.findall(date_pattern, query)
        if len(dates) >= 2:
            return {"start": dates[0], "end": dates[1]}
        
        return None
    
    def _extract_target_entity(self, query: str) -> Optional[str]:
        """쿼리에서 대상 엔티티 추출"""
        
        # 간단한 구현 (실제로는 NER 모델 활용)
        import re
        
        # 병원 패턴
        hospital_pattern = r'([가-힣]+병원|[가-힣]+의원|[가-힣]+클리닉)'
        hospital_match = re.search(hospital_pattern, query)
        if hospital_match:
            return hospital_match.group(1)
        
        # 거래처 패턴
        company_pattern = r'([가-힣]+약국|[가-힣]+제약|[가-힣]+유통)'
        company_match = re.search(company_pattern, query)
        if company_match:
            return company_match.group(1)
        
        return None
    
    def _get_applicable_regulations(self, domain_type: str) -> List[str]:
        """적용 가능한 규정 목록"""
        
        regulations_map = {
            "문서생성": ["의료법", "리베이트법", "공정거래규약", "내부규정"],
            "규정검토": ["의료법", "리베이트법", "공정거래규약", "내부규정"],
            "실적분석": ["개인정보보호법"],
            "정보검색": ["개인정보보호법", "정보공개법"]
        }
        
        return regulations_map.get(domain_type, [])
    
    def _determine_priority(self, query: str) -> str:
        """우선순위 결정"""
        
        high_priority_keywords = ["긴급", "즉시", "바로", "urgent", "asap"]
        low_priority_keywords = ["나중", "천천히", "여유있게"]
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in high_priority_keywords):
            return "high"
        elif any(keyword in query_lower for keyword in low_priority_keywords):
            return "low"
        else:
            return "medium"
    
    def _check_parallel_capability(self, domain_type: str) -> bool:
        """병렬 실행 가능 여부"""
        
        # 규정검토는 순차적으로 수행
        if domain_type == "규정검토":
            return False
        
        return True
    
    def get_agent_specific_context(
        self,
        agent_name: str,
        full_context: MedicalContext
    ) -> Dict[str, Any]:
        """
        에이전트별 최적화된 컨텍스트 반환
        불필요한 정보는 제거
        """
        
        agent_context_map = {
            "DataAnalysisAgent": {
                "required_fields": ["data_sources", "complex_columns_metadata", "time_range", "target_entity"],
                "exclude_fields": ["applicable_regulations", "compliance_level"]
            },
            "InformationRetrievalAgent": {
                "required_fields": ["data_sources", "target_entity", "domain_type"],
                "exclude_fields": ["complex_columns_metadata", "compliance_level"]
            },
            "DocumentGenerationAgent": {
                "required_fields": ["domain_type", "target_entity", "applicable_regulations"],
                "exclude_fields": ["complex_columns_metadata", "data_sources"]
            },
            "ComplianceValidationAgent": {
                "required_fields": ["applicable_regulations", "compliance_level", "domain_type"],
                "exclude_fields": ["data_sources", "complex_columns_metadata"]
            }
        }
        
        config = agent_context_map.get(agent_name, {})
        
        # 필요한 필드만 추출
        context_dict = full_context.dict()
        
        if "required_fields" in config:
            filtered_context = {
                k: v for k, v in context_dict.items()
                if k in config["required_fields"]
            }
        else:
            filtered_context = context_dict
        
        # 불필요한 필드 제거
        if "exclude_fields" in config:
            for field in config["exclude_fields"]:
                filtered_context.pop(field, None)
        
        # 에이전트별 추가 정보
        filtered_context["agent_name"] = agent_name
        filtered_context["timestamp"] = datetime.now().isoformat()
        
        return filtered_context
    
    def update_context_from_results(
        self,
        context: MedicalContext,
        agent_results: Dict[str, Any]
    ) -> MedicalContext:
        """
        에이전트 실행 결과로 컨텍스트 업데이트
        """
        
        # 새로운 데이터 소스 추가
        if "discovered_sources" in agent_results:
            context.data_sources.extend(agent_results["discovered_sources"])
            context.data_sources = list(set(context.data_sources))
        
        # 새로운 규정 발견
        if "additional_regulations" in agent_results:
            context.applicable_regulations.extend(agent_results["additional_regulations"])
            context.applicable_regulations = list(set(context.applicable_regulations))
        
        # 타겟 엔티티 업데이트
        if "refined_target" in agent_results:
            context.target_entity = agent_results["refined_target"]
        
        return context


class ContextOptimizer:
    """
    컨텍스트 최적화 유틸리티
    """
    
    @staticmethod
    def remove_handoff_messages(messages: List[Dict]) -> List[Dict]:
        """
        Handoff 메시지 제거하여 컨텍스트 정리
        """
        return [
            msg for msg in messages
            if not (msg.get("type") == "tool" and "handoff" in msg.get("name", ""))
        ]
    
    @staticmethod
    def summarize_long_context(
        context: str,
        max_length: int = 2000
    ) -> str:
        """
        긴 컨텍스트 요약
        """
        if len(context) <= max_length:
            return context
        
        # 중요한 부분만 추출
        # 실제로는 LLM을 사용한 요약
        return context[:max_length] + "... [truncated]"
    
    @staticmethod
    def merge_duplicate_info(
        contexts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        중복 정보 병합
        """
        merged = {}
        
        for ctx in contexts:
            for key, value in ctx.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(value, list) and isinstance(merged[key], list):
                    # 리스트는 합치고 중복 제거
                    merged[key] = list(set(merged[key] + value))
                elif isinstance(value, dict) and isinstance(merged[key], dict):
                    # 딕셔너리는 재귀적으로 병합
                    merged[key] = {**merged[key], **value}
        
        return merged
