"""Sprint 13 테스트 공용 fixture.

pyproject.toml:
  pythonpath = ["backend"]
  asyncio_mode = "auto"
→ backend/ 루트에서 import 가능 + async 함수 자동 인식
"""

import asyncio
import sys

import pytest


# Windows: psycopg async는 ProactorEventLoop와 호환 안 됨 (live 테스트 PostgreSQL용).
# run_server_v2.py와 동일한 정책 설정.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture
def fresh_conn_manager():
    """매 테스트마다 새 ConnectionManager — 싱글톤 간섭 차단."""
    from api_v2.connection_manager import ConnectionManager
    return ConnectionManager()


@pytest.fixture
def fresh_concurrency():
    """매 테스트마다 새 ConcurrencyManager."""
    from app.dream_agent.workflow_managers.concurrency_manager import ConcurrencyManager
    return ConcurrencyManager()


@pytest.fixture(autouse=True)
def _isolate_layer_guard_log(tmp_path, monkeypatch):
    """layer_guard.jsonl(POC 페어 누적 로그)을 테스트 노이즈로부터 전역 격리 (2026-06-11).

    _LOG_PATH 가 리포 루트 절대경로로 고정되면서, 실그래프를 돌리는 통합 테스트가
    프로덕션 페어 파일에 기록하게 되므로 autouse 로 tmp 우회.
    (과거: CWD 상대경로 + 미격리 → backend/logs 사본이 100% 테스트 픽스처로 오염됐었음.)
    """
    import app.dream_agent.system_graph.layer_inspector as lg_mod
    monkeypatch.setattr(lg_mod, "_LOG_PATH", tmp_path / "layer_guard.jsonl")


@pytest.fixture
def fresh_hitl():
    """HITL 싱글톤을 매 테스트마다 리셋 (I7).

    _progress / _paused / _resume_queues / _active_turns(Sprint 14~) 모두 초기화.
    싱글톤이라 같은 인스턴스 반환하지만 상태는 클린.
    """
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager
    h = get_hitl_manager()
    h._progress.clear()
    h._paused.clear()
    if hasattr(h, "_reset_resume_queues_for_test"):
        h._reset_resume_queues_for_test()
    # Sprint 14 A1 — _active_turns (HITL timeout 가드용). defensive hasattr.
    if hasattr(h, "_active_turns"):
        h._active_turns.clear()
    # Sprint 14 A3 — _session_locks (per-session asyncio.Lock). 테스트 간 격리 위해 clear.
    if hasattr(h, "_session_locks"):
        h._session_locks.clear()
    return h


@pytest.fixture
def reset_conn_manager():
    """conn_manager 싱글톤 리셋 (I9 Integration 테스트용)."""
    from api_v2.connection_manager import conn_manager
    conn_manager._connections.clear()
    yield conn_manager
    conn_manager._connections.clear()
