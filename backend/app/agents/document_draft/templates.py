"""
문서 템플릿 매니저

다양한 업무 문서 템플릿을 관리하고 생성하는 클래스입니다.
"""

from typing import Dict, List, Any, Optional
import logging
from .config import DocumentDraftConfig

logger = logging.getLogger(__name__)

class DocumentTemplateManager:
    """문서 템플릿 관리 클래스"""
    
    def __init__(self, config: DocumentDraftConfig):
        self.config = config
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """기본 문서 템플릿 로드"""
        return {
            "report": {
                "name": "업무 보고서",
                "structure": [
                    "제목",
                    "목차", 
                    "요약",
                    "배경 및 목적",
                    "주요 내용",
                    "결론 및 제언",
                    "첨부 자료"
                ],
                "sections": {
                    "제목": "제목을 간결하고 명확하게 작성하세요.",
                    "요약": "보고서의 핵심 내용을 2-3문단으로 요약하세요.",
                    "배경 및 목적": "보고서 작성 배경과 목적을 설명하세요.",
                    "주요 내용": "보고서의 핵심 내용을 상세히 기술하세요.",
                    "결론 및 제언": "분석 결과와 향후 방향을 제시하세요."
                }
            },
            "proposal": {
                "name": "사업 제안서",
                "structure": [
                    "제목",
                    "목차",
                    "개요",
                    "사업 배경",
                    "제안 내용",
                    "추진 계획",
                    "예상 효과",
                    "예산 및 일정",
                    "결론"
                ],
                "sections": {
                    "개요": "제안하는 사업의 핵심 내용을 요약하세요.",
                    "사업 배경": "제안 사업의 필요성과 배경을 설명하세요.",
                    "제안 내용": "구체적인 사업 내용과 방법을 기술하세요.",
                    "추진 계획": "단계별 추진 계획을 상세히 작성하세요.",
                    "예상 효과": "기대되는 성과와 효과를 제시하세요."
                }
            },
            "plan": {
                "name": "업무 계획서",
                "structure": [
                    "제목",
                    "목차",
                    "계획 개요",
                    "현황 분석",
                    "목표 설정",
                    "세부 계획",
                    "추진 일정",
                    "예산 계획",
                    "기대 효과"
                ],
                "sections": {
                    "계획 개요": "계획의 목적과 범위를 명확히 하세요.",
                    "현황 분석": "현재 상황과 문제점을 분석하세요.",
                    "목표 설정": "달성하고자 하는 구체적 목표를 설정하세요.",
                    "세부 계획": "목표 달성을 위한 세부 실행 방안을 작성하세요."
                }
            },
            "memo": {
                "name": "업무 메모",
                "structure": [
                    "제목",
                    "날짜",
                    "수신자",
                    "발신자",
                    "주요 내용",
                    "조치 사항"
                ],
                "sections": {
                    "주요 내용": "전달하고자 하는 핵심 내용을 기술하세요.",
                    "조치 사항": "필요한 후속 조치나 요청사항을 명시하세요."
                }
            },
            "meeting_minutes": {
                "name": "회의록",
                "structure": [
                    "회의명",
                    "일시 및 장소",
                    "참석자",
                    "회의 안건",
                    "주요 논의 내용",
                    "결정 사항",
                    "조치 사항",
                    "다음 회의 일정"
                ],
                "sections": {
                    "주요 논의 내용": "각 안건별 논의 내용을 정리하세요.",
                    "결정 사항": "회의에서 결정된 사항을 명확히 기록하세요.",
                    "조치 사항": "담당자별 후속 조치사항을 정리하세요."
                }
            },
            "procedure": {
                "name": "업무 절차서",
                "structure": [
                    "제목",
                    "목차",
                    "목적 및 적용 범위",
                    "관련 규정",
                    "용어 정의",
                    "절차 흐름도",
                    "세부 절차",
                    "관련 양식",
                    "개정 이력"
                ],
                "sections": {
                    "목적 및 적용 범위": "절차서의 목적과 적용 대상을 명확히 하세요.",
                    "세부 절차": "각 단계별 세부 절차를 순서대로 기술하세요.",
                    "관련 양식": "절차 수행에 필요한 양식을 제시하세요."
                }
            }
        }
    
    def get_template(self, document_type: str) -> Optional[Dict[str, Any]]:
        """템플릿 조회"""
        return self.templates.get(document_type)
    
    def get_available_templates(self) -> List[Dict[str, str]]:
        """사용 가능한 템플릿 목록"""
        return [
            {
                "type": doc_type,
                "name": template["name"],
                "description": f"{template['name']} 템플릿"
            }
            for doc_type, template in self.templates.items()
        ]
    
    def generate_document_structure(self, document_type: str, title: str = "") -> Dict[str, Any]:
        """문서 구조 생성"""
        template = self.get_template(document_type)
        if not template:
            return {}
        
        structure = {
            "title": title or f"새로운 {template['name']}",
            "type": document_type,
            "template_name": template["name"],
            "sections": []
        }
        
        for section_name in template["structure"]:
            section = {
                "name": section_name,
                "content": "",
                "guidance": template["sections"].get(section_name, ""),
                "completed": False
            }
            structure["sections"].append(section)
        
        return structure
    
    def generate_section_prompt(self, document_type: str, section_name: str, 
                              context: Dict[str, Any] = None) -> str:
        """섹션별 생성 프롬프트 생성"""
        template = self.get_template(document_type)
        if not template:
            return ""
        
        guidance = template["sections"].get(section_name, "")
        context_info = ""
        
        if context:
            context_info = f"\n참고 정보:\n"
            for key, value in context.items():
                context_info += f"- {key}: {value}\n"
        
        prompt = f"""
다음 문서의 '{section_name}' 섹션을 작성해주세요.

문서 유형: {template['name']}
섹션: {section_name}
작성 가이드: {guidance}
{context_info}

전문적이고 체계적인 내용으로 작성해주세요.
좋은제약 회사의 업무 문서 스타일에 맞게 작성해주세요.
"""
        return prompt
    
    def validate_document_structure(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """문서 구조 검증"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "completeness": 0.0
        }
        
        if not document.get("title"):
            validation_result["errors"].append("문서 제목이 없습니다.")
            validation_result["is_valid"] = False
        
        if not document.get("sections"):
            validation_result["errors"].append("문서 섹션이 없습니다.")
            validation_result["is_valid"] = False
            return validation_result
        
        completed_sections = 0
        total_sections = len(document["sections"])
        
        for section in document["sections"]:
            if section.get("completed") or section.get("content"):
                completed_sections += 1
            elif section.get("name") in ["제목", "목차", "날짜"]:
                # 자동 생성 가능한 섹션은 완료로 간주
                completed_sections += 1
        
        validation_result["completeness"] = completed_sections / total_sections if total_sections > 0 else 0
        
        if validation_result["completeness"] < 0.5:
            validation_result["warnings"].append("문서 완성도가 낮습니다.")
        
        return validation_result
    
    def apply_company_style(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """회사 스타일 가이드 적용"""
        styled_document = document.copy()
        
        # 스타일 정보 추가
        styled_document["style"] = self.config.company_style.copy()
        
        # 헤더/푸터 정보 추가
        if self.config.company_style["header_style"]["include_logo"]:
            styled_document["header"] = "좋은제약 로고"
        
        if self.config.company_style["footer_style"]["include_company_name"]:
            styled_document["footer"] = "좋은제약 | 기밀문서"
        
        return styled_document
    
    def add_custom_template(self, template_type: str, template_data: Dict[str, Any]):
        """사용자 정의 템플릿 추가"""
        self.templates[template_type] = template_data
        logger.info(f"사용자 정의 템플릿 추가: {template_type}")
    
    def get_template_suggestions(self, query: str) -> List[str]:
        """쿼리 기반 템플릿 제안"""
        suggestions = []
        query_lower = query.lower()
        
        suggestion_keywords = {
            "보고서": ["report"],
            "제안서": ["proposal"], 
            "계획서": ["plan"],
            "메모": ["memo"],
            "회의록": ["meeting_minutes"],
            "절차서": ["procedure"]
        }
        
        for keyword, template_types in suggestion_keywords.items():
            if keyword in query_lower:
                suggestions.extend(template_types)
        
        # 기본 제안
        if not suggestions:
            suggestions = ["report", "memo", "plan"]
        
        return suggestions 