"""
Document Generation Agent
문서 생성 및 보고서 작성 에이전트
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

logger = logging.getLogger(__name__)


class DocumentGenerationAgent:
    """문서 생성 및 보고서 작성을 담당하는 에이전트"""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize document generation agent"""
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.name = "DocumentGenerationAgent"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """메인 실행 메서드"""
        start_time = datetime.now()

        try:
            # Extract task parameters
            document_type = task.get("document_type", "report")
            content_data = task.get("content_data", {})
            template = task.get("template", None)
            format_type = task.get("format", "markdown")
            language = task.get("language", "ko")
            style = task.get("style", "professional")

            # Generate document based on type
            if document_type == "report":
                result = await self._generate_report(content_data, template, format_type, style)
            elif document_type == "summary":
                result = await self._generate_summary(content_data, format_type)
            elif document_type == "email":
                result = await self._generate_email(content_data, style)
            elif document_type == "memo":
                result = await self._generate_memo(content_data, style)
            else:  # presentation
                result = await self._generate_presentation(content_data, format_type)

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "confidence_score": result.get("confidence", 0.9),
                "execution_time": execution_time,
                "document_content": result.get("content", ""),
                "document_format": format_type,
                "word_count": result.get("word_count", 0),
                "sections": result.get("sections", []),
                "metadata": result.get("metadata", {})
            }

        except Exception as e:
            logger.error(f"Document generation failed: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "confidence_score": 0.0,
                "execution_time": execution_time,
                "error": str(e)
            }

    async def _generate_report(self, content_data: Dict, template: Optional[str], 
                              format_type: str, style: str) -> Dict[str, Any]:
        """보고서 생성"""
        
        system_prompt = f"""당신은 전문적인 보고서 작성자입니다.
        스타일: {style}
        형식: {format_type}
        한국어로 작성하되 전문적이고 명확하게 작성하세요."""

        user_prompt = f"""다음 데이터를 바탕으로 보고서를 작성해주세요:
        {json.dumps(content_data, ensure_ascii=False, indent=2)}
        
        보고서 구조:
        1. 요약
        2. 주요 발견사항
        3. 상세 분석
        4. 결론 및 제언"""

        if template:
            user_prompt += f"\n\n템플릿: {template}"

        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        content = response.content.strip()
        
        # Extract sections
        sections = self._extract_sections(content)
        
        return {
            "content": content,
            "word_count": len(content.split()),
            "sections": sections,
            "metadata": {
                "type": "report",
                "generated_at": datetime.now().isoformat(),
                "style": style
            },
            "confidence": 0.92
        }

    async def _generate_summary(self, content_data: Dict, format_type: str) -> Dict[str, Any]:
        """요약문 생성"""
        
        prompt = f"""다음 데이터를 간결하게 요약해주세요:
        {json.dumps(content_data, ensure_ascii=False, indent=2)}
        
        요약 규칙:
        - 핵심 정보만 포함
        - 3-5개의 주요 포인트
        - 각 포인트는 1-2문장
        - {format_type} 형식으로 작성"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        return {
            "content": content,
            "word_count": len(content.split()),
            "sections": ["summary"],
            "metadata": {
                "type": "summary",
                "generated_at": datetime.now().isoformat()
            },
            "confidence": 0.88
        }

    async def _generate_email(self, content_data: Dict, style: str) -> Dict[str, Any]:
        """이메일 생성"""
        
        recipient = content_data.get("recipient", "수신자")
        subject = content_data.get("subject", "제목")
        main_content = content_data.get("content", {})
        
        prompt = f"""다음 내용으로 비즈니스 이메일을 작성해주세요:
        수신자: {recipient}
        제목: {subject}
        내용: {json.dumps(main_content, ensure_ascii=False)}
        스타일: {style}
        
        이메일 구조:
        - 인사말
        - 본문 (핵심 내용)
        - 마무리 인사
        - 서명"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        return {
            "content": content,
            "word_count": len(content.split()),
            "sections": ["greeting", "body", "closing", "signature"],
            "metadata": {
                "type": "email",
                "recipient": recipient,
                "subject": subject,
                "generated_at": datetime.now().isoformat()
            },
            "confidence": 0.91
        }

    async def _generate_memo(self, content_data: Dict, style: str) -> Dict[str, Any]:
        """메모/공지 생성"""
        
        title = content_data.get("title", "메모")
        points = content_data.get("points", [])
        
        prompt = f"""다음 내용으로 업무 메모를 작성해주세요:
        제목: {title}
        주요 내용: {json.dumps(points, ensure_ascii=False)}
        스타일: {style}
        
        메모 형식:
        - 제목
        - 일시
        - 대상
        - 내용 (간결하고 명확하게)
        - 조치사항"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        return {
            "content": content,
            "word_count": len(content.split()),
            "sections": ["header", "content", "action_items"],
            "metadata": {
                "type": "memo",
                "title": title,
                "generated_at": datetime.now().isoformat()
            },
            "confidence": 0.89
        }

    async def _generate_presentation(self, content_data: Dict, format_type: str) -> Dict[str, Any]:
        """프레젠테이션 자료 생성"""
        
        title = content_data.get("title", "프레젠테이션")
        slides_data = content_data.get("slides", [])
        
        prompt = f"""다음 내용으로 프레젠테이션 슬라이드를 작성해주세요:
        제목: {title}
        슬라이드 데이터: {json.dumps(slides_data, ensure_ascii=False)}
        
        각 슬라이드:
        - 제목
        - 주요 포인트 (불릿 포인트)
        - 설명 (간단한 노트)
        
        형식: {format_type}"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        # Parse slides
        slides = self._parse_slides(content)

        return {
            "content": content,
            "word_count": len(content.split()),
            "sections": [f"slide_{i+1}" for i in range(len(slides))],
            "metadata": {
                "type": "presentation",
                "title": title,
                "slide_count": len(slides),
                "generated_at": datetime.now().isoformat()
            },
            "confidence": 0.87
        }

    def _extract_sections(self, content: str) -> List[str]:
        """문서에서 섹션 추출"""
        sections = []
        lines = content.split('\n')
        
        for line in lines:
            if line.strip() and (line.startswith('#') or line.startswith('##') or 
                                line.endswith(':') or line[0].isdigit()):
                sections.append(line.strip())
        
        return sections[:10]  # Return top 10 sections

    def _parse_slides(self, content: str) -> List[Dict]:
        """프레젠테이션 슬라이드 파싱"""
        slides = []
        current_slide = None
        
        for line in content.split('\n'):
            if line.startswith('##') or line.startswith('슬라이드'):
                if current_slide:
                    slides.append(current_slide)
                current_slide = {"title": line.strip(), "content": []}
            elif current_slide:
                current_slide["content"].append(line.strip())
        
        if current_slide:
            slides.append(current_slide)
        
        return slides

    async def execute_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph 노드 실행 메서드"""
        
        # Extract task from state
        execution_state = state.get("execution_manager_state", {})
        pending_tasks = execution_state.get("pending_tasks", [])
        
        if not pending_tasks:
            logger.warning("No pending tasks for document generation")
            return state
        
        # Get first task for this agent
        task = None
        for t in pending_tasks:
            if t.get("agent") == "DocumentGenerationAgent":
                task = t
                break
        
        if not task:
            logger.warning("No document generation task found")
            return state
        
        # Execute task
        result = await self.execute(task)
        
        # Update state
        completed_tasks = execution_state.get("completed_tasks", [])
        completed_tasks.append({
            "task_id": task.get("task_id"),
            "agent": self.name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        # Remove from pending
        pending_tasks.remove(task)
        
        state["execution_manager_state"]["pending_tasks"] = pending_tasks
        state["execution_manager_state"]["completed_tasks"] = completed_tasks
        
        # Store agent-specific result
        if "agent_results" not in state:
            state["agent_results"] = {}
        state["agent_results"][self.name] = result
        
        logger.info(f"Document generation completed for task {task.get('task_id')}")
        return state