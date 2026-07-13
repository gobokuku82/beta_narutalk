"""Responder — ExecutionResult → ResponsePayload

4-Layer의 마지막 변환 — "기계 언어 → 사용자 언어" 역번역.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.core.logging import get_logger
from app.dream_agent.schemas.execution_result import ExecutionResult, TodoStatus
from app.dream_agent.schemas.response_payload import Attachment, ResponseFormat, ResponsePayload
from app.dream_agent.schemas.structured_query import (
    DEGRADE_OPS,
    SCOPE_PARAMS,
    StructuredQuery,
    scope_ask_text,
)
from app.dream_agent.tools.shared.display import is_infra, resolve as _resolve_display

logger = get_logger(__name__)

# ── 정직 degrade 문구 (사용자 언어 = response 레이어 책임) ──────────────────
# 왜 비었나 = 인과/예측/기여 *기능 미구현*. 데이터가 없어서가 아님(수치는 계산됨).
# LLM 에 빈 execution_summary 를 주면 "데이터 제공 안 됨"이라 지어내고 내부용어 누출 →
# 데이터 0 케이스는 결정론으로 진짜 이유를 말한다 (criteria_map C3 정직 degrade).
_DEGRADE_MESSAGES = {
    "diagnose": (
        "요청하신 '왜'(원인) 분석 기능은 아직 준비 중이에요. "
        "대신 해당 지표의 수치나 기간별 추이는 바로 보여드릴 수 있습니다."
    ),
    "forecast": (
        "향후 예측 기능은 아직 준비 중이에요. "
        "과거 실적과 기간별 추이는 바로 보여드릴 수 있습니다."
    ),
    "attribute": (
        "기여도(어떤 요인이 얼마나 영향을 줬는지) 분석 기능은 아직 준비 중이에요. "
        "요인별 실적 수치는 바로 보여드릴 수 있습니다."
    ),
}
_DEGRADE_DEFAULT = "요청하신 분석 기능은 아직 준비 중이에요. 관련 수치나 추이는 보여드릴 수 있습니다."
_DEGRADE_NEXT_ACTIONS = {
    "diagnose": ["해당 지표의 수치/기간별 추이 조회"],
    "forecast": ["과거 실적/추이 조회"],
    "attribute": ["요인별 실적 수치 조회"],
}


def build_degrade_payload(
    structured_query: StructuredQuery,
    exec_result: ExecutionResult,
) -> ResponsePayload | None:
    """정직 degrade payload — degrade op 이 *아무것도 실행 못 한* 경우만 결정론 렌더.

    None 반환 = 정상 LLM 경로 (degrade 아니거나 뭔가 실행됨). 순수 함수(LLM 무관).
      - intent.operation ∈ DEGRADE_OPS (diagnose/forecast/attribute) 그리고
      - exec_result.todos 비어있음 (= shim 이 빈 tasks → planning skip → 실행 0)
    todos 가 차 있으면(예: 텍스트 분석이 실행됨) LLM 이 실제 결과를 요약.
    """
    intent = structured_query.intent
    if intent is None:
        return None
    op = (intent.operation or "").lower()
    if op not in DEGRADE_OPS:
        return None
    if exec_result.todos:            # 뭔가 실행됨 → LLM 이 요약 (degrade 아님)
        return None
    return ResponsePayload(
        format=ResponseFormat.TEXT,
        text=_DEGRADE_MESSAGES.get(op, _DEGRADE_DEFAULT),
        next_actions=_DEGRADE_NEXT_ACTIONS.get(op, []),
        meta={"degraded": True, "operation": op},
    )


def build_insufficient_data_payload(
    exec_result: ExecutionResult,
) -> ResponsePayload | None:
    """데이터 불충분으로 분석이 통째로 막힌 경우 결정론 정직 degrade (B2.1 W3).

    None 반환 = 정상 LLM 경로. 발동 조건:
      - data_gate 가 SKIPPED 처리한 todo(data.reason == "data_insufficient")가 있고
      - collector 외에 COMPLETED 산출이 하나도 없음 (= 모든 분석/변환이 0건/부재에 막힘).
    부분 성공(다른 체인이 완료)이면 None → LLM 이 부분 결과 + skip 사유를 요약.

    순수 함수(LLM 무관). build_degrade_payload(미구현 기능)의 데이터 계약 버전 —
    criteria_map C3 정직 degrade. 데이터 0건을 결정론으로 정직히 답해, 표시 dispatcher 가
    빈 결과를 오해석할 위험을 차단. 인프라 tool 판별 = display.infra (구 'collector' 규약 대체).
    """
    todos = exec_result.todos
    if not todos:
        return None
    skipped_insuf = [
        r for r in todos.values()
        if r.status == TodoStatus.SKIPPED
        and isinstance(r.data, dict)
        and r.data.get("reason") == "data_insufficient"
    ]
    if not skipped_insuf:
        return None
    # 인프라 외 COMPLETED 산출이 있으면 부분 성공 → LLM 이 요약 (결정론 degrade 아님)
    produced = any(
        r.status == TodoStatus.COMPLETED and r.tool and not is_infra(r.tool)
        for r in todos.values()
    )
    if produced:
        return None
    details = [r.data.get("detail") for r in skipped_insuf if r.data.get("detail")]
    return ResponsePayload(
        format=ResponseFormat.TEXT,
        text=(
            "요청하신 분석에 필요한 데이터가 해당 조건에서 충분하지 않아(0건/부재) "
            "결과를 만들 수 없었습니다. 기간이나 대상을 바꿔 다시 시도해 주세요."
        ),
        next_actions=["기간을 넓혀 재요청", "다른 대상/조건으로 조회"],
        meta={"degraded": True, "reason": "data_insufficient", "details": details},
    )


def build_missing_scope_payload(
    exec_result: ExecutionResult,
) -> ResponsePayload | None:
    """스코프 param 미바인딩/비정형으로 실행이 막힌 경우 결정론 되묻기 (슬라이스 1-⑤, 헌법 D3).

    None 반환 = 정상 경로. 발동: executor param 경계가 SKIPPED 처리한 todo 중
    data.reason ∈ {missing_param, invalid_param} 이고 data.param ∈ SCOPE_PARAMS.
    되묻기 문구는 scope_ask_text(param) (scope_params.yaml 의 spec.ask). 미주입(빈 SCOPE_PARAMS)
    이면 blocked=[] → None → 일반 경로(inert). 자동 기본값 금지(D3) — 가정한 값 대신 되묻는다.
    부분 완료가 있어도 발동 — "스코프 없는 질문에 값을 단정하지 않는다"가 G2 의 DoD.
    이미 생성된 attachment 도 의도적으로 미표시 — 무스코프 수치가 든 산출물 제시는 같은 위반.
    단 실행이 FAILED 면 양보 — 실패 고지(ERROR 경로)가 우선 (I1, 리뷰 R-5). 순수 함수(LLM 무관).
    """
    if exec_result.overall_status == TodoStatus.FAILED:
        return None
    blocked = [
        r for r in exec_result.todos.values()
        if r.status == TodoStatus.SKIPPED
        and isinstance(r.data, dict)
        and r.data.get("reason") in ("missing_param", "invalid_param")
        and r.data.get("param") in SCOPE_PARAMS
    ]
    if not blocked:
        return None

    # M1-S2 (2026-06-12, G19 의도 단위화): ask 가 응답 *전체*를 점령해 완료된 비스코프 의도까지
    # 침묵시키던 M0 실측(축2)의 수술. ask 선두 불변(D3 — 스코프 값 단정 금지) + 완료 **서술**
    # 산출·파일만 뒤에 공존. 스코프 미정 *수치*(_render_metrics)는 의도적으로 계속 미표시.
    blocked_params = sorted({r.data.get("param") for r in blocked if r.data.get("param")})
    ask_lines: list[str] = []
    for p in blocked_params:
        text, ex = scope_ask_text(p)          # 도메인 선언 문구(scope_params.yaml spec.ask)
        ask_lines.append(text + (f" (예: {ex})" if ex else ""))
    ask = " ".join(ask_lines) + " 값을 가정하는 대신 여쭤봅니다."

    blocked_tools = sorted({r.tool for r in blocked if r.tool})
    parts = [ask]

    completed_sections = _narrative_sections(exec_result)   # display.narrative_keys 로 완료 서술 수집
    if completed_sections:
        parts.append(
            "지정과 무관하게 완료된 결과를 먼저 전해 드립니다:\n\n"
            + "\n\n".join(completed_sections)
        )
    parts.append("⏸ 값이 필요해 보류된 분석: " + ", ".join(blocked_tools))
    # S3 합류: 스코프 외 사유(드롭·데이터 부족)로 안 돈 분석도 침묵 금지 (G8 "사유 명시")
    skipped_note = _render_skipped_note(exec_result, exclude=set(blocked_tools))
    if skipped_note:
        parts.append(skipped_note)

    atts = _collect_attachments(exec_result)
    return ResponsePayload(
        format=ResponseFormat.TEXT,
        text="\n\n".join(parts),
        next_actions=["필요한 값을 포함해 다시 요청"],
        attachments=atts,
        meta={
            "degraded": True,
            "reason": "missing_scope",
            "blocked_tools": blocked_tools,
            "blocked_params": blocked_params,
        },
    )


# ── 결정론 표시 dispatcher (2c, 2026-06-09) — 받은 산출물 종류로 분류해 시각화 (LLM 0) ──
# 설계 모델: response = 표시 결정자. 서술은 tool(report_writer/summary_generator), response 는
# "있는 산출물을 종류별로 시각화"(text/excel/pdf/ppt/chart)만. 정직 degrade 는 앞 게이트가 처리.

# OutputFormat(structured_query) → ResponseFormat 직매핑 (거의 1:1).
_OUTPUT_TO_RESPONSE_FORMAT = {
    "text": ResponseFormat.TEXT,
    "pdf": ResponseFormat.PDF,
    "ppt": ResponseFormat.PPT,
    "excel": ResponseFormat.EXCEL,
    "image": ResponseFormat.IMAGE,
    "chart": ResponseFormat.CHART,
    "video": ResponseFormat.VIDEO,
    "mixed": ResponseFormat.MIXED,
}

# (2026-07-02) 파일 산출 artifact → kind 하드코딩 맵 제거 — attachment 는 tool 의
# display.attachment([{key,kind,multi}]) 선언에서 온다(_collect_attachments).

# metric 결정론 렌더에서 제외할 구조 노이즈 (표시 대상 아님).
_RENDER_NOISE = frozenset({
    "count", "file_no", "source_id", "is_mock", "reason", "detail", "artifact",
    "word_count", "char_count", "length", "report_markdown", "summary",
    # 구조/provenance — 답이 아닌 내부 메타 (raw-leak 방지, stage1 감사 C). "schema_version: <ver>" 류 차단.
    # label/value/unit 은 아래 _render_metrics 가 "label: value unit" 으로 합쳐 렌더(노이즈 아님).
    "schema_version", "op", "field",
})


def _find_artifact(exec_result: ExecutionResult, key: str) -> Any:
    """todo 결과들에서 produces key 의 첫 non-empty 값."""
    for r in exec_result.todos.values():
        data = r.data if isinstance(r.data, dict) else {}
        v = data.get(key)
        if v:
            return v
    return None


# (2026-07-02) _find_artifacts(복수 키 스캔) 제거 — 서술 수집이 _narrative_sections
# (display.narrative_keys 기반)로 대체되어 호출자 0. _find_artifact(단수, summary floor)는 유지.


def _narrative_sections(exec_result: ExecutionResult) -> list[str]:
    """완료 todo 의 서술형 산출을 per-todo display.narrative_keys 로 수집 (2026-07-02).

    과거엔 report_markdown/answer/recommendation_text 고정 키를 전역 스캔했다. 이제 각 tool 이
    display.narrative_keys 로 '어떤 산출 키가 서술인지' 선언한다. 미선언 tool = 서술 0 (honest
    floor 는 _render_metrics/summary). 순서 = todo 순서 × 선언 키 순서, 중복 제거.
    """
    out: list[str] = []
    for r in exec_result.todos.values():
        if r.status != TodoStatus.COMPLETED or not isinstance(r.data, dict):
            continue
        for key in _resolve_display(r.tool).narrative_keys:
            v = r.data.get(key)
            if isinstance(v, str) and v and v not in out:
                out.append(v)
    return out


_MAX_BREAKDOWN_LINES = 10


def _render_breakdowns(exec_result: ExecutionResult) -> str:
    """완료 todo 의 분해 산출(rows 표 · {그룹: 스칼라} dict)을 결정론 컴팩트 렌더 (M1-S1).

    or-체인·스칼라 한정 렌더가 차원분해 결과를 통째 침묵시키던 M0 실측
    (차원별 질의 — breakdown tool completed 인데 표출 0%, 3/3런)의 수술.
    행 수 cap 으로 단일 의도 응답을 시끄럽게 만들지 않음.
    """
    lines: list[str] = []
    for r in exec_result.todos.values():
        if r.status != TodoStatus.COMPLETED or not isinstance(r.data, dict):
            continue
        d = r.data
        table_key = _resolve_display(r.tool).table_key   # 표(행) 산출 키 (미선언=None)
        rows = d.get(table_key) if table_key else None
        if isinstance(rows, list) and rows and all(isinstance(x, dict) for x in rows):
            for row in rows[:_MAX_BREAKDOWN_LINES]:
                cells = " · ".join(
                    f"{k} {v}" for k, v in row.items()
                    if v is not None and not isinstance(v, (list, dict)) and k not in _RENDER_NOISE
                )
                if cells:
                    lines.append(f"- {cells}")
            if len(rows) > _MAX_BREAKDOWN_LINES:
                lines.append(f"  (+{len(rows) - _MAX_BREAKDOWN_LINES}행 더)")
            continue
        for k, v in d.items():
            if k.startswith("_") or k in _RENDER_NOISE or not isinstance(v, dict) or not v:
                continue
            if len(v) <= 20 and all(not isinstance(x, (list, dict)) for x in v.values()):
                head = " · ".join(f"{gk}: {gv}" for gk, gv in list(v.items())[:_MAX_BREAKDOWN_LINES])
                lines.append(f"{k} — {head}")
    return "\n".join(lines)


def _render_insights(exec_result: ExecutionResult) -> str:
    """insights(list[{title, description, ...}]) 산출의 결정론 렌더 (M1-S1c, 2026-06-12).

    T3 재실행 실측: 해석 tool 이 completed 인데 산출 키(insights)가 표시 어휘 밖이라
    '개선안' 의도가 통째 침묵 — 진단 false-red 와 동종 함정의 실증. 상한 5건.
    """
    lines: list[str] = []
    for r in exec_result.todos.values():
        if r.status != TodoStatus.COMPLETED or not isinstance(r.data, dict):
            continue
        for key in _resolve_display(r.tool).insight_keys:   # 인사이트 산출 키 (미선언=없음)
            ins = r.data.get(key)
            if not isinstance(ins, list):
                continue
            for it in ins[:5]:
                if isinstance(it, dict):
                    title = it.get("title") or ""
                    desc = it.get("description") or ""
                    if title or desc:
                        lines.append(f"- {title}{': ' if title and desc else ''}{desc}")
                elif isinstance(it, str) and it:
                    lines.append(f"- {it}")
    return ("주요 인사이트·제안\n" + "\n".join(lines)) if lines else ""


# SKIPPED 사유 → 사용자 어휘 (M1-S3 가시화 — G8: "B의 부재가 침묵" 금지)
_SKIP_REASON_KO = {
    "missing_param": "필수 입력 누락",
    "invalid_param": "입력 형식 오류",
    "data_insufficient": "데이터 부족",
    "not_executed": "선행 의존 미해결로 미실행",
}


def _render_skipped_note(exec_result: ExecutionResult, exclude: set[str] | None = None) -> str:
    """실행되지 않은 분석 단계의 결정론 고지 한 줄 (인프라 tool = display.infra 는 제외)."""
    items: list[str] = []
    for r in exec_result.todos.values():
        if r.status != TodoStatus.SKIPPED or not r.tool or is_infra(r.tool):
            continue
        if exclude and r.tool in exclude:
            continue
        reason = r.data.get("reason") if isinstance(r.data, dict) else None
        items.append(f"{r.tool}({_SKIP_REASON_KO.get(reason, reason or '건너뜀')})")
    if not items:
        return ""
    head = ", ".join(items[:5]) + (f" 외 {len(items) - 5}건" if len(items) > 5 else "")
    return f"※ 실행되지 않은 분석: {head}"


def _render_metrics(exec_result: ExecutionResult) -> str:
    """metric/숫자 산출을 결정론 'label: value' 로 text 시각화 (서술 tool 부재 시 정상 분기).

    completed todo 의 표시가능 스칼라만. 구조 노이즈·복합값(raw 덤프)은 제외.
    """
    lines: list[str] = []
    seen: set[str] = set()
    for r in exec_result.todos.values():
        if r.status != TodoStatus.COMPLETED or not isinstance(r.data, dict):
            continue
        d = r.data
        # metric tool 관례 {label, value, unit} → "label: value unit" 한 줄 (value 만 떨궈 무의미해지는 것 방지)
        val = d.get("value")
        if "label" in d and val is not None and not isinstance(val, (list, dict)):
            label = str(d["label"])
            if label not in seen:
                seen.add(label)
                unit = d.get("unit") or ""
                lines.append(f"{label}: {val}{unit}")
            continue
        for k, v in d.items():
            if k in seen or k.startswith("_") or k in _RENDER_NOISE:
                continue
            if v is None or isinstance(v, (list, dict)):
                continue  # 스칼라만 (복합은 단순 text 렌더 대상 아님)
            seen.add(k)
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


def _download_url(local_path: str) -> str | None:
    """로컬 산출물 경로 → /api/files/download 링크 (data/ 하위 상대경로). data 밖이면 None."""
    parts = Path(str(local_path)).parts
    if "data" not in parts:
        return None
    rel = "/".join(parts[parts.index("data") + 1:])
    return f"/api/files/download?p={quote(rel)}" if rel else None


def _collect_attachments(exec_result: ExecutionResult) -> list[Attachment]:
    """파일 산출을 attachment 로 분류 + 다운로드 url 부여 (tool 의 display.attachment 선언 기반).

    display.attachment = [{key, kind, multi}]. multi=True 면 그 키가 경로 list(예 차트 여러 장),
    아니면 단일 경로. 미선언 tool = 첨부 0 (honest). data/ 하위 경로만 다운로드 url 부여.
    """
    atts: list[Attachment] = []
    for r in exec_result.todos.values():
        data = r.data if isinstance(r.data, dict) else {}
        for att in _resolve_display(r.tool).attachment:
            key = att.get("key")
            if not key:
                continue
            kind = att.get("kind", "link")
            val = data.get(key)
            if not val:
                continue
            paths = val if (att.get("multi") and isinstance(val, list)) else [val]
            atts.extend(
                Attachment(kind=kind, path=str(p), url=_download_url(str(p)))
                for p in paths if p
            )
    return atts


def build_display_payload(
    structured_query: StructuredQuery,
    exec_result: ExecutionResult,
) -> ResponsePayload:
    """결정론 표시 dispatcher — 받은 산출물 종류로 분류해 ResponsePayload 조립 (LLM 0).

    text 시각화: report_markdown > summary > metric 렌더 (있는 걸 text 로 — 동등 분기, 우선순위는
      동시 존재 시만). 파일 시각화: pdf/excel/ppt/chart → attachments.
    format: goal.output_format 직매핑 (halted=error). 정직 degrade 는 호출 전 게이트가 처리.

    (2026-06-11 정직화) FAILED 실행은 성공 문구 fallback("분석을 완료했습니다.") 금지 —
    실패 사실·중단 지점을 먼저 고지하고, 부분 산출이 있으면 그 뒤에 표시. error 필드 설정.
    """
    if exec_result.overall_status == TodoStatus.FAILED:
        fmt = ResponseFormat.ERROR
    else:
        of = getattr(getattr(structured_query, "goal", None), "output_format", None)
        of_val = of.value if hasattr(of, "value") else (of or "text")
        fmt = _OUTPUT_TO_RESPONSE_FORMAT.get(of_val, ResponseFormat.TEXT)

    summary = _find_artifact(exec_result, "summary")   # 'summary' = 프레임 공통 floor 키(도메인 무관)

    # M1-S1 (2026-06-12): or-체인 단일선택 → 의도별 **합성**. 서술 산출은 tool 의
    # display.narrative_keys 선언에서 수집(구 report_markdown/answer/... 고정키 대체).
    # 수치·분해 렌더를 서술에 없는 것만 덧붙인다. summary 는 서술이 없을 때만 본문 승격.
    sections = _narrative_sections(exec_result)
    insights_text = _render_insights(exec_result)   # S1c — insights(display.insight_keys)도 서술 산출
    if insights_text:
        sections.append(insights_text)
    if not sections and isinstance(summary, str) and summary:
        sections.append(summary)

    metrics_text = _render_metrics(exec_result)
    if sections and metrics_text:
        narrative_blob = "\n".join(sections)
        metrics_text = "\n".join(
            ln for ln in metrics_text.splitlines()
            if ln.split(":", 1)[-1].strip() not in narrative_blob   # 서술이 이미 말한 수치는 중복 금지
        )
    breakdown_text = _render_breakdowns(exec_result)
    data_block = "\n".join(p for p in (metrics_text, breakdown_text) if p)
    if data_block:
        sections.append(f"주요 수치\n{data_block}" if len(sections) else data_block)

    skipped_note = _render_skipped_note(exec_result)   # M1-S3 가시화 (G8: 부재의 침묵 금지)
    artifact_text = "\n\n".join(sections) if sections else ""
    if artifact_text and skipped_note:
        artifact_text = f"{artifact_text}\n\n{skipped_note}"

    error_msg: str | None = None
    if fmt == ResponseFormat.ERROR:
        failed_n = sum(1 for r in exec_result.todos.values() if r.status == TodoStatus.FAILED)
        completed_n = sum(1 for r in exec_result.todos.values() if r.status == TodoStatus.COMPLETED)
        note = f"분석 중 일부 단계가 실패했습니다 (완료 {completed_n} · 실패 {failed_n}"
        if exec_result.halted_at:
            note += f" · 중단 지점: {exec_result.halted_at}"
        note += "). 아래는 실패 전까지의 부분 결과입니다." if (
            isinstance(artifact_text, str) and artifact_text
        ) else ")."
        text = (
            f"{note}\n\n{artifact_text}"
            if isinstance(artifact_text, str) and artifact_text
            else note
        )
        error_msg = exec_result.halt_reason or note
    elif artifact_text:
        text = artifact_text
    elif not exec_result.todos:
        # 실행된 todo 자체가 0 (빈 카탈로그·미주입·팀선택 0) → 거짓 "완료" 금지 (헌법 I1).
        text = "실행된 분석 단계가 없습니다."
    elif any(
        r.status == TodoStatus.SKIPPED for r in exec_result.todos.values()
    ) and not any(
        r.status == TodoStatus.COMPLETED and r.tool and not is_infra(r.tool)
        for r in exec_result.todos.values()
    ):
        # 분석 산출 없이 "완료" 둔갑 금지 (헌법 I1, 슬라이스 1 + 리뷰 R-6) — 인프라 tool 만 완료된
        # 채 분석 단계가 전부 건너뜀이어도 발동. 인프라 판별 = display.infra (구 collector convention).
        skipped_n = sum(
            1 for r in exec_result.todos.values() if r.status == TodoStatus.SKIPPED
        )
        text = f"분석 단계가 실행되지 못해 결과를 만들지 못했습니다 (건너뜀 {skipped_n}건)."
    else:
        text = "분석을 완료했습니다."

    return ResponsePayload(
        format=fmt,
        text=text,
        summary=summary if isinstance(summary, str) else None,
        attachments=_collect_attachments(exec_result),
        meta={"display": True},   # 결정론 표시 식별(관측) — LLM 산출과 구분
        error=error_msg,
    )


class Responder:
    """Response 레이어 — ExecutionResult → ResponsePayload (결정론 표시, LLM 0).

    2c(2026-06-09): LLM 재서술 제거. 서술은 tool(report_writer/summary_generator), response 는
    산출물을 종류별로 시각화(build_display_payload). 정직 degrade 2 게이트는 앞단 유지.
    """

    async def respond(
        self,
        structured_query: StructuredQuery,
        exec_result: ExecutionResult,
    ) -> ResponsePayload:
        # 정직 degrade: 실행할 게 없던 인과/예측/기여 요청은 결정론으로 답.
        degrade = build_degrade_payload(structured_query, exec_result)
        if degrade is not None:
            logger.info("response honest-degrade (deterministic)",
                        operation=degrade.meta.get("operation"))
            return degrade

        # 스코프 param 미바인딩/비정형으로 막힌 경우 — 값 가정 대신 결정론 되묻기 (슬라이스 1-⑤, D3).
        # insufficient 보다 먼저: 스코프 SKIP 의 하류 cascade 가 data_insufficient 로도 잡히는데,
        # 원인(스코프 없음)이 증상(데이터 0건)보다 정확한 안내라서. 미주입(빈 SCOPE_PARAMS)=inert.
        scope_ask = build_missing_scope_payload(exec_result)
        if scope_ask is not None:
            logger.info("response honest-ask (missing scope, deterministic)",
                        blocked=scope_ask.meta.get("blocked_tools"))
            return scope_ask

        # 데이터 불충분(0건/부재)으로 전 분석이 막힌 경우도 결정론 정직 degrade (B2.1 게이트 cascade).
        insufficient = build_insufficient_data_payload(exec_result)
        if insufficient is not None:
            logger.info("response honest-degrade (data insufficient, deterministic)",
                        details=insufficient.meta.get("details"))
            return insufficient

        # 표시 dispatcher: 산출물 종류로 분류 → 시각화 (LLM 없음 — 서술은 tool 책임).
        payload = build_display_payload(structured_query, exec_result)
        payload.meta.setdefault(
            "completed_todos",
            sum(1 for r in exec_result.todos.values() if r.status == TodoStatus.COMPLETED),
        )
        payload.meta.setdefault("total_duration_ms", exec_result.total_duration_ms)
        logger.info("response done (deterministic display)",
                    format=payload.format.value, attachments=len(payload.attachments))
        return payload
