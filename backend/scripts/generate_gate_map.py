"""Gate Map 생성기 — 43_gate_ledger §1 표 → §4 Mermaid + §4-2 두 평면 뷰 + 브라우저용 HTML (그림=파생, 표=진실).

게이트 ~28개 시대의 구조도 전략(오너 결정 2026-06-12): 손그림 세부도는 그리는 날
예쁘고 다음 주에 거짓말이 된다 → 대장(표)만 사람이 갱신하고 그림·HTML 은 여기서 재생성.

검사 대상 축(v1.3): §1 검사 열(언어/접점/데이터/표면)이 §4 노드 색과 §4-2 두 평면 뷰를 결정 —
"데이터를 못 보는 cognitive·planning에 왜 게이트가?"의 답("언어를 검사한다")을 그림으로 박제.

사용:   cd backend && python -m scripts.generate_gate_map
산출:   ① 43_gate_ledger §4 Mermaid + §4-2 두 평면 뷰 재작성 (git 추적)
        ② docs/_claude/gate_ledger.html — 브라우저 열람용 (gitignored, 오너 상시 참조)
강제:   tests/test_gate_ledger_sync.py 가 표↔그림(§4·§4-2) 불일치를 RED 로 만든다 (HTML 은 비강제 — 명령으로 갱신).
"""
from __future__ import annotations

import html as _html
import re
from datetime import date
from pathlib import Path

_DOCS = Path(__file__).resolve().parents[2] / "docs"
LEDGER = _DOCS / "agent_specs" / "43_gate_ledger_v1.0.md"
HTML_OUT = _DOCS / "_claude" / "gate_ledger.html"
BEGIN, END = "<!-- GATE-MAP:BEGIN -->", "<!-- GATE-MAP:END -->"
PLANE_BEGIN, PLANE_END = "<!-- PLANE-MAP:BEGIN -->", "<!-- PLANE-MAP:END -->"

_SECTION_RE = re.compile(r"^### (1[a-g])\. (.+)$")
_ROW_RE = re.compile(r"^\| (G\d{2}) \| ([^|]+?) \|")

# frontend Warm Neutral 미러 (globals.css --chart-1~5 / --primary 옥스블러드)
_GROUP_COLORS = ["#5C7A99", "#A87257", "#507C6D", "#92799A", "#91826E", "#5C7A99", "#A87257"]
_ACCENT = "#962C3D"

# 검사 대상 축 — §1 검사 열 값 → (mermaid class, 평면 뷰 제목, fill, stroke)
_INSPECT = {
    "언어": ("lang", "🅛 언어 — LLM이 만든 layer 간 전달물 검사 (제어 평면)", "#E7EDF3", "#5C7A99"),
    "접점": ("junction", "🅛↔🅓 접점 — 언어의 약속 vs 데이터 현실 대조", "#EFE9F2", "#92799A"),
    "데이터": ("data", "🅓 데이터 — 실데이터·저장 형태 (저장 평면)", "#E3EBE6", "#507C6D"),
    "표면": ("surface", "표면 — 사람에게 나가는 표시·입력의 정직", "#F6E7D8", "#A87257"),
}
_PLANE_IDS = {"언어": "P_LANG", "접점": "P_JUNC", "데이터": "P_DATA", "표면": "P_SURF"}


def _short(name: str) -> str:
    """게이트명 셀에서 코드 괄호·백틱 제거 — 노드 라벨용."""
    name = re.sub(r"\(`[^)]*`[^)]*\)", "", name)
    name = name.replace("`", "").strip()
    return re.sub(r"\s+", " ", name)


def _parse_groups(md: str) -> list[tuple[str, str, list[list[str]]]]:
    """§1 의 (key, title, rows) — rows 는 셀 전체(ID·게이트·층·검사·무엇을·신호·박제)."""
    groups: list[tuple[str, str, list[list[str]]]] = []
    cur: tuple[str, str, list[list[str]]] | None = None
    for line in md.splitlines():
        m = _SECTION_RE.match(line)
        if m:
            cur = (m.group(1), m.group(2).strip(), [])
            groups.append(cur)
            continue
        if cur is not None and _ROW_RE.match(line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            cur[2].append(cells)
    return groups


def _inspect_of(cells: list[str]) -> str:
    """행의 검사 대상 값 (셀 4번째 — 없으면 빈 문자열)."""
    return cells[3] if len(cells) > 3 and cells[3] in _INSPECT else ""


def _class_lines(by_class: dict[str, list[str]]) -> list[str]:
    """classDef + class 할당 라인 (검사 대상 → 노드 색)."""
    lines = [
        f"  classDef {cls} fill:{fill},stroke:{stroke},color:#3D3833"
        for cls, _, fill, stroke in _INSPECT.values()
    ]
    for cls, gids in by_class.items():
        if gids:
            lines.append(f"  class {','.join(gids)} {cls}")
    return lines


def build_mermaid(md: str) -> str:
    lines = ["```mermaid", "flowchart TB"]
    order: list[str] = []
    by_class: dict[str, list[str]] = {cls: [] for cls, _, _, _ in _INSPECT.values()}
    for key, title, rows in _parse_groups(md):
        if not rows:
            continue
        sg = f"SG_{key}"
        order.append(sg)
        lines.append(f'  subgraph {sg}["{title.replace(chr(34), chr(39))}"]')
        for cells in rows:
            gid, label = cells[0], _short(cells[1])
            lines.append(f'    {gid}["{gid} {label.replace(chr(34), chr(39))}"]')
            insp = _inspect_of(cells)
            if insp:
                by_class[_INSPECT[insp][0]].append(gid)
        lines.append("  end")
    for a, b in zip(order, order[1:]):
        lines.append(f"  {a} --> {b}")
    lines.extend(_class_lines(by_class))
    lines.append("```")
    return "\n".join(lines)


def build_plane_mermaid(md: str) -> str:
    """§4-2 두 평면 뷰 — 같은 게이트를 검사 대상 축으로 재배열 (언어→접점→데이터 + 표면)."""
    by_inspect: dict[str, list[tuple[str, str]]] = {k: [] for k in _INSPECT}
    for _, _, rows in _parse_groups(md):
        for cells in rows:
            insp = _inspect_of(cells)
            if insp:
                by_inspect[insp].append((cells[0], _short(cells[1])))

    lines = ["```mermaid", "flowchart LR"]
    by_class: dict[str, list[str]] = {cls: [] for cls, _, _, _ in _INSPECT.values()}
    for insp, gates in by_inspect.items():
        if not gates:
            continue
        cls, title, _, _ = _INSPECT[insp]
        pid = _PLANE_IDS[insp]
        lines.append(f'  subgraph {pid}["{title} ({len(gates)})"]')
        lines.append("    direction TB")
        for gid, label in gates:
            lines.append(f'    {gid}["{gid} {label.replace(chr(34), chr(39))}"]')
            by_class[cls].append(gid)
        lines.append("  end")
    lines.append('  P_LANG -->|"계획·params"| P_JUNC')
    lines.append('  P_JUNC -->|"조회 (DataSource 관절 §2)"| P_DATA')
    lines.append('  P_JUNC -->|"SKIP·사유 신호"| P_SURF')
    lines.extend(_class_lines(by_class))
    lines.append("```")
    return "\n".join(lines)


def render(md: str) -> str:
    """§4·§4-2 마커 블록을 표에서 재생성한 Mermaid 로 치환한 전문 반환 (순수 함수)."""
    for begin, end, builder in (
        (BEGIN, END, build_mermaid),
        (PLANE_BEGIN, PLANE_END, build_plane_mermaid),
    ):
        pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.S)
        md = pattern.sub(begin + "\n" + builder(md) + "\n" + end, md)
    return md


# ─────────────────────────── HTML (브라우저 열람용) ───────────────────────────

def _inline(s: str) -> str:
    """md 셀 → HTML (escape 후 굵게/코드만 변환, 링크는 텍스트로)."""
    s = _html.escape(s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def _extract_mermaid_after(md: str, header_prefix: str) -> str:
    """주어진 헤더/마커 이후 첫 ```mermaid 블록 본문."""
    try:
        seg = md.split(header_prefix, 1)[1]
        return seg.split("```mermaid", 1)[1].split("```", 1)[0].strip()
    except IndexError:
        return ""


def _extract_table_after(md: str, header_prefix: str) -> list[list[str]]:
    """헤더 이후 첫 md 표의 데이터 행들 (헤더/구분선 제외)."""
    try:
        seg = md.split(header_prefix, 1)[1]
    except IndexError:
        return []
    rows: list[list[str]] = []
    started = False
    for line in seg.splitlines():
        if line.startswith("|"):
            started = True
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= {"-", " "} for c in cells):
                continue
            rows.append(cells)
        elif started:
            break
    return rows[1:] if rows else []   # 첫 행 = 헤더


def build_html(md: str) -> str:
    groups = _parse_groups(md)
    overlay = _extract_mermaid_after(md, "## §5")
    gatemap = _extract_mermaid_after(md, BEGIN)
    planemap = _extract_mermaid_after(md, PLANE_BEGIN)
    plane_rows = _extract_table_after(md, "## §2")
    n_gates = sum(len(r) for _, _, r in groups)
    planned = sum(1 for _, _, rs in groups for c in rs if "예정" in c[1])
    insp_counts: dict[str, int] = {k: 0 for k in _INSPECT}
    for _, _, rows in groups:
        for cells in rows:
            insp = _inspect_of(cells)
            if insp:
                insp_counts[insp] += 1

    sec_html = []
    for i, (key, title, rows) in enumerate(groups):
        color = _GROUP_COLORS[i % len(_GROUP_COLORS)]
        trs = []
        for cells in rows:
            gid = cells[0]
            badge = '<span class="badge planned">예정</span>' if "예정" in cells[1] else '<span class="badge live">현역</span>'
            cols = []
            for j, c in enumerate(cells[1:]):
                if j == 2 and c in _INSPECT:   # 검사 열 → 색 배지
                    cols.append(f'<td><span class="insp {_INSPECT[c][0]}">{c}</span></td>')
                else:
                    cols.append(f"<td>{_inline(c)}</td>")
            trs.append(f'<tr><td class="gid">{gid} {badge}</td>{"".join(cols)}</tr>')
        sec_html.append(
            f'<details open><summary style="border-left:6px solid {color}">{_html.escape(title)}'
            f' <span class="cnt">{len(rows)}</span></summary>'
            f'<table><thead><tr><th>ID</th><th>게이트 (코드)</th><th>층</th><th>검사</th><th>무엇을</th>'
            f'<th>신호 → 소비자</th><th>박제</th></tr></thead><tbody>{"".join(trs)}</tbody></table></details>'
        )

    plane_trs = "".join(
        "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>" for cells in plane_rows
    )
    insp_pills = "".join(
        f'<span class="pill"><span class="insp {_INSPECT[k][0]}">{k}</span> <b>{v}</b></span>'
        for k, v in insp_counts.items()
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>OctorAD Gate Ledger — 뼈대 시각화</title>
<style>
  :root {{ --bg:#FAF7F2; --text:#3D3833; --muted:#8A8178; --line:#E8E2D9; --accent:{_ACCENT}; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Pretendard','Malgun Gothic',sans-serif;
         max-width:1280px; margin:0 auto; padding:32px 24px; line-height:1.55; }}
  h1 {{ font-size:22px; margin:0 0 4px; }} h1 small {{ color:var(--muted); font-weight:400; font-size:13px; }}
  h2 {{ font-size:16px; margin:36px 0 10px; padding-bottom:6px; border-bottom:1px solid var(--line); }}
  .meta {{ color:var(--muted); font-size:12.5px; margin-bottom:8px; }}
  .meta code {{ background:#F0EAE2; padding:1px 6px; border-radius:4px; }}
  .pill {{ display:inline-block; background:#F0EAE2; border-radius:999px; padding:2px 10px; font-size:12px; margin-right:6px; }}
  .pill b {{ color:var(--accent); }}
  details {{ margin:10px 0; }}
  summary {{ cursor:pointer; font-weight:600; font-size:14px; padding:6px 10px; background:#fff;
             border:1px solid var(--line); border-radius:8px; }}
  summary .cnt {{ color:var(--muted); font-weight:400; font-size:12px; }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px; margin:8px 0 4px; background:#fff;
           border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
  th {{ text-align:left; background:#F4EFE8; padding:7px 9px; font-size:12px; border-bottom:1px solid var(--line); }}
  td {{ padding:7px 9px; border-bottom:1px solid #F0EAE2; vertical-align:top; }}
  td.gid {{ white-space:nowrap; font-weight:700; }}
  code {{ background:#F0EAE2; padding:0 4px; border-radius:3px; font-size:11.5px; }}
  .badge {{ font-size:10.5px; border-radius:4px; padding:1px 5px; margin-left:4px; font-weight:600; }}
  .badge.live {{ background:#E3EBE6; color:#2F5D46; }}
  .badge.planned {{ background:#F6E7D8; color:#8A5A22; }}
  .insp {{ font-size:11px; border-radius:4px; padding:1px 7px; font-weight:600; white-space:nowrap; }}
  .insp.lang {{ background:#E7EDF3; color:#41607D; }}
  .insp.junction {{ background:#EFE9F2; color:#6E5A77; }}
  .insp.data {{ background:#E3EBE6; color:#2F5D46; }}
  .insp.surface {{ background:#F6E7D8; color:#8A5A22; }}
  .mermaid {{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:14px; margin:10px 0; }}
  .note {{ font-size:12px; color:var(--muted); }}
</style>
</head>
<body>
<h1>🛡 Gate Ledger — 뼈대 시각화 <small>생성물 · {date.today().isoformat()}</small></h1>
<p class="meta">진실 소스 = <code>docs/agent_specs/43_gate_ledger_v1.0.md</code> (표) ·
재생성 = <code>cd backend &amp;&amp; python -m scripts.generate_gate_map</code> · 이 파일은 gitignored(_claude) — 직접 고치지 말 것</p>
<p><span class="pill">게이트 <b>{n_gates}</b></span><span class="pill">현역 <b>{n_gates - planned}</b></span>
<span class="pill">예정 <b>{planned}</b></span> {insp_pills}</p>

<h2>① 두 평면 뷰 — 무엇을 검사하나 (검사 대상 축)</h2>
<p class="note">"데이터를 못 보는 cognitive·planning에 왜 게이트가?" → 그 게이트들은 데이터가 아니라
<strong>에이전트 언어</strong>(LLM이 만든 layer 간 전달물)를 검사한다. LLM 출력은 불신 입력 —
데이터를 못 보는 층일수록 자기 산출물이 틀려도 스스로 모르기 때문에 언어 게이트가 필요하다.
접점 게이트(execution 입구)는 언어의 약속을 데이터 현실과 대조하는 관문.</p>
<pre class="mermaid">{_html.escape(planemap)}</pre>

<h2>② 건설 현황 오버레이 — 2트랙이 뼈대의 어디를 짓는가</h2>
<p class="note">🅰 멀티쿼리(위층) · 🅱 pushdown(아래층). E번호 = 테스트 기반 검증 실측. 진실 = 마스터 계획서.</p>
<pre class="mermaid">{_html.escape(overlay)}</pre>

<h2>③ 게이트 구조도 — 어디 있나 (§4 와 동일, 색 = 검사 대상)</h2>
<pre class="mermaid">{_html.escape(gatemap)}</pre>

<h2>④ 게이트 대장 (전 행 코드 실측)</h2>
{"".join(sec_html)}

<h2>⑤ 데이터 평면 관절</h2>
<table><thead><tr><th>관절</th><th>위치/상태</th><th>역할</th></tr></thead><tbody>{plane_trs}</tbody></table>
<p class="note">오프라인 하네스(감사실)·갱신 규약은 43 문서 §3·§6 참조. mermaid 미렌더 시 인터넷 연결 확인 (CDN).</p>

<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
mermaid.initialize({{ startOnLoad: true, theme: "neutral", flowchart: {{ htmlLabels: true }} }});
</script>
</body>
</html>
"""


def main() -> None:
    md = LEDGER.read_text(encoding="utf-8")
    new_md = render(md)
    LEDGER.write_text(new_md, encoding="utf-8", newline="\n")
    print(f"gate map regenerated -> {LEDGER}")
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(build_html(new_md), encoding="utf-8", newline="\n")
    print(f"html view regenerated -> {HTML_OUT}")


if __name__ == "__main__":
    main()
