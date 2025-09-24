"""
LLM Manager - Centralized LLM management for the service layer
Simplified version focused on intent analysis and planning
"""

import os
from typing import Dict, Any, Optional, List
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import json

load_dotenv()
logger = logging.getLogger(__name__)


class LLMManager:
    """Centralized LLM Manager for agent orchestration"""

    def __init__(self):
        """Initialize LLM clients"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # Different clients for different purposes
        self.clients = {
            # For intent analysis (more creative)
            "intent": ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=api_key,
                max_retries=2
            ),
            # For planning and reasoning (more deterministic)
            "planning": ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=api_key,
                max_retries=2
            ),
            # For general responses
            "general": ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.5,
                api_key=api_key,
                max_retries=2
            )
        }

        logger.info("LLMManager initialized successfully")

    async def analyze_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyze user intent and determine which agent(s) to use

        Args:
            query: User query in Korean

        Returns:
            Intent analysis result with agent routing
        """
        system_prompt = """You are an expert in analyzing user intent and routing to appropriate agents.

Available Agents with Detailed Descriptions:

1. search_agent
   - Description: Searches and retrieves information from HR database and organizational data
   - Functions: Employee search, department info, HR policies, organizational structure
   - Keywords: employee, staff, person, team, department, organization, HR, policy, rule
   - Examples: "김철수 직원 정보", "영업팀 구성원", "인사 규정", "조직도"

2. sales_analytics
   - Description: Analyzes sales performance, calculates statistics, and identifies trends
   - Functions: Sales analysis, performance metrics, trend analysis, ranking, statistics
   - Keywords: sales, revenue, performance, achievement, statistics, trend, analysis, ranking
   - Examples: "3월 실적 분석", "매출 통계", "실적 순위", "성장률 분석"

3. compliance_check
   - Description: Checks compliance with regulations and company policies
   - Functions: Policy compliance verification, violation detection, regulatory check
   - Keywords: compliance, regulation, policy, violation, check, verify, audit, rule
   - Examples: "규정 위반 확인", "정책 준수 여부", "감사 사항 검토"

4. document_generation
   - Description: Generates reports, documents, and formatted outputs
   - Functions: Report creation, document formatting, summary generation, template filling
   - Keywords: report, document, generate, create, write, format, summary, template
   - Examples: "월간 보고서 작성", "실적 요약 문서", "분석 리포트 생성"

Selection Rules:
- Analyze the Korean query carefully
- One query can require multiple agents (e.g., analyze sales AND generate report)
- Select agents based on actual functions needed, not just keywords
- Consider dependencies between agents

Respond in JSON format:
{
    "intent": "primary_intent_in_english",
    "agents": ["agent1", "agent2"],
    "confidence": 0.95,
    "entities": {
        "person": "name_if_exists",
        "period": "time_period",
        "type": "query_type"
    },
    "keywords": ["keyword1", "keyword2"],
    "reasoning": "brief explanation of why these agents were selected"
}"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"쿼리 분석: {query}")
            ]

            response = await self.clients["intent"].ainvoke(messages)

            # Log raw response for debugging
            logger.debug(f"Raw LLM response: {response.content}")

            # Parse JSON response
            try:
                # Clean response content - remove markdown code blocks if present
                content = response.content.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                result = json.loads(content)
                result["original_query"] = query
                logger.info(f"Intent analyzed: {result.get('intent')} with confidence {result.get('confidence')}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response was: {response.content}")

                # Return failure instead of fallback
                return {
                    "intent": "unknown",
                    "agents": [],  # Empty list - no agents selected
                    "confidence": 0.0,
                    "entities": {},
                    "keywords": query.split(),
                    "error": "Failed to parse LLM response",
                    "original_query": query
                }

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return {
                "intent": "unknown",
                "agents": ["search_agent"],
                "confidence": 0.0,
                "error": str(e),
                "original_query": query
            }

    async def create_execution_plan(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an execution plan based on intent analysis

        Args:
            intent_result: Result from analyze_intent

        Returns:
            Execution plan with steps
        """
        agents = intent_result.get("agents", [])
        entities = intent_result.get("entities", {})

        system_prompt = """당신은 작업 실행 계획을 수립하는 전문가입니다.
주어진 의도 분석 결과를 바탕으로 실행 계획을 수립하세요.

JSON 형식으로 응답:
{
    "steps": [
        {
            "order": 1,
            "agent": "agent_name",
            "action": "action_description",
            "input": {"key": "value"},
            "expected_output": "description"
        }
    ],
    "parallel_possible": true/false,
    "estimated_time_seconds": 10
}"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"""
의도: {intent_result.get('intent')}
에이전트: {agents}
엔티티: {entities}
쿼리: {intent_result.get('original_query')}

실행 계획을 수립하세요.""")
            ]

            response = await self.clients["planning"].ainvoke(messages)

            try:
                plan = json.loads(response.content)
                logger.info(f"Execution plan created with {len(plan.get('steps', []))} steps")
                return plan
            except json.JSONDecodeError:
                logger.warning("Failed to parse plan as JSON, using simple plan")
                return {
                    "steps": [
                        {
                            "order": 1,
                            "agent": agents[0] if agents else "search_agent",
                            "action": "process_query",
                            "input": {"query": intent_result.get('original_query')},
                            "expected_output": "results"
                        }
                    ],
                    "parallel_possible": False,
                    "estimated_time_seconds": 5
                }

        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            return {
                "steps": [],
                "error": str(e)
            }

    async def generate_response(
        self,
        query: str,
        agent_results: Dict[str, Any],
        response_type: str = "general"
    ) -> str:
        """
        Generate a natural language response from agent results

        Args:
            query: Original user query
            agent_results: Results from agent execution
            response_type: Type of response needed

        Returns:
            Natural language response
        """
        system_prompt = """당신은 친절한 업무 도우미입니다.
에이전트 실행 결과를 바탕으로 사용자에게 명확하고 유용한 답변을 제공하세요.
한국어로 자연스럽게 응답하세요."""

        try:
            # Format agent results for presentation
            formatted_results = self._format_results(agent_results)

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"""
사용자 질문: {query}

실행 결과:
{formatted_results}

위 결과를 바탕으로 사용자에게 답변을 작성하세요.""")
            ]

            response = await self.clients["general"].ainvoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return f"죄송합니다. 결과를 처리하는 중 오류가 발생했습니다: {str(e)}"

    def _format_results(self, results: Dict[str, Any]) -> str:
        """Format agent results for presentation"""
        if not results:
            return "결과 없음"

        formatted = []

        # Format based on result type
        if "final_results" in results:
            final = results["final_results"]
            if "results" in final:
                formatted.append(f"검색 결과: {len(final['results'])}건")
                for i, item in enumerate(final["results"][:3], 1):
                    formatted.append(f"  {i}. {item.get('type', 'N/A')}: {item.get('content', {})}")

        if "final_report" in results:
            report = results["final_report"]
            if "statistics" in report:
                stats = report["statistics"]
                formatted.append("통계 정보:")
                formatted.append(f"  - 총 매출: {stats.get('total_sales', 0):,.0f}")
                formatted.append(f"  - 평균: {stats.get('average_sale', 0):,.0f}")
            if "insights" in report:
                formatted.append("인사이트:")
                for insight in report["insights"][:3]:
                    formatted.append(f"  - {insight}")

        return "\n".join(formatted) if formatted else str(results)


# Singleton instance
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """Get or create LLMManager singleton instance"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager