"""
Document Generation Agent
문서 생성 에이전트 - 다양한 Word 양식 처리
"""

from typing import Dict, Any, List, Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentInput(BaseModel):
    """문서 생성 입력 데이터"""
    
    document_type: Literal[
        "visit_report",           # 방문결과보고서
        "product_seminar_request", # 제품설명회 신청서
        "product_seminar_report",  # 제품설명회 결과보고서
        "sample_request",         # 샘플신청서
        "region_info"            # 지역정보
    ]
    raw_content: str  # 자연어 입력
    metadata: Dict[str, Any] = Field(default_factory=dict)
    user_info: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[str] = Field(default_factory=list)


class DocumentOutput(BaseModel):
    """문서 생성 결과"""
    
    document_id: str
    document_type: str
    file_path: Optional[str] = None
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    storage_type: Literal["structured", "unstructured", "hybrid"]
    created_at: str
    validation_status: str


class DocumentGenerationAgent:
    """
    문서 생성 에이전트
    - 자연어 입력을 정제하여 적절한 필드 매핑
    - 문서 종류별 다른 Tool 호출
    - Word 양식 활용 (추후 템플릿 추가 예정)
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Initialize Document Generation Agent
        
        Args:
            api_base_url: FastAPI 서버 URL
        """
        
        self.api_base_url = api_base_url
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # 문서별 도구 초기화
        self.tools = self._initialize_document_tools()
        
        # 템플릿 저장소 (추후 Word 템플릿 경로)
        self.template_registry = {}
        
        # 필드 매핑 규칙
        self.field_mapping_rules = self._load_field_mapping_rules()
    
    def _initialize_document_tools(self) -> Dict[str, Tool]:
        """문서 종류별 도구 초기화"""
        
        tools = {
            "visit_report": Tool(
                name="create_visit_report",
                description="방문결과보고서 작성",
                func=self._create_visit_report
            ),
            "product_seminar_request": Tool(
                name="create_seminar_request",
                description="제품설명회 신청서 작성",
                func=self._create_seminar_request
            ),
            "product_seminar_report": Tool(
                name="create_seminar_report",
                description="제품설명회 결과보고서 작성",
                func=self._create_seminar_report
            ),
            "sample_request": Tool(
                name="create_sample_request",
                description="샘플신청서 작성",
                func=self._create_sample_request
            ),
            "region_info": Tool(
                name="save_region_info",
                description="지역정보 저장",
                func=self._save_region_info
            )
        }
        
        return tools
    
    def _load_field_mapping_rules(self) -> Dict[str, Dict[str, Any]]:
        """필드 매핑 규칙 로드"""
        
        return {
            "visit_report": {
                "required_fields": ["hospital_name", "visit_date", "doctor_name", "discussion_content"],
                "optional_fields": ["next_action", "product_mentioned", "feedback"],
                "field_types": {
                    "hospital_name": "str",
                    "visit_date": "date",
                    "doctor_name": "str",
                    "discussion_content": "text",
                    "product_mentioned": "list",
                    "feedback": "text"
                }
            },
            "product_seminar_request": {
                "required_fields": ["hospital_name", "requested_date", "expected_attendees", "products"],
                "optional_fields": ["venue", "budget", "special_requirements"],
                "field_types": {
                    "hospital_name": "str",
                    "requested_date": "datetime",
                    "expected_attendees": "int",
                    "products": "list",
                    "venue": "str",
                    "budget": "float"
                }
            },
            "sample_request": {
                "required_fields": ["hospital_name", "doctor_name", "product_name", "quantity"],
                "optional_fields": ["purpose", "delivery_date", "special_notes"],
                "field_types": {
                    "hospital_name": "str",
                    "doctor_name": "str",
                    "product_name": "str",
                    "quantity": "int",
                    "purpose": "str",
                    "delivery_date": "date"
                }
            }
        }
    
    async def process_document_request(self, input_data: DocumentInput) -> DocumentOutput:
        """
        문서 생성 요청 처리 메인 메서드
        """
        
        logger.info(f"Processing document request: {input_data.document_type}")
        
        # 1. 자연어 입력 정제 및 필드 추출
        extracted_fields = await self._extract_fields_from_text(
            input_data.raw_content,
            input_data.document_type
        )
        
        # 2. 필드 검증 및 보완
        validated_fields = await self._validate_and_enrich_fields(
            extracted_fields,
            input_data.document_type,
            input_data.metadata
        )
        
        # 3. 적절한 도구 선택 및 실행
        tool = self.tools.get(input_data.document_type)
        if not tool:
            raise ValueError(f"Unsupported document type: {input_data.document_type}")
        
        # 4. 문서 생성
        result = await tool.afunc(validated_fields)
        
        # 5. 저장 타입 결정
        storage_type = self._determine_storage_type(
            input_data.document_type,
            validated_fields
        )
        
        # 6. 결과 구성
        output = DocumentOutput(
            document_id=self._generate_document_id(),
            document_type=input_data.document_type,
            file_path=result.get("file_path"),
            content=validated_fields,
            metadata={
                **input_data.metadata,
                "user_info": input_data.user_info,
                "processing_time": datetime.now().isoformat()
            },
            storage_type=storage_type,
            created_at=datetime.now().isoformat(),
            validation_status="pending_compliance_check"
        )
        
        logger.info(f"Document created: {output.document_id}")
        return output
    
    async def _extract_fields_from_text(
        self,
        raw_text: str,
        document_type: str
    ) -> Dict[str, Any]:
        """자연어에서 필드 추출"""
        
        field_rules = self.field_mapping_rules.get(document_type, {})
        
        system_prompt = f"""당신은 의료/제약 문서 작성 전문가입니다.
        
        문서 타입: {document_type}
        필수 필드: {field_rules.get('required_fields', [])}
        선택 필드: {field_rules.get('optional_fields', [])}
        
        사용자의 자연어 입력에서 위 필드들을 추출하세요.
        추출된 내용을 JSON 형식으로 반환하세요.
        
        예시:
        - 날짜는 YYYY-MM-DD 형식으로
        - 시간은 HH:MM 형식으로
        - 리스트는 배열로
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"입력 텍스트: {raw_text}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            # JSON 파싱
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            extracted = json.loads(content)
            return extracted
        except:
            # 파싱 실패시 기본 구조
            return {"raw_text": raw_text}
    
    async def _validate_and_enrich_fields(
        self,
        fields: Dict[str, Any],
        document_type: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """필드 검증 및 보완"""
        
        field_rules = self.field_mapping_rules.get(document_type, {})
        required_fields = field_rules.get("required_fields", [])
        
        # 필수 필드 확인
        missing_fields = [f for f in required_fields if f not in fields or not fields[f]]
        
        if missing_fields:
            # LLM을 활용하여 누락된 필드 추론
            enriched = await self._infer_missing_fields(
                fields,
                missing_fields,
                metadata
            )
            fields.update(enriched)
        
        # 타입 변환
        field_types = field_rules.get("field_types", {})
        for field_name, field_type in field_types.items():
            if field_name in fields:
                fields[field_name] = self._convert_field_type(
                    fields[field_name],
                    field_type
                )
        
        return fields
    
    async def _infer_missing_fields(
        self,
        existing_fields: Dict[str, Any],
        missing_fields: List[str],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """누락된 필드 추론"""
        
        system_prompt = f"""기존 정보와 메타데이터를 바탕으로 누락된 필드를 추론하세요.
        
        기존 필드: {json.dumps(existing_fields, ensure_ascii=False)}
        메타데이터: {json.dumps(metadata, ensure_ascii=False)}
        누락된 필드: {missing_fields}
        
        합리적인 추론이 불가능한 경우 기본값을 사용하세요:
        - 날짜: 오늘 날짜
        - 텍스트: "추후 보완 필요"
        - 숫자: 0
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="누락된 필드를 JSON으로 반환하세요.")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            return json.loads(content)
        except:
            # 기본값 반환
            return {field: "추후 보완 필요" for field in missing_fields}
    
    def _convert_field_type(self, value: Any, field_type: str) -> Any:
        """필드 타입 변환"""
        
        if field_type == "date":
            # 날짜 변환 로직
            if isinstance(value, str):
                # 간단한 날짜 파싱 (실제로는 더 정교한 파싱 필요)
                return value
            return str(value)
        
        elif field_type == "int":
            try:
                return int(value)
            except:
                return 0
        
        elif field_type == "float":
            try:
                return float(value)
            except:
                return 0.0
        
        elif field_type == "list":
            if isinstance(value, list):
                return value
            elif isinstance(value, str):
                return [item.strip() for item in value.split(",")]
            return [value]
        
        else:
            return str(value)
    
    def _determine_storage_type(
        self,
        document_type: str,
        fields: Dict[str, Any]
    ) -> str:
        """저장 타입 결정 (정형/비정형/하이브리드)"""
        
        # 규칙 기반 결정
        structured_types = ["sample_request", "product_seminar_request"]
        unstructured_types = ["region_info"]
        
        if document_type in structured_types:
            return "structured"
        elif document_type in unstructured_types:
            return "unstructured"
        else:
            # 필드 복잡도에 따라 결정
            has_long_text = any(
                isinstance(v, str) and len(v) > 500
                for v in fields.values()
            )
            
            if has_long_text:
                return "hybrid"
            else:
                return "structured"
    
    def _generate_document_id(self) -> str:
        """문서 ID 생성"""
        
        from uuid import uuid4
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"DOC_{timestamp}_{str(uuid4())[:8]}"
    
    # === 문서별 생성 도구 구현 ===
    
    async def _create_visit_report(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """방문결과보고서 생성"""
        
        # TODO: Word 템플릿 활용
        # 현재는 JSON 형태로 반환
        
        report = {
            "title": f"방문결과보고서 - {fields.get('hospital_name', '')}",
            "sections": {
                "basic_info": {
                    "hospital": fields.get("hospital_name"),
                    "date": fields.get("visit_date"),
                    "doctor": fields.get("doctor_name")
                },
                "content": {
                    "discussion": fields.get("discussion_content"),
                    "products": fields.get("product_mentioned", []),
                    "feedback": fields.get("feedback")
                },
                "follow_up": {
                    "next_action": fields.get("next_action")
                }
            }
        }
        
        # FastAPI로 저장 요청
        # await self._save_to_database(report, "visit_report")
        
        return {
            "status": "success",
            "content": report,
            "file_path": None  # Word 파일 생성 후 경로 반환
        }
    
    async def _create_seminar_request(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """제품설명회 신청서 생성"""
        
        request = {
            "title": "제품설명회 신청서",
            "request_info": {
                "hospital": fields.get("hospital_name"),
                "date": fields.get("requested_date"),
                "attendees": fields.get("expected_attendees"),
                "products": fields.get("products", [])
            },
            "logistics": {
                "venue": fields.get("venue", "미정"),
                "budget": fields.get("budget", 0),
                "requirements": fields.get("special_requirements", "")
            }
        }
        
        return {
            "status": "success",
            "content": request,
            "file_path": None
        }
    
    async def _create_seminar_report(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """제품설명회 결과보고서 생성"""
        
        report = {
            "title": "제품설명회 결과보고서",
            "event_summary": {
                "date": fields.get("event_date"),
                "venue": fields.get("venue"),
                "actual_attendees": fields.get("actual_attendees"),
                "products_presented": fields.get("products", [])
            },
            "results": {
                "feedback": fields.get("feedback"),
                "follow_up_required": fields.get("follow_up"),
                "sales_opportunity": fields.get("opportunity")
            }
        }
        
        return {
            "status": "success",
            "content": report,
            "file_path": None
        }
    
    async def _create_sample_request(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """샘플신청서 생성"""
        
        request = {
            "title": "샘플신청서",
            "request_details": {
                "hospital": fields.get("hospital_name"),
                "doctor": fields.get("doctor_name"),
                "product": fields.get("product_name"),
                "quantity": fields.get("quantity", 1)
            },
            "purpose": fields.get("purpose", "제품 평가"),
            "delivery": {
                "date": fields.get("delivery_date", "조속한 시일 내"),
                "special_notes": fields.get("special_notes", "")
            }
        }
        
        return {
            "status": "success",
            "content": request,
            "file_path": None
        }
    
    async def _save_region_info(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """지역정보 저장"""
        
        # AI가 정형/비정형 저장 결정
        storage_decision = await self._decide_storage_strategy(fields)
        
        region_data = {
            "region": fields.get("region"),
            "hospitals": fields.get("hospitals", []),
            "key_doctors": fields.get("key_doctors", []),
            "market_info": fields.get("market_info"),
            "competitor_status": fields.get("competitors"),
            "storage_type": storage_decision
        }
        
        return {
            "status": "success",
            "content": region_data,
            "storage_type": storage_decision,
            "file_path": None
        }
    
    async def _decide_storage_strategy(self, data: Dict[str, Any]) -> str:
        """AI가 저장 전략 결정"""
        
        system_prompt = """데이터를 분석하여 최적의 저장 방식을 결정하세요.
        
        - structured: 정형화된 데이터, SQL 쿼리 필요
        - unstructured: 자유 형식 텍스트, 문서
        - hybrid: 정형+비정형 혼합
        
        데이터의 특성, 검색 필요성, 분석 용도를 고려하세요.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"데이터: {json.dumps(data, ensure_ascii=False)}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # 응답 파싱
        if "structured" in response.content.lower():
            return "structured"
        elif "unstructured" in response.content.lower():
            return "unstructured"
        else:
            return "hybrid"
    
    def register_template(self, document_type: str, template_path: str):
        """Word 템플릿 등록"""
        
        if not Path(template_path).exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        self.template_registry[document_type] = template_path
        logger.info(f"Template registered for {document_type}: {template_path}")
    
    async def apply_word_template(
        self,
        document_type: str,
        fields: Dict[str, Any]
    ) -> str:
        """Word 템플릿 적용 (추후 구현)"""
        
        template_path = self.template_registry.get(document_type)
        if not template_path:
            logger.warning(f"No template registered for {document_type}")
            return None
        
        # TODO: python-docx 또는 python-docx-template 사용
        # from docx import Document
        # from docxtpl import DocxTemplate
        
        # template = DocxTemplate(template_path)
        # template.render(fields)
        # output_path = f"outputs/{document_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
        # template.save(output_path)
        
        return None  # output_path


# === Graph Node Function ===

async def document_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Graph node for document generation
    """
    
    agent = DocumentGenerationAgent()
    
    # 입력 데이터 구성
    input_data = DocumentInput(
        document_type=state.get("document_type", "visit_report"),
        raw_content=state.get("query", ""),
        metadata=state.get("metadata", {}),
        user_info=state.get("user_info", {})
    )
    
    # 문서 생성
    result = await agent.process_document_request(input_data)
    
    # 상태 업데이트
    return {
        "generated_documents": [result.dict()],
        "document_status": "generated",
        "next_step": "compliance_check"  # 규정 검토로 이동
    }
