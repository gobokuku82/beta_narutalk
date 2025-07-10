"""
모듈화된 라우터 시스템

이 패키지는 NaruTalk AI 시스템의 확장 가능한 라우터 아키텍처를 제공합니다.
각 라우터는 특정 기능을 담당하며, 동적으로 로드되고 서로 통신할 수 있습니다.
"""

from .base_router import BaseRouter
from .qa_router import QARouter
from .document_search_router import DocumentSearchRouter
from .employee_info_router import EmployeeInfoRouter
from .general_chat_router import GeneralChatRouter
from .analysis_router import AnalysisRouter
from .report_generator_router import ReportGeneratorRouter

__all__ = [
    "BaseRouter",
    "QARouter",
    "DocumentSearchRouter", 
    "EmployeeInfoRouter",
    "GeneralChatRouter",
    "AnalysisRouter",
    "ReportGeneratorRouter"
] 