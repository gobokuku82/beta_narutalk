r"""DC-PERM — ADR-027 5 주체 권한 분리 정적 검증 (진단 + 회귀 가드).

ADR-027 §7 의 DC-PERM-1~6 을 코드 정적 스캔으로 구현.

목적 = **진단**:
  - "신규 Phase-1 레이어가 ADR-027 권한을 지키는가" 를 hard-assert 로 회귀 방지.
  - 레거시(dashboard1/clumi pre-ADR-027) 의 *알려진* 위반은 baseline(frozenset)으로
    박제 → KNOWN DEBT 로 가시화 (M2 = tool 표준 schema 리팩터 대상).

baseline 정책 (lint 점진 도입 패턴):
  - `KNOWN_LEGACY_*` = 현재 알려진 레거시 위반 파일 집합 (동결).
  - 신규 위반(baseline 밖) = **hard fail** (회귀 가드).
  - 레거시 1개 M2 리팩터 완료 시 → baseline 에서 제거 (집합이 줄어듦 = 부채 상환 추적).
  - baseline 이 비면 = 전 코드 ADR-027 준수 → DC-PERM 을 CI hard-gate 로 승격 (MVP+).

ADR-027 §7 매핑:
  DC-PERM-1  Tool       client 종속 raw 컬럼 직접 결합 (표준 schema 미경유)  → 0
  DC-PERM-2  YAML       hardcode 컬럼 (axes/field 에 client 컬럼)            → 0
  DC-PERM-3  DataSource 계산 함수 (sum/mean/groupby)                         → 0
  DC-PERM-4  Runner     raw 데이터 파일 직접 fetch (Tool→DataSource 우회)    → 0
  DC-PERM-5  Maker/YAML 실행 코드 (eval/!!python/lambda)                     → 0
  DC-PERM-6  Tool       ml_model 우회 (ML SDK 직접 import)                   → 0

실행:
  uv run pytest backend/tests/permissions -m perm -v -s    # 진단 리포트 보기(-s 필수)
  uv run pytest backend/tests/permissions                  # 기본 수트에도 포함(회귀 가드)

분류 (신규 vs 레거시):
  - COMPLIANT  : Tool 이 app.schemas.inputs / app.ml_models import (표준 schema·어댑터 경유).
  - LEGACY     : app.workspace / tools.shared(clumi 헬퍼) import 또는 collection·analysis/ml·
                 analysis/llm 디렉터리 (Sprint 15·pre-ADR-027).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.perm


# ──────────────────────────────────────────────────────────────────
# 경로
# ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
TOOLS_DIR = BACKEND / "app" / "dream_agent" / "tools"
DATA_SOURCES_DIR = BACKEND / "app" / "data_sources"
PIPELINES_DIR = BACKEND / "app" / "pipelines"
FLOWS_DIR = PIPELINES_DIR / "flows"


def _rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


# 프레임워크 파일 (Tool 아님 — ABC·레지스트리). 스캔 제외.
_FRAMEWORK = {"base_tool.py", "registry.py"}


def _py_files(root: Path):
    """root 하위 *.py (단 __init__.py · 프레임워크 · _old · POC_legacy · .venv 제외)."""
    for p in root.rglob("*.py"):
        s = str(p)
        if (p.name == "__init__.py" or p.name in _FRAMEWORK
                or "_old" in s or "POC_legacy" in s or ".venv" in s):
            continue
        yield p


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ──────────────────────────────────────────────────────────────────
# 분류 헬퍼
# ──────────────────────────────────────────────────────────────────
def _uses_standard_schema(text: str) -> bool:
    """표준 schema·ml_model 어댑터 경유 = ADR-027 준수 신규 Tool."""
    return "app.schemas.inputs" in text or "app.ml_models" in text


def _uses_legacy_infra(text: str, path: Path) -> bool:
    """clumi 레거시 인프라(workspace·shared 헬퍼) 또는 pre-ADR-027 디렉터리."""
    s = str(path).replace("\\", "/")
    if "app.workspace" in text or "tools.shared" in text:
        return True
    return any(seg in s for seg in ("/collection/", "/analysis/ml/", "/analysis/llm/"))


def _data_touching_tools():
    """self.ds.get(...) 로 외부 데이터를 직접 받는 Tool (path, text)."""
    for p in _py_files(TOOLS_DIR):
        text = _read(p)
        if "self.ds.get(" in text:
            yield p, text


# ──────────────────────────────────────────────────────────────────
# baseline — 알려진 레거시 위반 (M2 리팩터 대상). 비면 hard-gate 승격 가능.
#
# 대부분의 레거시는 _uses_legacy_infra(workspace·shared·collection 등) 휴리스틱으로
# 자동 분류된다. 아래 frozenset 은 휴리스틱이 못 잡는 *예외 파일* 만 명시.
# (주의: 휴리스틱은 "workspace/shared import = 레거시"라 신규 Tool 이 그것을 import 하면
#  레거시로 묻힐 수 있음. 신규 Tool 은 cache=Runner·schema 경유라 정상이면 import 불필요.)
# ──────────────────────────────────────────────────────────────────
KNOWN_LEGACY_DC_PERM_1: frozenset[str] = frozenset()
KNOWN_LEGACY_DC_PERM_6: frozenset[str] = frozenset({
    # 보고서 요약 생성기 — llm_manager 직접 호출 (pre-ADR-027). report/ 파이프라인 영역,
    # ml_model 어댑터 경유 전환 = M2/MVP+ 대상.
    "backend/app/dream_agent/tools/report/summary_generator.py",
})


# ──────────────────────────────────────────────────────────────────
# 리포트 헬퍼
# ──────────────────────────────────────────────────────────────────
def _report(tag: str, desc: str, *, new: list[str], legacy: list[str], compliant: int) -> None:
    print(f"\n[{tag}] {desc}")
    print(f"  ✅ 준수(신규) {compliant} · 🟠 KNOWN DEBT(레거시) {len(legacy)} · 🔴 신규위반 {len(new)}")
    for f in sorted(legacy):
        print(f"    🟠 {f}")
    for f in sorted(new):
        print(f"    🔴 {f}  ← baseline 밖 신규 위반")


# ══════════════════════════════════════════════════════════════════
# DC-PERM-1 — Tool: client 종속 raw 컬럼 직접 결합 (표준 schema 미경유)
# ══════════════════════════════════════════════════════════════════
def test_DC_PERM_1_tool_no_raw_column_coupling():
    """데이터-접촉 Tool 은 app.schemas.inputs(Pydantic 표준 schema)/ml_models 를 경유해야 한다.

    raw DataFrame 을 직접 subscript(`df["payment_amount"]`)하면 client 컬럼이 Tool 에 박힘
    → ADR-027 §3 위반. 신규 위반(baseline 밖) = fail.
    """
    compliant, legacy, new = 0, [], []
    for path, text in _data_touching_tools():
        rel = _rel(path)
        if _uses_standard_schema(text):
            compliant += 1
        elif _uses_legacy_infra(text, path) or rel in KNOWN_LEGACY_DC_PERM_1:
            legacy.append(rel)
        else:
            new.append(rel)
    _report("DC-PERM-1", "Tool raw 컬럼 직접 결합 (표준 schema 미경유)",
            new=new, legacy=legacy, compliant=compliant)
    assert not new, (
        f"표준 schema 미경유 신규 Tool {len(new)}개 (baseline 밖):\n  "
        + "\n  ".join(new)
        + "\n→ app.schemas.inputs 의 load_X 로 데이터 접근하거나, 레거시면 baseline 등록."
    )


# ══════════════════════════════════════════════════════════════════
# DC-PERM-2 — YAML: hardcode client 컬럼 (axes/field 에 한글·AI_*)
# ══════════════════════════════════════════════════════════════════
_COLUMN_KEYS = {"field", "where_field", "where_value", "axes", "source_column",
                "columns", "group_by", "sort_by"}
# client 종속 컬럼 신호: 한글 또는 AI_<대문자> (예: "전환매출(원)", "AI_Sales")
_CLIENT_COL_RE = re.compile(r"[가-힣]|AI_[A-Z]")


def _walk_yaml(node, key=None):
    """(key, value) 쌍을 재귀 산출 — 컬럼 키 검사용."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_yaml(v, k)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_yaml(v, key)
    else:
        yield key, node


def test_DC_PERM_2_yaml_no_hardcoded_columns():
    """flow YAML 의 컬럼 키(field/axes/where_value 등) 값에 client 컬럼(한글·AI_*) 금지.

    label·description·name·tags 등 표시용 한글은 허용 (컬럼 키만 검사).
    """
    violations: list[str] = []
    for yml in sorted(FLOWS_DIR.glob("*.yaml")):
        doc = yaml.safe_load(_read(yml))
        for key, val in _walk_yaml(doc):
            if key in _COLUMN_KEYS and isinstance(val, str) and _CLIENT_COL_RE.search(val):
                violations.append(f"{_rel(yml)} — {key}: {val!r}")
    _report("DC-PERM-2", "YAML 컬럼 키에 client 컬럼 하드코딩",
            new=violations, legacy=[], compliant=len(list(FLOWS_DIR.glob('*.yaml'))) - len(violations))
    assert not violations, (
        f"flow YAML 컬럼 키 하드코딩 {len(violations)}건:\n  " + "\n  ".join(violations)
    )


# ══════════════════════════════════════════════════════════════════
# DC-PERM-3 — DataSource: 계산 함수 금지 (sum/mean/groupby)
# ══════════════════════════════════════════════════════════════════
_DS_COMPUTE_RE = re.compile(r"\.(sum|mean|median|groupby|agg|pivot_table|value_counts)\s*\(")


def test_DC_PERM_3_datasource_no_computation():
    """DataSource 는 데이터 *경로·매핑* 만. 집계·계산은 Tool 책임 (ADR-027 §1)."""
    violations: list[str] = []
    for p in _py_files(DATA_SOURCES_DIR):
        text = _read(p)
        for m in _DS_COMPUTE_RE.finditer(text):
            line = text[:m.start()].count("\n") + 1
            violations.append(f"{_rel(p)}:{line} — {m.group(0)}")
    _report("DC-PERM-3", "DataSource 계산 함수", new=violations, legacy=[],
            compliant=len(list(_py_files(DATA_SOURCES_DIR))) - (1 if violations else 0))
    assert not violations, (
        f"DataSource 계산 함수 {len(violations)}건 (Tool 로 이동 필요):\n  " + "\n  ".join(violations)
    )


# ══════════════════════════════════════════════════════════════════
# DC-PERM-4 — Runner: raw 데이터 파일 직접 fetch 금지
# ══════════════════════════════════════════════════════════════════
# 데이터 fetch 신호 (pipeline 정의 YAML 로드는 제외 — yaml.safe_load/.yaml 은 매칭 안 됨)
_RAW_FETCH_RE = re.compile(
    r"pd\.read_(csv|parquet|json|excel)|read_parquet|\.read_csv\(|"
    r"open\(\s*[^)]*['\"][^)]*\.(csv|parquet|jsonl)['\"]"
)


def test_DC_PERM_4_runner_no_direct_file_fetch():
    """Runner(pipelines/*.py) 는 raw 데이터를 직접 읽지 않는다.

    데이터 fetch = Tool→DataSource. Runner 는 Tool *호출* + cache(workspace) read-through 만.
    (workspace cache 접근은 Pipeline 권한 — ADR-027 §1 의 cache_key. 여기선 raw fetch 만 검사.)
    """
    violations: list[str] = []
    for p in _py_files(PIPELINES_DIR):
        text = _read(p)
        for m in _RAW_FETCH_RE.finditer(text):
            line = text[:m.start()].count("\n") + 1
            violations.append(f"{_rel(p)}:{line} — {m.group(0)}")
    _report("DC-PERM-4", "Runner raw 파일 직접 fetch", new=violations, legacy=[],
            compliant=len(list(_py_files(PIPELINES_DIR))) - (1 if violations else 0))
    assert not violations, (
        f"Runner raw fetch {len(violations)}건 (Tool→DataSource 경유 필요):\n  " + "\n  ".join(violations)
    )


# ══════════════════════════════════════════════════════════════════
# DC-PERM-5 — Maker/YAML: 실행 코드 금지 (선언적 데이터만)
# ══════════════════════════════════════════════════════════════════
_YAML_EXEC_RE = re.compile(r"!!python|\beval\s*\(|\bexec\s*\(|\blambda\b|os\.system|subprocess")


def test_DC_PERM_5_yaml_no_code_execution():
    """flow YAML 은 선언적 데이터. 실행 코드(eval/!!python/lambda) 금지 (ADR-027 §1 Maker)."""
    violations: list[str] = []
    for yml in sorted(FLOWS_DIR.glob("*.yaml")):
        text = _read(yml)
        for m in _YAML_EXEC_RE.finditer(text):
            line = text[:m.start()].count("\n") + 1
            violations.append(f"{_rel(yml)}:{line} — {m.group(0)}")
    _report("DC-PERM-5", "YAML 실행 코드", new=violations, legacy=[],
            compliant=len(list(FLOWS_DIR.glob('*.yaml'))) - len(violations))
    assert not violations, (
        f"YAML 실행 코드 {len(violations)}건:\n  " + "\n  ".join(violations)
    )


# ══════════════════════════════════════════════════════════════════
# DC-PERM-6 — Tool: ml_model 우회 (ML SDK 직접 import)
# ══════════════════════════════════════════════════════════════════
# ML/LLM 직접 호출 신호. ml_model adapter(app.ml_models) 를 거쳐야 함.
_ML_SDK_SIGNALS = [
    "import openai", "from openai", "import anthropic", "from anthropic",
    "langchain", "sentence_transformers", "from transformers", "import transformers",
    "import torch", "textblob", "TextBlob", "llm_manager", "LlmManager", "get_llm_manager",
]


def test_DC_PERM_6_tool_no_ml_model_bypass():
    """ML 추론은 ml_model 어댑터(app.ml_models) 경유. Tool 이 ML SDK 직접 import = 우회 금지.

    신규 ML Tool(review_sentiment 등) = get_default_ml_model() 경유 → 준수.
    레거시 analysis/ml·analysis/llm Tool = SDK 직접 호출 → KNOWN DEBT.
    """
    compliant, legacy, new = 0, [], []
    for p in _py_files(TOOLS_DIR):
        text = _read(p)
        hits = [sig for sig in _ML_SDK_SIGNALS if sig in text]
        if not hits:
            continue
        rel = _rel(p)
        if _uses_legacy_infra(text, p) or rel in KNOWN_LEGACY_DC_PERM_6:
            legacy.append(f"{rel} ({', '.join(sorted(set(hits)))})")
        else:
            new.append(f"{rel} ({', '.join(sorted(set(hits)))})")
    # app.ml_models 경유 신규 ML Tool 개수 (참고)
    compliant = sum(1 for _, t in _data_touching_tools() if "app.ml_models" in t)
    _report("DC-PERM-6", "Tool ml_model 우회 (ML SDK 직접 import)",
            new=new, legacy=legacy, compliant=compliant)
    assert not new, (
        f"ml_model 우회 신규 Tool {len(new)}개 (baseline 밖):\n  " + "\n  ".join(new)
        + "\n→ app.ml_models 의 get_default_ml_model() 경유 필요, 레거시면 baseline 등록."
    )
