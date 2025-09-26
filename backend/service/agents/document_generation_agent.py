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
from ..tools.template_analyzer import TemplateAnalyzer
from ..tools.document_query_analyzer import DocumentQueryAnalyzer
from ..subgraphs.interactive_data_collector import InteractiveDataCollector


logger = logging.getLogger(__name__)


class DocumentGenerationAgent(BaseAgent):
    """Agent for generating documents and reports with Runtime support"""

    def __init__(self):
        super().__init__("document_generation_agent")
        self.template_path = Path("./templates")
        self.word_generator = WordGenerator()
        self.template_analyzer = TemplateAnalyzer()
        self.query_analyzer = DocumentQueryAnalyzer()
        self.data_collector = InteractiveDataCollector()

    def _get_state_schema(self) -> Type:
        """Get the state schema for this agent"""
        return DocumentState

    def _build_graph(self):
        """Build the document generation workflow with interactive support"""
        # StateGraph with context_schema following LangGraph 0.6.x pattern
        self.workflow = StateGraph(DocumentState, context_schema=AgentContext)

        # Add nodes - all nodes will receive Runtime parameter
        self.workflow.add_node("analyze_query", self.analyze_query)
        self.workflow.add_node("analyze_template", self.analyze_template_fields)
        self.workflow.add_node("check_missing_fields", self.check_missing_fields)
        self.workflow.add_node("collect_data", self.collect_data_interactive)
        self.workflow.add_node("prepare_data", self.prepare_data)
        self.workflow.add_node("select_template", self.select_template)
        self.workflow.add_node("generate_content", self.generate_content)
        self.workflow.add_node("format_document", self.format_document)
        self.workflow.add_node("finalize_document", self.finalize_document)

        # Add edges
        self.workflow.add_edge(START, "analyze_query")
        self.workflow.add_edge("analyze_query", "analyze_template")
        self.workflow.add_edge("analyze_template", "check_missing_fields")

        # Conditional edge: check if data collection is needed
        self.workflow.add_conditional_edges(
            "check_missing_fields",
            self.needs_data_collection,
            {
                "collect": "collect_data",
                "proceed": "prepare_data"
            }
        )

        self.workflow.add_edge("collect_data", "prepare_data")
        self.workflow.add_edge("prepare_data", "select_template")
        self.workflow.add_edge("select_template", "generate_content")
        self.workflow.add_edge("generate_content", "format_document")
        self.workflow.add_edge("format_document", "finalize_document")
        self.workflow.add_edge("finalize_document", END)

    async def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        # For interactive mode, we just need a query
        if "user_query" in input_data:
            return True
        # For direct mode, we need doc_type
        if "doc_type" in input_data:
            return True
        self.logger.error("Missing both user_query and doc_type")
        return False

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
            "doc_type": input_data.get("doc_type", ""),
            "doc_format": input_data.get("doc_format", "word"),
            "title": input_data.get("title", ""),
            "input_data": input_data.get("data", {}),
            "template_id": "",
            "sections": [],
            "content": "",
            "formatted_content": "",
            "document_metadata": {},
            "final_document": {},

            # Interactive fields
            "user_query": input_data.get("user_query", ""),
            "query_analysis": None,
            "template_analysis": None,
            "required_fields": None,
            "missing_fields": None,
            "collected_data": {},
            "interaction_mode": input_data.get("interaction_mode", "auto"),
            "interaction_history": [],
            "needs_user_input": False,
            "current_prompt": None,
            "user_response": None
        }

    # ==================== New Interactive Node Functions ====================

    async def analyze_query(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Analyze user query to extract intent and data"""
        try:
            user_query = state.get("user_query", "")
            if not user_query:
                # If no query, use doc_type directly
                return {"execution_step": "query_analyzed"}

            self.logger.info(f"Analyzing query: {user_query[:100]}...")

            # Get available templates
            templates = self.template_analyzer.get_template_names()

            # Analyze query using LLM
            analysis = await self.query_analyzer.analyze_query(user_query, templates)

            # Extract document type from analysis
            doc_type = analysis.get("intent", "")
            if doc_type not in templates:
                # Try to match based on keywords
                if "신청" in user_query:
                    doc_type = "product_seminar_application"
                elif "결과" in user_query or "보고" in user_query:
                    doc_type = "product_seminar_report"
                else:
                    doc_type = "product_seminar_application"  # Default

            self.logger.info(f"Detected document type: {doc_type}")

            return {
                "execution_step": "query_analyzed",
                "query_analysis": analysis,
                "doc_type": doc_type,
                "input_data": analysis.get("extracted_data", {}),
                "collected_data": analysis.get("extracted_data", {})
            }

        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
            return {
                "execution_step": "query_analysis_failed",
                "errors": [str(e)]
            }

    async def analyze_template_fields(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Analyze template to identify required fields"""
        try:
            doc_type = state.get("doc_type", "")
            if not doc_type:
                return {"execution_step": "no_template"}

            self.logger.info(f"Analyzing template: {doc_type}")

            # Analyze template
            template_analysis = self.template_analyzer.analyze_template(doc_type)

            return {
                "execution_step": "template_analyzed",
                "template_analysis": template_analysis,
                "required_fields": template_analysis.get("required_fields", []),
                "doc_format": "word"  # Default to Word for these templates
            }

        except Exception as e:
            self.logger.error(f"Error analyzing template: {e}")
            return {
                "execution_step": "template_analysis_failed",
                "errors": [str(e)]
            }

    async def check_missing_fields(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Check which required fields are missing"""
        try:
            required_fields = state.get("required_fields", [])
            collected_data = state.get("collected_data", {})
            input_data = state.get("input_data", {})

            # Merge all available data
            all_data = {**input_data, **collected_data}

            # Find missing fields
            missing = await self.query_analyzer.identify_missing_fields(
                required_fields,
                all_data
            )

            self.logger.info(f"Missing {len(missing)} required fields")

            return {
                "execution_step": "fields_checked",
                "missing_fields": missing,
                "collected_data": all_data,
                "needs_user_input": len(missing) > 0
            }

        except Exception as e:
            self.logger.error(f"Error checking fields: {e}")
            return {"errors": [str(e)]}

    def needs_data_collection(self, state: Dict[str, Any]) -> str:
        """Determine if data collection is needed"""
        missing_fields = state.get("missing_fields", [])
        interaction_mode = state.get("interaction_mode", "auto")

        if interaction_mode == "auto" and not missing_fields:
            return "proceed"
        elif missing_fields:
            return "collect"
        else:
            return "proceed"

    async def collect_data_interactive(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Collect missing data interactively (simplified version)"""
        try:
            missing_fields = state.get("missing_fields", [])
            collected_data = state.get("collected_data", {})

            # For now, fill with default values
            # In real implementation, this would trigger the subgraph
            for field in missing_fields:
                field_name = field.get("name")
                field_type = field.get("type")

                # Generate default values based on field type
                if field_name == "date":
                    collected_data[field_name] = "2024-12-20 14:00"
                elif field_name == "location":
                    collected_data[field_name] = "서울 강남구 회의실"
                elif field_name == "product_name":
                    collected_data[field_name] = "신제품 A"
                elif field_name == "expected_attendees":
                    collected_data[field_name] = "15명"
                elif field_name == "actual_attendees":
                    collected_data[field_name] = "12명"
                elif field_name == "purpose":
                    collected_data[field_name] = "신제품 소개 및 효능 설명"
                elif field_name == "result":
                    collected_data[field_name] = "성공적으로 진행됨"
                elif field_name == "main_content":
                    collected_data[field_name] = "1. 제품 소개\n2. 임상 데이터\n3. Q&A"
                elif field_name == "payment_details":
                    collected_data[field_name] = "강의료: 500,000원"
                elif field_name == "budget_usage":
                    collected_data[field_name] = "총 예산: 1,000,000원\n사용: 700,000원"
                elif field_type == "select":
                    options = field.get("options", [])
                    collected_data[field_name] = options[0] if options else "기본값"
                else:
                    collected_data[field_name] = f"{field.get('label', field_name)} 정보"

            # Add default lists if needed
            if "staff_list" not in collected_data:
                collected_data["staff_list"] = [
                    {"no": "1", "team": "영업1팀", "name": "김담당", "signature": ""},
                    {"no": "2", "team": "마케팅팀", "name": "이과장", "signature": ""}
                ]

            if "hcp_list" not in collected_data:
                collected_data["hcp_list"] = [
                    {"no": "1", "hospital": "서울대병원", "name": "김의사", "signature": ""},
                    {"no": "2", "hospital": "삼성병원", "name": "박약사", "signature": ""}
                ]

            self.logger.info(f"Collected/generated data for {len(missing_fields)} fields")

            return {
                "execution_step": "data_collected",
                "collected_data": collected_data,
                "input_data": collected_data,
                "needs_user_input": False
            }

        except Exception as e:
            self.logger.error(f"Error collecting data: {e}")
            return {"errors": [str(e)]}

    # ==================== Original Node Functions with Runtime ====================
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
            user_id = runtime.context.get("user_id", "unknown") if hasattr(runtime, 'context') else "unknown"
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
            if hasattr(runtime, 'context') and isinstance(runtime.context, dict):
                # Context is a dict, can't call methods on it
                pass

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
            session_id = runtime.context.get("session_id", "unknown") if hasattr(runtime, 'context') else "unknown"
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
            if hasattr(runtime, 'context') and isinstance(runtime.context, dict):
                pass

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
            user_id = runtime.context.get("user_id", "unknown") if hasattr(runtime, 'context') else "unknown"
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
            if hasattr(runtime, 'context') and isinstance(runtime.context, dict):
                pass

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
            session_id = runtime.context.get("session_id", "unknown") if hasattr(runtime, 'context') else "unknown"
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
            if hasattr(runtime, 'context') and isinstance(runtime.context, dict):
                pass

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
            user_id = runtime.context.get("user_id", "unknown") if hasattr(runtime, 'context') else "unknown"
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
            if hasattr(runtime, 'context') and isinstance(runtime.context, dict):
                pass

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