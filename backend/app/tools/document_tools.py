"""
Document Tools
문서 생성 및 처리 관련 도구들
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun
import logging
logger = logging.getLogger(__name__)
import time
from datetime import datetime
from pathlib import Path
import json

from app.core.config import settings
from .base import BaseTool, ToolResult, StructuredTool


class DocumentGeneratorInput(BaseModel):
    """문서 생성 입력"""
    content: str = Field(description="문서 내용")
    document_type: str = Field(default="report", description="문서 유형: proposal, report, email, presentation")
    format: str = Field(default="markdown", description="출력 형식: markdown, html, pdf")


class TemplateManagerInput(BaseModel):
    """템플릿 관리자 입력"""
    template_name: str = Field(description="템플릿 이름")
    variables: Dict[str, Any] = Field(default_factory=dict, description="템플릿 변수")


class ReportBuilderInput(BaseModel):
    """리포트 빌더 입력"""
    title: str = Field(description="보고서 제목")
    sections: List[str] = Field(description="보고서 섹션 목록")
    data_sources: List[Dict] = Field(default_factory=list, description="데이터 소스")
    format: str = Field(default="PDF", description="출력 형식")


class DataFormatterInput(BaseModel):
    """데이터 포맷터 입력"""
    data: Dict[str, Any] = Field(description="포맷팅할 데이터")
    format_type: str = Field(default="table", description="포맷 유형: table, chart, list")
    include_charts: bool = Field(default=False, description="차트 포함 여부")


class PDFGeneratorInput(BaseModel):
    """PDF 생성 입력"""
    content: str = Field(description="변환할 내용")
    title: str = Field(description="문서 제목")
    metadata: Optional[Dict] = Field(None, description="메타데이터")


class DocumentGeneratorTool(StructuredTool):
    """문서 생성 도구"""
    
    name: str = "document_generator"
    description: str = "다양한 유형의 문서를 생성합니다. 제안서, 보고서, 이메일, 프레젠테이션 등을 만들 수 있습니다."
    args_schema: type[BaseModel] = DocumentGeneratorInput
    templates_dir: Any = Field(default=None, exclude=True)
    generated_dir: Any = Field(default=None, exclude=True)
    
    def __init__(self):
        super().__init__()
        self.templates_dir = settings.DOCUMENTS_DIR / "templates"
        self.generated_dir = settings.DOCUMENTS_DIR / "generated"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
    
    async def _arun(
        self,
        content: str,
        document_type: str = "report",
        format: str = "markdown",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """문서 생성 실행"""
        start_time = time.time()
        
        try:
            # 간단한 문서 생성 (content를 그대로 사용)
            document = f"# Document\n\nType: {document_type}\n\n{content}"
            
            # 형식 변환
            if format == "html":
                document = self._convert_to_html(document)
            elif format == "pdf":
                # PDF 변환은 별도 도구 사용
                pass
            
            # 파일 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{document_type}_{timestamp}.{format if format != 'pdf' else 'md'}"
            filepath = self.generated_dir / filename
            
            filepath.write_text(document, encoding="utf-8")
            
            return ToolResult(
                success=True,
                data={
                    "document": document,
                    "document_type": document_type,
                    "filename": filename,
                    "filepath": str(filepath),
                    "format": format,
                    "content_preview": document[:500],
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "word_count": len(document.split())
                    }
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    async def _generate_proposal(self, title: str, content: Dict) -> str:
        """제안서 생성"""
        default_features = '- 우수한 효과\n- 안전성 입증\n- 편리한 복용법'
        current_date = datetime.now().strftime('%Y년 %m월 %d일')
        
        template = f"""# {title}

## 1. 제품 소개
### 제품명: {content.get('product_name', 'N/A')}
- **성분명**: {content.get('generic_name', 'N/A')}
- **적응증**: {content.get('indication', 'N/A')}
- **용법용량**: {content.get('dosage', 'N/A')}

## 2. 제품 특장점
{content.get('features', default_features)}

## 3. 임상 데이터
{content.get('clinical_data', '임상시험 결과 요약')}

## 4. 경쟁 우위
{content.get('competitive_advantages', '경쟁 제품 대비 장점')}

## 5. 공급 조건
- **가격**: {content.get('price', '협의')}
- **최소 주문량**: {content.get('min_order', '협의')}
- **납기**: {content.get('delivery', '주문 후 3일 이내')}

## 6. 제안 요약
{content.get('summary', '귀 병원에 최적화된 의약품 공급 제안')}

---
**작성일**: {current_date}
**담당자**: {content.get('author', '영업팀')}
**연락처**: {content.get('contact', '02-1234-5678')}
"""
        return template
    
    async def _generate_report(self, title: str, content: Dict) -> str:
        """보고서 생성"""
        default_period = datetime.now().strftime('%Y년 %m월')
        current_date = datetime.now().strftime('%Y-%m-%d')
        default_achievements = '- 주요 성과 1\n- 주요 성과 2\n- 주요 성과 3'
        default_improvements = '- 개선 필요 사항 1\n- 개선 필요 사항 2'
        
        template = f"""# {title}

## 보고서 개요
- **기간**: {content.get('period', default_period)}
- **작성자**: {content.get("author", "영업팀")}
- **작성일**: {current_date}

## 1. 실적 요약
{content.get('performance_summary', '이번 기간 실적 요약')}

### 주요 지표
- **매출액**: {content.get('revenue', 'N/A')}
- **목표 달성률**: {content.get('achievement_rate', 'N/A')}%
- **신규 고객**: {content.get('new_customers', 'N/A')}개사

## 2. 세부 분석
{content.get('detailed_analysis', '세부 분석 내용')}

## 3. 주요 성과
{content.get('key_achievements', default_achievements)}

## 4. 개선 사항
{content.get('improvements', default_improvements)}

## 5. 향후 계획
{content.get('future_plans', '다음 기간 계획 및 전략')}

## 6. 결론
{content.get('conclusion', '종합 의견 및 제언')}
"""
        return template
    
    async def _generate_email(self, title: str, content: Dict) -> str:
        """이메일 생성"""
        current_date = datetime.now().strftime('%Y년 %m월 %d일')
        template = f"""제목: {title}

수신: {content.get('recipient', '고객님')}
발신: {content.get('sender', '영업팀')}
날짜: {current_date}

안녕하세요, {content.get('recipient_name', '선생님')}

{content.get('greeting', '평소 저희 제품에 관심을 가져주셔서 감사합니다.')}

{content.get('main_content', '본문 내용')}

{content.get('closing', '궁금하신 사항이 있으시면 언제든 연락 주시기 바랍니다.')}

감사합니다.

{content.get('sender_name', '홍길동')}
{content.get('sender_title', '영업 담당자')}
{content.get('company', '제약회사')}
{content.get('contact_info', 'Tel: 02-1234-5678 | Email: info@pharma.com')}
"""
        return template
    
    async def _generate_presentation(self, title: str, content: Dict) -> str:
        """프레젠테이션 생성"""
        current_date = datetime.now().strftime('%Y년 %m월 %d일')
        default_agenda = '1. 서론\n2. 본론\n3. 결론\n4. Q&A'
        
        template = f"""# {title}

---

## 슬라이드 1: 제목
### {title}
- 발표자: {content.get('presenter', '발표자')}
- 날짜: {current_date}

---

## 슬라이드 2: 목차
{content.get('agenda', default_agenda)}

---

## 슬라이드 3: 배경 및 목적
{content.get('background', '프레젠테이션 배경 및 목적')}

---

## 슬라이드 4-8: 주요 내용
{content.get('main_content', '주요 내용')}

---

## 슬라이드 9: 결론 및 제언
{content.get('conclusion', '결론 및 제언')}

---

## 슬라이드 10: 감사합니다
### 질문 있으신가요?

**연락처**
- {content.get('contact', 'email@company.com')}
"""
        return template
    
    def _convert_to_html(self, markdown_content: str) -> str:
        """Markdown을 HTML로 변환"""
        # 간단한 변환 (실제로는 markdown 라이브러리 사용)
        html = markdown_content.replace("# ", "<h1>").replace("\n", "</h1>\n", 1)
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n", 1)
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n", 1)
        html = html.replace("- ", "<li>").replace("\n", "</li>\n")
        html = f"<html><body>{html}</body></html>"
        return html
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class ReportBuilderTool(StructuredTool):
    """리포트 빌더 도구"""
    
    name: str = "report_builder"
    description: str = "구조화된 보고서를 생성합니다."
    args_schema: type[BaseModel] = ReportBuilderInput
    
    async def _arun(
        self,
        title: str,
        sections: List[str],
        data_sources: List[Dict] = None,
        format: str = "PDF",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """리포트 생성 실행"""
        start_time = time.time()
        
        try:
            # 보고서 구조 생성
            report_content = f"# {title}\n\n"
            current_date = datetime.now().strftime('%Y년 %m월 %d일')
            report_content += f"작성일: {current_date}\n\n"
            
            # 섹션별 내용 생성
            for i, section in enumerate(sections, 1):
                report_content += f"\n## {i}. {section}\n"
                
                # 데이터 소스가 있으면 활용
                if data_sources and i <= len(data_sources):
                    data = data_sources[i-1]
                    if isinstance(data, dict):
                        for key, value in data.items():
                            report_content += f"- {key}: {value}\n"
                    else:
                        report_content += f"{data}\n"
                else:
                    report_content += f"[{section} 내용]\n"
            
            # 메타데이터 추가
            metadata = {
                "title": title,
                "sections_count": len(sections),
                "format": format,
                "created_at": datetime.now().isoformat(),
                "word_count": len(report_content.split())
            }
            
            return ToolResult(
                success=True,
                data={
                    "report": {
                        "content": report_content,
                        "metadata": metadata
                    },
                    "format": format,
                    "sections": sections
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class TemplateManagerTool(StructuredTool):
    """템플릿 관리자 도구"""
    
    name: str = "template_manager"
    description: str = "템플릿을 관리하고 변수를 채워 문서를 생성합니다."
    args_schema: type[BaseModel] = TemplateManagerInput
    templates_dir: Any = Field(default=None, exclude=True)
    
    def __init__(self):
        super().__init__()
        self.templates_dir = settings.DOCUMENTS_DIR / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._init_templates()
    
    def _init_templates(self):
        """기본 템플릿 초기화"""
        templates = {
            "drug_info": """## 의약품 정보

**제품명**: {product_name}
**성분명**: {generic_name}
**제조사**: {manufacturer}
**적응증**: {indication}
**용법용량**: {dosage}
**부작용**: {side_effects}
**주의사항**: {precautions}
""",
            "sales_summary": """## 매출 요약 ({period})

**총 매출**: {total_revenue:,}원
**목표 달성률**: {achievement_rate}%
**전월 대비**: {mom_growth}%
**전년 동기 대비**: {yoy_growth}%

### 제품별 매출
{product_sales}

### 지역별 매출
{regional_sales}
""",
            "meeting_minutes": """## 회의록

**일시**: {date}
**장소**: {location}
**참석자**: {attendees}
**주제**: {topic}

### 논의 사항
{discussions}

### 결정 사항
{decisions}

### 액션 아이템
{action_items}

**다음 회의**: {next_meeting}
"""
        }
        
        for name, content in templates.items():
            filepath = self.templates_dir / f"{name}.txt"
            if not filepath.exists():
                filepath.write_text(content, encoding="utf-8")
    
    async def _arun(
        self,
        template_name: str,
        variables: Dict[str, Any],
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """템플릿 로드 및 변수 채우기"""
        start_time = time.time()
        
        try:
            template_path = self.templates_dir / f"{template_name}.txt"
            
            if not template_path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Template not found: {template_name}",
                    execution_time=time.time() - start_time,
                    tool_name=self.name
                )
            
            # 템플릿 로드
            template = template_path.read_text(encoding="utf-8")
            
            # 변수 채우기 (KeyError 무시하고 기본값 사용)
            filled_content = template
            for key, value in variables.items():
                filled_content = filled_content.replace(f"{{{key}}}", str(value))
            
            # 남은 플레이스홀더를 기본값으로 대체
            import re
            filled_content = re.sub(r'\{\w+\}', '[미입력]', filled_content)
            
            return ToolResult(
                success=True,
                data={
                    "rendered_document": filled_content,
                    "template_name": template_name,
                    "variables_used": list(variables.keys())
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class DataFormatterTool(StructuredTool):
    """데이터 포맷터 도구"""
    
    name: str = "data_formatter"
    description: str = "데이터를 다양한 형식으로 포맷팅합니다."
    args_schema: type[BaseModel] = DataFormatterInput
    
    async def _arun(
        self,
        data: Dict[str, Any],
        format_type: str = "table",
        include_charts: bool = False,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """데이터 포맷팅 실행"""
        start_time = time.time()
        
        try:
            formatted_output = ""
            
            if format_type == "table":
                # 테이블 형식으로 포맷팅
                formatted_output = "| Key | Value |\n|-----|-------|\n"
                for key, value in data.items():
                    formatted_output += f"| {key} | {value} |\n"
            
            elif format_type == "chart":
                # 차트 형식 (텍스트 기반)
                formatted_output = "Chart Data:\n"
                max_value = max((v for v in data.values() if isinstance(v, (int, float))), default=100)
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        bar_length = int((value / max_value) * 20)
                        bar = "█" * bar_length
                        formatted_output += f"{key}: {bar} {value}\n"
                    else:
                        formatted_output += f"{key}: {value}\n"
            
            elif format_type == "list":
                # 리스트 형식
                formatted_output = "Data List:\n"
                for key, value in data.items():
                    formatted_output += f"• {key}: {value}\n"
            
            else:
                # 기본 JSON 형식
                formatted_output = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 차트 추가 (텍스트 기반 시뮬레이션)
            if include_charts:
                formatted_output += "\n\n=== Chart Visualization ===\n"
                formatted_output += "[Chart would be displayed here]\n"
            
            return ToolResult(
                success=True,
                data={
                    "formatted_output": formatted_output,
                    "format_type": format_type,
                    "data_points": len(data),
                    "include_charts": include_charts
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class PDFGeneratorTool(StructuredTool):
    """PDF 생성 도구"""
    
    name: str = "pdf_generator"
    description: str = "텍스트나 마크다운 콘텐츠를 PDF로 변환합니다."
    args_schema: type[BaseModel] = PDFGeneratorInput
    
    async def _arun(
        self,
        content: str,
        title: str,
        metadata: Optional[Dict] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """PDF 생성 실행"""
        start_time = time.time()
        
        try:
            # Mock PDF 생성 (실제로는 reportlab이나 weasyprint 사용)
            generated_dir = settings.DOCUMENTS_DIR / "generated"
            generated_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"document_{timestamp}.pdf"
            filepath = generated_dir / filename
            
            # PDF 메타데이터
            pdf_metadata = {
                "title": title,
                "created_at": datetime.now().isoformat(),
                "page_count": len(content.split("\n")) // 40 + 1,  # 대략적인 페이지 수
                "file_size": len(content.encode()) * 1.5,  # 대략적인 파일 크기
                **(metadata or {})
            }
            
            # Mock PDF 생성 (실제로는 PDF 생성 로직)
            # 여기서는 메타데이터만 JSON으로 저장
            metadata_file = generated_dir / f"document_{timestamp}_metadata.json"
            metadata_file.write_text(json.dumps(pdf_metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            
            return ToolResult(
                success=True,
                data={
                    "filename": filename,
                    "filepath": str(filepath),
                    "title": title,
                    "metadata": pdf_metadata,
                    "status": "PDF 생성 완료 (시뮬레이션)"
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class DocumentSummarizerTool(BaseTool):
    """문서 요약 도구"""
    
    name: str = "document_summarizer"
    description: str = "긴 문서를 요약합니다."
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """문서 요약 실행"""
        start_time = time.time()
        
        try:
            # 입력 텍스트 분석
            word_count = len(query.split())
            
            # Mock 요약 생성
            if word_count < 100:
                summary = query  # 짧은 텍스트는 그대로
            else:
                # 간단한 요약 시뮬레이션
                sentences = query.split(".")[:3]  # 처음 3문장
                summary = ". ".join(sentences) + "."
                
                # 핵심 포인트 추출
                key_points = [
                    "주요 내용 1",
                    "주요 내용 2",
                    "주요 내용 3"
                ]
            
            return ToolResult(
                success=True,
                data={
                    "original_word_count": word_count,
                    "summary": summary,
                    "summary_word_count": len(summary.split()),
                    "compression_ratio": round(len(summary.split()) / word_count * 100, 1) if word_count > 0 else 100,
                    "key_points": key_points if word_count >= 100 else []
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


# Tool 레지스트리에 등록
def register_document_tools():
    """모든 문서 도구를 레지스트리에 등록"""
    from .base import tool_registry
    
    tools = [
        (DocumentGeneratorTool(), "document"),
        (ReportBuilderTool(), "document"),
        (TemplateManagerTool(), "document"),
        (DataFormatterTool(), "document"),
        (PDFGeneratorTool(), "document"),
        (DocumentSummarizerTool(), "document")
    ]
    
    for tool, category in tools:
        tool_registry.register(tool, category)
    
    logger.info(f"Registered {len(tools)} document tools")