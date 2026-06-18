"""AgentPool — Eager Initialization 싱글톤

서버 부팅 시 Team/Agent/Tool 카탈로그를 읽어 Agent 인스턴스를 미리 생성.
요청 시 Tool 실행은 warm 상태에서 바로 시작.

구조:
  Team → Agent → Tool
  (YAML 카탈로그 기반)

실재 Tool(status=implemented)은 ToolRegistry로 실제 import,
stub Tool은 mock executor로 대체.

Reference: docs/_claude/4layer_system/system_architecture.md  D-7
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.core.logging import get_logger
from app.dream_agent.tools.registry import get_registry

logger = get_logger(__name__)

CATALOG_PATH = (
    Path(__file__).parent.parent
    / "planning" / "catalog" / "team_catalog.yaml"
)


class AgentSpec:
    """단일 Agent 메타 + Tool 목록"""
    def __init__(self, team: str, name: str, description: str, handles_tasks: list[str], tools: list[dict]):
        self.team = team
        self.name = name
        self.description = description
        self.handles_tasks = handles_tasks
        self.tools = tools                 # raw tool dicts from catalog
        self.tool_names: set[str] = {t["name"] for t in tools}

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self.tool_names

    def get_tool_meta(self, tool_name: str) -> dict | None:
        for t in self.tools:
            if t["name"] == tool_name:
                return t
        return None


class AgentPool:
    """Eager 초기화 싱글톤"""
    _instance: "AgentPool | None" = None

    def __init__(self):
        self._teams: dict[str, dict] = {}       # team_name → {description, agents}
        self._agents: dict[str, AgentSpec] = {} # agent_name → AgentSpec
        self._catalog: dict = {}
        self._loaded = False

    @classmethod
    def instance(cls) -> "AgentPool":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load()
        return cls._instance

    def load(self) -> None:
        if self._loaded:
            return
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            self._catalog = yaml.safe_load(f)

        for team_name, team_data in (self._catalog.get("teams") or {}).items():
            self._teams[team_name] = team_data
            for agent_name, agent_data in (team_data.get("agents") or {}).items():
                spec = AgentSpec(
                    team=team_name,
                    name=agent_name,
                    description=agent_data.get("description", ""),
                    handles_tasks=agent_data.get("handles_tasks", []) or [],
                    tools=agent_data.get("tools", []) or [],
                )
                self._agents[agent_name] = spec

        self._loaded = True
        logger.info(
            "AgentPool loaded (Eager)",
            teams=len(self._teams),
            agents=len(self._agents),
        )

    # ── 조회 API ────────────────────────────────────────────
    def get_agent(self, name: str) -> AgentSpec | None:
        return self._agents.get(name)

    def get_tool_meta(self, agent_name: str, tool_name: str) -> dict | None:
        agent = self.get_agent(agent_name)
        meta = agent.get_tool_meta(tool_name) if agent else None
        if meta is None:
            # planning 이 (agent, tool) 에서 agent 를 틀리게 추측해도 tool 이름으로 복구.
            # (tool명은 카탈로그 유일 — get_real_tool 도 이미 이름만으로 인스턴스화.)
            meta = self._find_tool_meta_by_name(tool_name)
        return meta

    def _find_tool_meta_by_name(self, tool_name: str) -> dict | None:
        for agent in self._agents.values():
            m = agent.get_tool_meta(tool_name)
            if m is not None:
                return m
        return None

    def is_tool_implemented(self, agent_name: str, tool_name: str) -> bool:
        meta = self.get_tool_meta(agent_name, tool_name)
        return bool(meta and meta.get("status") == "implemented")

    def is_tool_stub(self, agent_name: str, tool_name: str) -> bool:
        meta = self.get_tool_meta(agent_name, tool_name)
        return bool(meta and meta.get("status") == "stub")

    def list_teams(self) -> list[str]:
        return list(self._teams.keys())

    def list_agents(self, team: str | None = None) -> list[str]:
        if team is None:
            return list(self._agents.keys())
        return [a.name for a in self._agents.values() if a.team == team]

    # ── 실재 Tool 인스턴스화 (Lazy resource: 처음 호출 시 로드) ──
    _tool_instance_cache: dict[str, Any] = {}

    def get_real_tool(self, tool_name: str) -> Any | None:
        """ToolRegistry를 통해 실재 Tool 인스턴스 반환 (캐시)"""
        if tool_name in self._tool_instance_cache:
            return self._tool_instance_cache[tool_name]

        registry = get_registry()
        if not registry.exists(tool_name):
            logger.warning("Real tool not in registry", tool=tool_name)
            return None

        try:
            tool_class = registry.import_tool(tool_name)
            spec = registry.get(tool_name)
            inst = tool_class(spec)
            self._tool_instance_cache[tool_name] = inst
            logger.info("Real tool loaded (lazy)", tool=tool_name)
            return inst
        except Exception as e:
            logger.error("Real tool load failed", tool=tool_name, error=str(e))
            return None


def get_agent_pool() -> AgentPool:
    return AgentPool.instance()
