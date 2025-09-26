"""
Document Query Analyzer with GPT-4o-mini
Analyzes natural language queries to extract document intent and data
"""

from typing import Dict, Any, List, Optional
import os
import json
import logging
from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class DocumentQueryAnalyzer:
    """Analyzes natural language queries using GPT-4o-mini"""

    def __init__(self):
        """Initialize with OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        logger.info(f"Initialized DocumentQueryAnalyzer with model: {self.model}")

    async def analyze_query(self, query: str, available_templates: List[str]) -> Dict[str, Any]:
        """
        Analyze a natural language query to extract document intent and data

        Args:
            query: User's natural language query
            available_templates: List of available template names

        Returns:
            Dictionary containing:
            - intent: Detected document type/template
            - extracted_data: Data extracted from the query
            - missing_fields: Fields that need to be collected
            - confidence: Confidence score
        """
        try:
            # Create prompt for GPT-4o-mini
            system_prompt = f"""당신은 문서 생성 시스템의 쿼리 분석 전문가입니다.
사용자의 자연어 요청을 분석하여 필요한 문서 유형과 데이터를 추출합니다.

사용 가능한 문서 템플릿:
1. product_seminar_application - 제품설명회 신청서
2. product_seminar_report - 제품설명회 결과보고서

다음 형식으로 JSON 응답을 제공하세요:
{{
    "intent": "템플릿 이름 (위 목록에서 선택)",
    "confidence": 0.0-1.0 사이의 신뢰도,
    "extracted_data": {{
        "필드명": "추출된 값"
    }},
    "context_clues": ["쿼리에서 발견된 단서들"]
}}

주요 필드들:
- seminar_type: 단일/복수
- pm_attendance: 참석/불참
- date: 일시
- location: 장소
- product_name: 제품명
- expected_attendees: 예정 인원
- actual_attendees: 실제 인원
- purpose: 목적
- result: 결과
- staff_list: 직원 명단
- hcp_list: 의료진 명단"""

            user_prompt = f"다음 요청을 분석하세요: {query}"

            # Call GPT-4o-mini
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            # Parse response
            result = json.loads(response.choices[0].message.content)

            # Validate and enhance result
            analysis = {
                "intent": result.get("intent", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "extracted_data": result.get("extracted_data", {}),
                "context_clues": result.get("context_clues", []),
                "original_query": query,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Query analyzed with intent: {analysis['intent']} (confidence: {analysis['confidence']})")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "extracted_data": {},
                "error": str(e)
            }

    async def extract_field_value(self, user_response: str, field: Dict[str, Any]) -> Any:
        """
        Extract a specific field value from user response using LLM

        Args:
            user_response: User's response to field prompt
            field: Field definition

        Returns:
            Extracted and validated value
        """
        try:
            field_type = field.get("type", "text")
            field_name = field.get("name")
            field_label = field.get("label", field_name)

            # Create extraction prompt
            system_prompt = f"""당신은 데이터 추출 전문가입니다.
사용자 응답에서 '{field_label}' 필드의 값을 추출하세요.

필드 정보:
- 이름: {field_name}
- 유형: {field_type}
- 라벨: {field_label}
"""

            if field_type == "select" and "options" in field:
                system_prompt += f"- 가능한 값: {', '.join(field['options'])}\n"
                system_prompt += "사용자 응답과 가장 일치하는 옵션을 선택하세요.\n"

            system_prompt += """
JSON 형식으로 응답:
{
    "value": "추출된 값",
    "confidence": 0.0-1.0,
    "normalized": true/false
}"""

            # Call GPT-4o-mini
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"사용자 응답: {user_response}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            extracted_value = result.get("value")

            # Type conversion based on field type
            if field_type == "number" and extracted_value:
                try:
                    # Remove non-numeric characters and convert
                    cleaned = ''.join(c for c in str(extracted_value) if c.isdigit() or c == '.')
                    extracted_value = float(cleaned) if '.' in cleaned else int(cleaned)
                except:
                    pass

            logger.info(f"Extracted {field_name}: {extracted_value}")
            return extracted_value

        except Exception as e:
            logger.error(f"Error extracting field value: {e}")
            # Return raw response as fallback
            return user_response

    async def generate_field_prompt(self, field: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Generate a context-aware prompt for collecting a field

        Args:
            field: Field definition
            context: Current context with already collected data

        Returns:
            Natural language prompt for the field
        """
        try:
            # Create prompt generation request
            system_prompt = """당신은 친절한 문서 작성 도우미입니다.
사용자에게 필요한 정보를 요청하는 자연스럽고 친절한 메시지를 생성합니다.
존댓말을 사용하고, 예시를 포함하면 좋습니다."""

            field_info = f"""
필드 정보:
- 이름: {field.get('name')}
- 라벨: {field.get('label')}
- 유형: {field.get('type')}
"""

            if field.get("type") == "select" and "options" in field:
                field_info += f"- 선택지: {', '.join(field['options'])}\n"

            if context:
                field_info += f"\n이미 수집된 정보:\n"
                for key, value in context.items():
                    if value:
                        field_info += f"- {key}: {value}\n"

            user_prompt = f"다음 필드에 대한 친절한 요청 메시지를 생성하세요:\n{field_info}"

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )

            prompt = response.choices[0].message.content.strip()
            return prompt

        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            # Fallback to simple prompt
            return f"{field.get('label', field.get('name'))}를 입력해주세요."

    async def identify_missing_fields(
        self,
        required_fields: List[Dict[str, Any]],
        collected_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify which required fields are missing

        Args:
            required_fields: List of required field definitions
            collected_data: Already collected data

        Returns:
            List of missing field definitions
        """
        missing = []
        for field in required_fields:
            field_name = field.get("name")
            if field_name and field_name not in collected_data:
                missing.append(field)
            elif field_name and not collected_data.get(field_name):
                missing.append(field)

        logger.info(f"Identified {len(missing)} missing fields")
        return missing

    async def generate_document_content(
        self,
        template_name: str,
        data: Dict[str, Any],
        section: Optional[str] = None
    ) -> str:
        """
        Generate document content using LLM

        Args:
            template_name: Name of the document template
            data: Collected data for the document
            section: Specific section to generate (optional)

        Returns:
            Generated content
        """
        try:
            # Prepare context
            doc_descriptions = {
                "product_seminar_application": "제품설명회 신청서",
                "product_seminar_report": "제품설명회 결과보고서"
            }

            doc_type = doc_descriptions.get(template_name, template_name)

            # Create generation prompt
            system_prompt = f"""당신은 전문적인 비즈니스 문서 작성 전문가입니다.
{doc_type}의 내용을 작성합니다.

문서 작성 지침:
1. 전문적이고 공식적인 어조 사용
2. 명확하고 간결한 표현
3. 필요한 모든 정보 포함
4. 적절한 섹션 구조 유지"""

            if section:
                system_prompt += f"\n\n특정 섹션: {section}"

            # Prepare data description
            data_desc = json.dumps(data, ensure_ascii=False, indent=2)
            user_prompt = f"다음 정보를 바탕으로 {doc_type} 내용을 작성하세요:\n\n{data_desc}"

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )

            content = response.choices[0].message.content.strip()
            logger.info(f"Generated content for {template_name} ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return ""

    async def summarize_document(self, content: str, max_length: int = 200) -> str:
        """
        Generate a summary of document content

        Args:
            content: Full document content
            max_length: Maximum length of summary

        Returns:
            Summary text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"문서 내용을 {max_length}자 이내로 요약하세요."},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=max_length
            )

            summary = response.choices[0].message.content.strip()
            return summary

        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return content[:max_length] + "..." if len(content) > max_length else content