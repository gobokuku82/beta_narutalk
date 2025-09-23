"""
Show Agent Dashboard - 에이전트 실행 상태 한번에 보기
"""

from agent_dashboard import AgentDashboard

def show_all():
    """모든 에이전트 상태 표시"""
    dashboard = AgentDashboard()

    # 전체 대시보드 표시
    dashboard.display_dashboard()

    # 각 에이전트 상세 분석
    agents = dashboard.list_agent_checkpoints()
    for agent in agents:
        dashboard.analyze_execution_flow(agent)

if __name__ == "__main__":
    show_all()