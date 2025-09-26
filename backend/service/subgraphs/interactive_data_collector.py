"""
Interactive Data Collector Subgraph
Handles conversational data collection with user
"""

from typing import Dict, Any, List, TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
import logging
from ..core.context import AgentContext
from ..tools.template_analyzer import TemplateAnalyzer
from ..tools.document_query_analyzer import DocumentQueryAnalyzer

logger = logging.getLogger(__name__)


class DataCollectionState(TypedDict):
    """State for interactive data collection"""

    # Input
    template_name: str  # Template being used
    initial_data: Dict[str, Any]  # Data from initial query

    # Field tracking
    required_fields: List[Dict[str, Any]]  # Required field definitions
    optional_fields: List[Dict[str, Any]]  # Optional field definitions
    dynamic_sections: List[Dict[str, Any]]  # Dynamic sections (lists)

    # Collection progress
    collected_data: Annotated[Dict[str, Any], lambda x, y: {**x, **y}]  # Merge collected data
    missing_fields: List[Dict[str, Any]]  # Fields still missing
    current_field: Optional[Dict[str, Any]]  # Field being collected
    current_prompt: Optional[str]  # Current prompt for user

    # User interaction
    user_response: Optional[str]  # Latest user response
    interaction_count: int  # Number of interactions

    # Status
    collection_status: str  # pending, collecting, completed, cancelled
    errors: Annotated[List[str], lambda x, y: x + y]  # Accumulate errors


class InteractiveDataCollector:
    """Subgraph for interactive data collection"""

    def __init__(self):
        """Initialize the data collector"""
        self.template_analyzer = TemplateAnalyzer()
        self.query_analyzer = DocumentQueryAnalyzer()
        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the interactive collection workflow"""
        workflow = StateGraph(DataCollectionState, context_schema=AgentContext)

        # Add nodes
        workflow.add_node("analyze_template", self.analyze_template)
        workflow.add_node("identify_missing", self.identify_missing)
        workflow.add_node("generate_prompt", self.generate_prompt)
        workflow.add_node("wait_for_response", self.wait_for_response)
        workflow.add_node("process_response", self.process_response)
        workflow.add_node("validate_data", self.validate_data)
        workflow.add_node("finalize_collection", self.finalize_collection)

        # Add edges
        workflow.add_edge(START, "analyze_template")
        workflow.add_edge("analyze_template", "identify_missing")

        # Conditional edge: check if fields are missing
        workflow.add_conditional_edges(
            "identify_missing",
            self.should_collect_more,
            {
                "collect": "generate_prompt",
                "complete": "finalize_collection"
            }
        )

        workflow.add_edge("generate_prompt", "wait_for_response")
        workflow.add_edge("wait_for_response", "process_response")
        workflow.add_edge("process_response", "identify_missing")
        workflow.add_edge("finalize_collection", END)

        return workflow

    async def analyze_template(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Analyze template to identify required fields"""
        try:
            template_name = state.get("template_name")
            logger.info(f"Analyzing template: {template_name}")

            # Analyze template
            template_info = self.template_analyzer.analyze_template(template_name)

            return {
                "required_fields": template_info["required_fields"],
                "optional_fields": template_info["optional_fields"],
                "dynamic_sections": template_info["dynamic_sections"],
                "collection_status": "collecting"
            }

        except Exception as e:
            logger.error(f"Error analyzing template: {e}")
            return {
                "collection_status": "error",
                "errors": [str(e)]
            }

    async def identify_missing(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Identify missing required fields"""
        try:
            required_fields = state.get("required_fields", [])
            collected_data = state.get("collected_data", {})

            # Merge initial data with collected data
            all_data = {**state.get("initial_data", {}), **collected_data}

            # Find missing fields
            missing = []
            for field in required_fields:
                field_name = field.get("name")
                if field_name and field_name not in all_data:
                    missing.append(field)
                elif field_name and not all_data.get(field_name):
                    missing.append(field)

            logger.info(f"Missing fields: {len(missing)}")

            # Update collected data with all available data
            return {
                "missing_fields": missing,
                "collected_data": all_data,
                "interaction_count": state.get("interaction_count", 0)
            }

        except Exception as e:
            logger.error(f"Error identifying missing fields: {e}")
            return {"errors": [str(e)]}

    def should_collect_more(self, state: Dict[str, Any]) -> str:
        """Determine if more data collection is needed"""
        missing_fields = state.get("missing_fields", [])
        interaction_count = state.get("interaction_count", 0)

        # Stop if too many interactions
        if interaction_count > 20:
            logger.warning("Too many interactions, stopping collection")
            return "complete"

        if missing_fields:
            return "collect"
        else:
            return "complete"

    async def generate_prompt(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Generate prompt for next missing field"""
        try:
            missing_fields = state.get("missing_fields", [])
            if not missing_fields:
                return {"collection_status": "completed"}

            # Get next field to collect
            next_field = missing_fields[0]

            # Generate context-aware prompt
            collected_data = state.get("collected_data", {})
            prompt = await self.query_analyzer.generate_field_prompt(
                next_field,
                collected_data
            )

            logger.info(f"Generated prompt for field: {next_field.get('name')}")

            return {
                "current_field": next_field,
                "current_prompt": prompt,
                "interaction_count": state.get("interaction_count", 0) + 1
            }

        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            return {"errors": [str(e)]}

    async def wait_for_response(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Wait for user response (placeholder - actual implementation would handle async user input)"""
        # In real implementation, this would pause and wait for user input
        # For now, we'll return the state with a flag indicating we're waiting
        return {
            "collection_status": "waiting_for_user",
            "current_prompt": state.get("current_prompt")
        }

    async def process_response(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Process user response and extract field value"""
        try:
            user_response = state.get("user_response")
            current_field = state.get("current_field")

            if not user_response or not current_field:
                return {"collection_status": "waiting_for_user"}

            # Extract value from response using LLM
            extracted_value = await self.query_analyzer.extract_field_value(
                user_response,
                current_field
            )

            # Validate the extracted value
            field_name = current_field.get("name")
            if self.template_analyzer.validate_field_value(current_field, extracted_value):
                logger.info(f"Successfully collected {field_name}: {extracted_value}")
                return {
                    "collected_data": {field_name: extracted_value},
                    "user_response": None  # Clear response
                }
            else:
                logger.warning(f"Invalid value for {field_name}")
                # Re-prompt for this field
                return {
                    "current_prompt": f"입력하신 값이 올바르지 않습니다. 다시 {current_field.get('label')}를 입력해주세요.",
                    "user_response": None
                }

        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return {"errors": [str(e)]}

    async def validate_data(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Validate all collected data"""
        try:
            collected_data = state.get("collected_data", {})
            required_fields = state.get("required_fields", [])

            # Validate all required fields are present
            validation_errors = []
            for field in required_fields:
                field_name = field.get("name")
                if field_name and field_name not in collected_data:
                    validation_errors.append(f"필수 필드 누락: {field.get('label', field_name)}")

            if validation_errors:
                return {
                    "collection_status": "validation_failed",
                    "errors": validation_errors
                }

            return {"collection_status": "validated"}

        except Exception as e:
            logger.error(f"Error validating data: {e}")
            return {"errors": [str(e)]}

    async def finalize_collection(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """Finalize the data collection process"""
        try:
            collected_data = state.get("collected_data", {})
            dynamic_sections = state.get("dynamic_sections", [])

            # Process any dynamic sections (simplified for now)
            for section in dynamic_sections:
                section_name = section.get("name")
                if section_name not in collected_data:
                    # Add placeholder data for dynamic sections
                    if section_name == "staff_list":
                        collected_data[section_name] = [
                            {"no": "1", "team": "영업팀", "name": "담당자", "signature": ""}
                        ]
                    elif section_name == "hcp_list":
                        collected_data[section_name] = [
                            {"no": "1", "hospital": "병원", "name": "의료진", "signature": ""}
                        ]

            logger.info(f"Collection completed with {len(collected_data)} fields")

            return {
                "collection_status": "completed",
                "collected_data": collected_data
            }

        except Exception as e:
            logger.error(f"Error finalizing collection: {e}")
            return {
                "collection_status": "error",
                "errors": [str(e)]
            }

    def compile(self):
        """Compile the workflow"""
        return self.workflow.compile()