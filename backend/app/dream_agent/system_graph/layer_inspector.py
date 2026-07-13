"""Sprint 13 I11-a — Layer Guard.

각 layer(cognitive/planning/execution/response) 출력 최소 검증 + JSONL 로그.

설계:
  - fatal: `_graph_runner_with_resume`가 complete(aborted) emit 후 중단
  - warning: 그래프 계속 진행, complete에 guard_warnings 누적
  - 모든 발견은 logs/layer_guard.jsonl에 append-only 기록 (POC 페어 누적)

R4 발견 보완: 각 layer는 해당 "기대 key"가 data에 없으면 inspect skip
  (planning reject 경로 `{"response": {...}}` 또는 error-only emit 시 false fatal 방지).

Sprint 14 A3 (D10 2026-04-23): dict literal 5곳 제거, `ErrorCodes` 중앙 카탈로그
참조로 통합. error_codes.py 가 단일 진실 소스 (22_error_codes v1.0+).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from app.core.error_codes import ErrorCodes


# (2026-06-11) CWD 상대경로 → 리포 루트 고정. 과거 상대경로 탓에 실행 위치(루트 서버 vs
# backend pytest)에 따라 페어 로그가 두 파일(루트 logs/ 111건 실페어 + backend/logs/ 63건
# 테스트 노이즈)로 분열됐음. 테스트는 conftest autouse 픽스처가 tmp 로 격리.
_REPO_ROOT = Path(__file__).resolve().parents[4]
_LOG_PATH = _REPO_ROOT / "logs" / "layer_guard.jsonl"
_LOG_LOCK = threading.Lock()


# ── '유의미 쿼리' 판정 보강 필드 (2026-07-02 — 도메인 중립화) ──────────────
# 과거엔 cognitive 가드가 targets.brand / intent.domain 같은 도메인 필드로 '유의미'를 판정해
# brand 없는 정상 쿼리를 COGNITIVE_EMPTY_QUERY(fatal)로 오판할 수 있었다. 이제 구조적 유효성
# (tasks 또는 intent 존재)만 본다. 추가 신호가 필요한 도메인은 settings.MEANINGFUL_QUERY_FIELDS
# (dotted-path 목록)로만 확장한다 — 미설정(기본 [])이면 순수 구조적 검사(도메인 필드 요구 0).
_DEFAULT_MEANINGFUL_FIELDS: list[str] = []


def _meaningful_query_fields() -> list[str]:
    """설정 구동 보강 필드 목록. 미설정=[] → 순수 구조적 검사. lazy import(순환 안전·inert)."""
    try:
        from app.core.config import settings
        return getattr(settings, "MEANINGFUL_QUERY_FIELDS", _DEFAULT_MEANINGFUL_FIELDS) or []
    except Exception:
        return _DEFAULT_MEANINGFUL_FIELDS


def _dig(data: Any, dotted: str) -> Any:
    """sq(dict)에서 dotted-path(예 'targets.brand') 값 조회. 경로 부재 시 None(무해)."""
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def inspect_layer_output(node: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Layer별 출력 검증. 발견된 문제 목록 반환 (빈 리스트면 OK).

    Args:
        node: "cognitive" | "planning" | "execution" | "response"
        data: chunk에서 해당 노드가 emit한 update dict
              예: planning 정상 → {"plan": {...}}
                  planning reject → {"response": {...}}  (skip 대상)

    Returns:
        [{"code", "layer", "severity", "message", "detail"}, ...]
    """
    errors: list[dict[str, Any]] = []

    if node == "cognitive":
        if "structured_query" not in data:
            return []
        sq = data["structured_query"] or {}
        # (2026-07-02) 유의미 = 구조적 유효성만: tasks 비어있지 않음 OR intent 존재.
        # 과거의 brand/intent.domain 하드코딩 제거 — brand 없는 정상 쿼리 오판 방지. honest
        # degrade(tasks 만 빈 정상 쿼리)는 intent 존재로 통과. 추가 신호는 설정으로만 확장.
        has_tasks = bool(sq.get("tasks"))
        intent = sq.get("intent")
        has_intent = isinstance(intent, dict) and bool(intent)
        has_configured = any(bool(_dig(sq, p)) for p in _meaningful_query_fields())
        if not sq or (not has_tasks and not has_intent and not has_configured):
            errors.append({
                **ErrorCodes.COGNITIVE_EMPTY_QUERY,
                "detail": {"structured_query": sq},
            })

    elif node == "planning":
        if "plan" not in data:
            return []
        plan = data["plan"] or {}
        todos = plan.get("todos", [])
        if not todos:
            errors.append({
                **ErrorCodes.PLANNING_EMPTY_PLAN,
                "detail": {"plan": plan},
            })

    elif node == "execution":
        if "execution_result" not in data:
            return []
        er = data["execution_result"] or {}
        todos_raw = er.get("todos", [])
        # todos는 dict({todo_id: {...}}) 또는 list 형태 가능 — 실제 코드는 dict
        if isinstance(todos_raw, dict):
            todos_list = list(todos_raw.values())
        elif isinstance(todos_raw, list):
            todos_list = todos_raw
        else:
            todos_list = []
        if todos_list:
            # (2026-06-11) "success" → "completed" 어휘 수정 — TodoStatus enum 에 "success"
            # 는 존재하지 않음(spec 20 §3.3 이 2026-05-15 문서화한 버그). 옛 비교는 succeeded
            # 가 항상 0 이라 부분 실패가 전부 ALL_FAILED(fatal)로 격상됐고(루트 logs 06-10
            # 실발화: 12개 중 1 실패 → "모든 Todo 실행이 실패"), PARTIAL(warning)은 도달 불가.
            succeeded = [
                t for t in todos_list
                if isinstance(t, dict) and t.get("status") == "completed"
            ]
            failed = [
                t for t in todos_list
                if isinstance(t, dict) and t.get("status") == "failed"
            ]
            skipped_count = sum(
                1 for t in todos_list
                if isinstance(t, dict) and t.get("status") == "skipped"
            )
            if len(succeeded) == 0 and len(failed) > 0:
                errors.append({
                    **ErrorCodes.EXECUTION_ALL_FAILED,
                    "detail": {
                        "failed_count": len(failed),
                        "skipped_count": skipped_count,
                    },
                })
            elif len(failed) > 0:
                errors.append({
                    **ErrorCodes.EXECUTION_PARTIAL_FAILED,
                    "message": f"{len(failed)}개 Todo가 실패했습니다.",  # 개수 반영 override
                    "detail": {
                        "failed_count": len(failed),
                        "succeeded_count": len(succeeded),
                        "skipped_count": skipped_count,
                    },
                })

    elif node == "response":
        if "response" not in data:
            return []
        resp = data["response"] or {}
        text = resp.get("text", "") if isinstance(resp, dict) else ""
        if not text.strip():
            errors.append({
                **ErrorCodes.RESPONSE_EMPTY,
                "detail": {"response": resp},
            })

    return errors


def summarize_state(final_state: dict[str, Any]) -> dict[str, Any]:
    """민감/큰 필드 제거한 state 요약 (JSONL 로그용, 파일 크기 제어)."""
    sq = final_state.get("structured_query") or {}
    plan = final_state.get("plan") or {}
    er = final_state.get("execution_result") or {}

    teams = list({
        t.get("team")
        for t in plan.get("todos", [])
        if t.get("team")
    })

    # (2026-07-02) 하드코딩 brand 제거 → 도메인 중립 구조 요약. 설정 선언 필드만 값 있으면 로깅.
    intent = sq.get("intent") if isinstance(sq.get("intent"), dict) else {}
    summary: dict[str, Any] = {
        "tasks": sq.get("tasks"),
        "intent_operation": intent.get("operation"),
        "plan_todos": len(plan.get("todos", [])),
        "plan_teams": teams,
        "execution_todos_total": len(er.get("todos", [])) if er else 0,
    }
    for path in _meaningful_query_fields():
        val = _dig(sq, path)
        if val:
            summary[path] = val
    return summary


def append_guard_log(entry: dict[str, Any]) -> None:
    """thread-safe JSONL append. 디렉토리 없으면 생성."""
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, default=str)
    with _LOG_LOCK:
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
