"""
Document Generation Agent - Report and document creation
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
import asyncio
from pathlib import Path
import logging
from datetime import datetime
import json

from ..core.base_agent import BaseAgent
from ..core.states import DocumentState
from ..core.config import Config


logger = logging.getLogger(__name__)


class DocumentGenerationAgent(BaseAgent):
    """Agent for generating documents and reports"""

    def __init__(self):
        super().__init__("document_generation_agent")
        self.templates_dir = Path("templates")  # Template directory

    def _build_graph(self):
        """Build the document generation workflow"""
        self.workflow = StateGraph(DocumentState)

        # Add nodes
        self.workflow.add_node("prepare_content", self.prepare_content)
        self.workflow.add_node("select_template", self.select_template)
        self.workflow.add_node("generate_sections", self.generate_sections)
        self.workflow.add_node("apply_formatting", self.apply_formatting)
        self.workflow.add_node("finalize_document", self.finalize_document)

        # Add edges
        self.workflow.add_edge(START, "prepare_content")
        self.workflow.add_edge("prepare_content", "select_template")
        self.workflow.add_edge("select_template", "generate_sections")
        self.workflow.add_edge("generate_sections", "apply_formatting")
        self.workflow.add_edge("apply_formatting", "finalize_document")
        self.workflow.add_edge("finalize_document", END)

    async def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        required_fields = ["document_type", "input_content"]
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        return True

    async def prepare_content(self, state: DocumentState) -> DocumentState:
        """Prepare and validate content for document generation"""
        try:
            state["status"] = "processing"

            # Set default document format if not specified
            if not state.get("document_format"):
                state["document_format"] = "markdown"

            # Initialize sections list
            state["sections"] = []

            # Validate input content
            input_content = state.get("input_content", {})
            if not input_content:
                raise ValueError("No input content provided")

            self.logger.info(f"Content prepared for {state.get('document_type')} document")
            return state

        except Exception as e:
            self.logger.error(f"Error preparing content: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["status"] = "failed"
            return state

    async def select_template(self, state: DocumentState) -> DocumentState:
        """Select appropriate template based on document type"""
        try:
            document_type = state.get("document_type", "report")
            template_name = state.get("template_name", "")

            # Select template based on document type
            if not template_name:
                template_map = {
                    "report": "standard_report",
                    "memo": "internal_memo",
                    "presentation": "presentation_outline",
                    "email": "email_template",
                    "summary": "executive_summary"
                }
                template_name = template_map.get(document_type, "standard_report")

            state["template_name"] = template_name

            # Load template structure
            template_structure = self._get_template_structure(template_name)
            state["formatting_rules"] = template_structure.get("formatting", {})

            self.logger.info(f"Template selected: {template_name}")

        except Exception as e:
            self.logger.error(f"Error selecting template: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]

        return state

    async def generate_sections(self, state: DocumentState) -> DocumentState:
        """Generate document sections based on template and content"""
        try:
            document_type = state.get("document_type", "report")
            input_content = state.get("input_content", {})
            template_name = state.get("template_name", "standard_report")

            sections = []

            # Generate sections based on document type
            if document_type == "report":
                sections = self._generate_report_sections(input_content)
            elif document_type == "memo":
                sections = self._generate_memo_sections(input_content)
            elif document_type == "email":
                sections = self._generate_email_sections(input_content)
            elif document_type == "presentation":
                sections = self._generate_presentation_sections(input_content)
            else:
                sections = self._generate_default_sections(input_content)

            state["sections"] = sections
            self.logger.info(f"Generated {len(sections)} document sections")

        except Exception as e:
            self.logger.error(f"Error generating sections: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["sections"] = []

        return state

    async def apply_formatting(self, state: DocumentState) -> DocumentState:
        """Apply formatting rules to document content"""
        try:
            sections = state.get("sections", [])
            document_format = state.get("document_format", "markdown")
            formatting_rules = state.get("formatting_rules", {})

            # Format content based on document format
            if document_format == "markdown":
                formatted_content = self._format_markdown(sections, formatting_rules)
            elif document_format == "html":
                formatted_content = self._format_html(sections, formatting_rules)
            elif document_format == "text":
                formatted_content = self._format_text(sections, formatting_rules)
            else:
                formatted_content = self._format_text(sections, formatting_rules)

            state["generated_content"] = formatted_content
            self.logger.info(f"Formatting applied: {document_format}")

        except Exception as e:
            self.logger.error(f"Error applying formatting: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["generated_content"] = ""

        return state

    async def finalize_document(self, state: DocumentState) -> DocumentState:
        """Finalize the document and prepare output"""
        try:
            generated_content = state.get("generated_content", "")

            # Add metadata
            metadata = {
                "created_at": datetime.now().isoformat(),
                "document_type": state.get("document_type", ""),
                "template": state.get("template_name", ""),
                "format": state.get("document_format", ""),
                "sections_count": len(state.get("sections", []))
            }

            state["final_document"] = {
                "status": "success",
                "content": generated_content,
                "metadata": metadata,
                "format": state.get("document_format", "text")
            }

            state["status"] = "completed"
            self.logger.info("Document finalized successfully")

        except Exception as e:
            self.logger.error(f"Error finalizing document: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["status"] = "failed"
            state["final_document"] = {
                "status": "error",
                "error": str(e)
            }

        return state

    def _get_template_structure(self, template_name: str) -> Dict[str, Any]:
        """Get template structure and formatting rules"""
        templates = {
            "standard_report": {
                "sections": ["title", "summary", "introduction", "body", "conclusion", "recommendations"],
                "formatting": {
                    "title_level": 1,
                    "section_level": 2,
                    "subsection_level": 3,
                    "bullet_style": "-"
                }
            },
            "internal_memo": {
                "sections": ["header", "subject", "body", "action_items"],
                "formatting": {
                    "title_level": 2,
                    "section_level": 3,
                    "bullet_style": "*"
                }
            },
            "email_template": {
                "sections": ["greeting", "body", "closing"],
                "formatting": {
                    "title_level": 3,
                    "bullet_style": "-"
                }
            }
        }

        return templates.get(template_name, templates["standard_report"])

    def _generate_report_sections(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate report sections"""
        sections = []

        # Title
        sections.append({
            "type": "title",
            "content": content.get("title", "분석 보고서")
        })

        # Executive Summary
        if content.get("summary"):
            sections.append({
                "type": "summary",
                "content": content.get("summary")
            })

        # Main content
        if content.get("data"):
            sections.append({
                "type": "body",
                "content": self._format_data_content(content.get("data"))
            })

        # Insights
        if content.get("insights"):
            sections.append({
                "type": "insights",
                "content": content.get("insights")
            })

        # Recommendations
        if content.get("recommendations"):
            sections.append({
                "type": "recommendations",
                "content": content.get("recommendations")
            })

        return sections

    def _generate_memo_sections(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate memo sections"""
        sections = []

        sections.append({
            "type": "header",
            "content": {
                "to": content.get("to", "All Staff"),
                "from": content.get("from", "Management"),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "subject": content.get("subject", "Important Notice")
            }
        })

        sections.append({
            "type": "body",
            "content": content.get("message", "")
        })

        if content.get("action_items"):
            sections.append({
                "type": "action_items",
                "content": content.get("action_items")
            })

        return sections

    def _generate_email_sections(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate email sections"""
        sections = []

        sections.append({
            "type": "greeting",
            "content": content.get("greeting", "안녕하세요,")
        })

        sections.append({
            "type": "body",
            "content": content.get("message", "")
        })

        sections.append({
            "type": "closing",
            "content": content.get("closing", "감사합니다.")
        })

        return sections

    def _generate_presentation_sections(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate presentation outline sections"""
        sections = []

        sections.append({
            "type": "title_slide",
            "content": content.get("title", "Presentation Title")
        })

        if content.get("agenda"):
            sections.append({
                "type": "agenda",
                "content": content.get("agenda")
            })

        if content.get("slides"):
            for i, slide in enumerate(content.get("slides", [])):
                sections.append({
                    "type": f"slide_{i+1}",
                    "content": slide
                })

        return sections

    def _generate_default_sections(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate default sections for unknown document types"""
        sections = []

        for key, value in content.items():
            sections.append({
                "type": key,
                "content": value
            })

        return sections

    def _format_markdown(self, sections: List[Dict[str, Any]], rules: Dict[str, Any]) -> str:
        """Format sections as Markdown"""
        lines = []

        for section in sections:
            section_type = section.get("type", "")
            content = section.get("content", "")

            if section_type == "title":
                lines.append(f"# {content}\n")
            elif section_type == "summary":
                lines.append(f"## 요약\n\n{content}\n")
            elif section_type == "body":
                lines.append(f"## 내용\n\n{self._format_content(content)}\n")
            elif section_type == "insights":
                lines.append(f"## 인사이트\n\n{self._format_list(content)}\n")
            elif section_type == "recommendations":
                lines.append(f"## 권고사항\n\n{self._format_list(content)}\n")
            else:
                lines.append(f"### {section_type}\n\n{self._format_content(content)}\n")

        return "\n".join(lines)

    def _format_html(self, sections: List[Dict[str, Any]], rules: Dict[str, Any]) -> str:
        """Format sections as HTML"""
        # Simple HTML formatting
        html = ["<html><body>"]

        for section in sections:
            section_type = section.get("type", "")
            content = section.get("content", "")

            if section_type == "title":
                html.append(f"<h1>{content}</h1>")
            else:
                html.append(f"<h2>{section_type}</h2>")
                html.append(f"<p>{content}</p>")

        html.append("</body></html>")
        return "\n".join(html)

    def _format_text(self, sections: List[Dict[str, Any]], rules: Dict[str, Any]) -> str:
        """Format sections as plain text"""
        lines = []

        for section in sections:
            section_type = section.get("type", "")
            content = section.get("content", "")

            lines.append(f"[{section_type.upper()}]")
            lines.append(str(content))
            lines.append("")

        return "\n".join(lines)

    def _format_content(self, content: Any) -> str:
        """Format content based on type"""
        if isinstance(content, dict):
            return json.dumps(content, ensure_ascii=False, indent=2)
        elif isinstance(content, list):
            return self._format_list(content)
        else:
            return str(content)

    def _format_list(self, items: List[Any]) -> str:
        """Format list items"""
        return "\n".join([f"- {item}" for item in items])

    def _format_data_content(self, data: Any) -> str:
        """Format data content for reports"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"**{key}**: {value}")
            return "\n".join(lines)
        else:
            return self._format_content(data)