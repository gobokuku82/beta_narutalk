"""Base Tool

도구 추상 기본 클래스.

Step 4 (2026-05-27): DataSource DI 추가 (사용자 P1·P2 — tool 순수 기능, data 관절 분리).
②-a (2026-05-30): tool 들은 `self.fetch(source_id, context)` 헬퍼로 데이터 접근.
                  client 는 context.client_id 에서만 흐름. raw 파일 직접 로드 금지.
⑷ (2026-06-01): validate_params 강화 — required + type 검증.
                Pipeline runner / Executor 가 execute 전 호출 → silent failure 차단.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.data_sources import DataSource, get_default_data_source
from app.dream_agent.models import ExecutionContext, ToolSpec


# ⑷ type 검증 매핑 — ToolParameterType (string/integer/float/boolean/array/object)
_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "float": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _check_type(val: Any, expected_type: Any) -> bool:
    """값 타입이 spec 타입과 일치하는가. 알 수 없는 타입은 pass (안전 fallback)."""
    type_key = expected_type.value if hasattr(expected_type, "value") else str(expected_type)
    expected = _TYPE_MAP.get(type_key)
    if expected is None:
        return True
    # bool 은 int 의 subclass 라 integer 매핑 시 분리 필요
    if type_key == "integer" and isinstance(val, bool):
        return False
    return isinstance(val, expected)


class BaseTool(ABC):
    """도구 기본 클래스"""

    def __init__(self, spec: ToolSpec, data_source: DataSource | None = None):
        """
        Args:
            spec: tool 메타 (YAML catalog)
            data_source: 외부 데이터 접근 관절 (DI). None 이면 default 싱글톤 사용.
        """
        self.spec = spec
        self.ds: DataSource = data_source or get_default_data_source()

    def fetch(self, source_id: str, context: ExecutionContext) -> Any:
        """tool용 데이터 요청 헬퍼 — client 는 context.client_id 에서 온다 (tool 은 client 모름).

        ADR-022 권한: tool 은 *무엇*(source_id)만 알고, *어느 client/어디*는 data layer.
        진입점(API/runner/agent)이 ctx.client_id 를 채운다. 없으면 fail-fast.
        helper-B (세부계획_작업①, 2026-05-29) — `self.ds.get(client, source_id)` 의 drop-in 대체.
        """
        client = context.client_id
        if not client:
            raise ValueError(
                "client 미지정: ExecutionContext.client_id 가 비어있음 "
                f"(진입점이 client 설정 필요). source_id={source_id!r}"
            )
        return self.ds.get(client, source_id)

    @property
    def name(self) -> str:
        """도구 이름"""
        return self.spec.name

    @property
    def description(self) -> str:
        """도구 설명"""
        return self.spec.description

    @abstractmethod
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """도구 실행

        Args:
            params: 파라미터
            context: 실행 컨텍스트

        Returns:
            실행 결과
        """
        pass

    def validate_params(self, params: dict[str, Any]) -> tuple[bool, list[str]]:
        """파라미터 검증 — required missing + type mismatch 사전 차단.

        ⑷ (2026-06-01): silent failure 차단 (디버깅 진단 Step 1).
        execute() 전 호출 권장 (Pipeline runner / Executor 진입점).

        Args:
            params: 검증할 파라미터

        Returns:
            (valid, errors) — errors 비면 valid=True
        """
        errors = []

        for ps in self.spec.parameters:
            # 1. required 누락
            if ps.required and ps.name not in params:
                errors.append(f"Required parameter missing: {ps.name}")
                continue
            # 2. type mismatch (값 있는 경우만)
            if ps.name in params and params[ps.name] is not None:
                val = params[ps.name]
                if not _check_type(val, ps.type):
                    errors.append(
                        f"Parameter '{ps.name}' type mismatch: "
                        f"expected {ps.type.value if hasattr(ps.type, 'value') else ps.type}, "
                        f"got {type(val).__name__}"
                    )

        return len(errors) == 0, errors

    def get_default_params(self) -> dict[str, Any]:
        """기본 파라미터 반환"""
        defaults = {}

        for param_spec in self.spec.parameters:
            if param_spec.default is not None:
                defaults[param_spec.name] = param_spec.default

        return defaults

    def merge_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """기본값과 파라미터 병합"""
        merged = self.get_default_params()
        merged.update(params)
        return merged
