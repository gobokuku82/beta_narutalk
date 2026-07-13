"""프레임 부트스모크 — DB 없이 임포트·앱 구성·그래프 컴파일이 살아있는지 검증.

(2026-07-03) db_design 스위트 제거(계획서 P2)로 비게 된 테스트 벨트의 최소 게이트 —
CLAUDE.md 의 부트스모크 한 줄을 pytest 로 승격. 도메인 주입 시 tool unit +
planner integration 스위트를 재구축한다 (문서 40 §5 기준선).
"""

from api.main import create_app
from app.dream_agent.system_graph.builder import build_graph


def test_app_constructs_and_registers_core_routes():
    app = create_app()
    paths = {getattr(r, "path", None) for r in app.routes}
    for required in ("/health/", "/api/conversations", "/ws/agent", "/ws/hitl"):
        assert required in paths, f"코어 라우트 누락: {required}"


def test_graph_compiles_without_checkpointer():
    assert build_graph(None) is not None
