# Session Compact 준비 (2026-05-31 v4) — 작업 ④·⑤·⑥·⑦·⑧·⑨·⑩ 완료, 변경 hub 갱신 + 박제 사슬 9 곳 완성

> v3 = 작업 ④·⑤·⑥·⑦ 완료 ([session_compact_recovery_2026-05-31_v3.md](./session_compact_recovery_2026-05-31_v3.md)).
> v4 = **추가 작업 ⑧ (33/* 7 문서 점검) + ⑨ (41+40 변경 hub v1.1) + ⑩-가/나 (빈 폴더 폐기 + _claude·ADR 갱신)**.

---

## ★ 이어가기 (compact 직후 진입)

### 1분 요약 (v4)

- **박제 단일소스 사슬 9 곳 + 메타 1 = 100% 정합** (작업 ⑨ 41+40 변경 hub 갱신 후 다음 변경 작업 가이드 100% 정확).
- **변경 시 봐야 할 문서** = [41 Change Hub v1.1](docs/agent_specs/41_agent_tool_change_hub_v1.0.md) → [40 Lifecycle v1.1](docs/agent_specs/40_agent_tool_lifecycle_v1.0.md). 작업 ⑨ commit `98f8563`·`b621a85`.
- **90 tool 8 카테고리** 정합 (collection 27 + normalization 6 + cleaning 3 + preprocessing 1 + metrics 35 + comparison 7 + analysis 9 + report 2).
- 골든 baseline 불변: **303 passed / 3 failed** (pyarrow), 분석 team **275/11/2** (HITL), sprint15 **17/54** (broken). S001=119,539,660.

### 작업 ④~⑩ 누적 commit (19)

| commit | 작업 | hash |
|---|---|---|
| 1 | 작업 ④-L4 dashboard_v1 docstring | `e0655ac` |
| 2 | 작업 ④-L5 C1 enum 8 추가 | `d517e9e` |
| 3 | 작업 ④-L5 C2 yaml 74 + strict + sprint15 + 옛 enum 제거 | `dd9dbd1` |
| 4 | 작업 ④-L5 C3 frontend classifyTool 폐기 | `7f0ee5f` |
| 5 | 작업 ④-L7 후속 (33_analysis·shared·admin·registry 死코드) | `3738be6` |
| 6 | 작업 ⑤ C0 §2.5 + 33/README 카테고리 8 | `aeee54f` |
| 7 | 작업 ⑤ C1 §5 BaseTool ADR-022 patch | `ccfcb6c` |
| 8 | 작업 ⑤ C2 §6 + _schema.yaml 정합 | `58c8228` |
| 9 | 작업 ⑤ C3 §7 전수표 폐기 (77 줄 삭제) | `9209d55` |
| 10 | 작업 ⑤ C4 §8 다이어그램 rewrite | `9f4373d` |
| 11 | 작업 ⑥ S1 30_DATA_MODELS + API_SPEC | `75cc921` |
| 12 | 작업 ⑥ S2 ADR-022 amend | `19c0ac9` |
| 13 | 작업 ⑦ (가) 32 §9·§11 + v1.1 → v1.2 헤더 | `b534ec6` |
| 14 | **작업 ⑦ (라) compact v3 박제** | `d26ec22` |
| 15 | **작업 ⑧ (가) 33_metrics 2 rename + 33_cleaning + 33_report 날짜** | `13a178a` |
| 16 | **작업 ⑨ C1 41 Change Hub v1.0 → v1.1** | `98f8563` |
| 17 | **작업 ⑨ C2 40 Lifecycle v1.0 → v1.1** | `b621a85` |
| 18 | **작업 ⑩ (가) tools/{image_creation, pdf, video_creation} 빈 폴더 폐기** | `a15f767` |
| 19 | **작업 ⑩ (나) ADR-014 + ADR-019 amend (옛 path 정합)** | `b5268ee` |

### compact 후 첫 행동

1. 본 문서 §0~§3 정독 (박제 사슬 + 변경 hub + 다음 우선순위).
2. §4 권장 다음 우선순위 (3 옵션) 중 선택 또는 사용자 다른 결정.
3. 진입 시 §5 함정 + §6 진입 안전 준수.

---

## 0. 박제 단일소스 사슬 9 곳 + 메타 1 (완성)

### 0.1 9 곳 정합 (모두 박제 + 변경 hub 안내)

| # | 박제 위치 | 작업 commit |
|---|---|---|
| 1 | `enums.py:29-40` ToolCategory 8값 | `dd9dbd1` |
| 2 | `catalog/{8 폴더}/` 90 yaml | `dd9dbd1` |
| 3 | `33_tools_by_category/*` (8 문서 + README) | `aeee54f`·`3738be6`·`13a178a` |
| 4 | `32 v1.2` §2.5·§5·§6·§7·§8·§9·§11 (파일명 v1.0 유지) | `aeee54f`~`b534ec6` |
| 5 | `_schema.yaml` line 20 | `58c8228` |
| 6 | `ADR-022 amended` §4·§5 | `19c0ac9` |
| 7 | `30_DATA_MODELS:409` | `75cc921` |
| 8 | `API_SPEC:834` | `75cc921` |
| 9 | `frontend ToolPalette` (`tool.category` 직접) | `7f0ee5f` |
| (메타) | `session_compact_recovery_2026-05-31_v4.md` (본 문서) | 현 commit |

### 0.2 변경 hub 갱신 (작업 ⑨)

| 문서 | 갱신 | commit |
|---|---|---|
| [41 Change Hub v1.1](../agent_specs/41_agent_tool_change_hub_v1.0.md) | §2.2 박제 단일소스 9 곳 표 신규 + §4 매트릭스 spec 33·ADR-022·30·API 행 + §5 Phase 2 다중 + §8 link 확장 | `98f8563` |
| [40 Lifecycle v1.1](../agent_specs/40_agent_tool_lifecycle_v1.0.md) | §5.2 박제 단일소스 9 곳 enumeration + §8 link 갱신 + §3.A 33/* 진입 안내 | `b621a85` |

→ **다음 변경 작업 (Tool 추가·rename·카테고리 변경) 시 41 → 40 진입 가이드 100% 정확**.

### 0.3 ADR amend (작업 ⑥·⑩)

| ADR | amend | commit |
|---|---|---|
| ADR-022 (DataSource DI) | §4·§5 helper-B + clumi default 폐기 + 46 → 90 tool | `19c0ac9` |
| ADR-014 (단일 책임 분리) | path 박제 갱신 (preprocessing/data_normalization → normalization) | `b5268ee` |
| ADR-019 (summary_generator) | path 박제 갱신 (shared → report) | `b5268ee` |

→ ADR 본문 결정 박제 시점 (2026-05-19) 이력 보존 + Status amend 안내 패턴.

### 0.4 카테고리 분포 (90 tool, 8 카테고리, registry strict 통과)

| 카테고리 | tool 수 | 33/* 문서 |
|---|---:|---|
| collection | 27 | [33_collection.md](../agent_specs/33_tools_by_category/33_collection.md) |
| normalization | 6 | [33_normalization.md](../agent_specs/33_tools_by_category/33_normalization.md) |
| cleaning | 3 | [33_cleaning.md](../agent_specs/33_tools_by_category/33_cleaning.md) |
| preprocessing | 1 | [33_preprocessing.md](../agent_specs/33_tools_by_category/33_preprocessing.md) |
| metrics | 35 | [33_metrics.md](../agent_specs/33_tools_by_category/33_metrics.md) |
| comparison | 7 | [33_comparison.md](../agent_specs/33_tools_by_category/33_comparison.md) |
| analysis | 9 | [33_analysis.md](../agent_specs/33_tools_by_category/33_analysis.md) (직속 6 + ml/ 2 + llm/ 1) |
| report (보조) | 2 | [33_report.md](../agent_specs/33_tools_by_category/33_report.md) |
| **합** | **90** | + [README.md](../agent_specs/33_tools_by_category/README.md) |

---

## 1. 검증 baseline (작업 ⑩ 종료 시점)

### 1.1 회귀 baseline (불변)

| 영역 | baseline | 검증 명령 (Bash) |
|---|---|---|
| dashboard1 영역 | 303 passed / 3 failed (pyarrow 환경) | `uv run pytest backend/tests/{pipelines,dashboard1,data_sources,workspace,permissions,ml_models} -q` |
| 분석 team (sprint13+14) | 275 passed / 11 failed (HITL) / 2 skipped | `uv run pytest backend/tests/sprint13 backend/tests/sprint14 -q` |
| sprint15 broken | 17 passed / 54 failed | `uv run pytest backend/tests/sprint15 -q` |
| frontend type-check | exit 0 | `cd frontend && pnpm exec tsc --noEmit` |

### 1.2 정합 검증 명령

```bash
# 90 tool 8 카테고리 분포 (registry strict 통과)
cd backend && uv run python -c "
from app.dream_agent.tools.registry import get_registry
from collections import Counter
reg = get_registry(); reg.load()
print(Counter(str(t.category.value) for t in reg.get_all()))
print('total:', len(reg.get_all()))
"
# 기대: collection 27, normalization 6, cleaning 3, preprocessing 1, metrics 35, comparison 7, analysis 9, report 2, total 90

# 90 tool 모두 Python import 가능
cd backend && uv run python -c "
from app.dream_agent.tools.registry import get_registry
reg = get_registry(); reg.load()
ok, fail = 0, []
for t in reg.get_all():
    try: reg.import_tool(t.name); ok += 1
    except Exception as e: fail.append((t.name, str(e)[:60]))
print(f'OK {ok}/{len(reg.get_all())}, FAIL: {fail}')
"
# 기대: OK 90/90, FAIL: []

# 4 카테고리 박제 잔존 (활성 outdated only)
grep -rn "data | analysis | content | ops\|data, analysis, content, ops" docs/agent_specs/ | grep -v "ADR-022\|tools_old"
# 기대: 0 hit (활성 spec 모두 정합)

# 빈 폴더 (작업 ⑩-가 후) 잔존 0
find backend/app/dream_agent/tools -maxdepth 1 -type d -empty
# 기대: 0 hit
```

---

## 2. 다음 우선순위 옵션

### 2.1 권장 옵션 (작업 ⑩-나 후)

| # | 옵션 | 작업 | 분량 |
|---|---|---|---|
| **(가)** | 65_dashboard_pages_v1.0.md 정합 | preprocessing/marketing 4 곳 + cleaning 카테고리 박제 오류 1 곳 = 5 곳 갱신 (작업 ⑩-나 발견, 활성 spec) | 中 |
| **(나)** | sprint15 broken 정리 | agent team 결합, 17/54 → 통과 (별 계획서) | 大 |
| **(다)** | mock raw 데이터 신규 진입 | 새 client 추가 시 표준 영어 컬럼 mock raw | 가변 |
| **(라)** | 옵션 C schema 신규 진입 시 점진 적용 | 32 §2.7, 신규 tool 진입 시 자연 적용 | 점진 |
| **(마)** | 멈춤 + 사용자 다른 우선순위 | — | — |

### 2.2 전문가 권장

- **(나) sprint15 broken** = 가장 큰 잔존 부담. agent team 결합 분리·재설계 (별 계획서 권장).
- (가) 65_dashboard = 작은 갱신 (5 곳), 활성 spec 정합 (中 분량).
- (다)·(라) = 신규 작업 진입 시점.

사용자 명시 (compact 후 진행 순서) = **(다) sprint15**.

---

## 3. 참조 문서 (모두 정합 확인)

### 3.1 변경 시 진입 (작업 ⑨ 갱신)

| 진입 단계 | 문서 |
|---|---|
| 1. **빠른 진입** | [41 v1.1 Change Hub](../agent_specs/41_agent_tool_change_hub_v1.0.md) — 5 시나리오 결정 + 박제 사슬 9 곳 + 5 Phase |
| 2. **시나리오 절차** | [40 v1.1 Lifecycle](../agent_specs/40_agent_tool_lifecycle_v1.0.md) §3.A~3.E + §5.2 박제 9 곳 |
| 3. **카테고리 진실 소스** | [33_tools_by_category/](../agent_specs/33_tools_by_category/) 8 문서 + README |
| 4. **카테고리 정의·BaseTool 패턴** | [32 v1.2](../agent_specs/32_execution_agent_tools_v1.0.md) §2.5·§5·§6·§8 |
| 5. **DataSource DI 패턴** | [ADR-022 amended](../agent_specs/adr/ADR-022_data_source_workspace_layer_separation.md) §4·§5 |

### 3.2 작업 계획서 (작업 ⑤·⑨ 패턴)

| 계획서 | 패턴 |
|---|---|
| [계획_작업④L5_카테고리enum정합_2026-05-31.md](./계획_작업④L5_카테고리enum정합_2026-05-31.md) | 작업 ④-L5 enum 정합 |
| [계획_작업⑤_32문서_§4-§9_정합_2026-05-31.md](./계획_작업⑤_32문서_§4-§9_정합_2026-05-31.md) | 작업 ⑤ 32 §4~§9 정합 — 1·2·3차 적대적 검증 루프 박제 |
| [계획_작업⑨_41+40_변경hub_정합_2026-05-31.md](./계획_작업⑨_41+40_변경hub_정합_2026-05-31.md) | 작업 ⑨ 41+40 정합 — 1·2차 적대적 검증 |

### 3.3 이전 recovery (시간순)

| 문서 | 시점 |
|---|---|
| [v3 (2026-05-31, 작업 ⑦까지)](session_compact_recovery_2026-05-31_v3.md) | 작업 ④·⑤·⑥·⑦ 완료 |
| [v2 (2026-05-30, 작업 ③+④ 진입)](session_compact_recovery_2026-05-30_v2.md) | 작업 ④ 진입 |
| [v1 (2026-05-30, 작업 ② 마무리)](session_compact_recovery_2026-05-30.md) | 작업 ② contract A |

### 3.4 진입 지도

| 문서 | 역할 |
|---|---|
| [.claude/CLAUDE.md](../../.claude/CLAUDE.md) | 매 세션 자동 로드 |
| [docs/agent_specs/INDEX.md](../agent_specs/INDEX.md) | spec 진입 |
| MEMORY.md (user) | 사용자 원칙 (auto-load) |

---

## 4. compact 후 첫 행동 (권장)

1. **★ 이어가기 정독** (본 문서 최상단).
2. **§0 박제 사슬 정독** — 9 곳 정합 + 변경 hub 갱신 + ADR amend 상태 확인.
3. **§1.2 정합 검증 명령 실행** (선택, 안전 진입 시):
   ```bash
   cd backend && uv run python -c "..."  # §1.2 참조
   # 기대: total 90, 8 카테고리 분포 정합
   ```
4. **§2.2 권장 우선순위**: 사용자 명시 (compact 후 진행) = **(다) sprint15 broken 정리** (별 계획서 권장).
5. 진입 시 §5 함정 + §6 진입 안전 준수.

---

## 5. 함정·교훈 (작업 ④·⑤·⑥·⑦·⑧·⑨·⑩ 누적)

1. **박제 단일소스 분산** — 9 곳 + 메타 1. 1 곳 갱신 시 다른 8 곳 일관성 확인 필수 (silent bug 위험).
2. **agent attribution 오류** — workflow agent 가 line 번호 잘못 박제 가능 (작업 ⑤ §4·§9 의 §6 line 인용 오류). 직접 Read 로 spot-check.
3. **계획서 검증 ROI 감소** — 1차 검증 가치 多, 3차 ROI 한계. 실 commit 진입이 최종 검증.
4. **fail verdict 노이즈** — agent 가 "계획 미실행 = fail" 잘못 verdict. 계획 = 미래 청사진.
5. **line shift 영향** — 표 행 추가 시 후속 line 번호 +1. 메서드명 기준 grep 권장.
6. **status 박제 2 시스템** — yaml status (registry, 폐기) vs team_catalog status (Planner, 활성). 갱신 시 구분.
7. **ADR amend vs supersede** — POC 단계 ADR 본문 갱신 = amend (Status 박제 + 본문 결정 시점 이력 보존). ADR-022·014·019 모두 amend 패턴.
8. **glob 의존성** — `**/*.yaml` bash globstar 옵션 의존. `find ... -name "*.yaml"` 권장.
9. **PowerShell vs Bash** — `&` background, `kill %1`, here-doc 부적합. Bash 명시 또는 git-bash.
10. **history vs active 박제 구분** — recovery·계획·과거 보고서 = history (시점 박제 보존), INDEX·가이드·spec = active (갱신 필요).
11. **_claude/ = .gitignored** — local 자취 보존, git 추적 X. _claude 갱신 = local only.
12. **빈 폴더 git rm 자동 폐기** — `git rm __init__.py` 후 빈 폴더는 git 자동 무관 (rmdir 불요).
13. **broken link 점검** — spec 의 yaml link 가 실 없는 파일 박제 가능 (작업 ⑤ C4 의 32 §6 예제 발견).
14. **이력 박제 보존** — ADR §10 "46 tool" 같은 작업 회고 = 갱신 불요 (history).

---

## 6. 진입 안전 (compact 후 작업 ⑪ 진입 시)

- 작업 진입 전 골든 baseline 확인 (303/3 + 275/11/2 + sprint15 17/54).
- ONE 변경 원칙: 한 turn = 한 의미 단위 commit.
- 큰 결정만 surface, 작은 진행은 자명.
- 死코드 즉시 폐기 (사용자 원칙).
- 큰 작업 = 계획서 → 1·2차 적대적 검증 → 사용자 승인 → 진입 (작업 ⑤·⑨ 패턴).
- 사용자 = 비전공자, 직설 전문가 단일 권장.
- workflow tool 적극 활용 (ultracode 모드).
- 변경 작업 진입 = [41 v1.1](../agent_specs/41_agent_tool_change_hub_v1.0.md) → [40 v1.1](../agent_specs/40_agent_tool_lifecycle_v1.0.md) 순서.

---

## 7. 작업 ⑪ 진입 (사용자 명시 = sprint15)

### 7.1 (다) sprint15 broken 정리 (사용자 우선순위)

대상: `backend/tests/sprint15/*` (17 passed / 54 failed broken baseline).

큰 작업 = agent team 결합 분석 + 통과 가능 테스트 분리 + broken 테스트 재설계 또는 폐기.

**별 계획서 권장** — 작업 ⑤·⑨ 패턴 (측정 workflow → 계획서 → 1·2차 적대적 검증 → 사용자 승인 → 진입).

진입 순서:
1. sprint15 broken 원인 분석 (workflow 측정)
2. 분류 (통과 가능 / agent team 결합 / 폐기)
3. 계획서 작성
4. 1·2차 적대적 검증
5. 사용자 승인 → 단계별 commit

### 7.2 (가) 65_dashboard_pages 정합 (별 ONE)

대상: docs/agent_specs/65_dashboard_pages_v1.0.md (5 곳 outdated 박제 — preprocessing/marketing 파이프라인 다이어그램).

분량: 中. 작업 ⑩-나 발견 (5 곳: line 195 cleaning 카테고리 박제 오류 1 + line 479·872·942·1277 preprocessing/marketing 다이어그램 4). (다) 후 진입 가능.

---

**작성 완료**: 2026-05-31. 본 문서 = 작업 ④·⑤·⑥·⑦·⑧·⑨·⑩ 완료 박제. compact 진입 가능.
