"""
Template Analyzer Tool
Analyzes Word document templates to extract required fields
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class TemplateAnalyzer:
    """Analyzes Word templates to identify required fields"""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize template analyzer

        Args:
            template_dir: Directory containing template JSON files
        """
        self.template_dir = template_dir or Path("./backend/service/templates")
        self.templates_cache = {}
        self._load_templates()

    def _load_templates(self):
        """Load all template definitions"""
        try:
            # Load product seminar application template
            app_path = self.template_dir / "product_seminar_application.json"
            if app_path.exists():
                with open(app_path, 'r', encoding='utf-8') as f:
                    self.templates_cache["product_seminar_application"] = json.load(f)

            # Load product seminar report template
            report_path = self.template_dir / "product_seminar_report.json"
            if report_path.exists():
                with open(report_path, 'r', encoding='utf-8') as f:
                    self.templates_cache["product_seminar_report"] = json.load(f)

            logger.info(f"Loaded {len(self.templates_cache)} templates")

        except Exception as e:
            logger.error(f"Error loading templates: {e}")

    def analyze_template(self, template_name: str) -> Dict[str, Any]:
        """
        Analyze a template to extract required fields

        Args:
            template_name: Name of the template to analyze

        Returns:
            Dictionary containing:
            - required_fields: List of required field definitions
            - optional_fields: List of optional field definitions
            - dynamic_sections: List of dynamic sections (e.g., participant lists)
        """
        if template_name not in self.templates_cache:
            logger.error(f"Template not found: {template_name}")
            return {
                "required_fields": [],
                "optional_fields": [],
                "dynamic_sections": []
            }

        template = self.templates_cache[template_name]
        required_fields = []
        optional_fields = []
        dynamic_sections = []

        # Extract fields from template structure
        if "row_templates" in template.get("table_structure", {}):
            for row_template in template["table_structure"]["row_templates"]:
                for cell in row_template.get("cells", []):
                    if "field" in cell:
                        field_info = {
                            "name": cell["field"],
                            "label": cell.get("content", cell["field"]),
                            "type": self._infer_field_type(cell["field"]),
                            "required": True  # Default to required
                        }

                        # Check if field is optional based on name
                        if any(opt in cell["field"] for opt in ["optional", "notes", "remarks"]):
                            field_info["required"] = False
                            optional_fields.append(field_info)
                        else:
                            required_fields.append(field_info)

        # Extract dynamic sections
        if "dynamic_sections" in template.get("table_structure", {}):
            for section in template["table_structure"]["dynamic_sections"]:
                dynamic_info = {
                    "name": section["data_key"],
                    "label": section.get("label", section["data_key"]),
                    "columns": []
                }

                for col in section.get("columns", []):
                    dynamic_info["columns"].append({
                        "field": col.get("field"),
                        "label": col.get("label", col.get("field"))
                    })

                dynamic_sections.append(dynamic_info)

        # Template-specific field definitions
        if template_name == "product_seminar_application":
            required_fields = [
                {"name": "seminar_type", "label": "세미나 유형", "type": "select",
                 "options": ["단일", "복수"], "required": True},
                {"name": "pm_attendance", "label": "PM 참석 여부", "type": "select",
                 "options": ["참석", "불참"], "required": True},
                {"name": "date", "label": "일시", "type": "datetime", "required": True},
                {"name": "location", "label": "장소", "type": "text", "required": True},
                {"name": "product_name", "label": "제품명", "type": "text", "required": True},
                {"name": "expected_attendees", "label": "참석 예정 인원", "type": "text", "required": True},
                {"name": "purpose", "label": "시행 목적", "type": "textarea", "required": True},
                {"name": "main_content", "label": "주요 내용", "type": "textarea", "required": True}
            ]

            dynamic_sections = [
                {
                    "name": "staff_list",
                    "label": "직원 명단",
                    "columns": [
                        {"field": "no", "label": "번호"},
                        {"field": "team", "label": "팀"},
                        {"field": "name", "label": "이름"},
                        {"field": "signature", "label": "서명"}
                    ]
                },
                {
                    "name": "hcp_list",
                    "label": "보건의료전문가 명단",
                    "columns": [
                        {"field": "no", "label": "번호"},
                        {"field": "hospital", "label": "병원"},
                        {"field": "name", "label": "이름"},
                        {"field": "signature", "label": "서명"}
                    ]
                }
            ]

        elif template_name == "product_seminar_report":
            required_fields = [
                {"name": "seminar_type", "label": "세미나 유형", "type": "select",
                 "options": ["단일", "복수"], "required": True},
                {"name": "pm_attendance", "label": "PM 참석 여부", "type": "select",
                 "options": ["참석", "불참"], "required": True},
                {"name": "date", "label": "일시", "type": "datetime", "required": True},
                {"name": "location", "label": "장소", "type": "text", "required": True},
                {"name": "product_name", "label": "제품명", "type": "text", "required": True},
                {"name": "actual_attendees", "label": "실제 참석 인원", "type": "text", "required": True},
                {"name": "result", "label": "시행 결과", "type": "textarea", "required": True},
                {"name": "main_content", "label": "주요 내용", "type": "textarea", "required": True},
                {"name": "payment_details", "label": "지급 내역", "type": "textarea", "required": True},
                {"name": "budget_usage", "label": "예산 사용 내역", "type": "textarea", "required": True}
            ]

            dynamic_sections = [
                {
                    "name": "staff_list",
                    "label": "직원 명단",
                    "columns": [
                        {"field": "no", "label": "번호"},
                        {"field": "team", "label": "팀"},
                        {"field": "name", "label": "이름"},
                        {"field": "signature", "label": "서명"}
                    ]
                },
                {
                    "name": "hcp_list",
                    "label": "보건의료전문가 명단",
                    "columns": [
                        {"field": "no", "label": "번호"},
                        {"field": "hospital", "label": "병원"},
                        {"field": "name", "label": "이름"},
                        {"field": "signature", "label": "서명"}
                    ]
                }
            ]

        return {
            "template_name": template_name,
            "required_fields": required_fields,
            "optional_fields": optional_fields,
            "dynamic_sections": dynamic_sections
        }

    def _infer_field_type(self, field_name: str) -> str:
        """
        Infer field type from field name

        Args:
            field_name: Name of the field

        Returns:
            Inferred field type
        """
        field_lower = field_name.lower()

        if any(dt in field_lower for dt in ["date", "time", "일시", "날짜"]):
            return "datetime"
        elif any(sel in field_lower for sel in ["type", "유형", "attendance", "참석"]):
            return "select"
        elif any(num in field_lower for num in ["count", "number", "인원", "명수"]):
            return "number"
        elif any(txt in field_lower for txt in ["content", "내용", "purpose", "목적", "result", "결과"]):
            return "textarea"
        else:
            return "text"

    def get_field_prompt(self, field: Dict[str, Any]) -> str:
        """
        Generate a prompt for collecting a specific field

        Args:
            field: Field definition

        Returns:
            User-friendly prompt for the field
        """
        label = field.get("label", field.get("name", "정보"))
        field_type = field.get("type", "text")

        if field_type == "select" and "options" in field:
            options_str = ", ".join(field["options"])
            return f"{label}를 선택해주세요 ({options_str})"
        elif field_type == "datetime":
            return f"{label}를 입력해주세요 (예: 2024-12-15 14:00)"
        elif field_type == "number":
            return f"{label}를 숫자로 입력해주세요"
        elif field_type == "textarea":
            return f"{label}를 자세히 입력해주세요"
        else:
            return f"{label}를 입력해주세요"

    def validate_field_value(self, field: Dict[str, Any], value: Any) -> bool:
        """
        Validate a field value

        Args:
            field: Field definition
            value: Value to validate

        Returns:
            True if valid, False otherwise
        """
        if field.get("required", False) and not value:
            return False

        field_type = field.get("type", "text")

        if field_type == "select" and "options" in field:
            return value in field["options"]
        elif field_type == "number":
            try:
                float(value)
                return True
            except:
                return False
        elif field_type == "datetime":
            # Simple datetime validation
            if isinstance(value, str) and len(value) > 0:
                return True

        return True  # Default to valid for text fields

    def get_template_names(self) -> List[str]:
        """Get list of available template names"""
        return list(self.templates_cache.keys())

    def get_template_description(self, template_name: str) -> str:
        """Get human-readable description of a template"""
        descriptions = {
            "product_seminar_application": "제품설명회 신청서 - 제품 설명회 개최를 신청하는 문서",
            "product_seminar_report": "제품설명회 결과보고서 - 제품 설명회 진행 후 결과를 보고하는 문서"
        }
        return descriptions.get(template_name, f"{template_name} 문서")