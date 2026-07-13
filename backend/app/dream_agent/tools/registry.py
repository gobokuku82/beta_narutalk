"""Tool Registry

YAML 기반 도구 레지스트리 — catalog/ 트리 재귀 스캔
"""

import importlib
from pathlib import Path
from typing import Any, Optional

import yaml

from app.core.logging import get_logger
from app.dream_agent.models import (
    KNOWN_TOOL_CATEGORIES,
    DisplaySpec,
    StoragePolicy,
    ToolParameter,
    ToolParameterType,
    ToolSpec,
)

logger = get_logger(__name__)

# 도구 카탈로그 디렉토리 (메타 중앙화)
TOOLS_DIR = Path(__file__).parent
CATALOG_DIR = TOOLS_DIR / "catalog"


class ToolRegistry:
    """도구 레지스트리

    catalog/ 트리에서 YAML 정의를 재귀 로드하고 관리.
    컨벤션 기반 자동 매핑: YAML 경로 → Python 구현 경로.
    """

    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}
        self._tool_classes: dict[str, type] = {}
        self._loaded = False

    def load(self) -> None:
        """도구 정의 로드 — catalog/ 트리 전체를 재귀 스캔"""
        if self._loaded:
            return

        logger.info("Loading tool catalog", path=str(CATALOG_DIR))

        # catalog/ 아래 모든 YAML을 재귀 스캔
        yaml_files = CATALOG_DIR.rglob("*.yaml")

        for yaml_file in yaml_files:
            # _로 시작하는 파일 무시 (_schema.yaml 등)
            if yaml_file.name.startswith("_"):
                continue

            try:
                tool_spec = self._load_yaml(yaml_file)
                if tool_spec:
                    self._tools[tool_spec.name] = tool_spec
                    logger.debug("Tool loaded", name=tool_spec.name,
                                 path=str(yaml_file.relative_to(CATALOG_DIR)))
            except Exception as e:
                logger.error("Failed to load tool", file=str(yaml_file), error=str(e))

        self._loaded = True
        logger.info("Tool definitions loaded", count=len(self._tools))

    def _load_yaml(self, path: Path) -> Optional[ToolSpec]:
        """YAML 파일에서 도구 정의 로드"""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or not data.get("name"):
            return None

        # Category 파싱 — open-vocab (2026-07-02): 검증된 자유 문자열.
        # non-empty 만 강제(누락/빈 = raise → load() try/except 가 해당 tool 만 스킵=honest degrade,
        # 거부-우선·강제변환 금지). 값 공간은 개방 — 미지 카테고리도 수용(raise 안 함).
        # KNOWN_TOOL_CATEGORIES = 문서화된 관례(조직화/요약용). 관례 밖 = debug 로그만.
        category = data.get("category")
        if not isinstance(category, str) or not category.strip():
            raise ValueError(
                f"Missing/empty 'category' in {path}. "
                f"category = non-empty string (관례값: {sorted(KNOWN_TOOL_CATEGORIES)})"
            )
        category = category.strip()
        if category not in KNOWN_TOOL_CATEGORIES:
            logger.debug(
                "Non-conventional tool category accepted (open-vocab)",
                category=category, file=str(path.relative_to(CATALOG_DIR)),
            )

        # Parameters 파싱
        parameters = []
        for param_data in data.get("parameters", []):
            param_type_str = param_data.get("type", "string")
            try:
                param_type = ToolParameterType(param_type_str)
            except ValueError:
                param_type = ToolParameterType.STRING

            parameters.append(
                ToolParameter(
                    name=param_data.get("name", ""),
                    type=param_type,
                    required=param_data.get("required", False),
                    default=param_data.get("default"),
                    description=param_data.get("description", ""),
                )
            )

        # Storage 정책 파싱 (tool 산출물 — normalized/computed 저장 분기)
        storage_data = data.get("storage")
        storage = StoragePolicy.model_validate(storage_data) if storage_data else None

        # Display 메타 파싱 (Response 표시). 미선언 = None = inert.
        display_data = data.get("display")
        display = DisplaySpec.model_validate(display_data) if display_data else None

        return ToolSpec(
            name=data.get("name"),
            description=data.get("description", ""),
            category=category,
            executor=data.get("executor", ""),
            parameters=parameters,
            timeout_sec=data.get("timeout_sec", 300),
            max_retries=data.get("max_retries", 3),
            dependencies=data.get("dependencies", []),
            produces=data.get("produces", []),
            requires_approval=data.get("requires_approval", False),
            has_cost=data.get("has_cost", False),
            estimated_cost_usd=data.get("estimated_cost", 0.0),
            storage=storage,
            display=display,
        )

    def get(self, name: str) -> Optional[ToolSpec]:
        """도구 조회

        Args:
            name: 도구 이름

        Returns:
            ToolSpec 또는 None
        """
        if not self._loaded:
            self.load()

        return self._tools.get(name)

    def get_all(self) -> list[ToolSpec]:
        """모든 도구 조회"""
        if not self._loaded:
            self.load()

        return list(self._tools.values())

    def get_names(self) -> list[str]:
        """도구 이름 목록"""
        if not self._loaded:
            self.load()

        return list(self._tools.keys())

    def exists(self, name: str) -> bool:
        """도구 존재 여부"""
        if not self._loaded:
            self.load()

        return name in self._tools

    def import_tool(self, name: str) -> type:
        """Tool 이름으로 구현 클래스 동적 import

        컨벤션: catalog 경로 → Python 경로 자동 추론
        예: catalog/collection/<tool>.yaml
            → app.dream_agent.tools.collection.<tool>.<ToolClass>

        Args:
            name: 도구 이름

        Returns:
            BaseTool 서브클래스

        Raises:
            ImportError: 구현 클래스를 찾을 수 없을 때
        """
        if not self._loaded:
            self.load()

        # 캐시 확인
        if name in self._tool_classes:
            return self._tool_classes[name]

        spec = self._tools.get(name)
        if not spec:
            raise ImportError(f"Tool '{name}' not found in catalog")

        # executor 필드가 명시되어 있으면 그대로 사용
        if spec.executor:
            module_path, class_name = spec.executor.rsplit(".", 1)
            full_module = f"app.dream_agent.tools.{module_path}"
        else:
            # 컨벤션 기반 자동 추론: YAML이 등록된 경로로부터 추론
            full_module, class_name = self._infer_import_path(name)

        try:
            module = importlib.import_module(full_module)
            cls = getattr(module, class_name)
        except (ModuleNotFoundError, AttributeError) as e:
            raise ImportError(
                f"Tool '{name}': cannot import {full_module}.{class_name} — {e}"
            ) from e

        self._tool_classes[name] = cls
        logger.debug("Tool class imported", name=name, cls=f"{full_module}.{class_name}")
        return cls

    def _infer_import_path(self, name: str) -> tuple[str, str]:
        """YAML 카탈로그 경로로부터 Python import 경로 추론

        catalog/collection/<tool>.yaml
          → module: app.dream_agent.tools.collection.<tool>
          → class:  <ToolClass>

        catalog/preprocessing/text_cleaning/<tool>.yaml
          → module: app.dream_agent.tools.preprocessing.text_cleaning.<tool>
          → class:  <ToolClass>
        """
        # catalog에서 이 이름의 YAML 찾기
        for yaml_file in CATALOG_DIR.rglob(f"{name}.yaml"):
            if yaml_file.name.startswith("_"):
                continue
            rel = yaml_file.relative_to(CATALOG_DIR).with_suffix("")
            parts = rel.parts  # ('collection', '<tool>')
            module_path = ".".join(parts)
            class_name = "".join(word.capitalize() for word in name.split("_"))
            return f"app.dream_agent.tools.{module_path}", class_name

        # 폴더형 subgraph: name/__init__.py
        for init_file in TOOLS_DIR.rglob(f"{name}/__init__.py"):
            rel = init_file.parent.relative_to(TOOLS_DIR)
            module_path = ".".join(rel.parts)
            class_name = "".join(word.capitalize() for word in name.split("_")) + "Tool"
            return f"app.dream_agent.tools.{module_path}", class_name

        raise ImportError(f"Cannot infer import path for tool '{name}'")


# 싱글톤 인스턴스
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """레지스트리 싱글톤 반환"""
    global _registry

    if _registry is None:
        _registry = ToolRegistry()
        _registry.load()

    return _registry
