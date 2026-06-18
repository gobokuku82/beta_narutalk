"""ResponsePayload — Response 레이어 산출물

4-Layer의 마지막 변환: ExecutionResult → 사용자 언어
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ResponseFormat(str, Enum):
    TEXT  = "text"
    PDF   = "pdf"
    PPT   = "ppt"           # 2026-06-09: 슬라이드 출력 (OutputFormat 정합)
    EXCEL = "excel"         # 표 출력 (렌더 구현 보류)
    IMAGE = "image"
    CHART = "chart"
    VIDEO = "video"
    MIXED = "mixed"
    ERROR = "error"         # 실행 실패 폴백


class Attachment(BaseModel):
    """첨부 파일/자원"""
    kind: str                 # "pdf" | "image" | "chart" | "video" | "link"
    path: Optional[str] = None
    url: Optional[str] = None
    caption: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)


class ResponsePayload(BaseModel):
    """Response Layer 최종 산출물"""
    format: ResponseFormat
    text: str                 # 메인 텍스트 응답 (항상 존재)
    summary: Optional[str] = None             # 1~2 문장 핵심 요약
    next_actions: list[str] = Field(default_factory=list)   # 추천 후속 작업
    attachments: list[Attachment] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)      # 처리 시간, 완료 Todo 수 등
    error: Optional[str] = None               # format=error일 때
