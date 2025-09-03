"""
Compliance Check Agent - 규정위반검색 에이전트
약사법, KGSP, 리베이트 등 규정 준수 검증
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from loguru import logger
import json
from pathlib import Path
from datetime import datetime

from app.langgraph.state import AgentState
from app.core.config import settings


class ComplianceAgent:
    """규정 검사 전문 에이전트"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,  # gpt-4o
            temperature=0.0,  # 규정 검사는 정확성이 중요
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # 규정 DB 경로
        self.rule_db_path = settings.RULE_DB_DIR
        
        # 규정 데이터 초기화
        self._initialize_regulations()
        
        # 도구 등록
        self.tools = {
            "check_regulation": self.check_regulation,
            "analyze_risk": self.analyze_risk,
            "audit_content": self.audit_content,
            "validate_promotion": self.validate_promotion
        }
        
        # 위험 레벨 정의
        self.risk_levels = {
            "LOW": {"score": 0.0, "color": "green"},
            "MEDIUM": {"score": 0.3, "color": "yellow"},
            "HIGH": {"score": 0.6, "color": "orange"},
            "CRITICAL": {"score": 0.8, "color": "red"}
        }
    
    def _initialize_regulations(self):
        """규정 데이터 초기화"""
        # 규정 파일 생성
        regulations = {
            "kgsp_rules.json": {
                "title": "KGSP (Korea Good Supply Practice) 규정",
                "version": "2024.1",
                "rules": [
                    {
                        "id": "KGSP-001",
                        "category": "샘플 제공",
                        "description": "의약품 샘플은 의료전문가에게만 제공 가능",
                        "penalty": "경고 또는 과태료"
                    },
                    {
                        "id": "KGSP-002",
                        "category": "경제적 이익",
                        "description": "1회 10만원, 연간 100만원 초과 경제적 이익 제공 금지",
                        "penalty": "영업정지 또는 과징금"
                    },
                    {
                        "id": "KGSP-003",
                        "category": "학술대회",
                        "description": "학술대회 지원은 사전 신고 필요",
                        "penalty": "시정명령"
                    }
                ]
            },
            "rebate_rules.json": {
                "title": "리베이트 쌍벌제 규정",
                "version": "2024.1",
                "prohibited_items": [
                    "현금 또는 현금성 물품 제공",
                    "개인적 용도의 물품 제공",
                    "접대 목적의 식사 제공 (1인 3만원 초과)",
                    "골프, 유흥업소 등 접대",
                    "개인 여행 경비 지원"
                ],
                "allowed_items": [
                    "제품 설명을 위한 소액 식사 (1인 3만원 이하)",
                    "학술 목적의 도서 제공",
                    "의학 학술대회 등록비 지원",
                    "임상시험 관련 정당한 대가"
                ]
            },
            "promotion_guidelines.json": {
                "title": "의약품 프로모션 가이드라인",
                "version": "2024.1",
                "requirements": [
                    "허가사항 범위 내 정보 제공",
                    "과학적 근거 기반 설명",
                    "부작용 정보 명시",
                    "비교 광고 시 객관적 데이터 제시"
                ],
                "prohibited": [
                    "미허가 적응증 프로모션",
                    "과장된 효능 주장",
                    "경쟁사 제품 비방",
                    "의료진 개인정보 무단 수집"
                ]
            }
        }
        
        # 규정 파일 저장
        for filename, content in regulations.items():
            filepath = self.rule_db_path / filename
            if not filepath.exists():
                filepath.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
                logger.info(f"규정 파일 생성: {filename}")
    
    async def check_regulation(self, content: str, category: str = "general") -> Dict:
        """규정 위반 검사"""
        try:
            # 규정 데이터 로드
            kgsp_path = self.rule_db_path / "kgsp_rules.json"
            kgsp_rules = json.loads(kgsp_path.read_text(encoding="utf-8"))
            
            # LLM으로 규정 위반 검사
            prompt = f"""
            다음 내용이 KGSP 규정을 위반하는지 검사하세요:
            
            검사 대상: {content}
            카테고리: {category}
            
            KGSP 규정:
            {json.dumps(kgsp_rules['rules'], ensure_ascii=False)}
            
            위반 사항이 있다면 구체적으로 설명하고, 위험도를 평가하세요.
            응답 형식:
            - 위반 여부: (예/아니오)
            - 위반 규정: (규정 ID)
            - 설명: (상세 설명)
            - 위험도: (LOW/MEDIUM/HIGH/CRITICAL)
            """
            
            response = await self.llm.ainvoke(prompt)
            
            # 결과 파싱
            result = {
                "checked_content": content[:100] + "..." if len(content) > 100 else content,
                "category": category,
                "violation_found": "예" in response.content,
                "details": response.content,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"규정 검사 오류: {e}")
            return {"error": str(e)}
    
    async def analyze_risk(self, activity: str) -> Dict:
        """리베이트 위험도 분석"""
        try:
            # 리베이트 규정 로드
            rebate_path = self.rule_db_path / "rebate_rules.json"
            rebate_rules = json.loads(rebate_path.read_text(encoding="utf-8"))
            
            # 위험도 분석
            prompt = f"""
            다음 영업 활동의 리베이트 위험도를 분석하세요:
            
            활동: {activity}
            
            금지 사항:
            {json.dumps(rebate_rules['prohibited_items'], ensure_ascii=False)}
            
            허용 사항:
            {json.dumps(rebate_rules['allowed_items'], ensure_ascii=False)}
            
            위험도를 0-1 점수로 평가하고 이유를 설명하세요.
            """
            
            response = await self.llm.ainvoke(prompt)
            
            # 위험도 점수 추출 (간단한 휴리스틱)
            risk_score = 0.5  # 기본값
            if "금지" in response.content or "위반" in response.content:
                risk_score = 0.8
            elif "허용" in response.content:
                risk_score = 0.2
            
            # 위험 레벨 결정
            risk_level = "LOW"
            for level, info in self.risk_levels.items():
                if risk_score >= info["score"]:
                    risk_level = level
            
            return {
                "activity": activity,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "analysis": response.content,
                "recommendations": self._get_recommendations(risk_level)
            }
            
        except Exception as e:
            logger.error(f"위험도 분석 오류: {e}")
            return {"error": str(e)}
    
    async def audit_content(self, content: str, content_type: str = "promotion") -> Dict:
        """프로모션 자료 감사"""
        try:
            # 가이드라인 로드
            guidelines_path = self.rule_db_path / "promotion_guidelines.json"
            guidelines = json.loads(guidelines_path.read_text(encoding="utf-8"))
            
            # 내용 감사
            prompt = f"""
            다음 프로모션 자료를 의약품 프로모션 가이드라인에 따라 감사하세요:
            
            자료 내용: {content}
            자료 유형: {content_type}
            
            필수 요구사항:
            {json.dumps(guidelines['requirements'], ensure_ascii=False)}
            
            금지 사항:
            {json.dumps(guidelines['prohibited'], ensure_ascii=False)}
            
            문제점과 개선사항을 제시하세요.
            """
            
            response = await self.llm.ainvoke(prompt)
            
            return {
                "content_type": content_type,
                "audit_result": response.content,
                "compliance_status": "통과" if "문제없음" in response.content else "수정필요",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"감사 오류: {e}")
            return {"error": str(e)}
    
    async def validate_promotion(self, promotion_plan: Dict) -> Dict:
        """프로모션 계획 검증"""
        # 프로모션 계획의 각 요소 검증
        validation_results = []
        
        for item in promotion_plan.get("items", []):
            result = await self.check_regulation(
                json.dumps(item, ensure_ascii=False),
                "promotion"
            )
            validation_results.append(result)
        
        # 전체 평가
        violations_count = sum(1 for r in validation_results if r.get("violation_found"))
        
        return {
            "total_items": len(promotion_plan.get("items", [])),
            "violations_found": violations_count,
            "validation_results": validation_results,
            "overall_status": "승인" if violations_count == 0 else "재검토 필요"
        }
    
    def _get_recommendations(self, risk_level: str) -> List[str]:
        """위험도에 따른 권고사항"""
        recommendations = {
            "LOW": [
                "현재 활동은 규정 준수 범위 내입니다.",
                "지속적인 모니터링을 권장합니다."
            ],
            "MEDIUM": [
                "주의가 필요한 활동입니다.",
                "법무팀 사전 검토를 권장합니다.",
                "활동 내역을 문서화하세요."
            ],
            "HIGH": [
                "높은 위험도의 활동입니다.",
                "즉시 법무팀 검토가 필요합니다.",
                "대안 방법을 고려하세요."
            ],
            "CRITICAL": [
                "매우 위험한 활동입니다.",
                "즉시 중단하고 법무팀에 보고하세요.",
                "대체 방안을 마련해야 합니다."
            ]
        }
        
        return recommendations.get(risk_level, ["검토가 필요합니다."])
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """에이전트 처리 로직"""
        logger.info("규정검사 에이전트 처리 시작")
        
        # 최신 메시지 확인
        last_message = state["messages"][-1]
        user_request = last_message.get("content", "")
        
        # 규정 검사 수행
        result = await self.check_regulation(user_request, "general")
        
        # 위험도 분석
        risk_analysis = await self.analyze_risk(user_request)
        
        # 응답 생성
        response = f"""
규정 검사 결과:

📋 **검사 내용**: {user_request[:100]}...

⚖️ **규정 위반 여부**: {'위반 발견' if result.get('violation_found') else '위반 없음'}

🎯 **위험도 평가**:
- 점수: {risk_analysis.get('risk_score', 0):.2f} / 1.0
- 레벨: {risk_analysis.get('risk_level', 'UNKNOWN')}

💡 **권고사항**:
"""
        
        for rec in risk_analysis.get('recommendations', []):
            response += f"\n- {rec}"
        
        if result.get('details'):
            response += f"\n\n📝 **상세 분석**:\n{result['details'][:500]}"
        
        return {
            "messages": [{"role": "assistant", "content": response}],
            "agent_outputs": {
                "compliance": {
                    "regulation_check": result,
                    "risk_analysis": risk_analysis
                }
            },
            "next_agent": None
        }