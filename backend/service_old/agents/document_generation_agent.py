"""
    문서를 자동으로 생성해줍니다. 각 문서 생성은 tool로 관리합니다.
"""

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from datetime import datetime
import json
from pathlib import Path
import logging
from jinja2 import Template, Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class DocumentState(TypedDict):
    document_type: str  # report, contract, memo, form
    template_id: str
    input_data: Dict[str, Any]
    generated_content: str
    format_type: str  # pdf, docx, html, text
    metadata: Dict[str, Any]
    validation_errors: List[str]
    final_document: Dict[str, Any]
    execution_status: str

class DocumentGenerationAgent:
    def __init__(self):
        self.workflow = StateGraph(DocumentState)
        self._initialize_templates()
        self._build_graph()

    def _initialize_templates(self):
        """문서 템플릿 초기화"""
        self.template_dir = Path("backend/service/tools/templates")

        # Jinja2 환경 설정
        if self.template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True
            )
        else:
            self.jinja_env = Environment()
            logger.warning(f"Template directory not found: {self.template_dir}")

        # 사전 정의된 템플릿 매핑
        self.template_registry = {
            "sales_report": {
                "template_file": "sales_report.html",
                "required_fields": ["period", "sales_data", "analysis", "author"],
                "description": "매출 실적 보고서"
            },
            "compliance_report": {
                "template_file": "compliance_report.html",
                "required_fields": ["review_date", "violations", "recommendations", "reviewer"],
                "description": "규정 준수 검토 보고서"
            },
            "meeting_minutes": {
                "template_file": "meeting_minutes.html",
                "required_fields": ["meeting_date", "attendees", "agenda", "decisions", "action_items"],
                "description": "회의록"
            },
            "purchase_order": {
                "template_file": "purchase_order.html",
                "required_fields": ["order_id", "vendor", "items", "total_amount", "delivery_date"],
                "description": "구매 주문서"
            },
            "hr_notice": {
                "template_file": "hr_notice.html",
                "required_fields": ["notice_type", "subject", "content", "effective_date", "department"],
                "description": "인사 공지사항"
            }
        }

    def _build_graph(self):
        """그래프 구성"""
        # 노드 추가
        self.workflow.add_node("identify_template", self.identify_document_template)
        self.workflow.add_node("validate_data", self.validate_input_data)
        self.workflow.add_node("prepare_data", self.prepare_document_data)
        self.workflow.add_node("generate_content", self.generate_document_content)
        self.workflow.add_node("format_document", self.format_final_document)
        self.workflow.add_node("add_metadata", self.add_document_metadata)
        self.workflow.add_node("handle_errors", self.handle_generation_errors)

        # 엔트리 포인트 설정 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "identify_template")

        # 템플릿 식별 후 검증
        self.workflow.add_edge("identify_template", "validate_data")

        # 검증 결과에 따른 분기
        self.workflow.add_conditional_edges(
            "validate_data",
            self.check_validation_result,
            {
                "valid": "prepare_data",
                "invalid": "handle_errors"
            }
        )

        # 데이터 준비 후 생성
        self.workflow.add_edge("prepare_data", "generate_content")

        # 내용 생성 후 포맷팅
        self.workflow.add_edge("generate_content", "format_document")

        # 포맷팅 후 메타데이터 추가
        self.workflow.add_edge("format_document", "add_metadata")

        # 에러 처리 후 종료
        self.workflow.add_edge("handle_errors", END)

        # 메타데이터 추가 후 종료
        self.workflow.add_edge("add_metadata", END)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 실행 인터페이스"""
        initial_state = DocumentState(
            document_type=input_data.get("document_type", ""),
            template_id=input_data.get("template_id", ""),
            input_data=input_data.get("data", {}),
            generated_content="",
            format_type=input_data.get("format", "html"),
            metadata={},
            validation_errors=[],
            final_document={},
            execution_status="initializing"
        )

        # 워크플로우 컴파일 및 실행
        app = self.workflow.compile()
        result = await app.ainvoke(initial_state)

        return result.get("final_document", {})

    async def identify_document_template(self, state: DocumentState) -> DocumentState:
        """문서 템플릿 식별"""
        state["execution_status"] = "identifying_template"

        document_type = state.get("document_type", "")
        template_id = state.get("template_id", "")

        # 템플릿 ID가 직접 지정된 경우
        if template_id and template_id in self.template_registry:
            state["template_id"] = template_id
        # 문서 타입으로 추론
        elif document_type:
            # 문서 타입과 매칭되는 템플릿 찾기
            for tid, tinfo in self.template_registry.items():
                if document_type.lower() in tinfo["description"].lower():
                    state["template_id"] = tid
                    break

        if not state.get("template_id"):
            # 기본 템플릿 사용
            state["template_id"] = "generic_document"
            logger.warning(f"No template found for type: {document_type}, using generic")

        logger.info(f"Selected template: {state['template_id']}")
        return state

    async def validate_input_data(self, state: DocumentState) -> DocumentState:
        """입력 데이터 검증"""
        state["execution_status"] = "validating_data"

        template_id = state.get("template_id", "")
        input_data = state.get("input_data", {})
        validation_errors = []

        # 템플릿 정보 가져오기
        template_info = self.template_registry.get(template_id, {})
        required_fields = template_info.get("required_fields", [])

        # 필수 필드 검증
        for field in required_fields:
            if field not in input_data or input_data[field] is None:
                validation_errors.append(f"Missing required field: {field}")

        # 데이터 타입 검증
        if "sales_data" in input_data:
            if not isinstance(input_data["sales_data"], (list, dict)):
                validation_errors.append("sales_data must be a list or dict")

        if "total_amount" in input_data:
            if not isinstance(input_data["total_amount"], (int, float)):
                validation_errors.append("total_amount must be numeric")

        state["validation_errors"] = validation_errors

        if validation_errors:
            logger.warning(f"Validation errors: {validation_errors}")
        else:
            logger.info("Data validation successful")

        return state

    def check_validation_result(self, state: DocumentState) -> str:
        """검증 결과 확인"""
        if state.get("validation_errors"):
            return "invalid"
        return "valid"

    async def prepare_document_data(self, state: DocumentState) -> DocumentState:
        """문서 생성을 위한 데이터 준비"""
        state["execution_status"] = "preparing_data"

        input_data = state.get("input_data", {})
        template_id = state.get("template_id", "")

        # 데이터 전처리
        prepared_data = input_data.copy()

        # 날짜 포맷팅
        for key, value in prepared_data.items():
            if "date" in key.lower() and isinstance(value, str):
                try:
                    # ISO 형식 날짜를 읽기 쉬운 형식으로
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    prepared_data[key] = dt.strftime("%Y년 %m월 %d일")
                except:
                    pass

        # 숫자 포맷팅
        if "total_amount" in prepared_data:
            amount = prepared_data["total_amount"]
            if isinstance(amount, (int, float)):
                prepared_data["total_amount_formatted"] = f"{amount:,.0f}원"

        # 매출 데이터 처리
        if "sales_data" in prepared_data and isinstance(prepared_data["sales_data"], list):
            # 요약 통계 추가
            total_sales = sum(item.get("amount", 0) for item in prepared_data["sales_data"])
            prepared_data["total_sales"] = f"{total_sales:,.0f}원"
            prepared_data["sales_count"] = len(prepared_data["sales_data"])

        # 기본값 설정
        prepared_data.setdefault("generation_date", datetime.now().strftime("%Y년 %m월 %d일"))
        prepared_data.setdefault("document_number", self._generate_document_number())

        state["input_data"] = prepared_data

        logger.info("Document data prepared")
        return state

    async def generate_document_content(self, state: DocumentState) -> DocumentState:
        """문서 내용 생성"""
        state["execution_status"] = "generating_content"

        template_id = state.get("template_id", "")
        input_data = state.get("input_data", {})

        try:
            template_info = self.template_registry.get(template_id, {})
            template_file = template_info.get("template_file")

            if template_file and self.jinja_env:
                # Jinja2 템플릿 렌더링
                try:
                    template = self.jinja_env.get_template(template_file)
                    generated_content = template.render(**input_data)
                except Exception as e:
                    logger.warning(f"Template rendering failed: {e}")
                    generated_content = self._generate_fallback_content(template_id, input_data)
            else:
                # 폴백: 간단한 템플릿 생성
                generated_content = self._generate_fallback_content(template_id, input_data)

            state["generated_content"] = generated_content

            logger.info(f"Document content generated: {len(generated_content)} chars")

        except Exception as e:
            logger.error(f"Error generating document: {e}")
            state["generated_content"] = "문서 생성 중 오류가 발생했습니다."

        return state

    async def format_final_document(self, state: DocumentState) -> DocumentState:
        """최종 문서 포맷팅"""
        state["execution_status"] = "formatting"

        content = state.get("generated_content", "")
        format_type = state.get("format_type", "html")

        formatted_document = {
            "content": content,
            "format": format_type,
            "length": len(content)
        }

        # 포맷별 처리
        if format_type == "html":
            # HTML 그대로 유지
            formatted_document["mime_type"] = "text/html"

        elif format_type == "text":
            # HTML 태그 제거
            import re
            text_content = re.sub('<[^<]+?>', '', content)
            formatted_document["content"] = text_content
            formatted_document["mime_type"] = "text/plain"

        elif format_type == "json":
            # JSON 형식으로 변환
            formatted_document["content"] = json.dumps({
                "document": content,
                "metadata": state.get("metadata", {})
            }, ensure_ascii=False, indent=2)
            formatted_document["mime_type"] = "application/json"

        elif format_type in ["pdf", "docx"]:
            # PDF/DOCX 변환은 별도 라이브러리 필요
            formatted_document["conversion_required"] = True
            formatted_document["mime_type"] = f"application/{format_type}"
            logger.info(f"{format_type.upper()} conversion required - returning HTML")

        state["final_document"]["formatted_content"] = formatted_document

        logger.info(f"Document formatted as {format_type}")
        return state

    async def add_document_metadata(self, state: DocumentState) -> DocumentState:
        """문서 메타데이터 추가"""
        state["execution_status"] = "adding_metadata"

        # 메타데이터 구성
        metadata = {
            "document_id": self._generate_document_id(),
            "template_id": state.get("template_id", ""),
            "document_type": state.get("document_type", ""),
            "created_at": datetime.now().isoformat(),
            "format": state.get("format_type", ""),
            "status": "completed",
            "validation_passed": len(state.get("validation_errors", [])) == 0
        }

        # 최종 문서 구성
        final_document = state.get("final_document", {})
        final_document["metadata"] = metadata
        final_document["content"] = state.get("generated_content", "")
        final_document["status"] = "success"

        state["final_document"] = final_document
        state["execution_status"] = "completed"

        logger.info("Document generation completed")
        return state

    async def handle_generation_errors(self, state: DocumentState) -> DocumentState:
        """문서 생성 에러 처리"""
        state["execution_status"] = "error"

        validation_errors = state.get("validation_errors", [])

        error_document = {
            "status": "error",
            "errors": validation_errors,
            "message": "문서 생성 실패",
            "timestamp": datetime.now().isoformat()
        }

        # 에러 상세 정보 추가
        if validation_errors:
            error_document["error_type"] = "validation_error"
            error_document["required_fields"] = self._get_required_fields(state.get("template_id", ""))

        state["final_document"] = error_document

        logger.error(f"Document generation failed: {validation_errors}")
        return state

    def _generate_fallback_content(self, template_id: str, data: Dict) -> str:
        """폴백 템플릿 콘텐츠 생성"""
        template_info = self.template_registry.get(template_id, {})
        description = template_info.get("description", "문서")

        content = f"""
        <html>
        <head>
            <title>{description}</title>
            <style>
                body {{ font-family: 'Malgun Gothic', sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .field {{ margin: 10px 0; }}
                .label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>{description}</h1>
            <div class="document-info">
                <div class="field">
                    <span class="label">문서번호:</span> {data.get('document_number', 'N/A')}
                </div>
                <div class="field">
                    <span class="label">생성일:</span> {data.get('generation_date', 'N/A')}
                </div>
            </div>
            <hr>
            <div class="document-content">
        """

        # 데이터 필드 동적 추가
        for key, value in data.items():
            if key not in ["document_number", "generation_date"]:
                # 키를 읽기 쉬운 레이블로 변환
                label = key.replace("_", " ").title()

                if isinstance(value, list):
                    content += f"""
                    <div class="field">
                        <span class="label">{label}:</span>
                        <ul>
                    """
                    for item in value:
                        content += f"<li>{item}</li>"
                    content += "</ul></div>"
                elif isinstance(value, dict):
                    content += f"""
                    <div class="field">
                        <span class="label">{label}:</span>
                        <pre>{json.dumps(value, ensure_ascii=False, indent=2)}</pre>
                    </div>
                    """
                else:
                    content += f"""
                    <div class="field">
                        <span class="label">{label}:</span> {value}
                    </div>
                    """

        content += """
            </div>
        </body>
        </html>
        """

        return content

    def _generate_document_number(self) -> str:
        """문서 번호 생성"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"DOC-{timestamp}"

    def _generate_document_id(self) -> str:
        """문서 ID 생성"""
        import uuid
        return str(uuid.uuid4())

    def _get_required_fields(self, template_id: str) -> List[str]:
        """템플릿의 필수 필드 반환"""
        template_info = self.template_registry.get(template_id, {})
        return template_info.get("required_fields", [])