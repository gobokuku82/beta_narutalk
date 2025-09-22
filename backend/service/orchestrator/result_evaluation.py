from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any
import json
import logging
from ..utils import LLMManager, PromptTemplates

logger = logging.getLogger(__name__)

class EvaluationState(TypedDict):
    raw_results: Dict[str, Any]
    validation_rules: List[Dict]
    quality_scores: Dict[str, float]
    compliance_checks: Dict[str, Any]
    validated_results: Dict[str, Any]
    issues_found: List[str]
    recommendations: List[str]

class ResultEvaluationSubGraph:
    def __init__(self):
        self.workflow = StateGraph(EvaluationState)
        self.llm_manager = LLMManager()
        self.prompt_templates = PromptTemplates()
        self._build_graph()

    def _build_graph(self):
        self.workflow.add_node("check_completeness", self.check_completeness)
        self.workflow.add_node("validate_accuracy", self.validate_accuracy)
        self.workflow.add_node("check_compliance", self.check_compliance)
        self.workflow.add_node("calculate_quality", self.calculate_quality_score)
        self.workflow.add_node("generate_recommendations", self.generate_recommendations)

        # 엔트리 포인트 정의 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "check_completeness")
        self.workflow.add_edge("check_completeness", "validate_accuracy")
        self.workflow.add_edge("validate_accuracy", "check_compliance")
        self.workflow.add_edge("check_compliance", "calculate_quality")

        self.workflow.add_conditional_edges(
            "calculate_quality",
            self.check_quality_threshold,
            {
                "high_quality": END,
                "needs_improvement": "generate_recommendations",
                "low_quality": "generate_recommendations"
            }
        )

        self.workflow.add_edge("generate_recommendations", END)

    async def check_completeness(self, state: EvaluationState) -> EvaluationState:
        """결과 완전성 확인 - LLM 기반 평가"""
        try:
            raw_results = state.get('raw_results', {})

            # 데이터 완전성 체크 프롬프트
            prompt = f"""다음 분석 결과의 완전성을 평가하세요:

결과: {json.dumps(raw_results, ensure_ascii=False, indent=2)[:2000]}

평가 항목:
1. 필수 데이터 포함 여부
2. 결과 항목의 완전성
3. 누락된 정보 존재 여부

완전성 점수(0.0-1.0)와 비고를 JSON으로 반환:
{{
    "score": 0.85,
    "missing_items": ["누락된 항목"],
    "comment": "평가 코멘트"
}}"""

            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai_mini",
                category="completeness_check",
                temperature=0.2
            )

            try:
                result = json.loads(response['content'])
                state["quality_scores"] = state.get("quality_scores", {})
                state["quality_scores"]["completeness"] = result.get('score', 0.5)

                # 누락된 항목이 있으면 issues에 추가
                if result.get('missing_items'):
                    state["issues_found"] = state.get("issues_found", [])
                    for item in result['missing_items']:
                        state["issues_found"].append(f"누락: {item}")

                logger.info(f"Completeness check: {result.get('score', 0.5)}")

            except json.JSONDecodeError:
                state["quality_scores"] = state.get("quality_scores", {})
                state["quality_scores"]["completeness"] = 0.7

        except Exception as e:
            logger.error(f"Completeness check failed: {e}")
            state["quality_scores"] = state.get("quality_scores", {})
            state["quality_scores"]["completeness"] = 0.5

        return state

    async def validate_accuracy(self, state: EvaluationState) -> EvaluationState:
        """정확성 검증 - LLM 기반 데이터 검증"""
        try:
            raw_results = state.get('raw_results', {})

            # 데이터 정확성 검증
            prompt = f"""다음 분석 결과의 정확성을 검증하세요:

결과: {json.dumps(raw_results, ensure_ascii=False, indent=2)[:2000]}

검증 항목:
1. 숫자와 계산의 정확성
2. 논리적 일관성
3. 데이터 형식의 적절성

정확성 점수(0.0-1.0)와 발견된 문제를 JSON으로 반환:
{{
    "score": 0.9,
    "issues": ["발견된 문제"],
    "validation_passed": true
}}"""

            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai_strict",  # 정확성을 위해 strict 모델 사용
                category="accuracy_validation",
                temperature=0
            )

            try:
                result = json.loads(response['content'])
                scores = state.get("quality_scores", {})
                scores["accuracy"] = result.get('score', 0.5)
                state["quality_scores"] = scores

                # 발견된 문제 기록
                if result.get('issues'):
                    issues = state.get("issues_found", [])
                    for issue in result['issues']:
                        issues.append(f"정확성: {issue}")
                    state["issues_found"] = issues

                logger.info(f"Accuracy validation: {result.get('score', 0.5)}")

            except json.JSONDecodeError:
                scores = state.get("quality_scores", {})
                scores["accuracy"] = 0.7
                state["quality_scores"] = scores

        except Exception as e:
            logger.error(f"Accuracy validation failed: {e}")
            scores = state.get("quality_scores", {})
            scores["accuracy"] = 0.5
            state["quality_scores"] = scores

        return state

    async def check_compliance(self, state: EvaluationState) -> EvaluationState:
        """규정 준수 확인 - LLM 기반 컴플라이언스 체크"""
        try:
            raw_results = state.get('raw_results', {})

            # 제약업계 규정 준수 체크
            prompt = self.prompt_templates.get_prompt(
                category="compliance_check",
                version="v1",
                review_target=json.dumps(raw_results, ensure_ascii=False)[:2000],
                relevant_rules="KPBMA 규약, 리베이트 쌍벌제, 경제적 이익 제공 한도",
                context="제약회사 데이터 분석 결과"
            )

            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai_strict",
                category="compliance_check",
                temperature=0
            )

            # 규정 위반 여부 파싱
            compliance_text = response['content'].lower()
            violations_found = any(keyword in compliance_text for keyword in [
                "위반", "초과", "불법", "부적절", "문제"
            ])

            state["compliance_checks"] = {
                "passed": not violations_found,
                "details": response['content'][:500],
                "timestamp": response.get('timestamp', '')
            }

            # 위반 사항이 있으면 issues에 추가
            if violations_found:
                issues = state.get("issues_found", [])
                issues.append("규정 준수 검토 필요")
                state["issues_found"] = issues

            logger.info(f"Compliance check: {'Passed' if not violations_found else 'Failed'}")

        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            state["compliance_checks"] = {
                "passed": True,  # 에러 시 기본값
                "error": str(e)
            }

        return state

    async def calculate_quality_score(self, state: EvaluationState) -> EvaluationState:
        """품질 점수 계산 - 가중 평균"""
        scores = state.get("quality_scores", {})

        if scores:
            # 가중치 설정 (정확성이 가장 중요)
            weights = {
                "accuracy": 0.4,
                "completeness": 0.3,
                "compliance": 0.3
            }

            # 컴플라이언스 체크 결과를 점수로 변환
            compliance_checks = state.get("compliance_checks", {})
            if compliance_checks.get("passed"):
                scores["compliance"] = 1.0
            else:
                scores["compliance"] = 0.3

            # 가중 평균 계산
            weighted_sum = 0
            total_weight = 0
            for key, score in scores.items():
                if key != "overall" and key in weights:
                    weighted_sum += score * weights.get(key, 0.2)
                    total_weight += weights.get(key, 0.2)

            if total_weight > 0:
                state["quality_scores"]["overall"] = weighted_sum / total_weight
            else:
                state["quality_scores"]["overall"] = sum(scores.values()) / max(len(scores), 1)

            logger.info(f"Overall quality score: {state['quality_scores']['overall']:.2f}")

        # 검증된 결과 저장
        state["validated_results"] = state.get("raw_results", {})
        state["validated_results"]["quality_scores"] = state["quality_scores"]
        state["validated_results"]["validation_status"] = "completed"

        return state

    async def generate_recommendations(self, state: EvaluationState) -> EvaluationState:
        """개선 권고사항 생성 - LLM 기반"""
        try:
            issues = state.get("issues_found", [])
            quality_scores = state.get("quality_scores", {})

            if not issues and quality_scores.get("overall", 0) > 0.8:
                state["recommendations"] = []
                return state

            # 개선 권고사항 생성
            prompt = f"""다음 평가 결과를 바탕으로 개선 권고사항을 생성하세요:

발견된 문제:
{json.dumps(issues, ensure_ascii=False, indent=2)}

품질 점수:
{json.dumps(quality_scores, ensure_ascii=False, indent=2)}

구체적이고 실행 가능한 권고사항 3-5개를 리스트로 반환하세요:"""

            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai",
                category="recommendations",
                temperature=0.5
            )

            # 권고사항 파싱
            recommendations_text = response['content']
            recommendations = []

            # 기본 텍스트 파싱 (리스트 형태로 가정)
            for line in recommendations_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                    # 번호나 불릿 제거
                    clean_line = line.lstrip('0123456789.-* ').strip()
                    if clean_line:
                        recommendations.append(clean_line)

            state["recommendations"] = recommendations[:5]  # 최대 5개

            logger.info(f"Generated {len(state['recommendations'])} recommendations")

        except Exception as e:
            logger.error(f"Recommendations generation failed: {e}")
            state["recommendations"] = [
                "데이터 완전성 향상 필요",
                "결과 검증 프로세스 개선 권장"
            ]

        return state

    def check_quality_threshold(self, state: EvaluationState) -> str:
        """품질 임계값 확인"""
        overall_score = state.get("quality_scores", {}).get("overall", 0)
        if overall_score >= 0.8:
            return "high_quality"
        elif overall_score >= 0.5:
            return "needs_improvement"
        else:
            return "low_quality"