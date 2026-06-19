"""Recovery — 데이터 없음 → HITL 복구의 *순수 코어* (G6, 2026-06-07).

사용자 요구: "어떤 행동을 줄지(메뉴)는 테스트하며 계속 바뀐다 → 코드 말고 설정만 고쳐 바꾼다."

두 층 분리:
  - 기계(본 모듈): 감지·페이로드·동사해석 = 거의 안 바뀜.
  - 메뉴(actions.yaml): 어떤 옵션/문구/파라미터/막힘기준 = 자유롭게 바뀜. 런타임 read(재시작 불요).

그래프 wiring(execution_stage 의 interrupt 발동·resume 라우팅)은 본 모듈을 *호출*만 한다(별도).

Status: partial — 감지(detect_recovery)·복구 메뉴 빌드까지 배선. resolve_choice·interrupt
발동·사용자 선택 루프는 미배선(G6 후반 — 현재는 로그 + R1 정직 메시지로 진행).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_ACTIONS_PATH = Path(__file__).parent / "actions.yaml"


# ── 설정 로드 (런타임 read — 매 호출 읽어 재시작 없이 수정 반영) ──

def load_actions(path: str | Path | None = None) -> dict[str, Any]:
    """actions.yaml 을 매 호출 읽는다(hot — 테스트 중 수정 즉시 반영)."""
    p = Path(path) if path else _ACTIONS_PATH
    return yaml.safe_load(p.read_text(encoding="utf-8"))


# ── TodoResult | dict 양쪽 접근 (execution_stage 는 dict, 테스트도 dict) ──

def _get(r: Any, key: str, default: Any = None) -> Any:
    if isinstance(r, dict):
        return r.get(key, default)
    return getattr(r, key, default)


def _status(r: Any) -> str:
    s = _get(r, "status")
    return s.value if hasattr(s, "value") else (s or "")


def _data(r: Any) -> dict:
    d = _get(r, "data", {})
    return d if isinstance(d, dict) else {}


def _tool(r: Any) -> str:
    return _get(r, "tool") or ""


# ── 감지: "데이터 없음으로 막힘"인가 (기준도 config = block_when) ──

def is_blocked(todos: dict[str, Any], config: dict[str, Any]) -> bool:
    """block_when 기준으로 판정.

    기본: 어떤 todo 가 reason(=data_insufficient)으로 SKIP 됐고,
          (no_other_output 면) collector 외 COMPLETED 산출이 하나도 없을 때 = 막힘.
    build_insufficient_data_payload(responder)와 같은 결 — 단 기준을 데이터(config)로 노출.
    """
    bw = config.get("block_when") or {}
    reason = bw.get("reason", "data_insufficient")

    skipped = [
        r for r in todos.values()
        if _status(r) == "skipped" and _data(r).get("reason") == reason
    ]
    if not skipped:
        return False

    if bw.get("no_other_output", True):
        produced = any(
            _status(r) == "completed" and _tool(r) and "collector" not in _tool(r)
            for r in todos.values()
        )
        if produced:
            return False
    return True


# ── interrupt 페이로드 (메뉴는 config 에서) ──

def build_recovery_payload(config: dict[str, Any], context: dict | None = None) -> dict[str, Any]:
    """data_recovery interrupt 페이로드. 표시용 메뉴(id·label·desc)만 노출."""
    options = [
        {"id": o["id"], "label": o.get("label", o["id"]), "desc": o.get("desc")}
        for o in (config.get("options") or [])
    ]
    return {
        "type": "data_recovery",
        "message": config.get("message", "해당 데이터가 없습니다. 어떻게 할까요?"),
        "options": options,
        "context": context or {},
    }


# ── 동사 해석 (선택 → verb + params). 모르면 안전하게 end ──

def resolve_choice(option_id: str, config: dict[str, Any]) -> dict[str, Any]:
    """선택된 option_id 를 그 옵션의 action(verb)·params 로 해석.

    그래프 wiring 이 verb 로 라우팅한다(adjust_query/ask_input/restart/end).
    모르는 id(타임아웃/오류 포함) → end(정직 종료) 로 안전 강등.
    """
    for o in (config.get("options") or []):
        if o.get("id") == option_id:
            return {
                "verb": o.get("action", "end"),
                "params": o.get("params", {}) or {},
                "prompt": o.get("prompt"),
                "option_id": option_id,
            }
    return {"verb": "end", "params": {}, "prompt": None, "option_id": option_id}


# ── 통합 단위: execution_result(model_dump) → 복구 메뉴 | None (execution_stage 가 호출) ──

def detect_recovery(execution_result: dict, config: dict | None = None) -> dict | None:
    """막힘이면 복구 메뉴 페이로드, 아니면 None.

    감지(is_blocked) + 메뉴(build_recovery_payload) + 설정 로드/가드를 한 단위로 묶어
    execution_stage 가 한 줄로 부른다(테스트 가능).

    config 미지정 시 load_actions(). **절대 raise 하지 않는다** — actions.yaml 로드/파싱/검사
    오류는 삼켜 None 반환 → 호출부가 별도 try 없이도 정상 실행이 보호됨(이 파일 자유 편집 전제).
    """
    try:
        cfg = config if config is not None else load_actions()
        if not isinstance(cfg, dict):
            return None
        todos = (execution_result or {}).get("todos", {})
        if is_blocked(todos, cfg):
            return build_recovery_payload(cfg, context={"reason": "data_insufficient"})
    except Exception:
        return None
    return None


__all__ = [
    "load_actions",
    "is_blocked",
    "build_recovery_payload",
    "resolve_choice",
    "detect_recovery",
]
