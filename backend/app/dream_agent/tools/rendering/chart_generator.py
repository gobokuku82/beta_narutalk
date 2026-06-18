"""Chart Generator — 분석 산출 → 문서용 정적 차트 PNG (2026-06-12, 오너 결정: stub→구현).

■ 정체성 — "문서에 들어가는 차트"
  소비처 3곳이 이 tool 의 존재 이유이자 출력 포맷(PNG)의 근거:
    ① 채팅 답변 첨부      — responder._collect_attachments (kind="chart" + 다운로드 링크)
    ② PDF 보고서          — reportlab 은 이미지만 수용 (HTML 불가)
    ③ PPT 슬라이드        — python-pptx 도 이미지만 수용 (pptx_generator 가 선택 소비)

■ 왜 PNG 인가 (HTML 인터랙티브가 아니라) — 고도화 전 반드시 읽을 것
  - PDF/PPT 라는 최종 문서 포맷이 이미지만 받는다. HTML 차트(plotly/echarts)로 만들면
    결국 헤드리스 브라우저로 HTML→PNG 변환을 거쳐야 해서 같은 결과물에 의존성만 늘어남.
  - 화면용 인터랙티브 차트는 frontend 대시보드의 영역 (recharts — 분업 경계).
    "에이전트 답변에 인터랙티브 차트"가 필요해지면: 이 tool 을 HTML 로 바꾸는 게 아니라,
    이 tool 이 차트화한 *데이터*(rows/dict — 이미 응답 payload 에 있음)를 frontend 가
    직접 렌더하는 표시 기능을 추가하는 것이 올바른 자리 (백엔드=문서, 프론트=화면).

■ 차트 선택 — 산출 *형태* 기반 결정론 (LLM 0)
  dict[str, number]            (by_channel·감성 분포 류)   → 가로 막대
  dict[str, dict[str, number]] (by_category 류 — 첫 숫자키) → 가로 막대 (제목에 수치명 표기)
  rows: list[dict] + 'date' 키                             → 라인 (수치열 최대 2)
  rows: list[dict] + 범주 키                               → 가로 막대 (대표 수치열 1 — roas 우선)

■ 고도화 지도 (어디를 고치면 무엇이 바뀌나 — [[project_extension_ease_priority]])
  · 새 산출 키 차트화      → _DICT_ARTIFACTS 에 "키: 제목" 한 줄
  · 새 차트 종류           → _render_* 함수 1개 + execute 분기 1곳 (형태 기반 결정론 유지)
  · 색/스타일              → _PALETTE·_TEXT·_GRID 상수 1곳 (frontend globals.css --chart-1~5
                             미러 — 원본이 진실, frontend 팔레트 변경 시 여기 동기)
  · 축 포맷(₩ 천단위·%)    → _fmt 1곳
  · 브랜드 디자인 적용     → D10(브랜드 컬러·폰트 가이드) 확보 후 — slide_designer 재채용과 같은 트리거
  · "어떤 차트가 적절한가" 를 LLM 이 고르게 하는 진화 → 결정론 분기를 후보 생성으로 바꾸고
    LLM 은 선택만 (계산·수치는 계속 결정론 — 숫자를 LLM 이 만들면 I1 위반)

■ 정직 (헌법 19 I1·H1)
  - COMPLETED 산출만 차트화 (ctx.previous_results = executor 가 COMPLETED 만 병합, R-8).
  - _dataref/_state_guard 참조 스텁은 데이터가 아니므로 차트화 제외 (모형을 그리지 않는다).
  - 차트화 가능한 산출이 없으면 data_insufficient (SKIPPED) — 빈/장식 차트 생성 금지.
  - 그라데이션·장식 금지, 시리즈당 단색 ([[feedback_no_ai_looking_ui]]).

Status: complete — 1차 (형태 기반 4종 + 문서 삽입). 고도화는 위 지도 참조.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool

logger = get_logger(__name__)

# chart_generator.py → rendering(0) tools(1) dream_agent(2) app(3) backend(4) repo(5)
_REPO_ROOT = Path(__file__).resolve().parents[5]

# frontend globals.css 차트 팔레트 미러 (hsl→hex 변환값. 원본이 진실 — 변경 시 동기)
_PALETTE = ["#5C7A99", "#A87257", "#507C6D", "#92799A", "#91826E"]  # --chart-1~5
_TEXT = "#3D3833"   # warm neutral 본문 톤
_GRID = "#E8E2D9"   # warm neutral 경계 톤

_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\malgun.ttf",                     # Windows 맑은 고딕
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Linux 나눔고딕
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",       # macOS
]

# 차트화 대상 dict 산출 키 → 제목 라벨 (도메인 라벨 — 신규 산출은 한 줄 추가)
_DICT_ARTIFACTS = {
    "by_channel": "채널별",
    "by_group": "채널 그룹별",
    "by_category": "카테고리별",
    "sentiment_distribution": "감성 분포 (%)",
    "source_dist": "UTM 소스 분포",
    "medium_dist": "UTM 매체 분포",
}

_MAX_CHARTS = 4
_MAX_BARS = 10


def _setup_matplotlib() -> None:
    """Agg(헤드리스) + 한국어 폰트 등록. 폰트 없으면 기본 폰트로 진행(라벨 깨짐 > 크래시)."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import font_manager, rcParams

    for p in _FONT_CANDIDATES:
        if Path(p).exists():
            font_manager.fontManager.addfont(p)
            rcParams["font.family"] = font_manager.FontProperties(fname=p).get_name()
            break
    rcParams["axes.unicode_minus"] = False


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _fmt(v: float) -> str:
    return f"{v:,.1f}".rstrip("0").rstrip(".") if isinstance(v, float) else f"{v:,}"


def _style_axes(ax) -> None:
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(_GRID)
    ax.tick_params(colors=_TEXT, labelsize=9)
    ax.title.set_color(_TEXT)


def _render_hbar(title: str, items: list[tuple[str, float]], out: Path) -> None:
    from matplotlib import pyplot as plt

    items = items[:_MAX_BARS]
    labels = [k for k, _ in items][::-1]   # 큰 값이 위로
    values = [v for _, v in items][::-1]
    fig, ax = plt.subplots(figsize=(7, max(2.2, 0.5 * len(items) + 1)), dpi=150)
    bars = ax.barh(labels, values, color=_PALETTE[0], height=0.62)
    ax.bar_label(bars, labels=[_fmt(v) for v in values], padding=4, fontsize=8.5, color=_TEXT)
    ax.set_title(title, loc="left", fontsize=12, pad=12)
    ax.xaxis.grid(True, color=_GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out, facecolor="white")
    plt.close(fig)


def _render_line(title: str, dates: list[str], series: dict[str, list[float]], out: Path) -> None:
    from matplotlib import pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    for i, (name, vals) in enumerate(series.items()):
        ax.plot(dates, vals, label=name, color=_PALETTE[i % len(_PALETTE)], linewidth=1.8)
    ax.set_title(title, loc="left", fontsize=12, pad=12)
    ax.yaxis.grid(True, color=_GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    step = max(1, len(dates) // 8)   # x축 라벨 과밀 방지
    ax.set_xticks(range(0, len(dates), step))
    ax.tick_params(axis="x", rotation=45)
    if len(series) > 1:
        ax.legend(frameon=False, fontsize=9, labelcolor=_TEXT)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out, facecolor="white")
    plt.close(fig)


def _dict_to_items(value: dict, key: str) -> tuple[list[tuple[str, float]], str] | None:
    """dict 산출 → (정렬된 (라벨, 값) 리스트, 제목 접미사). 차트화 불가면 None."""
    title_suffix = ""
    numeric: dict[str, float] = {}
    for k, v in value.items():
        if _is_number(v):
            numeric[str(k)] = float(v)
        elif isinstance(v, dict):
            # by_category 류 {cat: {count, revenue}} — 첫 숫자 하위키로 통일
            sub = next((sk for sk, sv in v.items() if _is_number(sv)), None)
            if sub is None:
                return None
            numeric[str(k)] = float(v[sub])
            title_suffix = f" ({sub})"
    if not numeric or all(v == 0 for v in numeric.values()):
        return None
    items = sorted(numeric.items(), key=lambda kv: -kv[1])
    return items, title_suffix


def _rows_chart(rows: list[dict], out: Path) -> str | None:
    """rows 산출 → 라인(date 키) 또는 가로 막대(범주 키). 제목 반환, 불가면 None."""
    if not rows or not isinstance(rows[0], dict):
        return None
    first = rows[0]
    numeric_keys = [k for k, v in first.items() if _is_number(v)]
    if "date" in first:
        keys = numeric_keys[:2]
        if not keys:
            return None
        dates = [str(r.get("date", "")) for r in rows]
        series = {k: [float(r.get(k, 0) or 0) for r in rows] for k in keys}
        title = f"일별 추이 ({', '.join(keys)})"
        _render_line(title, dates, series, out)
        return title
    cat_key = next((k for k, v in first.items() if isinstance(v, str)), None)
    if cat_key is None or not numeric_keys:
        return None
    metric = "roas" if "roas" in numeric_keys else numeric_keys[0]
    items = sorted(
        ((str(r.get(cat_key, "")), float(r.get(metric, 0) or 0)) for r in rows),
        key=lambda kv: -kv[1],
    )
    if all(v == 0 for _, v in items):
        return None
    title = f"{cat_key}별 {metric}"
    _render_hbar(title, items, out)
    return title


class ChartGenerator(BaseTool):
    """분석 산출 → 차트 PNG. 렌더 단계(ToolCategory.RENDERING) — responder 가 attachment 표시."""

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        _setup_matplotlib()

        # 후보 = 상류 COMPLETED 산출들 + params 직접 전달분 (직접 호출·테스트 경로)
        candidates: list[dict] = []
        for v in (context.previous_results or {}).values():
            data = v.get("data") if isinstance(v, dict) and isinstance(v.get("data"), dict) else v
            if isinstance(data, dict):
                candidates.append(data)
        candidates.append(params)

        out_dir = Path(
            params.get("output_dir")
            or (_REPO_ROOT / "data" / (context.client_id or "default") / "outputs" / "charts")
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        paths: list[str] = []
        charts_meta: list[dict[str, str]] = []
        seen_keys: set[str] = set()

        for data in candidates:
            if len(paths) >= _MAX_CHARTS:
                break
            for key, value in data.items():
                if len(paths) >= _MAX_CHARTS:
                    break
                if key.startswith("_") or key in seen_keys:
                    continue
                if isinstance(value, dict) and (value.get("_dataref") or value.get("_state_guard")):
                    continue  # 참조 스텁 = 데이터 아님 (정직 — 모형을 차트화하지 않는다)

                out = out_dir / f"chart_{ts}_{len(paths)}_{key}.png"
                title: str | None = None
                if key in _DICT_ARTIFACTS and isinstance(value, dict):
                    converted = _dict_to_items(value, key)
                    if converted:
                        items, suffix = converted
                        title = f"{_DICT_ARTIFACTS[key]}{suffix}"
                        _render_hbar(title, items, out)
                elif key == "rows" and isinstance(value, list):
                    title = _rows_chart(value, out)

                if title:
                    seen_keys.add(key)
                    paths.append(str(out))
                    charts_meta.append({"title": title, "source_key": key})

        if not paths:
            logger.info("chart_generator skipped — 차트화 가능한 산출 없음(data_insufficient)",
                        session_id=context.session_id)
            return {"chart_image_paths": [], "reason": "data_insufficient",
                    "detail": "차트화 가능한 분석 산출(by_*·분포·rows) 0건"}

        logger.info("chart_generator completed", charts=len(paths),
                    titles=[c["title"] for c in charts_meta])
        return {"chart_image_paths": paths, "chart_count": len(paths), "charts": charts_meta}
