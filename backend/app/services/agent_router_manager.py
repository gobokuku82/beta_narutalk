"""
4개 전문 에이전트 라우터 매니저

질문을 받아서 적절한 전문 에이전트로 라우팅하는 시스템입니다.
- 문서검색 에이전트
- 업무문서 초안작성 에이전트  
- 실적분석 에이전트
- 거래처분석 에이전트
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from ..agents import (
    DocumentSearchAgent,
    DocumentDraftAgent, 
    PerformanceAnalysisAgent,
    ClientAnalysisAgent,
    AgentContext,
    AgentResult,
    AgentAction
)

logger = logging.getLogger(__name__)

class AgentRouterManager:
    """4개 전문 에이전트 라우터 매니저"""
    
    def __init__(self):
        self.agents = {}
        self.routing_history = []
        self.max_agent_switches = 3  # 최대 에이전트 전환 횟수
        
    def initialize_agents(self, **services):
        """4개 전문 에이전트 초기화"""
        try:
            # 1. 문서검색 에이전트
            self.agents["document_search"] = DocumentSearchAgent()
            self.agents["document_search"].set_services(**services)
            
            # 2. 업무문서 초안작성 에이전트
            self.agents["document_draft"] = DocumentDraftAgent()
            self.agents["document_draft"].set_services(**services)
            
            # 3. 실적분석 에이전트
            self.agents["performance_analysis"] = PerformanceAnalysisAgent()
            self.agents["performance_analysis"].set_services(**services)
            
            # 4. 거래처분석 에이전트
            self.agents["client_analysis"] = ClientAnalysisAgent()
            self.agents["client_analysis"].set_services(**services)
            
            logger.info("4개 전문 에이전트 초기화 완료")
            
        except Exception as e:
            logger.error(f"에이전트 초기화 실패: {str(e)}")
            raise
    
    async def route_message(self, message: str, user_id: str, session_id: str, 
                          conversation_history: List[Dict[str, str]] = None,
                          user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """메시지를 적절한 에이전트로 라우팅"""
        try:
            # 컨텍스트 생성
            context = AgentContext(
                current_message=message,
                user_id=user_id,
                session_id=session_id,
                conversation_history=conversation_history or [],
                current_agent="",
                agent_switches=0,
                user_preferences=user_preferences or {}
            )
            
            # 최적 에이전트 선택
            selected_agent_id, confidence = await self.select_best_agent(context)
            
            if not selected_agent_id:
                return {
                    "error": "적절한 에이전트를 찾을 수 없습니다.",
                    "suggestions": await self.get_general_suggestions()
                }
            
            # 선택된 에이전트로 처리
            context.current_agent = selected_agent_id
            result = await self.process_with_agent(context, selected_agent_id)
            
            # 라우팅 기록 저장
            self.routing_history.append({
                "message": message,
                "selected_agent": selected_agent_id,
                "confidence": confidence,
                "result_action": result.action.value if result else None,
                "timestamp": context.current_message  # 실제로는 datetime 사용
            })
            
            return {
                "agent_id": selected_agent_id,
                "agent_name": self.get_agent_name(selected_agent_id),
                "confidence": confidence,
                "response": result.response if result else "처리 중 오류가 발생했습니다.",
                "action": result.action.value if result else "error",
                "metadata": result.metadata if result else {},
                "sources": result.sources if result else [],
                "next_agent": result.next_agent if result and hasattr(result, 'next_agent') else None
            }
            
        except Exception as e:
            logger.error(f"메시지 라우팅 실패: {str(e)}")
            return {
                "error": f"메시지 처리 중 오류가 발생했습니다: {str(e)}",
                "suggestions": await self.get_general_suggestions()
            }
    
    async def select_best_agent(self, context: AgentContext) -> Tuple[Optional[str], float]:
        """최적의 에이전트 선택"""
        try:
            agent_scores = {}
            
            # 각 에이전트의 신뢰도 계산
            for agent_id, agent in self.agents.items():
                try:
                    confidence = await agent.can_handle(context)
                    priority_weight = agent.priority / 10.0  # 우선순위를 0.1~1.0 범위로 정규화
                    
                    # 최종 점수 = 신뢰도 70% + 우선순위 30%
                    final_score = (confidence * 0.7) + (priority_weight * 0.3)
                    agent_scores[agent_id] = {
                        "confidence": confidence,
                        "priority": agent.priority,
                        "final_score": final_score
                    }
                    
                    logger.debug(f"{agent_id}: confidence={confidence:.3f}, priority={agent.priority}, score={final_score:.3f}")
                    
                except Exception as e:
                    logger.warning(f"{agent_id} 신뢰도 계산 실패: {str(e)}")
                    agent_scores[agent_id] = {"confidence": 0.0, "priority": 0, "final_score": 0.0}
            
            # 최고 점수 에이전트 선택
            if not agent_scores:
                return None, 0.0
            
            best_agent = max(agent_scores.keys(), key=lambda k: agent_scores[k]["final_score"])
            best_score = agent_scores[best_agent]["final_score"]
            
            # 최소 임계값 확인
            if best_score < 0.3:  # 30% 미만이면 처리하지 않음
                logger.warning(f"모든 에이전트의 신뢰도가 낮음. 최고점: {best_score:.3f}")
                return None, best_score
            
            logger.info(f"선택된 에이전트: {best_agent} (점수: {best_score:.3f})")
            return best_agent, agent_scores[best_agent]["confidence"]
            
        except Exception as e:
            logger.error(f"에이전트 선택 실패: {str(e)}")
            return None, 0.0
    
    async def process_with_agent(self, context: AgentContext, agent_id: str) -> Optional[AgentResult]:
        """선택된 에이전트로 메시지 처리"""
        try:
            if agent_id not in self.agents:
                logger.error(f"에이전트 '{agent_id}'를 찾을 수 없습니다.")
                return None
            
            agent = self.agents[agent_id]
            result = await agent.process(context)
            
            # 에이전트 전환 처리
            if result.action == AgentAction.SWITCH and result.next_agent:
                if context.agent_switches < self.max_agent_switches:
                    logger.info(f"에이전트 전환: {agent_id} -> {result.next_agent}")
                    context.agent_switches += 1
                    context.current_agent = result.next_agent
                    return await self.process_with_agent(context, result.next_agent)
                else:
                    logger.warning("최대 에이전트 전환 횟수 초과")
                    result.response += "\n\n최대 처리 단계에 도달했습니다."
            
            return result
            
        except Exception as e:
            logger.error(f"에이전트 처리 실패 ({agent_id}): {str(e)}")
            return None
    
    def get_agent_name(self, agent_id: str) -> str:
        """에이전트 ID를 한국어 이름으로 변환"""
        agent_names = {
            "document_search": "문서검색 에이전트",
            "document_draft": "업무문서 초안작성 에이전트", 
            "performance_analysis": "실적분석 에이전트",
            "client_analysis": "거래처분석 에이전트"
        }
        return agent_names.get(agent_id, agent_id)
    
    async def get_general_suggestions(self) -> List[str]:
        """일반적인 사용 제안사항"""
        return [
            "📄 문서 검색: '좋은제약 복리후생 정책 찾아줘'",
            "✍️ 문서 작성: '월간 실적 보고서 작성해줘'",
            "📊 실적 분석: '올해 매출 분석해줘'",
            "🏢 거래처 분석: '고객 세분화 분석해줘'",
            "❓ 도움말: '어떤 기능을 사용할 수 있나요?'"
        ]
    
    def get_agent_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """각 에이전트의 기능 소개"""
        capabilities = {}
        
        for agent_id, agent in self.agents.items():
            capabilities[agent_id] = {
                "name": self.get_agent_name(agent_id),
                "description": agent.description,
                "keywords": agent.keywords[:10],  # 주요 키워드 10개만
                "supported_tasks": agent.supported_tasks,
                "priority": agent.priority
            }
        
        return capabilities
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """라우팅 통계 정보"""
        if not self.routing_history:
            return {"message": "아직 처리된 메시지가 없습니다."}
        
        agent_usage = {}
        total_requests = len(self.routing_history)
        
        for record in self.routing_history:
            agent_id = record["selected_agent"]
            if agent_id not in agent_usage:
                agent_usage[agent_id] = 0
            agent_usage[agent_id] += 1
        
        # 사용률 계산
        for agent_id in agent_usage:
            agent_usage[agent_id] = {
                "count": agent_usage[agent_id],
                "percentage": (agent_usage[agent_id] / total_requests) * 100
            }
        
        return {
            "total_requests": total_requests,
            "agent_usage": agent_usage,
            "most_used_agent": max(agent_usage.keys(), key=lambda k: agent_usage[k]["count"]) if agent_usage else None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """에이전트 시스템 상태 확인"""
        health_status = {
            "system_status": "healthy",
            "total_agents": len(self.agents),
            "agents": {}
        }
        
        for agent_id, agent in self.agents.items():
            try:
                # 간단한 테스트 메시지로 에이전트 상태 확인
                test_context = AgentContext(
                    current_message="테스트",
                    user_id="system",
                    session_id="health_check",
                    conversation_history=[],
                    current_agent=agent_id,
                    agent_switches=0,
                    user_preferences={}
                )
                
                confidence = await agent.can_handle(test_context)
                
                health_status["agents"][agent_id] = {
                    "name": self.get_agent_name(agent_id),
                    "status": "healthy",
                    "test_confidence": confidence,
                    "description": agent.description
                }
                
            except Exception as e:
                health_status["agents"][agent_id] = {
                    "name": self.get_agent_name(agent_id),
                    "status": "error",
                    "error": str(e)
                }
                health_status["system_status"] = "degraded"
        
        return health_status
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """시스템 전체 개요"""
        return {
            "system_name": "4개 전문 에이전트 시스템",
            "version": "1.0.0",
            "description": "문서검색, 문서작성, 실적분석, 거래처분석을 담당하는 전문 에이전트 시스템",
            "agents": self.get_agent_capabilities(),
            "routing_stats": self.get_routing_statistics(),
            "health": await self.health_check(),
            "suggestions": await self.get_general_suggestions()
        } 