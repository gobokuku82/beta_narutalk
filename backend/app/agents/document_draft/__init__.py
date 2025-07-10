"""
업무문서 초안작성 에이전트 (Document Draft Agent)

업무 문서의 초안을 자동 생성하는 전문 에이전트입니다.
- 보고서, 제안서, 계획서 등 다양한 문서 템플릿 제공
- AI 기반 내용 생성 및 구조화
- 회사 스타일 가이드 적용
"""

from .agent import DocumentDraftAgent
from .config import DocumentDraftConfig
from .templates import DocumentTemplateManager

__all__ = ["DocumentDraftAgent", "DocumentDraftConfig", "DocumentTemplateManager"] 