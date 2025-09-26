"""
Document Generation Agent - Report and document generation
Fully compliant with LangGraph 0.6.x Context API
"""

from typing import Dict, Any, List, Type
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
import asyncio
from pathlib import Path
import logging
from datetime import datetime
import json

from ..core.base_agent import BaseAgent
from ..core.states import DocumentState
from ..core.context import AgentContext
from ..core.config import Config
from ..tools.word_generator import WordGenerator


logger = logging.getLogger(__name__)


class DocumentGenerationAgent(BaseAgent):
    """Agent for generating documents and reports with Runtime support"""

    def __init__(self):
        super().__init__("document_generation_agent")
        self.template_path = Path("./templates")
        self.word_generator = WordGenerator()

    def _get_state_schema(self) -> Type:
        """Get the state schema for this agent"""
        return DocumentState

    def _build_graph(self):
        """Build the document generation workflow with context support"""
        # StateGraph with context_schema following LangGraph 0.6.x pattern
        self.workflow = StateGraph(DocumentState, context_schema=AgentContext)

        # Add nodes - all nodes will receive Runtime parameter
        self.workflow.add_node("prepare_data", self.prepare_data)
        self.workflow.add_node("select_template", self.select_template)
        self.workflow.add_node("generate_content", self.generate_content)
        self.workflow.add_node("format_document", self.format_document)
        self.workflow.add_node("finalize_document", self.finalize_document)

        # Add edges
        self.workflow.add_edge(START, "prepare_data")
        self.workflow.add_edge("prepare_data", "select_template")
        self.workflow.add_edge("select_template", "generate_content")
        self.workflow.add_edge("generate_content", "format_document")
        self.workflow.add_edge("format_document", "finalize_document")
        self.workflow.add_edge("finalize_document", END)

    async def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        required_fields = ["doc_type"]
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        return True

    def _create_initial_state(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create initial DocumentState from input data
        Only workflow data, no context fields
        """
        return {
            # Workflow status fields
            "status": "pending",
            "execution_step": "starting",

            # DocumentState specific fields
            "doc_type": input_data.get("doc_type", "general"),
            "doc_format": input_data.get("doc_format", "markdown"),
            "title": input_data.get("title", ""),
            "input_data": input_data.get("data", {}),
            "template_id": "",
            "sections": [],
            "content": "",
            "formatted_content": "",
            "document_metadata": {},
            "final_document": {}
        }

    # ==================== Node Functions with Runtime ====================
    # All nodes now receive Runtime[AgentContext] and return partial updates

    async def prepare_data(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Prepare data for document generation

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update (only changed fields)
        """
        try:
            # Access context through runtime
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Preparing data for user: {user_id}")

            doc_type = state.get("doc_type", "general")
            input_data = state.get("input_data", {})

            # Prepare document metadata
            metadata = {
                "created_by": user_id,
                "created_at": datetime.now().isoformat(),
                "doc_type": doc_type,
                "version": "1.0"
            }

            # Define sections based on document type
            sections = []
            if doc_type == "sales_report":
                sections = [
                    {"name": "summary", "title": "요약"},
                    {"name": "performance", "title": "실적 분석"},
                    {"name": "insights", "title": "주요 인사이트"},
                    {"name": "recommendations", "title": "제안 사항"}
                ]
            elif doc_type == "compliance_report":
                sections = [
                    {"name": "overview", "title": "개요"},
                    {"name": "findings", "title": "점검 결과"},
                    {"name": "violations", "title": "위반 사항"},
                    {"name": "actions", "title": "조치 사항"}
                ]
            elif doc_type == "leave_request":
                sections = [
                    {"name": "info", "title": "신청자 정보"},
                    {"name": "details", "title": "휴가 상세"},
                    {"name": "reason", "title": "사유"}
                ]
            else:
                sections = [
                    {"name": "introduction", "title": "소개"},
                    {"name": "body", "title": "본문"},
                    {"name": "conclusion", "title": "결론"}
                ]

            self.logger.info(f"Prepared {len(sections)} sections for {doc_type}")

            # Return ONLY changed fields (Context API pattern)
            return {
                "status": "processing",
                "execution_step": "data_prepared",
                "sections": sections,
                "document_metadata": metadata
            }

        except Exception as e:
            self.logger.error(f"Error preparing data: {e}")

            # Log error in context if possible
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Data preparation failed: {str(e)}")

            # Return failure status
            return {
                "status": "failed",
                "execution_step": "preparation_failed"
            }

    async def select_template(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Select appropriate template for document

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update
        """
        try:
            # Access context
            session_id = getattr(runtime.context, "session_id", "unknown")
            self.logger.info(f"Selecting template for session: {session_id}")

            doc_type = state.get("doc_type", "general")

            # Mock template selection
            # TODO: Implement real template management
            template_map = {
                "sales_report": "TMPL_SALES_001",
                "compliance_report": "TMPL_COMP_001",
                "leave_request": "TMPL_HR_001",
                "general": "TMPL_GEN_001"
            }

            template_id = template_map.get(doc_type, "TMPL_GEN_001")
            self.logger.info(f"Selected template: {template_id}")

            # Return partial update
            return {
                "execution_step": "template_selected",
                "template_id": template_id
            }

        except Exception as e:
            self.logger.error(f"Error selecting template: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Template selection failed: {str(e)}")

            return {
                "execution_step": "template_selection_failed",
                "template_id": ""
            }

    async def generate_content(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Generate document content

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update
        """
        try:
            # Access context for logging
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Generating content for user: {user_id}")

            doc_type = state.get("doc_type", "general")
            sections = state.get("sections", [])
            input_data = state.get("input_data", {})
            title = state.get("title", "")

            # Generate content based on document type
            content_parts = []

            # Add title if provided
            if not title:
                title_map = {
                    "sales_report": "월간 실적 보고서",
                    "compliance_report": "규정 준수 점검 보고서",
                    "leave_request": "휴가 신청서",
                    "general": "문서"
                }
                title = title_map.get(doc_type, "문서")

            content_parts.append(f"# {title}\n")

            # Generate section content
            for section in sections:
                content_parts.append(f"\n## {section['title']}\n")

                # Mock content generation based on section
                if section["name"] == "summary":
                    content_parts.append(self._generate_summary(input_data))
                elif section["name"] == "performance":
                    content_parts.append(self._generate_performance(input_data))
                elif section["name"] == "insights":
                    content_parts.append(self._generate_insights(input_data))
                elif section["name"] == "findings":
                    content_parts.append(self._generate_findings(input_data))
                else:
                    content_parts.append(f"{section['title']} 내용이 여기에 표시됩니다.\n")

            content = "\n".join(content_parts)
            self.logger.info(f"Generated content with {len(content)} characters")

            # Return partial update
            return {
                "execution_step": "content_generated",
                "content": content,
                "title": title
            }

        except Exception as e:
            self.logger.error(f"Error generating content: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Content generation failed: {str(e)}")

            return {
                "execution_step": "content_generation_failed",
                "content": ""
            }

    async def format_document(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Format the document content

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update
        """
        try:
            # Access context
            session_id = getattr(runtime.context, "session_id", "unknown")
            self.logger.info(f"Formatting document for session: {session_id}")

            content = state.get("content", "")
            doc_format = state.get("doc_format", "markdown")

            formatted_content = content

            # Apply formatting based on format type
            if doc_format == "html":
                # Simple markdown to HTML conversion
                formatted_content = self._markdown_to_html(content)
            elif doc_format == "text":
                # Remove markdown formatting
                formatted_content = self._markdown_to_text(content)
            elif doc_format == "word":
                # Generate Word document
                formatted_content = await self._generate_word_document(state, runtime)
            # else keep markdown format

            self.logger.info(f"Document formatted as {doc_format}")

            # Return partial update
            return {
                "execution_step": "document_formatted",
                "formatted_content": formatted_content
            }

        except Exception as e:
            self.logger.error(f"Error formatting document: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Document formatting failed: {str(e)}")

            return {
                "execution_step": "formatting_failed",
                "formatted_content": ""
            }

    async def finalize_document(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Finalize the document

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with final document
        """
        try:
            # Access context
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Finalizing document for user: {user_id}")

            final_document = {
                "status": "success",
                "doc_type": state.get("doc_type", ""),
                "title": state.get("title", ""),
                "format": state.get("doc_format", ""),
                "content": state.get("formatted_content", ""),
                "metadata": state.get("document_metadata", {}),
                "generated_at": datetime.now().isoformat(),
                "word_count": len(state.get("content", "").split()),
                "sections": state.get("sections", [])
            }

            self.logger.info("Document finalized successfully")

            # Return partial update
            return {
                "status": "completed",
                "execution_step": "document_finalized",
                "final_document": final_document
            }

        except Exception as e:
            self.logger.error(f"Error finalizing document: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Document finalization failed: {str(e)}")

            return {
                "status": "failed",
                "execution_step": "finalization_failed",
                "final_document": {
                    "status": "error",
                    "error": str(e)
                }
            }

    # ==================== Helper Methods ====================

    def _generate_summary(self, data: Dict[str, Any]) -> str:
        """Generate summary section"""
        if "statistics" in data:
            stats = data["statistics"]
            return f"""
- 총 매출: {stats.get('total_sales', 0):,.0f}원
- 평균 거래액: {stats.get('average_sale', 0):,.0f}원
- 거래 건수: {stats.get('transaction_count', 0)}건
"""
        return "요약 정보가 여기에 표시됩니다.\n"

    def _generate_performance(self, data: Dict[str, Any]) -> str:
        """Generate performance section"""
        if "aggregated_data" in data:
            perf_text = "### 월별 실적\n"
            for period, values in data["aggregated_data"].items():
                perf_text += f"- {period}: {values.get('amount', 0):,.0f}원 ({values.get('count', 0)}건)\n"
            return perf_text
        return "실적 정보가 여기에 표시됩니다.\n"

    def _generate_insights(self, data: Dict[str, Any]) -> str:
        """Generate insights section"""
        if "insights" in data:
            insights_text = ""
            for insight in data["insights"]:
                insights_text += f"- {insight}\n"
            return insights_text
        return "인사이트가 여기에 표시됩니다.\n"

    def _generate_findings(self, data: Dict[str, Any]) -> str:
        """Generate findings section"""
        if "violations" in data:
            if not data["violations"]:
                return "위반 사항이 발견되지 않았습니다.\n"
            findings_text = "### 발견된 위반 사항\n"
            for violation in data["violations"]:
                findings_text += f"- {violation.get('description', 'N/A')}\n"
            return findings_text
        return "점검 결과가 여기에 표시됩니다.\n"

    def _markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion"""
        html = markdown
        # Headers
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n", 1)
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n", 1)
        html = html.replace("# ", "<h1>").replace("\n", "</h1>\n", 1)
        # Lists
        html = html.replace("- ", "<li>").replace("\n", "</li>\n")
        # Paragraphs
        html = f"<html><body>{html}</body></html>"
        return html

    def _markdown_to_text(self, markdown: str) -> str:
        """Remove markdown formatting"""
        text = markdown
        text = text.replace("### ", "")
        text = text.replace("## ", "")
        text = text.replace("# ", "")
        text = text.replace("- ", "* ")
        return text

    async def _generate_word_document(self, state: Dict[str, Any], runtime: Runtime[AgentContext]) -> str:
        """Generate Word document based on document type and data"""
        try:
            doc_type = state.get("doc_type", "")
            input_data = state.get("input_data", {})

            # Map document type to template
            if doc_type == "product_seminar_application":
                # 제품설명회 신청서
                doc_path = self.word_generator.create_product_seminar_application(input_data)
                self.logger.info(f"Created product seminar application: {doc_path}")
                return doc_path

            elif doc_type == "product_seminar_report":
                # 제품설명회 결과보고서
                doc_path = self.word_generator.create_product_seminar_report(input_data)
                self.logger.info(f"Created product seminar report: {doc_path}")
                return doc_path

            else:
                # Default Word document generation
                self.logger.warning(f"Unknown Word document type: {doc_type}")
                # Return path information instead of content for Word documents
                return f"Word document type '{doc_type}' not implemented"

        except Exception as e:
            self.logger.error(f"Error generating Word document: {e}")
            return f"Error: {str(e)}"