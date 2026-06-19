"""Planner — StructuredQuery → Plan (Todo[] + DAG)

3계층 프롬프트 (Sprint 9-2):
  Stage 1: team_selector  — "어느 팀?"
  Stage 2: agent_selector — "팀 내 어떤 Agent?"
  Stage 3: todo_builder   — "Agent의 Tool로 Todo + DAG"

각 단계 프롬프트가 분리되어 LLM이 관련 정보만 봄 → 집중도 향상.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.logging import get_logger
from app.dream_agent.llm_manager import get_llm_client
from app.dream_agent.schemas.structured_query import SCOPE_PARAMS, StructuredQuery, TaskType

logger = get_logger(__name__)

# Paths
CATALOG_PATH = Path(__file__).parent / "catalog" / "team_catalog.yaml"
PROMPTS_DIR = Path(__file__).parent.parent / "llm_manager" / "prompts"

# ───────────────────────────────────────────────────────
# Subject-coherence 게이트 (F2 수정 — 2026-06-04)
#
# 문제(일반화 테스트 실측): cognitive 가 인과/인사이트 task 를
# 라벨링하면 planning 이 텍스트 파이프로 들어가, *숫자 주제* 질문에
# 무관한 텍스트 항목을 분석해 자신만만한 (틀린) 리포트를 씀.
# 근본: 해석 tool 의 필수입력이 텍스트 수집 체인 전체를 빨아들이고,
# Stage3 프롬프트 default 가 텍스트 collector 로 기운다.
#
# 게이트: 텍스트 의도(텍스트 task 또는 텍스트 주제)가 없으면
# 텍스트-데이터 tool 을 Stage3 메뉴에서 제외 → LLM 이 고를 수 없음 → 숫자/빈-plan 으로 정직 degrade.
# 식별 = tool 이 선언한 *텍스트 데이터 산출물* (이름 denylist 아님, 데이터 계약 기반).
# ───────────────────────────────────────────────────────

# 주제-결속(텍스트) 데이터 산출물은 카탈로그가 선언한다 (도메인 무관 — 하드코딩 이름·명명 휴리스틱 아님).
#   catalog["subject_bound_artifacts"] = [<artifact_name>, ...]
# = collector→preprocessor→분석→해석 텍스트 체인의 input/output 산출물 이름들.
# 미선언/빈 카탈로그 = 빈 set → subject-coherence 게이트가 잡을 tool 0 → dormant(no-op).

# 텍스트 파이프를 정당화하는 task id — 설정-주입(도메인 등록), 기본 빈 set(도메인 무관).
# 빈 카탈로그에선 subject-coherence/텍스트-helper 가 dormant(no-op).
_TEXT_INTENT_TASKS: set[str] = set()

# 주제가 텍스트 분석임을 시사하는 자연어 마커 — 설정-주입(도메인 등록), 기본 빈 tuple(도메인 무관).
# cognitive 가 텍스트 task 를 놓쳐도 주제 마커로 구제. 빈 tuple = 마커 구제 비활성.
_SUBJECT_INTENT_MARKERS: tuple[str, ...] = ()


def _subject_bound_artifacts(catalog: dict) -> set[str]:
    """카탈로그가 선언한 주제-결속(텍스트) 데이터 산출물 집합 — 미선언 시 빈 set(게이트 dormant)."""
    return set(catalog.get("subject_bound_artifacts") or [])


def _tool_is_subject_bound(tool: dict, subject_artifacts: set[str]) -> bool:
    """tool 이 주제-결속(텍스트) 데이터에 의존하는가 — 데이터 계약 기반(이름 denylist·명명 휴리스틱 아님).

    선언된 produces/consumes/params_required 중 하나라도 카탈로그의 subject_bound_artifacts
    와 겹치면 True (collector→preprocessor→해석 체인 어디든). subject_artifacts 빈 set 이면 항상 False.
    """
    if not subject_artifacts:
        return False
    io = (
        set(tool.get("produces") or [])
        | set(tool.get("consumes") or [])
        | set(tool.get("params_required") or [])
    )
    return bool(io & subject_artifacts)


def _collect_subject_bound_tool_names(catalog: dict) -> set[str]:
    """카탈로그 전체에서 주제-결속(텍스트) tool 이름 집합 (post-filter 용)."""
    subject_artifacts = _subject_bound_artifacts(catalog)
    if not subject_artifacts:
        return set()
    names: set[str] = set()
    for team in (catalog.get("teams", {}) or {}).values():
        for agent in (team.get("agents", {}) or {}).values():
            for t in (agent.get("tools", []) or []):
                if _tool_is_subject_bound(t, subject_artifacts) and t.get("name"):
                    names.add(t["name"])
    return names


# ───────────────────────────────────────────────────────
# Pydantic models (Plan output)
# ───────────────────────────────────────────────────────

class PlannedTodo(BaseModel):
    """Planning이 생성하는 단일 Todo (Execution이 소비)"""
    id: str
    task_type: str
    team: str | None = None
    agent: str | None = None
    tool: str | None = None
    tool_params: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    priority: int = 1
    rationale: str = ""


class Plan(BaseModel):
    """Planning 산출물"""
    teams_selected: list[str] = Field(default_factory=list)
    todos: list[PlannedTodo] = Field(default_factory=list)
    dag: dict[str, list[str]] = Field(default_factory=dict)
    plan_notes: str = ""
    gaps: list[str] = Field(default_factory=list)   # ② planning 자가평가: 부족한 것(미바인딩 param 등)
                                                     # 진단·관측용 (LLM 무관 결정론). 추후 graceful degrade 의 씨앗.


# ───────────────────────────────────────────────────────
# DAG validation
# ───────────────────────────────────────────────────────

def detect_cycle(dag: dict[str, list[str]]) -> str | None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {k: WHITE for k in dag}
    parent: dict[str, str | None] = {k: None for k in dag}

    def dfs(u: str) -> list[str] | None:
        color[u] = GRAY
        for v in dag.get(u, []):
            if v not in color:
                continue
            if color[v] == GRAY:
                path = [v, u]
                x = parent[u]
                while x is not None and x != v:
                    path.append(x)
                    x = parent[x]
                if x == v:
                    path.append(v)
                return list(reversed(path))
            if color[v] == WHITE:
                parent[v] = u
                found = dfs(v)
                if found:
                    return found
        color[u] = BLACK
        return None

    for node in list(color.keys()):
        if color[node] == WHITE:
            cyc = dfs(node)
            if cyc:
                return " -> ".join(cyc)
    return None


def apply_subject_coherence_filter(
    plan: Plan, subject_tool_names: set[str], allow_text: bool,
) -> Plan:
    """텍스트 의도 없으면 주제-결속(텍스트) todo 를 *확정* 제거하고 DAG/deps 정리 (F2 게이트 post-filter).

    Status: complete — menu-filter(_get_agent_tools) 가 메뉴에서 빼도 LLM 이 Stage3
    프롬프트의 하드코딩 예시(해석 tool 등)를 복사할 수 있으므로, 결정론적으로
    재차 제거한다. menu-filter 와 동일 규칙(subject_tool_names).
    Pure — plan 을 in-place 수정 후 반환 (단위테스트 대상).
    """
    if allow_text:
        return plan
    drop = {t.id for t in plan.todos if t.tool in subject_tool_names}
    if not drop:
        return plan
    plan.todos = [t for t in plan.todos if t.id not in drop]
    for t in plan.todos:
        t.depends_on = [d for d in t.depends_on if d not in drop]
    plan.dag = {
        k: [d for d in v if d not in drop]
        for k, v in plan.dag.items() if k not in drop
    }
    plan.plan_notes = (plan.plan_notes or "") + \
        f" [subject-coherence: 주제-결속(텍스트) todo {len(drop)}개 제거 (텍스트 의도 없음)]"
    logger.info("subject-coherence post-filter dropped subject-bound todos", count=len(drop))
    return plan


# ───────────────────────────────────────────────────────
# Dataflow 체인 완성 (결정론) — 2026-06-05
#
# Stage3 LLM 이 고정 전처리 체인(예: collector→normalizer→
# preprocessor→분석)에서 필수 tool 을 빠뜨리면 체인이 끊겨 분석 input=0
# (~40% silent-0 실측). tool 의 선언된 produces/consumes 로 "consumer 가 먹는
# artifact 의 생산자가 plan 에 있는가" 검사 → 없으면 카탈로그 생산자를 삽입·배선.
# 하드코딩 체인 아님 — 카탈로그 메타 기반(신규 체인은 consumes/produces 선언만 하면 자동).
# ───────────────────────────────────────────────────────

def _build_tool_index(catalog: dict) -> dict[str, dict]:
    """tool_name → {agent, team, task_type, consumes, produces} (카탈로그 평면화)."""
    idx: dict[str, dict] = {}
    for team_name, team in (catalog.get("teams") or {}).items():
        for agent_name, agent in (team.get("agents") or {}).items():
            handles = agent.get("handles_tasks") or []
            for t in (agent.get("tools") or []):
                name = t.get("name")
                if not name:
                    continue
                idx[name] = {
                    "agent": agent_name,
                    "team": team_name,
                    "task_type": handles[0] if handles else "data_collection",
                    "consumes": list(t.get("consumes") or []),
                    "produces": list(t.get("produces") or []),
                    "params_required": list(t.get("params_required") or []),  # ② gap-check
                    "params_optional": list(t.get("params_optional") or []),  # R-1 optional period 바인딩
                }
    return idx


def _build_producer_index(tool_index: dict[str, dict]) -> dict[str, str]:
    """artifact → 생산 tool_name. 복수면 결정론적으로 sorted-first."""
    prod: dict[str, str] = {}
    for name in sorted(tool_index):
        for art in tool_index[name]["produces"]:
            prod.setdefault(art, name)
    return prod


def detect_plan_gaps(plan: Plan, tool_index: dict[str, dict]) -> list[str]:
    """② planning 자가평가 — plan 이 *실행 전*에 못 채우는 것을 결정론으로 잡는다 (LLM 무관).

    현 체크: 각 todo 의 카탈로그 `params_required` 가 (a) todo.tool_params 또는 (b) 직속
    upstream(depends_on) 산출 artifact 로 채워지나. 못 채우면 gap.
    예: metric tool 은 period 필수인데 기간 없는 질문 → tool_params 에 period 부재
        → gap → (추후) 크래시 대신 "기간 알려주세요" 정직 degrade 의 씨앗.

    Pure — plan 불변, gap 리스트만 반환. (params_required 가 카탈로그에 정확해야 잡힘 —
    drift 면 못 잡으니, drift 수정이 선행 = "기본부터 고침". [[project_catalog_code_drift]])
    """
    produced_by: dict[str, set[str]] = {
        t.id: set(tool_index.get(t.tool or "", {}).get("produces", [])) for t in plan.todos
    }
    gaps: list[str] = []
    for t in plan.todos:
        required = tool_index.get(t.tool or "", {}).get("params_required", [])
        if not required:
            continue
        upstream: set[str] = set()
        for dep in t.depends_on:
            upstream |= produced_by.get(dep, set())
        for p in required:
            # 스코프 param(period 류)은 상류 artifact 로 충족 안 됨 — executor 가 주입을
            # 금지하므로(슬라이스 1, 헌법 R2) plan 자가평가도 같은 진실로 gap 판정.
            if p in t.tool_params or (p in upstream and p not in SCOPE_PARAMS):
                continue
            gaps.append(f"{t.id}({t.tool}): 필수 param '{p}' 미바인딩")
    return gaps


def _prev_month(ym: str) -> str | None:
    """'2026-04' → '2026-03' (연 경계: '2026-01' → '2025-12'). 'YYYY-MM' 아니면 None."""
    parts = ym.strip().split("-")
    if len(parts) != 2 or not (parts[0].isdigit() and len(parts[0]) == 4 and parts[1].isdigit()):
        return None
    y, mo = int(parts[0]), int(parts[1])
    if not 1 <= mo <= 12:
        return None
    return f"{y - 1}-12" if mo == 1 else f"{y}-{mo - 1:02d}"


def _resolved_month(sq) -> str | None:
    """쿼리의 절대 월(YYYY-MM). targets.period.resolved > window 순.

    월 범위(01~12) 검증 + zero-pad 정규화('2026-4'→'2026-04') — 슬라이스 1-③.
    '2026-13' 류(LLM 환각)는 None = gap 유지 → 경계 SKIP → "기간을 알려주세요" 정직 경로.
    (구버전은 digit 여부만 봐서 '2026-13' 이 바인딩되고, '2026-4' 는 startswith 0건이었음.)
    """
    period = getattr(getattr(sq, "targets", None), "period", None)
    if period is None:
        return None
    for cand in (getattr(period, "resolved", None), getattr(period, "window", None)):
        if isinstance(cand, str):
            s = cand.strip()
            parts = s.split("-")
            if len(parts) == 2 and len(parts[0]) == 4 and parts[0].isdigit() and parts[1].isdigit():
                mo = int(parts[1])
                if 1 <= mo <= 12:
                    return f"{parts[0]}-{mo:02d}"
    return None


def bind_temporal_params(plan: Plan, sq, tool_index: dict) -> Plan:
    """시간 param 결정론 바인딩 — stage3 LLM 이 놓친 period / period_a·period_b 를 쿼리 기간으로 채운다.

    · period 필수/선택 tool      → period   = 쿼리 절대월 (선택도 바인딩 — R-1, 무언 전체기간 확장 방지)
    · period_a·period_b 필수(MoM) → period_b = 쿼리월 / period_a = 직전 달 (MoM = 정의상 전월 대비)

    날짜 산술은 LLM 보다 결정론이 정확 → 여기서 결정론으로. setdefault 라 LLM 이 이미 채운 값은
    안 덮음(멱등). 쿼리월이 절대화 안됐으면(YYYY-MM 아님) 건너뜀 → gap 유지(정직, B2 reference-date 대기).
    Pure-ish — plan.todos[].tool_params 만 보강, 구조 불변. (R3 param 바인딩, 2026-06-09)
    """
    month = _resolved_month(sq)
    if not month:
        return plan
    prev = _prev_month(month)
    for t in plan.todos:
        meta = tool_index.get(t.tool or "", {})
        required = meta.get("params_required", [])
        optional = meta.get("params_optional", [])
        if "period_a" in required and "period_b" in required:
            t.tool_params.setdefault("period_b", month)
            if prev:
                t.tool_params.setdefault("period_a", prev)
        elif "period" in required or "period" in optional:
            # optional period 도 결정론 바인딩 (적대 리뷰 R-1, 2026-06-12): 구버전에선 상류
            # 데이터 주입(폐지된 'all' 오염 경로)이 우연히 월-정합을 전파했음 — 월 쿼리에서
            # optional tool 이 무언 전체기간으로 넓어지지 않게 정공법으로 대체. 값은 쿼리에서만(R2).
            t.tool_params.setdefault("period", month)
    return plan


def complete_dataflow_chain(plan: Plan, catalog: dict) -> Plan:
    """consumer 가 먹는 artifact 의 생산자가 plan 에 없으면 카탈로그 생산자를 삽입·배선 (멱등·순수).

    Status: complete — Stage3 LLM 의 전처리 tool 누락(예 review_normalizer) 결정론 보강.
    삽입 시 depends_on/dag 를 배선해 생산자가 소비자보다 앞 phase 에 오도록 한다.
    """
    tool_index = _build_tool_index(catalog)
    producer_index = _build_producer_index(tool_index)
    inserted = 0
    guard = 0

    while guard < 100:
        guard += 1
        produced: dict[str, list[str]] = {}
        for t in plan.todos:
            for art in tool_index.get(t.tool or "", {}).get("produces", []):
                produced.setdefault(art, []).append(t.id)

        mutated = False
        for t in list(plan.todos):
            meta = tool_index.get(t.tool or "")
            if not meta:
                continue
            for art in meta["consumes"]:
                producers = produced.get(art)
                if not producers:
                    prod_tool = producer_index.get(art)
                    if not prod_tool:
                        logger.warning("dataflow: 생산자 없는 artifact", artifact=art, consumer=t.tool)
                        continue
                    pmeta = tool_index[prod_tool]
                    new_id = f"auto_{prod_tool}"
                    if any(td.id == new_id for td in plan.todos):
                        new_id = f"auto_{prod_tool}_{len(plan.todos)}"
                    plan.todos.append(PlannedTodo(
                        id=new_id, task_type=pmeta["task_type"],
                        team=pmeta["team"], agent=pmeta["agent"], tool=prod_tool,
                        depends_on=[], priority=max(1, t.priority - 1),
                        rationale=f"auto: {art} 생산자 누락 보강 (dataflow)",
                    ))
                    plan.dag.setdefault(new_id, [])
                    if new_id not in t.depends_on:
                        t.depends_on.append(new_id)
                    plan.dag.setdefault(t.id, [])
                    if new_id not in plan.dag[t.id]:
                        plan.dag[t.id].append(new_id)
                    inserted += 1
                    mutated = True
                    break
                elif t.id not in producers and not any(p in t.depends_on for p in producers):
                    # 생산자는 있으나 소비자가 의존 안 함 → phase 순서 보장 위해 의존 추가
                    dep = sorted(producers)[0]
                    t.depends_on.append(dep)
                    plan.dag.setdefault(t.id, []).append(dep)
                    mutated = True
                    break
            if mutated:
                break
        if not mutated:
            break

    if inserted:
        plan.plan_notes = (plan.plan_notes or "") + f" [dataflow: 누락 생산자 {inserted}개 보강]"
        logger.info("dataflow completion inserted producers", count=inserted)
    return plan


# 해석(LLM 추론) tool — 계산된 분석 산출을 *먹어야* 함. 도메인무관(consumes 미선언)이라
# complete_dataflow_chain 이 못 챙김 → 별도 feeding 안전망(아래).
_INTERPRETATION_TOOLS = frozenset({"insight_extractor", "diagnoser", "forecaster"})
# 도메인 → 그 도메인의 대표(headline) metric tool 매핑은 카탈로그가 선언한다 (도메인 무관):
#   catalog["domain_headline_metric"] = {<domain>: <metric_tool_name>}
# 해석 tool 이 raw 만 받는 plan 에 대표 metric 을 결정론 보강할 때 사용. 미선언/매핑밖 = 무발동.
# 해석 tool 의 '먹이' = 계산된 metric/분포 산출자(아래 task_type). 출력 tool(summary/report)·
# 해석 tool 자신은 제외 — generic 계산 task_type 집합으로 명시(도메인 무관, '아니면 computed' 식 오판 방지).
_COMPUTED_TASKS = frozenset({"metric_calculation", "comparison", "analysis"})


def ensure_interpretation_fed(plan: Plan, sq: StructuredQuery, catalog: dict) -> Plan:
    """해석 tool(insight_extractor/diagnoser/forecaster)이 *계산된 산출* 없이 raw 만 받는 plan 에
    도메인 대표 metric 을 삽입하고 의존 배선 (결정론 안전망·멱등·순수).

    근거(stage1 coverage 감사): 해석 tool 은 도메인무관(consumes 미선언)이라 complete_dataflow_chain
    이 metric 생산자를 못 끼움 → Stage3 LLM 이 metric 단계를 빠뜨리면 해석 tool 이 빈입력 가드로
    EMPTY. metric tool 은 self.fetch 로 독립 데이터 로드 → 단독 삽입 가능
    (collector 불요, period 는 bind_temporal 이 채움).
    """
    interp = [t for t in plan.todos if (t.tool or "") in _INTERPRETATION_TOOLS]
    if not interp:
        return plan

    tool_index = _build_tool_index(catalog)

    def _is_computed(tool: str | None) -> bool:
        if not tool or tool in _INTERPRETATION_TOOLS:
            return False
        return tool_index.get(tool, {}).get("task_type", "") in _COMPUTED_TASKS

    computed = [t.id for t in plan.todos if _is_computed(t.tool)]
    if computed:
        # 계산 산출자 있음 → 해석 tool 이 의존하도록만 보장(phase 순서 — 안 그러면 같은/앞 phase 면 못 봄)
        for it in interp:
            for pid in computed:
                if pid != it.id and pid not in it.depends_on:
                    it.depends_on.append(pid)
                    plan.dag.setdefault(it.id, [])
                    if pid not in plan.dag[it.id]:
                        plan.dag[it.id].append(pid)
        return plan

    # 계산 산출자 없음(해석 tool 이 굶음) → 도메인 대표 metric 삽입
    # metric tool 은 period 필수(코드) → 결정론 월이 있어야 안전 삽입.
    # 월 없으면 미발동(degrade 유지 — 실패→halt 로 악화시키지 않음).
    month = _resolved_month(sq)
    if not month:
        return plan
    domains = [d.lower() for d in (sq.intent.domain if sq.intent else [])]
    headline = catalog.get("domain_headline_metric") or {}
    metric_tool = next((headline[d] for d in domains if d in headline), None)
    if not metric_tool or metric_tool not in tool_index:
        return plan   # graceful: 등록된 headline metric 없음/카탈로그 부재 → 무발동(정직 degrade, hallucination 안 함)

    pmeta = tool_index[metric_tool]
    new_id = f"auto_{metric_tool}"
    if not any(td.id == new_id for td in plan.todos):
        plan.todos.append(PlannedTodo(
            id=new_id, task_type=pmeta["task_type"], team=pmeta["team"], agent=pmeta["agent"],
            tool=metric_tool, depends_on=[], priority=1,
            tool_params={"period": month},   # 삽입 시점에 직접 명시 (bind_temporal 과 중복·멱등 — 구 'drift' 사유는 06-11 정합으로 해소)
            rationale=f"auto: 해석 tool feeding — {metric_tool} 결정론 보강 (interpretation_fed)",
        ))
        plan.dag.setdefault(new_id, [])
    for it in interp:
        if new_id not in it.depends_on:
            it.depends_on.append(new_id)
            plan.dag.setdefault(it.id, []).append(new_id)
    plan.plan_notes = (plan.plan_notes or "") + f" [feeding: 해석 tool 에 {metric_tool} 보강]"
    logger.info("interpretation feeding reinforced", metric=metric_tool, interp=[t.tool for t in interp])
    return plan


def enforce_breakdown_dimension(plan: Plan, sq: StructuredQuery, catalog: dict) -> Plan:
    """operation=breakdown + dimensions 있는데 plan 에 *차원 분해(rows 산출)* tool 이 없으면
    차원 대응 breakdown tool 을 삽입 (결정론 안전망·멱등·순수).

    근거(복합 베이스라인 2026-06-11): 차원별 질의(breakdown·dimensions=[<dim>])가 Stage3 에서
    per-dimension tool 대신 *전체* scalar tool 로 ~60% 비결정 붕괴 → 차원 누락.
    convention(하드코딩 맵 아님): 'rows' 산출 = 테이블 = 차원분해 신호 + name.startswith(dimension) 로
    차원 대응 tool 식별 — dimension 은 *쿼리가 요청한 토큰*이라 도메인 하드코딩 아님.
    매칭 없으면(per-dim rows tool 부재) graceful 무발동
    (정직 degrade, 환각 안 함). cognitive 는 dimension 을 영어 토큰으로 emit.
    breakdown tool 은 self.fetch 독립(consumes 미선언) → 단독 삽입 안전(silent-0 없음).
    """
    intent = getattr(sq, "intent", None)
    if not intent or (intent.operation or "") != "breakdown" or not intent.dimensions:
        return plan

    dims = [str(d).lower() for d in intent.dimensions]
    tool_index = _build_tool_index(catalog)

    def _is_dim_breakdown(tool: str | None) -> bool:
        meta = tool_index.get(tool or "", {})
        return "rows" in (meta.get("produces") or []) and any((tool or "").startswith(d) for d in dims)

    # 요청 차원에 대응하는 rows(분해) tool 이 이미 있으면 충족 → 무발동(멱등)
    if any(_is_dim_breakdown(t.tool) for t in plan.todos):
        return plan

    bd_tool = next((name for name in sorted(tool_index) if _is_dim_breakdown(name)), None)
    if not bd_tool:
        return plan   # graceful: 차원 분해 tool 부재 → 무발동(정직 degrade)

    pmeta = tool_index[bd_tool]
    new_id = f"auto_{bd_tool}"
    if not any(td.id == new_id for td in plan.todos):
        params: dict[str, Any] = {}
        month = _resolved_month(sq)
        if "period" in pmeta["params_required"] and month:
            params["period"] = month   # bind_temporal 도 채우나, 차원 tool 은 여기서 직접(안전)
        plan.todos.append(PlannedTodo(
            id=new_id, task_type=pmeta["task_type"], team=pmeta["team"], agent=pmeta["agent"],
            tool=bd_tool, depends_on=[], priority=1, tool_params=params,
            rationale=f"auto: breakdown 차원 보강 — {bd_tool} (operation=breakdown·dimensions={dims})",
        ))
        plan.dag.setdefault(new_id, [])
        plan.plan_notes = (plan.plan_notes or "") + f" [breakdown: {bd_tool} 차원 보강]"
        logger.info("breakdown dimension enforced", tool=bd_tool, dims=dims)
    return plan


def validate_dag(plan: Plan) -> list[str]:
    issues: list[str] = []
    todo_ids = {t.id for t in plan.todos}
    for t in plan.todos:
        for dep in t.depends_on:
            if dep not in todo_ids:
                issues.append(f"todo {t.id} depends on unknown id: {dep}")
    for tid, deps in plan.dag.items():
        if tid not in todo_ids:
            issues.append(f"dag references unknown todo: {tid}")
    cycle = detect_cycle(plan.dag)
    if cycle:
        issues.append(f"cycle detected: {cycle}")
    return issues


# ───────────────────────────────────────────────────────
# Prompt loader
# ───────────────────────────────────────────────────────

_prompt_cache: dict[str, dict] = {}


def _load_stage_prompt(stage_file: str) -> dict:
    if stage_file not in _prompt_cache:
        path = PROMPTS_DIR / stage_file
        with open(path, "r", encoding="utf-8") as f:
            _prompt_cache[stage_file] = yaml.safe_load(f)
    return _prompt_cache[stage_file]


def _build_prompt(config: dict, template_vars: dict) -> tuple[str, str]:
    """프롬프트 config에서 system_prompt + user_prompt 구성."""
    system_prompt = config.get("system_prompt", "")

    # few-shot embed
    examples = config.get("examples", [])
    if examples:
        block = "\n\n## Examples\n"
        for i, ex in enumerate(examples, 1):
            block += f"\n### Example {i}\n"
            block += f"Input:\n{json.dumps(ex.get('input', {}), ensure_ascii=False, indent=2)}\n"
            block += f"Output:\n{json.dumps(ex.get('output', {}), ensure_ascii=False, indent=2)}\n"
        system_prompt += block

    user_template = config.get("user_template", "")
    user_prompt = user_template.format(**template_vars)

    return system_prompt, user_prompt


# ───────────────────────────────────────────────────────
# Catalog helpers
# ───────────────────────────────────────────────────────

def _load_catalog() -> dict:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_teams_summary(catalog: dict) -> list[dict]:
    """팀 요약 리스트 (Stage 1용)."""
    teams = catalog.get("teams", {}) or {}
    return [
        {"name": name, "description": data.get("description", "")}
        for name, data in teams.items()
    ]


def _get_team_agents(catalog: dict, teams_selected: list[str]) -> dict:
    """선택 팀의 Agent 목록 (Stage 2용)."""
    result: dict[str, list[dict]] = {}
    teams = catalog.get("teams", {}) or {}
    for team_name in teams_selected:
        team_data = teams.get(team_name, {})
        agents = team_data.get("agents", {}) or {}
        result[team_name] = [
            {
                "name": agent_name,
                "description": agent_data.get("description", ""),
                "handles_tasks": agent_data.get("handles_tasks", []),
            }
            for agent_name, agent_data in agents.items()
        ]
    return result


def _get_agent_tools(catalog: dict, agents_selected: list[str], allow_text: bool = True) -> dict:
    """선택 Agent의 Tool 상세 (Stage 3용).

    Status: complete — allow_text=False 시 주제-결속(텍스트) tool 을 메뉴에서 제외
    (subject-coherence 게이트, F2 수정 2026-06-04). LLM 이 못 보면 못 고름.
    """
    result: dict[str, dict] = {}
    subject_artifacts = _subject_bound_artifacts(catalog) if not allow_text else set()
    teams = catalog.get("teams", {}) or {}
    for team_data in teams.values():
        agents = team_data.get("agents", {}) or {}
        for agent_name, agent_data in agents.items():
            if agent_name in agents_selected:
                tools = agent_data.get("tools", []) or []
                if not allow_text:
                    tools = [t for t in tools if not _tool_is_subject_bound(t, subject_artifacts)]
                result[agent_name] = {
                    "description": agent_data.get("description", ""),
                    "tools": tools,
                }
    return result


# ───────────────────────────────────────────────────────
# Main Planner (3계층)
# ───────────────────────────────────────────────────────

class Planner:
    """3계층 LLM 기반 Planning — StructuredQuery → Plan"""

    def __init__(self):
        self.client = get_llm_client("planning")
        self._catalog = _load_catalog()
        self._subject_bound_tool_names = _collect_subject_bound_tool_names(self._catalog)

    @staticmethod
    def _has_text_intent(sq: StructuredQuery) -> bool:
        """텍스트 파이프가 정당한가 — 텍스트 task 또는 텍스트 주제 마커.

        Status: complete — 없으면 _build_todos 가 텍스트-데이터 tool 을 제외 (F2 게이트).
        """
        if any(t.id in _TEXT_INTENT_TASKS for t in sq.tasks):
            return True
        if not _SUBJECT_INTENT_MARKERS:
            return False
        raw = (sq.meta.raw_input or sq.targets.product or "").lower()
        kw = " ".join(sq.targets.keywords).lower()
        hay = f"{raw} {kw}"
        return any(m in hay for m in _SUBJECT_INTENT_MARKERS)

    @staticmethod
    def _is_qa(sq: StructuredQuery) -> bool:
        """질의응답(factual_lookup) 쿼리인가 — 결정론 QA 라우팅 신호.

        cognitive 가 개념정의·시스템메타·대화 질문에 tasks=[factual_lookup] 을 emit
        (domain=[] 이라 intent_shim 미작동 → LLM tasks 보존). 설계서 §3.
        단 *단일 의도*일 때만 — 복합(sub_intents≥2)이면 우회(Stage3 가 다의도 처리, stage2 ⒟).
        """
        if sq.intent and len(sq.intent.sub_intents) >= 2:
            return False
        return any(t.id == TaskType.FACTUAL_LOOKUP for t in sq.tasks)

    @staticmethod
    def _build_qa_plan(sq: StructuredQuery) -> Plan:
        """질의응답 결정론 plan — LLM 팀/agent 선택 우회, qa_responder 단일 todo.

        질문을 tool_params 로 주입(ExecutionContext 엔 user_input 부재 — 설계서 §4).
        Status: complete — 단일 QA 결정론 라우팅(질의응답_설계서_260610.md §3).
        """
        question = (sq.meta.raw_input or sq.meta.cleaned or "").strip()
        todo = PlannedTodo(
            id="todo_qa_001",
            task_type=TaskType.FACTUAL_LOOKUP.value,
            team="qa_team",
            agent="qa_agent",
            tool="qa_responder",
            tool_params={"question": question},
            depends_on=[],
            priority=1,
            rationale="질의응답 — 지식·메타·대화 답변(데이터 파이프 우회)",
        )
        return Plan(
            teams_selected=["qa_team"],
            todos=[todo],
            dag={"todo_qa_001": []},
            plan_notes="질의응답(factual_lookup) — qa_responder 단일 todo 결정론 라우팅",
        )

    @staticmethod
    def _is_recommendation(sq: StructuredQuery) -> bool:
        """의사결정 추천(recommendation) 쿼리인가 — 결정론 라우팅 신호.

        cognitive operation=recommend → intent_shim RECOMMENDATION task. 의사결정_설계서 §4.
        단 *단일 의도*일 때만 — 복합(sub_intents≥2, 예 "분석 후 추천")이면 우회 →
        Stage3 가 선행 분석+추천 체인을 컴파일(lv4 붕괴 해소, stage2 근원귀속 ⒟).
        """
        if sq.intent and len(sq.intent.sub_intents) >= 2:
            return False
        return any(t.id == TaskType.RECOMMENDATION for t in sq.tasks)

    @staticmethod
    def _build_recommendation_plan(sq: StructuredQuery) -> Plan:
        """의사결정 결정론 plan — recommender 단일 todo (mock).

        mock 은 상류 분석 무시·fixture 반환 → 데이터 파이프 없이 작동(큰틀 구동). LLM 스테이지
        우회(Stage3 가 recommender 대신 분석 파이프를 짜는 비결정성 회피).
        Status: complete — 실모델 swap 시 분석 산출 feeding 은 추후.
        """
        todo = PlannedTodo(
            id="todo_rec_001",
            task_type=TaskType.RECOMMENDATION.value,
            team="decision_team",
            agent="decision_agent",
            tool="recommender",
            tool_params={},
            depends_on=[],
            priority=1,
            rationale="의사결정 추천 — recommender(ml_model mock)",
        )
        return Plan(
            teams_selected=["decision_team"],
            todos=[todo],
            dag={"todo_rec_001": []},
            plan_notes="의사결정(recommendation) — recommender 단일 todo 결정론 라우팅",
        )

    async def plan(
        self,
        structured_query: StructuredQuery,
    ) -> tuple[Plan | None, list[str]]:
        # ── 질의응답 short-circuit: factual_lookup → qa_responder 결정론 (LLM 스테이지 우회) ──
        if self._is_qa(structured_query):
            logger.info("planning QA short-circuit (factual_lookup → qa_responder)")
            return self._build_qa_plan(structured_query), []

        # ── 의사결정 short-circuit: recommendation → recommender 결정론 (mock=상류 불필요) ──
        if self._is_recommendation(structured_query):
            logger.info("planning recommendation short-circuit (recommendation → recommender)")
            return self._build_recommendation_plan(structured_query), []

        sq_json = json.dumps(
            structured_query.model_dump(mode="json"),
            ensure_ascii=False, indent=2,
        )
        allow_text = self._has_text_intent(structured_query)

        # ── Stage 1: 팀 선택 ──
        teams_selected = await self._select_teams(sq_json)
        logger.info("planning stage1 done", teams=teams_selected)

        if not teams_selected:
            return Plan(
                teams_selected=[],
                todos=[],
                dag={},
                plan_notes="팀 선택 0 — factual_lookup 또는 ambiguity",
            ), []

        # ── Stage 2: Agent 선택 ──
        agents_selected = await self._select_agents(sq_json, teams_selected)
        logger.info("planning stage2 done", agents=agents_selected)

        if not agents_selected:
            return Plan(
                teams_selected=teams_selected,
                todos=[],
                dag={},
                plan_notes="Agent 선택 0",
            ), ["no agents selected"]

        # ── Stage 3: Todo + DAG 생성 ──
        plan = await self._build_todos(sq_json, agents_selected, allow_text=allow_text)
        if plan is None:
            return None, ["stage3 todo_builder failed"]

        # breakdown 차원 보강 — operation=breakdown 인데 차원 분해(rows) tool 누락 시 삽입(복합 베이스라인 ⒠).
        # complete_dataflow_chain 보다 먼저 — 삽입 tool 이 consumes 있으면 chain 이 상류 backfill 하도록.
        plan = enforce_breakdown_dimension(plan, structured_query, self._catalog)

        # 전처리 체인 결정론 보강 — Stage3 LLM 이 필수 tool(예 normalizer)을 빠뜨려도
        # produces/consumes 로 생산자를 삽입해 체인 단절(silent-0)을 막는다.
        plan = complete_dataflow_chain(plan, self._catalog)

        # 해석 tool feeding 보강(B, stage1 감사) — insight/diagnoser/forecaster 가 계산 산출 없이
        # raw 만 받으면 도메인 대표 metric 삽입. 도메인무관(consumes 미선언)이라 위 chain 이 못 챙김.
        plan = ensure_interpretation_fed(plan, structured_query, self._catalog)

        # 시간 param 결정론 바인딩 — stage3 LLM 이 놓친 period / period_a·period_b(MoM)를 쿼리 기간으로
        # 채운다(전월=정의상 도출, 날짜 산술은 결정론). 미바인딩 → 실행 시 ValueError 방지. (R3)
        _tool_index = _build_tool_index(self._catalog)
        plan = bind_temporal_params(plan, structured_query, _tool_index)

        if not allow_text:
            logger.info("planning subject-coherence gate active (텍스트 의도 없음 → 리뷰-데이터 tool 제외)")

        plan.teams_selected = teams_selected

        # ② planning 자가평가: 실행 전 못 채우는 것(미바인딩 param 등) 결정론 탐지 (진단·관측)
        plan.gaps = detect_plan_gaps(plan, _tool_index)
        if plan.gaps:
            logger.warning("planning gaps detected (실행 전 자가평가)", gaps=plan.gaps)

        logger.info(
            "planning stage3 done",
            teams=plan.teams_selected,
            todos=len(plan.todos),
            gaps=len(plan.gaps),
        )

        # DAG 검증
        issues = validate_dag(plan)
        if issues:
            logger.warning("planner DAG issues", issues=issues)

        return plan, issues

    # ── Stage 1 ──

    async def _select_teams(self, sq_json: str) -> list[str]:
        config = _load_stage_prompt("planning_stage1_team.yaml")
        teams_summary = _get_teams_summary(self._catalog)

        system_prompt, user_prompt = _build_prompt(config, {
            "structured_query_json": sq_json,
            "teams_json": json.dumps(teams_summary, ensure_ascii=False, indent=2),
        })

        try:
            result = await self.client.generate_json(
                prompt=user_prompt, system_prompt=system_prompt,
            )
            return result.get("teams_selected", []) or []
        except Exception as e:
            logger.error("stage1 team_selector failed", error=str(e))
            return []

    # ── Stage 2 ──

    async def _select_agents(self, sq_json: str, teams_selected: list[str]) -> list[str]:
        config = _load_stage_prompt("planning_stage2_agent.yaml")
        team_agents = _get_team_agents(self._catalog, teams_selected)

        system_prompt, user_prompt = _build_prompt(config, {
            "structured_query_json": sq_json,
            "team_agents_json": json.dumps(team_agents, ensure_ascii=False, indent=2),
        })

        try:
            result = await self.client.generate_json(
                prompt=user_prompt, system_prompt=system_prompt,
            )
            return result.get("agents_selected", []) or []
        except Exception as e:
            logger.error("stage2 agent_selector failed", error=str(e))
            return []

    # ── Stage 3 ──

    async def _build_todos(
        self, sq_json: str, agents_selected: list[str], allow_text: bool = True,
    ) -> Plan | None:
        config = _load_stage_prompt("planning_stage3_todo.yaml")
        agent_tools = _get_agent_tools(self._catalog, agents_selected, allow_text=allow_text)

        system_prompt, user_prompt = _build_prompt(config, {
            "structured_query_json": sq_json,
            "agent_tools_json": json.dumps(agent_tools, ensure_ascii=False, indent=2),
        })

        try:
            result = await self.client.generate_json(
                prompt=user_prompt, system_prompt=system_prompt,
            )
        except Exception as e:
            logger.error("stage3 todo_builder LLM failed", error=str(e))
            return None

        try:
            plan = Plan.model_validate(result)
        except ValidationError as e:
            logger.error("stage3 todo_builder parse failed", error=str(e))
            return None

        # subject-coherence post-filter (F2 보강) — 순수 함수, 단위테스트 가능
        return apply_subject_coherence_filter(plan, self._subject_bound_tool_names, allow_text)
