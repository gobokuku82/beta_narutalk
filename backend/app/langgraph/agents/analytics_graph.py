"""
Analytics Agent - Subgraph Implementation
LangGraph 0.6.6 기반 데이터분석 에이전트 (Subgraph 구조)
"""

from typing import Dict, Any, List, TypedDict, Annotated, Sequence, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from loguru import logger
import operator
from datetime import datetime, timedelta
import json
import random

from app.core.config import settings


class AnalyticsState(TypedDict):
    """데이터분석 에이전트 전용 State"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    request: str
    analysis_type: str  # sales, performance, market, customer, trend, general
    data_source: str  # database, file, api, mock
    raw_data: Dict[str, Any]
    processed_data: Dict[str, Any]
    statistical_results: Dict[str, Any]
    visualization_config: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    analysis_report: str
    status: str  # analyzing, collecting, processing, calculating, visualizing, reporting, completed, error
    error_message: Optional[str]


class AnalyticsSubgraph:
    """데이터분석 Subgraph - 단계별 분석 워크플로우"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.3,  # 분석의 일관성을 위해 낮은 temperature
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Subgraph 생성
        self.graph = self._build_graph()
    
    def _generate_mock_sales_data(self) -> Dict:
        """모의 영업 데이터 생성"""
        months = ["1월", "2월", "3월", "4월", "5월", "6월"]
        products = ["제품A", "제품B", "제품C", "제품D"]
        regions = ["서울", "경기", "부산", "대구", "광주"]
        
        data = {
            "sales_by_month": {
                month: random.randint(1000, 5000) for month in months
            },
            "sales_by_product": {
                product: random.randint(2000, 8000) for product in products
            },
            "sales_by_region": {
                region: random.randint(1500, 6000) for region in regions
            },
            "growth_rate": round(random.uniform(-10, 30), 2),
            "total_revenue": random.randint(50000, 200000),
            "customer_count": random.randint(100, 500),
            "average_deal_size": random.randint(500, 2000)
        }
        
        return data
    
    def _generate_mock_performance_data(self) -> Dict:
        """모의 성과 데이터 생성"""
        teams = ["영업1팀", "영업2팀", "영업3팀"]
        metrics = ["목표달성률", "신규고객", "재구매율", "고객만족도"]
        
        data = {
            "team_performance": {
                team: {
                    metric: round(random.uniform(60, 120), 1) if "률" in metric or "도" in metric 
                    else random.randint(10, 50)
                    for metric in metrics
                }
                for team in teams
            },
            "top_performers": [
                {"name": "김영업", "achievement": 125.5},
                {"name": "이세일즈", "achievement": 118.3},
                {"name": "박마케팅", "achievement": 112.7}
            ],
            "kpi_status": {
                "revenue": {"target": 100000, "actual": 95000, "achievement": 95},
                "new_customers": {"target": 50, "actual": 48, "achievement": 96},
                "retention_rate": {"target": 85, "actual": 87, "achievement": 102}
            }
        }
        
        return data
    
    async def analyze_data_request_node(self, state: AnalyticsState) -> Dict:
        """데이터 분석 요청 분석 노드"""
        logger.info("데이터 분석 요청 분석")
        
        request = state.get("request", "")
        if not request and state.get("messages"):
            last_message = state["messages"][-1]
            request = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else str(last_message)
        
        # LLM으로 분석 유형 결정
        prompt = f"""
        사용자 요청: {request}
        
        이 요청이 어떤 유형의 데이터 분석인지 분류하세요:
        - sales: 매출, 판매 분석
        - performance: 실적, 성과 분석
        - market: 시장, 경쟁 분석
        - customer: 고객, 거래처 분석
        - trend: 트렌드, 패턴 분석
        - general: 일반적인 데이터 분석
        
        한 단어로만 답하세요:
        """
        
        response = await self.llm.ainvoke(prompt)
        analysis_type = response.content.strip().lower()
        
        # 유효성 검증
        valid_types = ["sales", "performance", "market", "customer", "trend", "general"]
        if analysis_type not in valid_types:
            # 키워드 기반 분류
            request_lower = request.lower()
            if any(word in request_lower for word in ["매출", "판매", "sales", "revenue"]):
                analysis_type = "sales"
            elif any(word in request_lower for word in ["실적", "성과", "performance", "kpi"]):
                analysis_type = "performance"
            elif any(word in request_lower for word in ["시장", "경쟁", "market", "competitor"]):
                analysis_type = "market"
            elif any(word in request_lower for word in ["고객", "거래처", "customer", "client"]):
                analysis_type = "customer"
            elif any(word in request_lower for word in ["트렌드", "패턴", "trend", "pattern"]):
                analysis_type = "trend"
            else:
                analysis_type = "general"
        
        # 데이터 소스 결정 (실제로는 요청에 따라 결정)
        data_source = "mock"  # 현재는 모의 데이터 사용
        
        return {
            "request": request,
            "analysis_type": analysis_type,
            "data_source": data_source,
            "status": "analyzing"
        }
    
    async def data_collection_node(self, state: AnalyticsState) -> Dict:
        """데이터 수집 노드"""
        logger.info("데이터 수집 시작")
        
        analysis_type = state.get("analysis_type", "general")
        data_source = state.get("data_source", "mock")
        
        raw_data = {}
        
        if data_source == "mock":
            # 모의 데이터 생성
            if analysis_type in ["sales", "general"]:
                raw_data["sales_data"] = self._generate_mock_sales_data()
            
            if analysis_type in ["performance", "general"]:
                raw_data["performance_data"] = self._generate_mock_performance_data()
            
            if analysis_type == "market":
                raw_data["market_data"] = {
                    "market_share": 23.5,
                    "competitors": [
                        {"name": "경쟁사A", "share": 31.2},
                        {"name": "경쟁사B", "share": 25.8},
                        {"name": "경쟁사C", "share": 19.5}
                    ],
                    "market_size": 1000000000,
                    "growth_rate": 8.5
                }
            
            if analysis_type == "customer":
                raw_data["customer_data"] = {
                    "total_customers": 342,
                    "new_customers": 45,
                    "churn_rate": 5.2,
                    "customer_segments": {
                        "대형병원": 45,
                        "중형병원": 120,
                        "개인의원": 177
                    },
                    "satisfaction_score": 4.2
                }
            
            if analysis_type == "trend":
                raw_data["trend_data"] = {
                    "sales_trend": [100, 105, 98, 112, 118, 125, 130],
                    "seasonal_pattern": "상반기 저조, 하반기 상승",
                    "growth_forecast": 15.5
                }
        
        # 데이터 수집 메타데이터
        raw_data["metadata"] = {
            "collection_time": datetime.now().isoformat(),
            "data_source": data_source,
            "record_count": len(raw_data)
        }
        
        return {
            "raw_data": raw_data,
            "status": "collecting"
        }
    
    async def data_processing_node(self, state: AnalyticsState) -> Dict:
        """데이터 처리 노드"""
        logger.info("데이터 처리 중")
        
        raw_data = state.get("raw_data", {})
        analysis_type = state.get("analysis_type", "general")
        
        processed_data = {}
        
        # 데이터 정제 및 변환
        if "sales_data" in raw_data:
            sales = raw_data["sales_data"]
            
            # 월별 매출 합계
            total_monthly = sum(sales.get("sales_by_month", {}).values())
            
            # 제품별 매출 비율
            total_product = sum(sales.get("sales_by_product", {}).values())
            product_ratio = {
                product: round(value/total_product * 100, 1) 
                for product, value in sales.get("sales_by_product", {}).items()
            } if total_product > 0 else {}
            
            processed_data["sales_summary"] = {
                "total_monthly_sales": total_monthly,
                "average_monthly_sales": round(total_monthly / 6, 2) if total_monthly else 0,
                "product_contribution": product_ratio,
                "best_performing_product": max(sales.get("sales_by_product", {}), 
                                              key=sales.get("sales_by_product", {}).get) if sales.get("sales_by_product") else None,
                "best_performing_region": max(sales.get("sales_by_region", {}), 
                                             key=sales.get("sales_by_region", {}).get) if sales.get("sales_by_region") else None
            }
        
        if "performance_data" in raw_data:
            perf = raw_data["performance_data"]
            
            # 팀별 평균 성과
            team_averages = {}
            for team, metrics in perf.get("team_performance", {}).items():
                avg = sum(metrics.values()) / len(metrics) if metrics else 0
                team_averages[team] = round(avg, 1)
            
            processed_data["performance_summary"] = {
                "team_rankings": sorted(team_averages.items(), key=lambda x: x[1], reverse=True),
                "top_performer": perf.get("top_performers", [{}])[0].get("name") if perf.get("top_performers") else None,
                "overall_kpi_achievement": round(
                    sum(kpi.get("achievement", 0) for kpi in perf.get("kpi_status", {}).values()) / 
                    len(perf.get("kpi_status", {})) if perf.get("kpi_status") else 0, 1
                )
            }
        
        processed_data["processing_timestamp"] = datetime.now().isoformat()
        
        return {
            "processed_data": processed_data,
            "status": "processing"
        }
    
    async def statistical_analysis_node(self, state: AnalyticsState) -> Dict:
        """통계 분석 노드"""
        logger.info("통계 분석 수행")
        
        processed_data = state.get("processed_data", {})
        raw_data = state.get("raw_data", {})
        
        statistical_results = {}
        
        # 기본 통계 계산
        if "sales_data" in raw_data:
            sales_values = list(raw_data["sales_data"].get("sales_by_month", {}).values())
            if sales_values:
                statistical_results["sales_statistics"] = {
                    "mean": round(sum(sales_values) / len(sales_values), 2),
                    "max": max(sales_values),
                    "min": min(sales_values),
                    "range": max(sales_values) - min(sales_values),
                    "growth_trend": "상승" if sales_values[-1] > sales_values[0] else "하락"
                }
        
        # 상관관계 분석 (시뮬레이션)
        statistical_results["correlations"] = {
            "sales_customer_correlation": 0.85,
            "performance_satisfaction_correlation": 0.72,
            "marketing_sales_correlation": 0.68
        }
        
        # 예측 분석 (간단한 선형 예측)
        if "trend_data" in raw_data:
            trend = raw_data["trend_data"].get("sales_trend", [])
            if len(trend) >= 2:
                growth_rate = (trend[-1] - trend[0]) / trend[0] * 100 if trend[0] != 0 else 0
                statistical_results["forecast"] = {
                    "next_period_estimate": round(trend[-1] * 1.1, 2),
                    "growth_rate": round(growth_rate, 2),
                    "confidence_level": "중간"
                }
        
        return {
            "statistical_results": statistical_results,
            "status": "calculating"
        }
    
    async def visualization_node(self, state: AnalyticsState) -> Dict:
        """시각화 설정 노드"""
        logger.info("시각화 구성 생성")
        
        analysis_type = state.get("analysis_type", "general")
        processed_data = state.get("processed_data", {})
        
        # 차트 설정 생성
        visualization_config = {
            "charts": [],
            "dashboard_layout": "grid"
        }
        
        if analysis_type in ["sales", "general"]:
            visualization_config["charts"].append({
                "type": "bar",
                "title": "월별 매출 현황",
                "data_key": "sales_by_month",
                "x_axis": "월",
                "y_axis": "매출액"
            })
            
            visualization_config["charts"].append({
                "type": "pie",
                "title": "제품별 매출 비중",
                "data_key": "product_contribution",
                "legend": True
            })
            
            visualization_config["charts"].append({
                "type": "line",
                "title": "매출 트렌드",
                "data_key": "sales_trend",
                "show_forecast": True
            })
        
        if analysis_type in ["performance", "general"]:
            visualization_config["charts"].append({
                "type": "horizontal_bar",
                "title": "팀별 성과",
                "data_key": "team_rankings",
                "x_axis": "성과 점수",
                "y_axis": "팀"
            })
            
            visualization_config["charts"].append({
                "type": "gauge",
                "title": "KPI 달성률",
                "data_key": "overall_kpi_achievement",
                "min": 0,
                "max": 150,
                "thresholds": [80, 100, 120]
            })
        
        if analysis_type == "customer":
            visualization_config["charts"].append({
                "type": "donut",
                "title": "고객 세그먼트 분포",
                "data_key": "customer_segments",
                "center_text": "총 고객수"
            })
        
        # 대시보드 메타데이터
        visualization_config["metadata"] = {
            "created_at": datetime.now().isoformat(),
            "chart_count": len(visualization_config["charts"]),
            "interactive": True,
            "export_formats": ["png", "pdf", "excel"]
        }
        
        return {
            "visualization_config": visualization_config,
            "status": "visualizing"
        }
    
    async def insights_generation_node(self, state: AnalyticsState) -> Dict:
        """인사이트 생성 노드"""
        logger.info("인사이트 도출")
        
        request = state.get("request", "")
        processed_data = state.get("processed_data", {})
        statistical_results = state.get("statistical_results", {})
        
        # LLM으로 인사이트 생성
        prompt = f"""
        분석 요청: {request}
        
        처리된 데이터 요약:
        {json.dumps(processed_data, ensure_ascii=False, indent=2)[:1000]}
        
        통계 분석 결과:
        {json.dumps(statistical_results, ensure_ascii=False, indent=2)[:500]}
        
        위 데이터를 바탕으로:
        1. 핵심 인사이트 3가지를 도출하세요
        2. 각 인사이트에 대한 실행 가능한 권고사항을 제시하세요
        
        JSON 형식으로 답하세요:
        {{
            "insights": ["인사이트1", "인사이트2", "인사이트3"],
            "recommendations": ["권고1", "권고2", "권고3"]
        }}
        """
        
        response = await self.llm.ainvoke(prompt)
        
        try:
            result = json.loads(response.content)
            insights = result.get("insights", [])
            recommendations = result.get("recommendations", [])
        except:
            # 파싱 실패 시 기본 인사이트
            insights = [
                "데이터 분석 결과 전반적인 성장 추세를 보이고 있습니다.",
                "특정 제품/지역의 성과가 두드러지게 나타났습니다.",
                "개선이 필요한 영역이 식별되었습니다."
            ]
            recommendations = [
                "성과가 좋은 영역에 집중 투자를 고려하세요.",
                "저조한 영역에 대한 원인 분석이 필요합니다.",
                "정기적인 모니터링 체계를 구축하세요."
            ]
        
        return {
            "insights": insights,
            "recommendations": recommendations,
            "status": "generating_insights"
        }
    
    async def generate_report_node(self, state: AnalyticsState) -> Dict:
        """분석 보고서 생성 노드"""
        logger.info("분석 보고서 생성")
        
        # 보고서 구성
        report_parts = [
            "# 데이터 분석 보고서",
            f"\n## 분석 요청\n{state.get('request', '')}",
            f"\n## 분석 유형\n{state.get('analysis_type', '').replace('_', ' ').title()}",
            f"\n## 분석 기간\n{datetime.now().strftime('%Y년 %m월 %d일')} 기준"
        ]
        
        # 핵심 지표
        report_parts.append("\n## 핵심 지표")
        
        processed_data = state.get("processed_data", {})
        if "sales_summary" in processed_data:
            summary = processed_data["sales_summary"]
            report_parts.append(f"- **월평균 매출**: {summary.get('average_monthly_sales', 'N/A'):,}원")
            report_parts.append(f"- **최고 실적 제품**: {summary.get('best_performing_product', 'N/A')}")
            report_parts.append(f"- **최고 실적 지역**: {summary.get('best_performing_region', 'N/A')}")
        
        if "performance_summary" in processed_data:
            perf = processed_data["performance_summary"]
            report_parts.append(f"- **전체 KPI 달성률**: {perf.get('overall_kpi_achievement', 0)}%")
            report_parts.append(f"- **최우수 성과자**: {perf.get('top_performer', 'N/A')}")
        
        # 통계 분석 결과
        statistical_results = state.get("statistical_results", {})
        if statistical_results:
            report_parts.append("\n## 통계 분석")
            
            if "sales_statistics" in statistical_results:
                stats = statistical_results["sales_statistics"]
                report_parts.append(f"- **평균값**: {stats.get('mean', 0):,}")
                report_parts.append(f"- **최대/최소**: {stats.get('max', 0):,} / {stats.get('min', 0):,}")
                report_parts.append(f"- **성장 추세**: {stats.get('growth_trend', 'N/A')}")
            
            if "forecast" in statistical_results:
                forecast = statistical_results["forecast"]
                report_parts.append(f"\n### 예측")
                report_parts.append(f"- **다음 기간 예상**: {forecast.get('next_period_estimate', 0):,}")
                report_parts.append(f"- **성장률**: {forecast.get('growth_rate', 0)}%")
        
        # 시각화 정보
        viz_config = state.get("visualization_config", {})
        if viz_config.get("charts"):
            report_parts.append(f"\n## 시각화")
            report_parts.append(f"- 생성된 차트: {len(viz_config['charts'])}개")
            for chart in viz_config["charts"][:3]:
                report_parts.append(f"  - {chart.get('title', 'N/A')} ({chart.get('type', 'N/A')})")
        
        # 인사이트
        insights = state.get("insights", [])
        if insights:
            report_parts.append("\n## 핵심 인사이트")
            for i, insight in enumerate(insights, 1):
                report_parts.append(f"{i}. {insight}")
        
        # 권고사항
        recommendations = state.get("recommendations", [])
        if recommendations:
            report_parts.append("\n## 권고사항")
            for i, rec in enumerate(recommendations, 1):
                report_parts.append(f"{i}. {rec}")
        
        # 마무리
        report_parts.append(f"\n---\n*보고서 생성: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        analysis_report = "\n".join(report_parts)
        
        return {
            "analysis_report": analysis_report,
            "status": "completed"
        }
    
    async def error_handler_node(self, state: AnalyticsState) -> Dict:
        """오류 처리 노드"""
        logger.error(f"데이터 분석 오류: {state.get('error_message')}")
        
        error_msg = state.get("error_message", "데이터 분석 중 오류가 발생했습니다.")
        
        return {
            "messages": [AIMessage(content=f"분석 오류: {error_msg}")],
            "status": "error"
        }
    
    def route_after_analysis(self, state: AnalyticsState) -> str:
        """분석 요청 후 라우팅"""
        if state.get("error_message"):
            return "error_handler"
        return "data_collection"
    
    def route_after_collection(self, state: AnalyticsState) -> str:
        """데이터 수집 후 라우팅"""
        if not state.get("raw_data"):
            return "error_handler"
        return "data_processing"
    
    def _build_graph(self) -> StateGraph:
        """Subgraph 구성"""
        workflow = StateGraph(AnalyticsState)
        
        # 노드 추가
        workflow.add_node("analyze_request", self.analyze_data_request_node)
        workflow.add_node("data_collection", self.data_collection_node)
        workflow.add_node("data_processing", self.data_processing_node)
        workflow.add_node("statistical_analysis", self.statistical_analysis_node)
        workflow.add_node("visualization", self.visualization_node)
        workflow.add_node("insights_generation", self.insights_generation_node)
        workflow.add_node("generate_report", self.generate_report_node)
        workflow.add_node("error_handler", self.error_handler_node)
        
        # 시작점
        workflow.add_edge(START, "analyze_request")
        
        # 조건부 라우팅
        workflow.add_conditional_edges(
            "analyze_request",
            self.route_after_analysis,
            {
                "data_collection": "data_collection",
                "error_handler": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "data_collection",
            self.route_after_collection,
            {
                "data_processing": "data_processing",
                "error_handler": "error_handler"
            }
        )
        
        # 순차적 워크플로우
        workflow.add_edge("data_processing", "statistical_analysis")
        workflow.add_edge("statistical_analysis", "visualization")
        workflow.add_edge("visualization", "insights_generation")
        workflow.add_edge("insights_generation", "generate_report")
        
        # 종료
        workflow.add_edge("generate_report", END)
        workflow.add_edge("error_handler", END)
        
        # 그래프 컴파일
        return workflow.compile()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor에서 호출하는 메인 처리 함수"""
        logger.info("Analytics Subgraph 처리 시작")
        
        # 입력 state를 subgraph state로 변환
        subgraph_state = AnalyticsState(
            messages=state.get("messages", []),
            request="",
            analysis_type="",
            data_source="",
            raw_data={},
            processed_data={},
            statistical_results={},
            visualization_config={},
            insights=[],
            recommendations=[],
            analysis_report="",
            status="",
            error_message=None
        )
        
        # Subgraph 실행
        try:
            result = await self.graph.ainvoke(subgraph_state)
            
            # 응답 메시지 생성
            if result.get("status") == "completed":
                response = result.get("analysis_report", "데이터 분석이 완료되었습니다.")
            else:
                response = result.get("error_message", "데이터 분석에 실패했습니다.")
            
            # 결과 반환
            return {
                "messages": [AIMessage(content=response)],
                "agent_outputs": {
                    "analytics": {
                        "analysis_type": result.get("analysis_type"),
                        "raw_data": result.get("raw_data"),
                        "processed_data": result.get("processed_data"),
                        "statistical_results": result.get("statistical_results"),
                        "visualization_config": result.get("visualization_config"),
                        "insights": result.get("insights"),
                        "recommendations": result.get("recommendations"),
                        "report": result.get("analysis_report"),
                        "status": result.get("status"),
                        "error": result.get("error_message")
                    }
                },
                "next_agent": None
            }
        except Exception as e:
            logger.error(f"Analytics Subgraph 실행 오류: {e}")
            return {
                "messages": [AIMessage(content=f"데이터 분석 중 오류가 발생했습니다: {str(e)}")],
                "agent_outputs": {"analytics": {"error": str(e)}},
                "next_agent": None
            }


# Subgraph 인스턴스 생성 함수
def create_analytics_subgraph():
    """Analytics Subgraph 생성"""
    return AnalyticsSubgraph()