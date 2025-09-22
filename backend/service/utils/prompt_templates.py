"""
프롬프트 템플릿 관리
버전 관리 및 동적 변수 치환 지원
"""

from typing import Dict, Any, Optional
from datetime import datetime

class PromptTemplates:
    """프롬프트 템플릿 관리 클래스"""

    def __init__(self):
        self.templates = {
            # === 의도 분석 템플릿 ===
            "intent_analysis": {
                "v1": """당신은 제약회사 챗봇의 의도 분석 전문가입니다.
사용자 질의를 분석하여 다중 의도를 분류하고 신뢰도를 평가하세요.

사용자 질의: {user_query}

가능한 의도 카테고리:
1. sales_analysis - 실적/매출 분석, 거래처 실적 조회
2. client_analysis - 거래처 정보, 거래처 상태 분석
3. hr_search - 인사정보 검색, 직원 정보 조회
4. rule_search - 내부 규정/지침 검색
5. doc_generation - 보고서/문서 생성 요청
6. compliance_check - 규정 위반 검토, 컴플라이언스 확인

출력 형식 (JSON):
{{
  "intents": [
    {{"type": "의도타입", "confidence": 0.95, "keywords": ["핵심", "키워드"]}}
  ],
  "entities": [
    {{"type": "기간/지역/제품 등", "value": "추출된 값"}}
  ],
  "ambiguous": false,
  "clarification_needed": null
}}

분석:""",
                "v2": """제약회사 비즈니스 컨텍스트에서 사용자 의도를 정확히 파악하세요.

질의: {user_query}
이전 대화: {conversation_history}

의도를 분류하고 필요한 엔티티를 추출하세요."""
            },

            # === SQL 생성 템플릿 ===
            "text_to_sql": {
                "v1": """당신은 SQL 전문가입니다. 자연어 질의를 정확한 SQL로 변환하세요.

데이터베이스 스키마:
{schema_info}

사용자 요청: {user_query}
추출된 엔티티: {entities}

규칙:
1. 안전한 SQL만 생성 (SELECT 쿼리만)
2. 적절한 JOIN 사용
3. WHERE 절로 필터링
4. 필요시 집계 함수 사용
5. 결과는 최대 1000행으로 제한

SQL 쿼리:""",
                "sales_performance": """매출 실적 분석을 위한 SQL을 생성하세요.

테이블 정보:
- sales_performance_db: 실적 데이터 (날짜, 거래처, 제품, 매출액, 수량)
- sales_target_db: 목표 데이터 (연도, 분기, 거래처, 목표액)
- clients_db: 거래처 기본 정보
- clients_info: 거래처 상세 정보

요청: {user_query}
기간: {period}
지역: {region}

최적화된 SQL:"""
            },

            # === 계획 수립 템플릿 ===
            "planning": {
                "v1": """다음 의도들을 효율적으로 처리하기 위한 실행 계획을 수립하세요.

의도 목록: {intents}
사용 가능한 에이전트: {available_agents}

다음을 고려하여 계획하세요:
1. 의존성 관계
2. 병렬 실행 가능 여부
3. 우선순위
4. 예상 소요 시간

출력 형식:
{{
  "execution_steps": [...],
  "parallel_groups": [...],
  "dependencies": {{...}},
  "estimated_time": ...
}}

실행 계획:"""
            },

            # === 문서 생성 템플릿 ===
            "document_generation": {
                "sales_report": """다음 데이터를 바탕으로 전문적인 매출 보고서를 작성하세요.

데이터: {data}
기간: {period}
요청사항: {requirements}

보고서 구조:
1. 요약
2. 주요 성과 지표
3. 상세 분석
4. 권고사항

보고서:""",
                "compliance_report": """규정 준수 검토 보고서를 작성하세요.

검토 대상: {target}
검토 항목: {check_items}
발견 사항: {findings}

규정 준수 보고서:"""
            },

            # === 규정 검토 템플릿 ===
            "compliance_check": {
                "v1": """다음 활동/데이터에 대해 제약업계 규정 준수 여부를 검토하세요.

검토 대상: {review_target}
관련 규정: {relevant_rules}
컨텍스트: {context}

검토 항목:
1. KPBMA 규약 준수
2. 리베이트 쌍벌제 위반 여부
3. 경제적 이익 제공 한도
4. 문서 보관 의무

검토 결과:""",
                "rebate_check": """리베이트 쌍벌제 관련 규정 위반 여부를 확인하세요.

거래 내역: {transaction_data}
거래처 정보: {client_info}

확인 사항:
- 약가 인하 여부
- 경제적 이익 제공 내역
- 한도 초과 여부

판정:"""
            },

            # === 응답 생성 템플릿 ===
            "response_generation": {
                "v1": """다음 분석 결과를 사용자 친화적으로 요약하세요.

원본 질의: {original_query}
분석 결과: {analysis_results}
추가 정보: {additional_info}

요구사항:
- 명확하고 간결한 표현
- 핵심 정보 우선
- 필요시 표나 차트 제안
- 전문 용어는 쉽게 설명

응답:""",
                "error_response": """오류 상황을 사용자에게 안내하세요.

오류 유형: {error_type}
상황: {context}

친절하고 도움이 되는 응답:"""
            },

            # === 검색 템플릿 ===
            "search": {
                "hr_search": """인사 정보 검색 쿼리를 최적화하세요.

검색어: {query}
검색 범위: {scope}
필터: {filters}

최적화된 검색 조건:""",
                "rule_search": """규정/지침 검색을 위한 의미론적 쿼리를 생성하세요.

원본 질의: {query}
카테고리: {category}

관련 키워드 및 동의어:"""
            }
        }

        # 시스템 프롬프트
        self.system_prompts = {
            "sql_expert": "You are a SQL expert specializing in pharmaceutical sales data analysis. Generate safe, optimized SELECT queries only.",
            "compliance_officer": "당신은 제약업계 컴플라이언스 전문가입니다. KPBMA 규약과 리베이트 쌍벌제 등 관련 규정을 정확히 이해하고 있습니다.",
            "report_writer": "당신은 제약회사의 전문 보고서 작성자입니다. 데이터를 명확하고 인사이트 있게 전달합니다.",
            "helpful_assistant": "당신은 제약회사 직원들을 돕는 친절하고 전문적인 AI 어시스턴트입니다."
        }

    def get_prompt(
        self,
        category: str,
        subcategory: Optional[str] = None,
        version: str = "v1",
        **kwargs
    ) -> str:
        """
        프롬프트 템플릿 가져오기

        Args:
            category: 대분류
            subcategory: 소분류
            version: 템플릿 버전
            **kwargs: 치환할 변수들

        Returns:
            완성된 프롬프트
        """
        if subcategory:
            template = self.templates.get(category, {}).get(subcategory, "")
        else:
            template = self.templates.get(category, {}).get(version, "")

        if not template:
            raise ValueError(f"Template not found: {category}/{subcategory or version}")

        # 변수 치환
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable for template: {e}")

    def get_system_prompt(self, role: str) -> Optional[str]:
        """시스템 프롬프트 가져오기"""
        return self.system_prompts.get(role)

    def add_template(self, category: str, name: str, template: str):
        """새 템플릿 추가"""
        if category not in self.templates:
            self.templates[category] = {}
        self.templates[category][name] = template

    def list_templates(self) -> Dict[str, list]:
        """사용 가능한 템플릿 목록"""
        return {
            category: list(templates.keys())
            for category, templates in self.templates.items()
        }

    def get_template_variables(self, category: str, name: str = "v1") -> list:
        """템플릿에 필요한 변수 목록 추출"""
        import re
        template = self.templates.get(category, {}).get(name, "")
        if not template:
            return []

        # {variable} 패턴 찾기
        variables = re.findall(r'\{(\w+)\}', template)
        return list(set(variables))