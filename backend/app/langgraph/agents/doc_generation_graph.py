"""
Document Generation Agent - Subgraph Implementation
LangGraph 0.6.6 기반 문서생성 에이전트 (Subgraph 구조)
"""

from typing import Dict, Any, List, TypedDict, Annotated, Sequence, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from loguru import logger
import operator
from datetime import datetime
from pathlib import Path
import json

from app.core.config import settings


class DocGenerationState(TypedDict):
    """문서생성 에이전트 전용 State"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    request: str
    document_type: str  # proposal, report, email, presentation, unknown
    template: str
    generated_content: Dict[str, str]
    metadata: Dict[str, Any]
    file_path: Optional[str]
    status: str  # analyzing, generating, formatting, saving, completed, error
    error_message: Optional[str]


class DocGenerationSubgraph:
    """문서생성 Subgraph - 단계별 문서 생성 워크플로우"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # 문서 디렉토리 설정
        self.templates_dir = settings.DOCUMENTS_DIR / "templates"
        self.generated_dir = settings.DOCUMENTS_DIR / "generated"
        
        # 디렉토리 생성
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        
        # 템플릿 초기화
        self._initialize_templates()
        
        # Subgraph 생성
        self.graph = self._build_graph()
    
    def _initialize_templates(self):
        """기본 템플릿 생성"""
        templates = {
            "proposal_template.md": """# 제약 제품 제안서

## 1. 제품 개요
- **제품명**: {product_name}
- **성분명**: {generic_name}
- **적응증**: {indication}

## 2. 제품 특징
{product_features}

## 3. 임상 데이터
{clinical_data}

## 4. 경쟁 우위
{competitive_advantages}

## 5. 가격 정책
{pricing}

## 6. 공급 조건
{supply_terms}

---
작성일: {date}
담당자: {author}
""",
            "report_template.md": """# 영업 활동 보고서

## 기간: {period}

### 1. 방문 현황
- 총 방문 건수: {total_visits}
- 신규 거래처: {new_customers}
- 기존 거래처: {existing_customers}

### 2. 실적 요약
{performance_summary}

### 3. 주요 성과
{key_achievements}

### 4. 이슈 사항
{issues}

### 5. 다음 계획
{next_plans}

---
작성자: {author}
작성일: {date}
""",
            "email_template.txt": """제목: {subject}

안녕하세요, {recipient_name}님

{greeting}

{main_content}

{closing}

감사합니다.

{sender_name}
{sender_title}
{company_name}
{contact_info}
""",
            "presentation_template.md": """# {title}

## 슬라이드 1: 제목
- {main_title}
- {subtitle}
- 발표자: {presenter}
- 날짜: {date}

## 슬라이드 2: 목차
{table_of_contents}

## 슬라이드 3: 배경 및 목적
{background}

## 슬라이드 4-8: 주요 내용
{main_content}

## 슬라이드 9: 결론
{conclusion}

## 슬라이드 10: Q&A
감사합니다.
질문 있으신가요?

---
준비일: {prepared_date}
"""
        }
        
        # 템플릿 파일 생성
        for filename, content in templates.items():
            template_path = self.templates_dir / filename
            if not template_path.exists():
                template_path.write_text(content, encoding="utf-8")
                logger.info(f"템플릿 생성: {filename}")
    
    async def analyze_request_node(self, state: DocGenerationState) -> Dict:
        """요청 분석 노드 - 문서 유형 결정"""
        logger.info("문서 생성 요청 분석")
        
        request = state.get("request", "")
        if not request and state.get("messages"):
            last_message = state["messages"][-1]
            request = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else str(last_message)
        
        # LLM으로 문서 유형 분석
        prompt = f"""
        사용자 요청: {request}
        
        이 요청이 어떤 유형의 문서 생성인지 분류하세요:
        - proposal: 제품 제안서, 영업 제안서
        - report: 보고서, 리포트, 실적 보고
        - email: 이메일, 메일
        - presentation: 프레젠테이션, 발표자료, PPT
        - unknown: 분류할 수 없음
        
        한 단어로만 답하세요:
        """
        
        response = await self.llm.ainvoke(prompt)
        doc_type = response.content.strip().lower()
        
        # 유효성 검증
        valid_types = ["proposal", "report", "email", "presentation", "unknown"]
        if doc_type not in valid_types:
            # 키워드 기반 fallback
            request_lower = request.lower()
            if any(word in request_lower for word in ["제안서", "proposal", "제안"]):
                doc_type = "proposal"
            elif any(word in request_lower for word in ["보고서", "report", "리포트"]):
                doc_type = "report"
            elif any(word in request_lower for word in ["이메일", "email", "메일"]):
                doc_type = "email"
            elif any(word in request_lower for word in ["프레젠테이션", "presentation", "ppt", "발표"]):
                doc_type = "presentation"
            else:
                doc_type = "unknown"
        
        return {
            "request": request,
            "document_type": doc_type,
            "status": "analyzing"
        }
    
    async def load_template_node(self, state: DocGenerationState) -> Dict:
        """템플릿 로드 노드"""
        logger.info(f"템플릿 로드: {state.get('document_type')}")
        
        doc_type = state.get("document_type", "unknown")
        
        template_map = {
            "proposal": "proposal_template.md",
            "report": "report_template.md",
            "email": "email_template.txt",
            "presentation": "presentation_template.md"
        }
        
        template_file = template_map.get(doc_type)
        
        if template_file:
            template_path = self.templates_dir / template_file
            if template_path.exists():
                template = template_path.read_text(encoding="utf-8")
                return {"template": template}
            else:
                logger.warning(f"템플릿 파일 없음: {template_file}")
                return {"template": "", "error_message": f"템플릿을 찾을 수 없습니다: {doc_type}"}
        
        return {"template": "", "error_message": f"알 수 없는 문서 유형: {doc_type}"}
    
    async def generate_content_node(self, state: DocGenerationState) -> Dict:
        """내용 생성 노드 - LLM으로 각 섹션 생성"""
        logger.info("문서 내용 생성")
        
        doc_type = state.get("document_type")
        request = state.get("request", "")
        template = state.get("template", "")
        
        generated_content = {}
        
        if doc_type == "proposal":
            # 제안서 내용 생성
            prompts = {
                "product_features": f"다음 요청에 대한 제품 특징을 3-5개 항목으로 작성하세요:\n{request}",
                "clinical_data": f"관련 임상 데이터나 연구 결과를 간단히 요약하세요:\n{request}",
                "competitive_advantages": f"경쟁 제품 대비 장점을 3개 작성하세요:\n{request}",
                "pricing": "표준 가격 정책을 간단히 설명하세요.",
                "supply_terms": "표준 공급 조건을 작성하세요."
            }
            
            for key, prompt in prompts.items():
                response = await self.llm.ainvoke(prompt)
                generated_content[key] = response.content
            
            # 기본 정보 추가
            generated_content.update({
                "product_name": "신약 제품명",
                "generic_name": "Generic Name",
                "indication": "주요 적응증",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "author": "영업팀"
            })
            
        elif doc_type == "report":
            # 보고서 내용 생성
            prompt = f"""
            다음 요청에 대한 영업 활동 보고서 내용을 생성하세요:
            {request}
            
            다음 항목들을 포함하세요:
            1. 실적 요약 (3-4문장)
            2. 주요 성과 (3개 항목)
            3. 이슈 사항 (있다면)
            4. 다음 계획 (3개 항목)
            """
            
            response = await self.llm.ainvoke(prompt)
            content_parts = response.content.split("\n\n")
            
            generated_content = {
                "period": datetime.now().strftime("%Y년 %m월"),
                "total_visits": "25",
                "new_customers": "5",
                "existing_customers": "20",
                "performance_summary": content_parts[0] if len(content_parts) > 0 else "",
                "key_achievements": content_parts[1] if len(content_parts) > 1 else "",
                "issues": content_parts[2] if len(content_parts) > 2 else "특이사항 없음",
                "next_plans": content_parts[3] if len(content_parts) > 3 else "",
                "author": "영업팀",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
        elif doc_type == "email":
            # 이메일 내용 생성
            prompt = f"""
            다음 요청에 대한 전문적인 비즈니스 이메일을 작성하세요:
            {request}
            
            포함할 내용:
            1. 인사말
            2. 본문 (핵심 메시지)
            3. 마무리 인사
            """
            
            response = await self.llm.ainvoke(prompt)
            
            generated_content = {
                "subject": "의약품 정보 안내",
                "recipient_name": "선생님",
                "greeting": "평소 저희 제품에 관심을 가져주셔서 감사합니다.",
                "main_content": response.content,
                "closing": "추가 문의사항이 있으시면 언제든 연락 주시기 바랍니다.",
                "sender_name": "홍길동",
                "sender_title": "영업 담당자",
                "company_name": "제약회사",
                "contact_info": "Tel: 02-1234-5678 | Email: info@pharma.com"
            }
            
        elif doc_type == "presentation":
            # 프레젠테이션 내용 생성
            prompt = f"""
            다음 요청에 대한 프레젠테이션 개요를 작성하세요:
            {request}
            
            10장 슬라이드 구성으로 작성하세요.
            """
            
            response = await self.llm.ainvoke(prompt)
            
            generated_content = {
                "title": "제품 소개 프레젠테이션",
                "main_title": "혁신적인 신약 소개",
                "subtitle": "더 나은 치료를 위한 선택",
                "presenter": "영업팀",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "table_of_contents": "1. 제품 개요\n2. 임상 데이터\n3. 경쟁 우위\n4. 가격 정책",
                "background": "치료 옵션의 필요성",
                "main_content": response.content,
                "conclusion": "최적의 치료 솔루션",
                "prepared_date": datetime.now().strftime("%Y-%m-%d")
            }
        
        return {
            "generated_content": generated_content,
            "status": "generating"
        }
    
    async def format_document_node(self, state: DocGenerationState) -> Dict:
        """문서 포맷팅 노드"""
        logger.info("문서 포맷팅")
        
        template = state.get("template", "")
        generated_content = state.get("generated_content", {})
        
        if not template:
            return {
                "status": "error",
                "error_message": "템플릿이 없습니다."
            }
        
        try:
            # 템플릿에 내용 채우기
            formatted_document = template.format(**generated_content)
            
            # 메타데이터 생성
            metadata = {
                "document_type": state.get("document_type"),
                "created_at": datetime.now().isoformat(),
                "request": state.get("request"),
                "word_count": len(formatted_document.split())
            }
            
            return {
                "generated_content": {**generated_content, "formatted": formatted_document},
                "metadata": metadata,
                "status": "formatting"
            }
        except Exception as e:
            logger.error(f"포맷팅 오류: {e}")
            return {
                "status": "error",
                "error_message": f"문서 포맷팅 실패: {str(e)}"
            }
    
    async def save_document_node(self, state: DocGenerationState) -> Dict:
        """문서 저장 노드"""
        logger.info("문서 저장")
        
        doc_type = state.get("document_type")
        formatted_content = state.get("generated_content", {}).get("formatted", "")
        
        if not formatted_content:
            return {
                "status": "error",
                "error_message": "저장할 내용이 없습니다."
            }
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = ".md" if doc_type != "email" else ".txt"
        filename = f"{doc_type}_{timestamp}{extension}"
        filepath = self.generated_dir / filename
        
        try:
            # 파일 저장
            filepath.write_text(formatted_content, encoding="utf-8")
            logger.info(f"문서 저장 완료: {filepath}")
            
            # 메타데이터 저장
            metadata_file = self.generated_dir / f"{doc_type}_{timestamp}_metadata.json"
            metadata = state.get("metadata", {})
            metadata["file_path"] = str(filepath)
            metadata_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            
            return {
                "file_path": str(filepath),
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"파일 저장 오류: {e}")
            return {
                "status": "error",
                "error_message": f"파일 저장 실패: {str(e)}"
            }
    
    async def error_handler_node(self, state: DocGenerationState) -> Dict:
        """오류 처리 노드"""
        logger.error(f"문서 생성 오류: {state.get('error_message')}")
        
        error_msg = state.get("error_message", "알 수 없는 오류가 발생했습니다.")
        
        return {
            "messages": [AIMessage(content=f"문서 생성에 실패했습니다: {error_msg}")],
            "status": "error"
        }
    
    def route_after_analysis(self, state: DocGenerationState) -> str:
        """분석 후 라우팅"""
        doc_type = state.get("document_type")
        if doc_type == "unknown":
            return "error_handler"
        return "load_template"
    
    def route_after_template(self, state: DocGenerationState) -> str:
        """템플릿 로드 후 라우팅"""
        if state.get("error_message"):
            return "error_handler"
        return "generate_content"
    
    def route_after_generation(self, state: DocGenerationState) -> str:
        """내용 생성 후 라우팅"""
        if state.get("error_message"):
            return "error_handler"
        return "format_document"
    
    def route_after_formatting(self, state: DocGenerationState) -> str:
        """포맷팅 후 라우팅"""
        if state.get("status") == "error":
            return "error_handler"
        return "save_document"
    
    def _build_graph(self) -> StateGraph:
        """Subgraph 구성"""
        workflow = StateGraph(DocGenerationState)
        
        # 노드 추가
        workflow.add_node("analyze_request", self.analyze_request_node)
        workflow.add_node("load_template", self.load_template_node)
        workflow.add_node("generate_content", self.generate_content_node)
        workflow.add_node("format_document", self.format_document_node)
        workflow.add_node("save_document", self.save_document_node)
        workflow.add_node("error_handler", self.error_handler_node)
        
        # 시작점
        workflow.add_edge(START, "analyze_request")
        
        # 조건부 라우팅
        workflow.add_conditional_edges(
            "analyze_request",
            self.route_after_analysis,
            {
                "load_template": "load_template",
                "error_handler": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "load_template",
            self.route_after_template,
            {
                "generate_content": "generate_content",
                "error_handler": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_content",
            self.route_after_generation,
            {
                "format_document": "format_document",
                "error_handler": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "format_document",
            self.route_after_formatting,
            {
                "save_document": "save_document",
                "error_handler": "error_handler"
            }
        )
        
        # 종료 엣지
        workflow.add_edge("save_document", END)
        workflow.add_edge("error_handler", END)
        
        # 그래프 컴파일
        return workflow.compile()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor에서 호출하는 메인 처리 함수"""
        logger.info("DocGeneration Subgraph 처리 시작")
        
        # 입력 state를 subgraph state로 변환
        subgraph_state = DocGenerationState(
            messages=state.get("messages", []),
            request="",
            document_type="",
            template="",
            generated_content={},
            metadata={},
            file_path=None,
            status="",
            error_message=None
        )
        
        # Subgraph 실행
        try:
            result = await self.graph.ainvoke(subgraph_state)
            
            # 응답 메시지 생성
            if result.get("status") == "completed":
                response = f"문서가 성공적으로 생성되었습니다.\n"
                response += f"문서 유형: {result.get('document_type')}\n"
                response += f"저장 위치: {result.get('file_path')}\n\n"
                
                # 미리보기 추가
                formatted = result.get("generated_content", {}).get("formatted", "")
                if formatted:
                    preview = formatted[:500] + "..." if len(formatted) > 500 else formatted
                    response += f"[미리보기]\n{preview}"
            else:
                response = result.get("error_message", "문서 생성에 실패했습니다.")
            
            # 결과 반환
            return {
                "messages": [AIMessage(content=response)],
                "agent_outputs": {
                    "doc_generation": {
                        "document_type": result.get("document_type"),
                        "file_path": result.get("file_path"),
                        "status": result.get("status"),
                        "metadata": result.get("metadata"),
                        "error": result.get("error_message")
                    }
                },
                "next_agent": None
            }
        except Exception as e:
            logger.error(f"DocGeneration Subgraph 실행 오류: {e}")
            return {
                "messages": [AIMessage(content=f"문서 생성 중 오류가 발생했습니다: {str(e)}")],
                "agent_outputs": {"doc_generation": {"error": str(e)}},
                "next_agent": None
            }


# Subgraph 인스턴스 생성 함수
def create_doc_generation_subgraph():
    """DocGeneration Subgraph 생성"""
    return DocGenerationSubgraph()