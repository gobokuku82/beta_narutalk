"""
Default Value Generator for Document Creation
Generates dynamic, contextual default values instead of hardcoded ones
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json
import random
import logging

logger = logging.getLogger(__name__)


class DefaultValueGenerator:
    """Generate intelligent default values for missing document fields"""

    def __init__(self, defaults_path: Optional[Path] = None):
        """
        Initialize with defaults configuration

        Args:
            defaults_path: Path to document_defaults.json
        """
        if defaults_path is None:
            defaults_path = Path("./backend/service/templates/document_defaults.json")

        self.defaults = self._load_defaults(defaults_path)
        self.used_values_cache = {}  # Track recently used values to avoid repetition

    def _load_defaults(self, path: Path) -> Dict[str, Any]:
        """Load default values from JSON file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Defaults file not found at {path}, using empty defaults")
            return {}
        except Exception as e:
            logger.error(f"Error loading defaults: {e}")
            return {}

    def get_date(self, context: Optional[Dict] = None, offset_days: int = 7) -> str:
        """
        Generate appropriate date and time

        Args:
            context: Optional context for date selection
            offset_days: Days to add from today

        Returns:
            Formatted date string
        """
        # Base date calculation
        base_date = datetime.now() + timedelta(days=offset_days)

        # Skip weekends
        while base_date.weekday() in [5, 6]:  # Saturday = 5, Sunday = 6
            base_date += timedelta(days=1)

        # Select appropriate time slot
        time_slots = self.defaults.get("time_slots", ["14:00"])

        # Prefer afternoon slots for seminars
        afternoon_slots = [t for t in time_slots if int(t.split(":")[0]) >= 14]
        selected_time = random.choice(afternoon_slots if afternoon_slots else time_slots)

        return f"{base_date.strftime('%Y-%m-%d')} {selected_time}"

    def get_location(self, context: Optional[Dict] = None) -> str:
        """
        Get a location from the pool

        Args:
            context: Optional context for location selection

        Returns:
            Location string
        """
        locations = self.defaults.get("locations", ["서울 강남구 회의실"])

        # Avoid recently used locations
        cache_key = "recent_locations"
        if cache_key not in self.used_values_cache:
            self.used_values_cache[cache_key] = []

        available = [loc for loc in locations if loc not in self.used_values_cache[cache_key]]
        if not available:
            # Reset cache if all locations have been used
            self.used_values_cache[cache_key] = []
            available = locations

        selected = random.choice(available)
        self.used_values_cache[cache_key].append(selected)

        # Keep only last 3 used locations in cache
        if len(self.used_values_cache[cache_key]) > 3:
            self.used_values_cache[cache_key].pop(0)

        return selected

    def get_product_name(self, context: Optional[Dict] = None) -> str:
        """
        Get a product name from the pool

        Args:
            context: Optional context

        Returns:
            Product name
        """
        products = self.defaults.get("common_products", ["신제품"])
        return random.choice(products)

    def get_attendees_count(self, size: str = "medium") -> str:
        """
        Get expected/actual attendee count

        Args:
            size: small, medium, or large

        Returns:
            Attendee count string
        """
        ranges = self.defaults.get("attendee_ranges", {})
        if size in ranges:
            min_val = ranges[size]["min"]
            max_val = ranges[size]["max"]
            count = random.randint(min_val, max_val)
        else:
            count = random.randint(15, 30)

        return f"{count}명"

    def get_staff_list(self, count: int = 3, department: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get a list of staff members

        Args:
            count: Number of staff members needed
            department: Optional department filter

        Returns:
            List of staff dictionaries
        """
        staff_pool = self.defaults.get("staff_pool", [])

        if department:
            filtered = [s for s in staff_pool if s.get("department") == department]
            if filtered:
                staff_pool = filtered

        # Ensure we don't request more staff than available
        count = min(count, len(staff_pool))

        # Random selection without replacement
        selected_staff = random.sample(staff_pool, count)

        # Add numbering
        result = []
        for i, staff in enumerate(selected_staff, 1):
            result.append({
                "no": str(i),
                "team": staff.get("team", ""),
                "name": staff.get("name", ""),
                "signature": ""
            })

        return result

    def get_hcp_list(self, count: int = 3) -> List[Dict[str, str]]:
        """
        Get a list of healthcare professionals

        Args:
            count: Number of HCPs needed

        Returns:
            List of HCP dictionaries
        """
        hcp_pool = self.defaults.get("hcp_pool", [])
        result = []

        for i in range(min(count, len(hcp_pool))):
            hospital_data = random.choice(hcp_pool)
            name = random.choice(hospital_data["names"])

            result.append({
                "no": str(i + 1),
                "hospital": hospital_data["hospital"],
                "name": name,
                "signature": ""
            })

        return result

    def get_purpose(self, context: Optional[Dict] = None) -> str:
        """Get a purpose statement"""
        purposes = self.defaults.get("purposes", ["제품 설명회"])
        return random.choice(purposes)

    def get_main_content(self, context: Optional[Dict] = None) -> str:
        """Get main content outline"""
        contents = self.defaults.get("main_contents", ["1. 제품 소개\n2. Q&A"])
        return random.choice(contents)

    def get_budget_details(self, size: str = "medium") -> Dict[str, str]:
        """
        Get budget details based on event size

        Args:
            size: small, medium, or large

        Returns:
            Budget details dictionary
        """
        templates = self.defaults.get("budget_templates", {})

        if size in templates:
            budget = templates[size]
        else:
            budget = templates.get("medium", {
                "total": 2000000,
                "lecture": 600000,
                "meal": 500000,
                "venue": 400000,
                "misc": 500000
            })

        return {
            "payment_details": f"강의료: {budget['lecture']:,}원\n식사비: {budget['meal']:,}원\n장소대여: {budget['venue']:,}원",
            "budget_usage": f"총 예산: {budget['total']:,}원\n사용액: {sum([budget['lecture'], budget['meal'], budget['venue']]):,}원\n잔액: {budget['misc']:,}원"
        }

    def get_result_statement(self, context: Optional[Dict] = None) -> str:
        """Get a result statement for reports"""
        results = [
            "성공적으로 진행됨. 참석자 만족도 높음.",
            "원활하게 진행됨. 활발한 질의응답이 있었음.",
            "계획대로 진행됨. 참석자들의 관심도가 높았음.",
            "성공적으로 완료됨. 긍정적인 피드백을 받음.",
            "잘 진행됨. 목표를 달성함."
        ]
        return random.choice(results)

    def generate_field_value(self, field_name: str, field_type: str = "text", context: Optional[Dict] = None) -> Any:
        """
        Generate appropriate value for any field

        Args:
            field_name: Name of the field
            field_type: Type of the field
            context: Optional context

        Returns:
            Generated value
        """
        # Map field names to generation methods
        generators = {
            "date": lambda: self.get_date(context),
            "location": lambda: self.get_location(context),
            "product_name": lambda: self.get_product_name(context),
            "expected_attendees": lambda: self.get_attendees_count("medium"),
            "actual_attendees": lambda: self.get_attendees_count("medium"),
            "purpose": lambda: self.get_purpose(context),
            "main_content": lambda: self.get_main_content(context),
            "result": lambda: self.get_result_statement(context),
            "staff_list": lambda: self.get_staff_list(),
            "hcp_list": lambda: self.get_hcp_list(),
            "seminar_type": lambda: "단일",
            "pm_attendance": lambda: random.choice(["참석", "불참"])
        }

        # Check for budget-related fields
        if field_name in ["payment_details", "budget_usage"]:
            budget = self.get_budget_details()
            return budget.get(field_name, "")

        # Use specific generator if available
        if field_name in generators:
            return generators[field_name]()

        # Default based on field type
        if field_type == "select":
            return "기본값"
        elif field_type == "number":
            return random.randint(10, 100)
        else:
            return f"{field_name} 정보"

    def reset_cache(self):
        """Reset the used values cache"""
        self.used_values_cache = {}
        logger.info("Value cache reset")