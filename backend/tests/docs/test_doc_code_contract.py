r"""Doc-Code Contract Test — agent_specs 문서와 실제 코드 간 drift 자동 검출.

목적:
  - 문서에 언급된 `backend/...` 경로가 실제 존재하는지
  - 문서의 클래스명/함수명이 코드에 grep 되는지
  - ErrorCodes.all_codes() 와 22_error_codes.md 일치
  - 내부 문서 링크 (_v\d\.\d\.md) 타깃 파일 존재
  - 메타 버전 ↔ 파일명 suffix ↔ 변경이력 삼자 일치

실행:
  uv run pytest backend/tests/docs -v -m docs

정책:
  drift 발견 시 문서 또는 코드를 수정하여 수렴. 완벽 0 실패 보다는
  **drift 조기 발견**이 목적. 일부 항목은 soft-assert (예: 변경이력 없을 때 경고).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


pytestmark = pytest.mark.docs


ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = ROOT / "docs" / "agent_specs"
BACKEND_DIR = ROOT / "backend"


def _spec_files() -> list[Path]:
    """검증 대상 문서 목록 (POC_legacy/ 제외)."""
    return sorted([
        p for p in DOCS_DIR.glob("*.md")
        if "POC_legacy" not in str(p)
    ])


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ══════════════════════════════════════════════════════════════════
# DC-1 문서 내 backend/... 경로가 실제 존재하는지
# ══════════════════════════════════════════════════════════════════

# backtick 안 또는 문장 내 backend/... 경로 (간단 휴리스틱)
_CODE_PATH_RE = re.compile(
    r"`(backend/[\w/.\-]+?\.py)`"
    r"|(?<![\w/`])backend/[\w/]+?\.py(?![\w/])"
)


def test_DC1_code_paths_exist():
    """문서에서 언급한 backend/*.py 경로 모두 실제 존재해야 함.

    예외: 직전 40자 내에 '(예정)' / '예정 —' / 'Sprint 14+' 마커가 있으면 skip (미구현 계획 문서화).
    """
    missing: list[tuple[str, str]] = []   # (doc, path)
    for doc in _spec_files():
        text = _read(doc)
        for m in _CODE_PATH_RE.finditer(text):
            raw = m.group(1) or m.group(0)
            path = raw.strip("`")
            # legacy 허용
            if path.startswith("backend/_old") or path.startswith("backend/api/"):
                continue
            # 미구현 계획 마커 확인 (직전 40자 + 직후 80자 범위)
            context = text[max(0, m.start()-40):m.end()+80]
            if any(marker in context for marker in ("(예정)", "*(예정)*", "예정 —", "Sprint 14+", "미구현", "보류")):
                continue
            full = ROOT / path
            if not full.exists():
                missing.append((doc.name, path))
    if missing:
        msg = "\n".join(f"  {d} → {p}" for d, p in missing)
        pytest.fail(f"문서 내 backend/*.py 경로 {len(missing)}개 누락:\n{msg}")


# ══════════════════════════════════════════════════════════════════
# DC-2 문서에 backtick 표기된 클래스/함수명이 코드에 grep 되는지
# ══════════════════════════════════════════════════════════════════

# 특정 심볼만 검증 — 대충 ``로 감싼 영문 CamelCase 또는 snake_case_func 전부 검증하면 false positive 많음.
# 대신 "진실 소스 = 코드" 선언된 핵심 심볼 목록을 명시적으로 체크.
_CORE_SYMBOLS = [
    # (symbol, 검색 경로 prefix)
    ("class ErrorCodes", "backend/app/core/error_codes.py"),
    ("def _graph_runner_with_resume", "backend/api_v2/ws_agent.py"),
    ("def _parse_query_message", "backend/api_v2/ws_agent.py"),
    ("def run_turn", "backend/api_v2/ws_agent.py"),
    ("def inspect_layer_output", "backend/app/dream_agent/system_graph/layer_inspector.py"),
    ("def _build_paused_data", "backend/api_v2/ws_agent.py"),
    ("def _extract_interrupt_value", "backend/api_v2/ws_agent.py"),
    ("def restore_progress", "backend/app/dream_agent/workflow_managers/hitl_manager/manager.py"),
    ("def signal_resume", "backend/app/dream_agent/workflow_managers/hitl_manager/manager.py"),
    ("def wait_for_resume", "backend/app/dream_agent/workflow_managers/hitl_manager/manager.py"),
    ("def broadcast_to_user", "backend/api_v2/connection_manager.py"),
    ("def try_acquire", "backend/app/dream_agent/workflow_managers/concurrency_manager.py"),
    ("def init_agent_state", "backend/app/dream_agent/states/agent_state.py"),
]


def test_DC2_core_symbols_exist():
    """문서에서 '진실 소스'로 선언된 핵심 심볼이 코드에 존재."""
    missing: list[tuple[str, str]] = []
    for symbol, path in _CORE_SYMBOLS:
        full = ROOT / path
        if not full.exists():
            missing.append((symbol, f"FILE MISSING: {path}"))
            continue
        text = _read(full)
        if symbol not in text:
            missing.append((symbol, path))
    if missing:
        msg = "\n".join(f"  {s} in {p}" for s, p in missing)
        pytest.fail(f"핵심 심볼 {len(missing)}개 누락:\n{msg}")


# ══════════════════════════════════════════════════════════════════
# DC-3 ErrorCodes.all_codes() ↔ 22_error_codes.md 일치
# ══════════════════════════════════════════════════════════════════

def test_DC3_error_codes_match():
    """ErrorCodes.all_codes() 각 코드가 22_error_codes 최신판에 표로 등장."""
    import sys
    sys.path.insert(0, str(BACKEND_DIR))
    from app.core.error_codes import ErrorCodes

    # 최신 버전 자동 선택 (Sprint 14 A3 D8 대비)
    candidates = sorted(DOCS_DIR.glob("22_error_codes_v*.md"), reverse=True)
    assert candidates, "22_error_codes doc 없음"
    doc = candidates[0]
    text = _read(doc)
    missing = []
    for code in ErrorCodes.all_codes():
        if f"`{code}`" not in text:
            missing.append(code)
    if missing:
        pytest.fail(f"ErrorCodes 의 {len(missing)}개 코드가 {doc.name} 에 backtick 표기 없음: {missing}")


# ══════════════════════════════════════════════════════════════════
# DC-6 (Sprint 14 A3 D8 중간) — Sprint 14 A3 ErrorCodes 3개 신규 확장 검증
# ══════════════════════════════════════════════════════════════════

def test_DC6_sprint14_a3_error_codes_added():
    """Sprint 14 A3 D7=A- 에서 추가한 3개 ErrorCode 존재 확인.

    Status: complete — Sprint 14 A3 Phase 7.

    3개: TODO_EDIT_NOT_PAUSED / INVALID_DAG / NL_INTENT_UNCLEAR.
    나머지 4개 (TODO_NOT_FOUND / CASCADE_FAILED / NL_LLM_UNAVAILABLE / REORDER_INVALID_DAG)
    는 free-form reason — enum 추가 보류 (D7=A- 정책).
    """
    import sys
    sys.path.insert(0, str(BACKEND_DIR))
    from app.core.error_codes import ErrorCodes

    required = {"TODO_EDIT_NOT_PAUSED", "INVALID_DAG", "NL_INTENT_UNCLEAR"}
    actual = set(ErrorCodes.all_codes())
    missing = required - actual
    assert not missing, f"Sprint 14 A3 D7=A- 3개 신규 ErrorCode 누락: {missing}"

    # D7=A- 에서 제외한 4개는 enum 에 없어야 함 (free-form 정책)
    excluded = {"TODO_NOT_FOUND", "CASCADE_FAILED", "NL_LLM_UNAVAILABLE", "REORDER_INVALID_DAG"}
    unexpected = excluded & actual
    assert not unexpected, (
        f"D7=A- 에서 free-form reason 으로 남긴 코드가 enum 에 추가됨: {unexpected}. "
        "정책 변경 시 22_error_codes v1.2 bump 필요."
    )


# ══════════════════════════════════════════════════════════════════
# DC-10 (Sprint 14 A3 D8 중간) — docstring Status 마커 ↔ plan 체크박스 교차 검증
# ══════════════════════════════════════════════════════════════════

_STATUS_RE = re.compile(r"^\s*Status:\s+(partial|complete|planned)(?:\s*—\s*(.+))?$", re.MULTILINE)


def test_DC10_status_markers_parseable():
    """docstring 내 `Status:` 라인이 정상 포맷 (D-11=A 단순).

    Status: complete — Sprint 14 A3 Phase 7 DC-10 구현.

    포맷: `Status: <partial|complete|planned> — <자유 설명>`
    검증 대상: backend/ 의 Python 파일 전수 (POC_legacy 제외).
    """
    import ast

    violations: list[str] = []
    checked = 0
    for pyfile in BACKEND_DIR.rglob("*.py"):
        if "POC_legacy" in str(pyfile) or "_old" in str(pyfile):
            continue
        if ".venv" in str(pyfile):
            continue
        try:
            text = pyfile.read_text(encoding="utf-8")
        except Exception:
            continue
        # Status: 라인 존재 확인
        for match in _STATUS_RE.finditer(text):
            checked += 1
            state = match.group(1)
            desc = match.group(2)
            # partial / planned 는 설명 필수 (추적 가능성)
            if state in ("partial", "planned") and not (desc and desc.strip()):
                # 파일과 라인 추출
                line_no = text[:match.start()].count("\n") + 1
                rel = pyfile.relative_to(ROOT)
                violations.append(f"{rel}:{line_no} — `Status: {state}` 는 설명 필수")

    # 적어도 1개 이상 발견돼야 함 (Sprint 14 A3 Phase 0 에서 5곳 이상 추가)
    assert checked >= 3, (
        f"Status 마커가 {checked}개만 발견 — Sprint 14 A3 Phase 0 에서 최소 5곳 추가 예정"
    )
    if violations:
        msg = "\n".join(f"  {v}" for v in violations)
        pytest.fail(f"{len(violations)}개 Status 마커 포맷 위반:\n{msg}")


def test_DC10_status_partial_has_plan_anchor():
    """`Status: partial — ...` 설명에 sprint/plan 참조 존재 권장 (soft).

    Sprint 14 A3 에서 추가한 marker 는 "Sprint XX" 또는 "Phase X" 또는
    "A3" 등의 키워드 포함 예상. 설명에 anchor 키워드가 있으면 추적 가능.
    """
    anchor_pattern = re.compile(r"(Sprint\s*\d+|Phase\s*\d|A\d\b|예정)")
    warnings: list[str] = []
    for pyfile in BACKEND_DIR.rglob("*.py"):
        if "POC_legacy" in str(pyfile) or "_old" in str(pyfile) or ".venv" in str(pyfile):
            continue
        try:
            text = pyfile.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in _STATUS_RE.finditer(text):
            if match.group(1) == "partial" and match.group(2):
                desc = match.group(2)
                if not anchor_pattern.search(desc):
                    line_no = text[:match.start()].count("\n") + 1
                    rel = pyfile.relative_to(ROOT)
                    warnings.append(f"{rel}:{line_no} — partial 설명에 sprint/phase 앵커 권장: {desc[:60]}")
    # Soft — 경고만 출력, 실패 아님
    if warnings:
        print(f"\n[DC-10 soft] partial 설명에 추적 앵커 권장 ({len(warnings)}건):")
        for w in warnings:
            print(f"  {w}")


# ══════════════════════════════════════════════════════════════════
# DC-4 내부 문서 링크 (_v\d\.\d\.md) 실제 파일 존재
# ══════════════════════════════════════════════════════════════════

_DOC_REF_RE = re.compile(r"`?(\d{2}_[\w.]+?_v\d+\.\d+\.md)`?|\]\(([\w.]+?_v\d+\.\d+\.md)\)")


def test_DC4_internal_doc_refs_exist():
    """agent_specs 간 버전 명시 링크가 실제 파일 가리키는지."""
    existing = {p.name for p in _spec_files()}
    missing: list[tuple[str, str]] = []
    for doc in _spec_files():
        text = _read(doc)
        for m in _DOC_REF_RE.finditer(text):
            ref = m.group(1) or m.group(2)
            # "예정" 표기나 파일명에 _v1.0.md 포함된 현재 파일 자기참조 허용
            if not ref:
                continue
            if "(예정)" in text[max(0, m.start()-40):m.start()]:
                continue
            if ref not in existing:
                missing.append((doc.name, ref))
    if missing:
        msg = "\n".join(f"  {d} → {r}" for d, r in missing)
        pytest.fail(f"존재하지 않는 문서 링크 {len(missing)}개:\n{msg}")


# ══════════════════════════════════════════════════════════════════
# DC-5 메타 버전 ↔ 파일명 suffix ↔ 변경이력 삼자 일치
# ══════════════════════════════════════════════════════════════════

_META_VERSION_RE = re.compile(r"\|\s*버전\s*\|\s*\*\*v(\d+\.\d+)\*\*\s*\|")
_FILENAME_VERSION_RE = re.compile(r"_v(\d+\.\d+)\.md$")
_CHANGELOG_VERSION_RE = re.compile(r"\|\s*\**v(\d+\.\d+(?:\.\d+)?)\**\s*\|\s*\**\d{4}-\d{2}-\d{2}")


def test_DC5_version_metadata_consistency():
    """메타 버전 = 파일명 suffix = 변경이력의 최신 버전."""
    mismatches: list[str] = []
    for doc in _spec_files():
        if doc.name == "INDEX.md":
            continue   # INDEX 는 버전 없음
        text = _read(doc)
        # 파일명 버전
        fn_m = _FILENAME_VERSION_RE.search(doc.name)
        if not fn_m:
            continue
        fn_ver = fn_m.group(1)
        # 메타 버전
        meta_m = _META_VERSION_RE.search(text)
        if not meta_m:
            mismatches.append(f"{doc.name}: 메타 테이블에 '| 버전 | **vX.Y** |' 없음")
            continue
        meta_ver = meta_m.group(1)
        # 변경이력 최신 버전 (마지막 등장)
        changelog = _CHANGELOG_VERSION_RE.findall(text)
        log_ver = changelog[-1] if changelog else None

        if fn_ver != meta_ver:
            mismatches.append(f"{doc.name}: 파일명 v{fn_ver} ≠ 메타 v{meta_ver}")
        if log_ver and fn_ver != log_ver:
            mismatches.append(f"{doc.name}: 파일명 v{fn_ver} ≠ 변경이력 최신 v{log_ver}")
    if mismatches:
        msg = "\n".join(f"  {m}" for m in mismatches)
        pytest.fail(f"버전 메타 불일치 {len(mismatches)}건:\n{msg}")
