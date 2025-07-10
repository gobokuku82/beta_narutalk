"""
업무문서 초안작성 에이전트

업무 문서의 초안을 자동 생성하는 전문 에이전트입니다.
다양한 문서 템플릿과 AI 기반 내용 생성으로 효율적인 문서 작성을 지원합니다.
"""

from typing import List, Dict, Any, Optional
import logging
from ..base_agent import BaseAgent, AgentContext, AgentResult, AgentAction
from .config import DocumentDraftConfig, default_config
from .templates import DocumentTemplateManager

logger = logging.getLogger(__name__)

class DocumentDraftAgent(BaseAgent):
    """업무문서 초안작성 전문 에이전트"""
    
    def __init__(self, config: DocumentDraftConfig = None):
        super().__init__("document_draft_agent")
        self.config = config or default_config
        self.template_manager = DocumentTemplateManager(self.config)
        
    @property
    def description(self) -> str:
        return "업무 문서의 초안을 자동 생성하는 전문 에이전트입니다. 보고서, 제안서, 계획서 등 다양한 문서 템플릿과 AI 기반 내용 생성을 제공합니다."
    
    @property
    def keywords(self) -> List[str]:
        return [
            # 한국어 키워드
            "작성", "초안", "문서", "보고서", "제안서", "계획서",
            "작성해", "만들어", "생성", "Draft", "만들기",
            "메모", "회의록", "절차서", "매뉴얼", "정책",
            "템플릿", "양식", "서식", "구조",
            "업무", "사업", "프로젝트", "계획", "제안",
            
            # 영어 키워드
            "draft", "create", "generate", "write", "compose",
            "document", "report", "proposal", "plan", "memo",
            "template", "format", "structure", "outline",
            "business", "project", "procedure", "manual"
        ]
    
    @property
    def priority(self) -> int:
        return 7  # 높은 우선순위 (문서 작성도 핵심 기능)
    
    @property
    def supported_tasks(self) -> List[str]:
        return [
            "document_draft",       # 문서 초안 작성
            "report_writing",       # 보고서 작성
            "proposal_writing",     # 제안서 작성
            "plan_writing",         # 계획서 작성
            "memo_writing",         # 메모 작성
            "meeting_minutes",      # 회의록 작성
            "procedure_writing",    # 절차서 작성
            "template_generation",  # 템플릿 생성
            "content_generation"    # 내용 생성
        ]
    
    async def can_handle(self, context: AgentContext) -> float:
        """메시지를 처리할 수 있는지 신뢰도 반환"""
        message = context.current_message.lower()
        confidence = 0.0
        
        # 작성 의도 확인
        write_indicators = ["작성", "만들어", "생성", "draft", "create", "write"]
        for indicator in write_indicators:
            if indicator in message:
                confidence += 0.4
                break
        
        # 문서 유형 키워드 확인
        doc_type_indicators = ["문서", "보고서", "제안서", "계획서", "메모", "회의록", 
                             "document", "report", "proposal", "plan", "memo"]
        for indicator in doc_type_indicators:
            if indicator in message:
                confidence += 0.3
                break
        
        # 키워드 매칭
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message)
        confidence += min(keyword_matches * 0.05, 0.3)
        
        # 템플릿 관련 키워드
        template_indicators = ["템플릿", "양식", "서식", "구조", "template", "format"]
        for indicator in template_indicators:
            if indicator in message:
                confidence += 0.1
                break
        
        return min(confidence, 1.0)
    
    async def process(self, context: AgentContext) -> AgentResult:
        """문서 초안 작성 처리 메인 로직"""
        try:
            # 다른 에이전트로 전환 확인
            next_agent = await self.should_switch_agent(context)
            if next_agent:
                return AgentResult(
                    response=f"{next_agent.replace('_', ' ').title()}로 전환합니다.",
                    action=AgentAction.SWITCH,
                    next_agent=next_agent,
                    confidence=0.9
                )
            
            # 문서 유형 분석
            document_type = await self.analyze_document_type(context)
            document_title = await self.extract_document_title(context)
            
            # 작업 유형 확인 (새 문서 작성 vs 템플릿 요청 vs 내용 생성)
            task_type = await self.analyze_task_type(context)
            
            if task_type == "template_request":
                # 템플릿 정보 제공
                response = await self.provide_template_info(document_type)
                
            elif task_type == "document_creation":
                # 새 문서 초안 생성
                document_draft = await self.create_document_draft(context, document_type, document_title)
                response = await self.format_document_response(document_draft, context)
                
            elif task_type == "content_generation":
                # 특정 섹션 내용 생성
                response = await self.generate_content_section(context, document_type)
                
            else:
                # 일반적인 문서 작성 도움
                response = await self.provide_writing_assistance(context)
            
            # 결과 반환
            result = AgentResult(
                response=response,
                action=AgentAction.COMPLETE,
                confidence=0.9,
                sources=[],
                metadata={
                    "agent_type": "document_draft",
                    "document_type": document_type,
                    "task_type": task_type,
                    "title": document_title,
                    "query": context.current_message
                }
            )
            
            await self.log_interaction(context, result)
            return result
            
        except Exception as e:
            logger.error(f"문서 초안 작성 처리 실패: {str(e)}")
            return AgentResult(
                response="죄송합니다. 문서 작성 중 오류가 발생했습니다. 다시 시도해 주세요.",
                action=AgentAction.ERROR,
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def analyze_document_type(self, context: AgentContext) -> str:
        """문서 유형 분석"""
        message = context.current_message.lower()
        
        # 문서 유형별 키워드 매핑
        type_keywords = {
            "report": ["보고서", "리포트", "report"],
            "proposal": ["제안서", "proposal"],
            "plan": ["계획서", "계획", "plan"],
            "memo": ["메모", "memo"],
            "meeting_minutes": ["회의록", "minutes"],
            "procedure": ["절차서", "프로세스", "procedure"],
            "manual": ["매뉴얼", "가이드", "manual", "guide"],
            "policy": ["정책", "policy"],
            "presentation": ["발표", "프레젠테이션", "presentation"]
        }
        
        for doc_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return doc_type
        
        return "report"  # 기본값
    
    async def extract_document_title(self, context: AgentContext) -> str:
        """문서 제목 추출"""
        message = context.current_message
        
        # 제목을 나타내는 패턴 찾기
        title_patterns = [
            "제목:", "title:", "주제:", "topic:",
            "\"", "'", "「", "」", "『", "』"
        ]
        
        for pattern in title_patterns:
            if pattern in message:
                # 패턴 이후의 텍스트를 제목으로 간주
                parts = message.split(pattern)
                if len(parts) > 1:
                    potential_title = parts[1].strip()
                    if len(potential_title) > 3 and len(potential_title) < 100:
                        return potential_title
        
        # 패턴이 없다면 메시지에서 제목 추정
        words = message.split()
        if len(words) >= 3:
            return " ".join(words[:5])  # 첫 5단어를 제목으로
        
        return ""
    
    async def analyze_task_type(self, context: AgentContext) -> str:
        """작업 유형 분석"""
        message = context.current_message.lower()
        
        if any(word in message for word in ["템플릿", "양식", "서식", "구조", "template"]):
            return "template_request"
        elif any(word in message for word in ["작성해", "만들어", "생성해", "create", "write"]):
            return "document_creation"
        elif any(word in message for word in ["내용", "섹션", "부분", "content", "section"]):
            return "content_generation"
        else:
            return "general_assistance"
    
    async def provide_template_info(self, document_type: str) -> str:
        """템플릿 정보 제공"""
        template = self.template_manager.get_template(document_type)
        if not template:
            available_templates = self.template_manager.get_available_templates()
            template_list = "\n".join([f"- {t['name']} ({t['type']})" for t in available_templates])
            return f"요청하신 문서 유형의 템플릿을 찾을 수 없습니다.\n\n사용 가능한 템플릿:\n{template_list}"
        
        structure_info = "\n".join([f"{i+1}. {section}" for i, section in enumerate(template["structure"])])
        
        return f"""
📋 **{template['name']} 템플릿**

**문서 구조:**
{structure_info}

**작성 가이드:**
{chr(10).join([f"• {section}: {guidance}" for section, guidance in template["sections"].items()])}

이 템플릿으로 문서를 작성하시겠습니까? "작성해줘" 또는 "만들어줘"라고 말씀해주시면 초안을 생성해드리겠습니다.
"""
    
    async def create_document_draft(self, context: AgentContext, document_type: str, title: str) -> Dict[str, Any]:
        """문서 초안 생성"""
        try:
            # 문서 구조 생성
            document_structure = self.template_manager.generate_document_structure(document_type, title)
            
            if not document_structure:
                return {"error": "템플릿을 찾을 수 없습니다."}
            
            # 각 섹션별 내용 생성
            for section in document_structure["sections"]:
                if section["name"] in ["제목", "목차", "날짜"]:
                    # 자동 생성 가능한 섹션
                    section["content"] = await self.generate_auto_section(section["name"], document_structure)
                    section["completed"] = True
                else:
                    # AI로 내용 생성
                    section["content"] = await self.generate_section_content(
                        document_type, section["name"], context, document_structure
                    )
                    section["completed"] = True
            
            # 회사 스타일 적용
            styled_document = self.template_manager.apply_company_style(document_structure)
            
            return styled_document
            
        except Exception as e:
            logger.error(f"문서 초안 생성 실패: {str(e)}")
            return {"error": str(e)}
    
    async def generate_auto_section(self, section_name: str, document_structure: Dict[str, Any]) -> str:
        """자동 생성 가능한 섹션 생성"""
        if section_name == "제목":
            return document_structure.get("title", "새로운 문서")
        elif section_name == "목차":
            toc_items = []
            for i, section in enumerate(document_structure["sections"], 1):
                if section["name"] != "목차":
                    toc_items.append(f"{i}. {section['name']}")
            return "\n".join(toc_items)
        elif section_name == "날짜":
            from datetime import datetime
            return datetime.now().strftime("%Y년 %m월 %d일")
        return ""
    
    async def generate_section_content(self, document_type: str, section_name: str, 
                                     context: AgentContext, document_structure: Dict[str, Any]) -> str:
        """섹션별 내용 생성"""
        try:
            if not self.openai_client:
                return f"[{section_name} 내용을 여기에 작성하세요]"
            
            # 컨텍스트 정보 구성
            context_info = {
                "사용자 요청": context.current_message,
                "문서 제목": document_structure.get("title", ""),
                "문서 유형": document_structure.get("template_name", ""),
                "회사명": "좋은제약"
            }
            
            # 섹션별 프롬프트 생성
            prompt = self.template_manager.generate_section_prompt(
                document_type, section_name, context_info
            )
            
            # OpenAI로 내용 생성
            content = await self.generate_openai_response(prompt, context)
            
            return content
            
        except Exception as e:
            logger.error(f"섹션 내용 생성 실패 ({section_name}): {str(e)}")
            return f"[{section_name} 내용 생성 중 오류 발생: {str(e)}]"
    
    async def format_document_response(self, document_draft: Dict[str, Any], context: AgentContext) -> str:
        """문서 초안 응답 포맷팅"""
        if "error" in document_draft:
            return f"문서 생성 중 오류가 발생했습니다: {document_draft['error']}"
        
        response = f"📄 **{document_draft.get('title', '새로운 문서')}** 초안이 생성되었습니다.\n\n"
        response += f"📋 문서 유형: {document_draft.get('template_name', '알 수 없음')}\n\n"
        
        # 각 섹션별 내용 표시
        for i, section in enumerate(document_draft.get("sections", []), 1):
            if section.get("content"):
                response += f"## {i}. {section['name']}\n"
                content = section["content"]
                if len(content) > 200:
                    content = content[:200] + "..."
                response += f"{content}\n\n"
        
        # 문서 완성도 정보
        validation = self.template_manager.validate_document_structure(document_draft)
        completeness = validation.get("completeness", 0.0) * 100
        
        response += f"📊 문서 완성도: {completeness:.1f}%\n"
        
        if validation.get("warnings"):
            response += f"⚠️ 주의사항: {', '.join(validation['warnings'])}\n"
        
        response += "\n추가로 수정이나 보완이 필요한 부분이 있으시면 말씀해주세요."
        
        return response
    
    async def generate_content_section(self, context: AgentContext, document_type: str) -> str:
        """특정 섹션 내용 생성"""
        if not self.openai_client:
            return "OpenAI 서비스가 설정되지 않아 내용을 생성할 수 없습니다."
        
        prompt = f"""
사용자가 다음과 같은 내용 생성을 요청했습니다:

요청 내용: {context.current_message}
문서 유형: {document_type}

좋은제약 회사의 업무 문서 스타일에 맞는 전문적인 내용을 생성해주세요.
구체적이고 실용적인 내용으로 작성해주세요.
"""
        
        return await self.generate_openai_response(prompt, context)
    
    async def provide_writing_assistance(self, context: AgentContext) -> str:
        """일반적인 문서 작성 도움 제공"""
        available_templates = self.template_manager.get_available_templates()
        template_list = "\n".join([f"• {t['name']} - \"{t['type']} 작성해줘\"" for t in available_templates])
        
        suggestions = self.template_manager.get_template_suggestions(context.current_message)
        suggestion_text = ""
        if suggestions:
            suggestion_text = f"\n\n💡 **추천 템플릿:**\n" + "\n".join([f"• {s}" for s in suggestions])
        
        return f"""
📝 **문서 작성 도우미**

다음과 같은 문서 작성을 도와드릴 수 있습니다:

{template_list}

**사용 방법:**
1. "보고서 작성해줘" - 새 문서 초안 생성
2. "회의록 템플릿 보여줘" - 템플릿 구조 확인  
3. "제목: 월간 실적 보고서" - 제목 지정하여 작성

{suggestion_text}

어떤 문서를 작성하시겠습니까?
"""
    
    def get_agent_status(self) -> Dict[str, Any]:
        """에이전트 상태 정보"""
        available_templates = self.template_manager.get_available_templates()
        
        return {
            **self.get_agent_info(),
            "config": {
                "max_length": self.config.max_document_length,
                "ai_model": self.config.ai_model,
                "ai_temperature": self.config.ai_temperature
            },
            "available_templates": available_templates,
            "supported_document_types": self.config.supported_document_types,
            "company_style": self.config.company_style
        } 