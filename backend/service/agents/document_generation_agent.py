"""
Document Generation Agent - Improved version without hardcoding
Dynamic default value generation with configurable defaults
"""

from typing import Dict, Any, List, Type, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
import asyncio
from pathlib import Path
import logging
from datetime import datetime
import os

from ..core.base_agent import BaseAgent
from ..core.states import DocumentState
from ..core.context import AgentContext
from ..tools.word_generator import WordGenerator
from ..tools.template_analyzer import TemplateAnalyzer
from ..tools.document_query_analyzer import DocumentQueryAnalyzer
from ..tools.default_value_generator import DefaultValueGenerator
from ..subgraphs.interactive_data_collector import InteractiveDataCollector


logger = logging.getLogger(__name__)


class DocumentGenerationAgent(BaseAgent):
    """Agent for document generation with dynamic default values"""

    def __init__(self):
        """Initialize the document generation agent"""
        super().__init__("document_generation_agent")

        # Initialize tools
        self.word_generator = WordGenerator()
        self.template_analyzer = TemplateAnalyzer()
        self.query_analyzer = DocumentQueryAnalyzer()
        self.default_generator = DefaultValueGenerator()  # New: Dynamic defaults
        self.data_collector = InteractiveDataCollector()

        # Output directory
        self.output_dir = Path("./generated_documents")
        self.output_dir.mkdir(exist_ok=True)

        logger.info("DocumentGenerationAgent initialized with dynamic defaults")

    def _get_state_schema(self) -> Type:
        """Get the state schema for this agent"""
        return DocumentState

    def _build_graph(self):
        """Build simplified workflow with 3 nodes"""
        # Create StateGraph with context support
        self.workflow = StateGraph(DocumentState, context_schema=AgentContext)

        # Add 3 core nodes
        self.workflow.add_node("analyze_and_extract", self.analyze_and_extract)
        self.workflow.add_node("collect_if_needed", self.collect_if_needed)
        self.workflow.add_node("generate_document", self.generate_document)

        # Define workflow edges
        self.workflow.add_edge(START, "analyze_and_extract")

        # Conditional edge based on data completeness
        self.workflow.add_conditional_edges(
            "analyze_and_extract",
            self.check_data_completeness,
            {
                "complete": "generate_document",
                "incomplete": "collect_if_needed"
            }
        )

        self.workflow.add_edge("collect_if_needed", "generate_document")
        self.workflow.add_edge("generate_document", END)

    async def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        # Need either a query or doc_type
        if "user_query" in input_data or "doc_type" in input_data:
            return True

        self.logger.error("Missing both user_query and doc_type")
        return False

    def _create_initial_state(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create initial state from input data"""
        return {
            # Status fields
            "status": "pending",
            "execution_step": "starting",
            "errors": [],

            # Document fields
            "doc_type": input_data.get("doc_type", ""),
            "doc_format": input_data.get("doc_format", "word"),
            "title": input_data.get("title", ""),

            # Data fields
            "user_query": input_data.get("user_query", ""),
            "input_data": input_data.get("data", {}),
            "collected_data": {},
            "missing_fields": [],

            # Workflow control
            "needs_user_input": False,
            "interaction_mode": input_data.get("interaction_mode", "auto"),

            # Context for default generation
            "generation_context": input_data.get("context", {}),

            # Results
            "final_document": {},
            "formatted_content": "",
            "content": "",

            # Metadata
            "sections": [],
            "template_id": "",
            "document_metadata": {},

            # Analysis results
            "query_analysis": None,
            "template_analysis": None,
            "required_fields": None,

            # Interaction tracking
            "interaction_history": [],
            "current_prompt": None,
            "user_response": None
        }

    # ==================== Node 1: Analyze and Extract ====================

    async def analyze_and_extract(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Node 1: Analyze query and extract all available data
        Combines query analysis, template analysis, and data extraction
        """
        try:
            self.logger.info("Starting analysis and extraction")

            # Step 1: Determine document type and extract initial data
            user_query = state.get("user_query", "")
            doc_type = state.get("doc_type", "")
            extracted_data = {}

            if user_query:
                # Use LLM to analyze natural language query
                self.logger.info(f"Analyzing query: {user_query[:100]}...")
                templates = self.template_analyzer.get_template_names()
                analysis = await self.query_analyzer.analyze_query(user_query, templates)

                # Extract document type
                doc_type = analysis.get("intent", "")
                if doc_type not in templates:
                    # Fallback keyword matching
                    if "신청" in user_query:
                        doc_type = "product_seminar_application"
                    elif "결과" in user_query or "보고" in user_query:
                        doc_type = "product_seminar_report"
                    else:
                        doc_type = templates[0] if templates else "product_seminar_application"

                extracted_data = analysis.get("extracted_data", {})
                query_analysis = analysis
            else:
                # Direct mode - use provided data
                extracted_data = state.get("input_data", {})
                query_analysis = None

            # Step 2: Analyze template requirements
            self.logger.info(f"Analyzing template: {doc_type}")
            template_analysis = self.template_analyzer.analyze_template(doc_type)
            required_fields = template_analysis.get("required_fields", [])

            # Step 3: Merge all available data
            all_data = {**state.get("input_data", {}), **extracted_data}

            # Step 4: Identify missing fields
            missing_fields = []
            for field in required_fields:
                field_name = field.get("name")
                if field_name and field_name not in all_data:
                    missing_fields.append(field)
                elif field_name and not all_data.get(field_name):
                    missing_fields.append(field)

            self.logger.info(f"Extracted {len(all_data)} fields, missing {len(missing_fields)} fields")

            # Return comprehensive update
            return {
                "execution_step": "analysis_complete",
                "doc_type": doc_type,
                "query_analysis": query_analysis,
                "template_analysis": template_analysis,
                "required_fields": required_fields,
                "collected_data": all_data,
                "missing_fields": missing_fields,
                "needs_user_input": len(missing_fields) > 0
            }

        except Exception as e:
            self.logger.error(f"Error in analysis: {e}")
            return {
                "execution_step": "analysis_failed",
                "status": "error",
                "errors": [str(e)]
            }

    def check_data_completeness(self, state: Dict[str, Any]) -> str:
        """Check if data is complete for document generation"""
        missing_fields = state.get("missing_fields", [])
        interaction_mode = state.get("interaction_mode", "auto")

        # In auto mode, proceed even with missing fields (will use dynamic defaults)
        if interaction_mode == "auto":
            return "incomplete"  # Always go through default generation

        # If interactive mode and missing fields, collect data
        if missing_fields:
            return "incomplete"

        return "complete"

    # ==================== Node 2: Collect Missing Data ====================

    async def collect_if_needed(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Node 2: Collect missing data if needed
        Uses dynamic defaults in auto mode or interactive collection
        """
        try:
            self.logger.info("Collecting missing data with dynamic defaults")

            missing_fields = state.get("missing_fields", [])
            collected_data = state.get("collected_data", {})
            interaction_mode = state.get("interaction_mode", "auto")
            generation_context = state.get("generation_context", {})

            if not missing_fields:
                # Even with no missing fields, ensure lists are populated
                if "staff_list" not in collected_data:
                    collected_data["staff_list"] = self.default_generator.get_staff_list()
                if "hcp_list" not in collected_data:
                    collected_data["hcp_list"] = self.default_generator.get_hcp_list()

                return {
                    "execution_step": "defaults_applied",
                    "collected_data": collected_data
                }

            # Auto mode: Fill with dynamic defaults
            if interaction_mode == "auto":
                self.logger.info(f"Generating dynamic defaults for {len(missing_fields)} fields")

                for field in missing_fields:
                    field_name = field.get("name")
                    field_type = field.get("type", "text")

                    # Generate contextual defaults using DefaultValueGenerator
                    generated_value = self.default_generator.generate_field_value(
                        field_name=field_name,
                        field_type=field_type,
                        context=generation_context
                    )

                    collected_data[field_name] = generated_value
                    self.logger.debug(f"Generated {field_name}: {generated_value}")

                # Ensure lists are properly generated if not present
                if "staff_list" not in collected_data or not collected_data.get("staff_list"):
                    collected_data["staff_list"] = self.default_generator.get_staff_list()

                if "hcp_list" not in collected_data or not collected_data.get("hcp_list"):
                    collected_data["hcp_list"] = self.default_generator.get_hcp_list()

                self.logger.info(f"Auto-generated {len(missing_fields)} fields with dynamic values")

            else:
                # Interactive mode: Would use subgraph for real user interaction
                self.logger.info("Interactive mode - collecting from user")

                # For demonstration, use the subgraph
                subgraph_result = await self.data_collector.execute({
                    "template_name": state.get("doc_type"),
                    "initial_data": collected_data,
                    "missing_fields": missing_fields
                })

                if subgraph_result.get("status") == "success":
                    collected_data = subgraph_result.get("data", {}).get("collected_data", collected_data)
                else:
                    # Fallback to dynamic defaults if subgraph fails
                    self.logger.warning("Interactive collection failed, using dynamic defaults")
                    for field in missing_fields:
                        field_name = field.get("name")
                        field_type = field.get("type", "text")
                        collected_data[field_name] = self.default_generator.generate_field_value(
                            field_name=field_name,
                            field_type=field_type,
                            context=generation_context
                        )

            return {
                "execution_step": "data_collected",
                "collected_data": collected_data,
                "missing_fields": [],
                "needs_user_input": False
            }

        except Exception as e:
            self.logger.error(f"Error collecting data: {e}")
            return {
                "execution_step": "collection_failed",
                "status": "error",
                "errors": [str(e)]
            }

    # ==================== Node 3: Generate Document ====================

    async def generate_document(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Node 3: Generate the final document
        Uses collected data to create Word document
        """
        try:
            self.logger.info("Generating document")

            doc_type = state.get("doc_type", "")
            doc_format = state.get("doc_format", "word")
            collected_data = state.get("collected_data", {})

            if not doc_type:
                raise ValueError("Document type not specified")

            # Log data being used
            self.logger.info(f"Using {len(collected_data)} data fields for document generation")

            # Generate appropriate document
            if doc_format == "word":
                # Generate Word document using the collected data
                doc_path = await self._generate_word_document(doc_type, collected_data)

                # Get file info
                if os.path.exists(doc_path):
                    file_size = os.path.getsize(doc_path)
                    self.logger.info(f"Generated Word document: {doc_path} ({file_size:,} bytes)")
                else:
                    raise FileNotFoundError(f"Generated file not found: {doc_path}")

                # Create final document metadata
                final_document = {
                    "status": "success",
                    "doc_type": doc_type,
                    "format": doc_format,
                    "file_path": doc_path,
                    "file_size": file_size,
                    "content": doc_path,  # For compatibility
                    "generated_at": datetime.now().isoformat(),
                    "data_used": len(collected_data),
                    "title": self._get_document_title(doc_type),
                    "generation_method": "dynamic_defaults"  # Indicate dynamic generation
                }
            else:
                # Other formats (markdown, html, etc.) - not implemented yet
                final_document = {
                    "status": "error",
                    "error": f"Format {doc_format} not implemented"
                }

            # Reset cache for next generation to ensure variety
            self.default_generator.reset_cache()

            return {
                "status": "completed",
                "execution_step": "document_generated",
                "final_document": final_document,
                "formatted_content": doc_path if doc_format == "word" else ""
            }

        except Exception as e:
            self.logger.error(f"Error generating document: {e}")
            return {
                "status": "failed",
                "execution_step": "generation_failed",
                "errors": [str(e)],
                "final_document": {
                    "status": "error",
                    "error": str(e)
                }
            }

    # ==================== Helper Methods ====================

    async def _generate_word_document(self, doc_type: str, data: Dict[str, Any]) -> str:
        """Generate Word document based on type and data"""
        try:
            self.logger.info(f"Generating Word document for type: {doc_type}")
            self.logger.debug(f"Using data fields: {list(data.keys())}")

            # Validate required data is present
            if not data:
                raise ValueError("No data provided for document generation")

            # Call appropriate Word generator method
            if doc_type == "product_seminar_application":
                doc_path = self.word_generator.create_product_seminar_application(data)
            elif doc_type == "product_seminar_report":
                doc_path = self.word_generator.create_product_seminar_report(data)
            else:
                # Generic document generation
                doc_path = self.word_generator.create_document_from_template(
                    template_name=doc_type,
                    data=data
                )

            return doc_path

        except Exception as e:
            self.logger.error(f"Error in Word generation: {e}")
            # Return error path for debugging
            return f"Error: {str(e)}"

    def _get_document_title(self, doc_type: str) -> str:
        """Get document title based on type"""
        titles = {
            "product_seminar_application": "제품설명회 신청서",
            "product_seminar_report": "제품설명회 결과보고서",
            "sales_report": "영업 실적 보고서",
            "compliance_report": "규정 준수 보고서"
        }
        return titles.get(doc_type, "문서")