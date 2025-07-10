"""
업무문서 초안작성 에이전트 설정

문서 생성과 관련된 모든 설정을 관리합니다.
"""

from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class DocumentDraftConfig:
    """업무문서 초안작성 에이전트 설정"""
    
    # 기본 설정
    agent_name: str = "document_draft_agent"
    max_document_length: int = 5000
    confidence_threshold: float = 0.7
    
    # 지원하는 문서 유형
    supported_document_types: List[str] = None
    
    # 문서 템플릿 설정
    template_directory: str = "templates"
    custom_templates: Dict[str, str] = None
    
    # 생성 옵션
    include_table_of_contents: bool = True
    include_executive_summary: bool = True
    include_appendix: bool = False
    
    # AI 생성 설정
    ai_model: str = "gpt-4"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 2000
    
    # 회사 스타일 가이드
    company_style: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.supported_document_types is None:
            self.supported_document_types = [
                "report",           # 보고서
                "proposal",         # 제안서  
                "plan",            # 계획서
                "memo",            # 메모
                "presentation",    # 프레젠테이션
                "procedure",       # 절차서
                "manual",          # 매뉴얼
                "policy",          # 정책문서
                "contract",        # 계약서
                "meeting_minutes"  # 회의록
            ]
        
        if self.custom_templates is None:
            self.custom_templates = {}
        
        if self.company_style is None:
            self.company_style = {
                "font_family": "맑은 고딕",
                "font_size": 11,
                "line_spacing": 1.5,
                "margin": {
                    "top": 25,
                    "bottom": 25,
                    "left": 20,
                    "right": 20
                },
                "header_style": {
                    "include_logo": True,
                    "include_date": True,
                    "include_page_number": True
                },
                "footer_style": {
                    "include_company_name": True,
                    "include_confidentiality": True
                }
            }

# 기본 설정 인스턴스
default_config = DocumentDraftConfig() 