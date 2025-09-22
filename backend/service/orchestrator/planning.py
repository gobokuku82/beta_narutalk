from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict

class PlanningState(TypedDict):
    intents: List[Dict]
    execution_steps: List[Dict]
    agent_sequence: List[str]
    dependencies: Dict[str, List[str]]
    parallel_groups: List[List[str]]
    estimated_time: float

class PlanningSubGraph:
    def __init__(self):
        self.workflow = StateGraph(PlanningState)
        self._build_graph()
    
    def _build_graph(self):
        self.workflow.add_node("analyze_dependencies", self.analyze_dependencies)
        self.workflow.add_node("optimize_sequence", self.optimize_execution_sequence)
        self.workflow.add_node("allocate_resources", self.allocate_resources)
        self.workflow.add_node("create_execution_plan", self.create_execution_plan)
        
        # 엔트리 포인트 정의 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "analyze_dependencies")
        self.workflow.add_edge("analyze_dependencies", "optimize_sequence")
        self.workflow.add_edge("optimize_sequence", "allocate_resources")
        self.workflow.add_edge("allocate_resources", "create_execution_plan")
        self.workflow.add_edge("create_execution_plan", END)
    
    async def optimize_execution_sequence(self, state: PlanningState):
        """병렬/순차 실행 최적화"""
        # 의존성 없는 태스크는 병렬 처리
        parallel_groups = []
        sequential_tasks = []
        
        for intent in state['intents']:
            if intent['type'] in ['sales_analysis', 'client_analysis']:
                # 데이터 분석은 함께 실행 가능
                parallel_groups.append(intent)
            elif intent['type'] == 'compliance_check':
                # 규정 검토는 다른 결과 필요할 수 있음
                sequential_tasks.append(intent)
        
        state['parallel_groups'] = parallel_groups
        return state

    async def analyze_dependencies(self, state: PlanningState) -> PlanningState:
        """의존성 분석"""
        state["dependencies"] = {}
        return state

    async def allocate_resources(self, state: PlanningState) -> PlanningState:
        """리소스 할당"""
        state["estimated_time"] = 10.0
        return state

    async def create_execution_plan(self, state: PlanningState) -> PlanningState:
        """실행 계획 생성"""
        state["execution_steps"] = []
        state["agent_sequence"] = []
        return state