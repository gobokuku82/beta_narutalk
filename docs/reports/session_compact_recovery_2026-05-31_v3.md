# Session Compact 준비 (2026-05-31 v3) — 작업 ④·⑤·⑥·⑦ 완료, 박제 단일소스 완성

> v2 = 작업 ③ 완료 + 작업 ④ 진입 ([session_compact_recovery_2026-05-30_v2.md](./session_compact_recovery_2026-05-30_v2.md)).
> v3 = **작업 ④ 완료 (5 commit, 7 layer 완주) + 작업 ⑤ 완료 (32 v1.2 정합, 5 commit) + 작업 ⑥ 완료 (별 ONE 정합, 2 commit) + 작업 ⑦ 완료 (32 §9·§11 + v1.2 헤더, 1 commit)**.

---

## ★ 이어가기 (compact 직후 진입)

### 1분 요약

- **박제 단일소스 사슬 완성** (9 곳): enum + catalog 폴더 + 33/* + 32 v1.2 + _schema.yaml + ADR-022 amended + 30_DATA_MODELS + API_SPEC + frontend.
- **90 tool 8 카테고리** (collection 27 + normalization 6 + cleaning 3 + preprocessing 1 + metrics 35 + comparison 7 + analysis 9 + report 2).
- 골든 baseline = **303 passed / 3 failed** (pyarrow), 분석 team **275/11/2** (HITL), sprint15 **17/54** (broken). S001=119,539,660.

### 작업 ④·⑤·⑥·⑦ commit (총 13)

| commit | 작업 | 시점 |
|---|---|---|
| `e0655ac` | 작업 ④-L4 dashboard_v1 docstring | 2026-05-30 |
| `d517e9e` | 작업 ④-L5 C1 enum 8 추가 | 2026-05-31 |
| `dd9dbd1` | 작업 ④-L5 C2 yaml 74 + strict + sprint15 + 옛 enum 제거 | 2026-05-31 |
| `7f0ee5f` | 작업 ④-L5 C3 frontend classifyTool 폐기 | 2026-05-31 |
| `3738be6` | 작업 ④-L7 후속 (33_analysis·shared·admin·registry 死코드) | 2026-05-31 |
| `aeee54f` | 작업 ⑤ C0 §2.5 + 33/README 카테고리 8 정합 | 2026-05-31 |
| `ccfcb6c` | 작업 ⑤ C1 §5 BaseTool ADR-022 정합 patch | 2026-05-31 |
| `58c8228` | 작업 ⑤ C2 §6 + _schema.yaml YAML 스키마 정합 | 2026-05-31 |
| `9209d55` | 작업 ⑤ C3 §7 구현 전수표 폐기 (77 줄 삭제) | 2026-05-31 |
| `9f4373d` | 작업 ⑤ C4 §8 다이어그램 rewrite + §6 예제 정합 | 2026-05-31 |
| `75cc921` | 작업 ⑥ S1 30_DATA_MODELS + API_SPEC 8 카테고리 정합 | 2026-05-31 |
| `19c0ac9` | 작업 ⑥ S2 ADR-022 amend (§4·§5 + 46 → 90 tool) | 2026-05-31 |
| `b534ec6` | 작업 ⑦ (가) 32 §9·§11 잔존 + v1.1 → v1.2 헤더 | 2026-05-31 |

### compact 후 첫 행동

1. 본 문서 §0 ~ §3 정독 (박제 사슬 완성 + 우선순위).
2. §4 권장 다음 우선순위 (3 옵션) 중 선택 또는 사용자 다른 결정.
3. 진입 시 §5 baseline + §6 함정 + §7 진입 안전 준수.

---

## 0. 박제 단일소스 사슬 완성 상태

### 0.1 9 곳 정합 (작업 ④·⑤·⑥·⑦)

| # | 박제 위치 | 정합 commit |
|---|---|---|
| 1 | `enums.py` ToolCategory 8값 | `d517e9e` + `dd9dbd1` |
| 2 | `catalog/{8 폴더}/` 90 yaml | `dd9dbd1` |
| 3 | `33_tools_by_category/*` 8 문서 + README | `aeee54f` + `3738be6` |
| 4 | `32 v1.2` §2.5·§5·§6·§7·§8·§9·§11 | `aeee54f`·`ccfcb6c`·`58c8228`·`9209d55`·`9f4373d`·`b534ec6` |
| 5 | `_schema.yaml` line 20 | `58c8228` |
| 6 | `ADR-022` amended §4·§5 | `19c0ac9` |
| 7 | `30_DATA_MODELS:409` | `75cc921` |
| 8 | `API_SPEC:834` | `75cc921` |
| 9 | `frontend ToolPalette` `tool.category` 직접 | `7f0ee5f` |

→ **카테고리 박제 + BaseTool DI 패턴 = 코드/spec/ADR/frontend 전 사슬 완성**.

### 0.2 카테고리 분포 (90 tool)

| 카테고리 | tool 수 | 출처 |
|---|---:|---|
| collection | 27 | catalog/collection/ + external/ + internal/ |
| normalization | 6 | catalog/normalization/ |
| cleaning | 3 | catalog/cleaning/ |
| preprocessing | 1 | catalog/preprocessing/ (text_preprocessor) |
| metrics | 35 | catalog/metrics/ |
| comparison | 7 | catalog/comparison/ |
| analysis | 9 | catalog/analysis/ (직속 6 + ml/ 2 + llm/ 1) |
| report (보조) | 2 | catalog/report/ (report_writer + summary_generator) |
| **합** | **90** | |

---

## 1. 검증 baseline (작업 ⑦ 종료 시점)

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
# 기대: collection 27, normalization 6, ..., report 2, total 90

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

# 카테고리 박제 4 카테고리 잔존 grep (전수)
grep -rn "data | analysis | content | ops\|data, analysis, content, ops" docs/ --include="*.md" | grep -v "session_compact\|계획_작업"
# 기대: 0 hit (계획서 인용은 history)
```

---

## 2. 다음 우선순위 옵션

### 2.1 권장 옵션 (작업 ⑦ 후)

| # | 옵션 | 작업 | 분량 |
|---|---|---|---|
| **(가)** | 33/* 8 문서 outdated 전체 점검 | 33_collection·normalization·cleaning·preprocessing·metrics·comparison·report 7 문서 (33_analysis 외) | 中 |
| **(나)** | `_claude/*` outdated grep + 정리 | 32·33·ADR 인용 outdated 잔존 | 中 |
| **(다)** | sprint15 broken 정리 | agent team 결합, 17/54 → 통과 | 大 |
| **(라)** | mock raw 데이터 신규 진입 | 새 client 추가 시 표준 영어 컬럼 mock raw 생성 | 가변 |
| **(마)** | 옵션 C schema 신규 진입 시 점진 적용 | 32 §2.7 박제, 신규 tool 진입 시 자연 적용 | 점진 |
| **(바)** | 멈춤 + 사용자 다른 우선순위 | — | — |

### 2.2 전문가 권장

- **(가) 33/* 8 문서 outdated 점검** = 박제 정합성 마무리. 작업 ④·⑤·⑥·⑦ 의 사슬 끝마무리. 분량 中.
- (다) sprint15 = 큰 작업, agent team 미완성 = POC 단계 우선순위 中.
- (라)·(마) = 신규 작업 진입 시점.

---

## 3. 참조 문서 (모두 정합 확인)

### 3.1 박제 단일소스 (작업 ⑤·⑥·⑦ 정합)

| 참조 | path | 의도 |
|---|---|---|
| 32 v1.2 | [docs/agent_specs/32_execution_agent_tools_v1.0.md](../agent_specs/32_execution_agent_tools_v1.0.md) | 카테고리 8 정의 + decision tree + 옵션 C + BaseTool ADR-022 정합 + 90 tool 다이어그램 |
| 33 README | [33_tools_by_category/README.md](../agent_specs/33_tools_by_category/README.md) | 8 카테고리 진입, 카테고리 8 정의 박제 |
| 33_collection.md | [33_collection.md](../agent_specs/33_tools_by_category/33_collection.md) | 27 tool |
| 33_normalization.md | [33_normalization.md](../agent_specs/33_tools_by_category/33_normalization.md) | 6 tool |
| 33_cleaning.md | [33_cleaning.md](../agent_specs/33_tools_by_category/33_cleaning.md) | 3 tool |
| 33_preprocessing.md | [33_preprocessing.md](../agent_specs/33_tools_by_category/33_preprocessing.md) | 1 tool |
| 33_metrics.md | [33_metrics.md](../agent_specs/33_tools_by_category/33_metrics.md) | 35 tool |
| 33_comparison.md | [33_comparison.md](../agent_specs/33_tools_by_category/33_comparison.md) | 7 tool |
| 33_analysis.md | [33_analysis.md](../agent_specs/33_tools_by_category/33_analysis.md) | 9 tool (직속 6 + ml/ 2 + llm/ 1) |
| 33_report.md | [33_report.md](../agent_specs/33_tools_by_category/33_report.md) | 2 tool |
| ADR-022 (amended) | [ADR-022_data_source_workspace_layer_separation.md](../agent_specs/adr/ADR-022_data_source_workspace_layer_separation.md) | DataSource DI + helper-B + client_id fail-fast + 90 tool |

### 3.2 작업 계획서 (작업 ⑤ 패턴 박제)

| 계획서 | 패턴 |
|---|---|
| [계획_작업④L5_카테고리enum정합_2026-05-31.md](./계획_작업④L5_카테고리enum정합_2026-05-31.md) | 작업 ④-L5 (C1·C2·C3 enum 정합) |
| [계획_작업⑤_32문서_§4-§9_정합_2026-05-31.md](./계획_작업⑤_32문서_§4-§9_정합_2026-05-31.md) | 작업 ⑤ (C0·C1·C2·C3·C4) — 1·2·3차 적대적 검증 루프 박제 |

### 3.3 이전 recovery (시간순)

| 문서 | 시점 |
|---|---|
| [v2 (2026-05-30, 작업 ③ 완료 + ④ 진입)](session_compact_recovery_2026-05-30_v2.md) | 작업 ④ 진입 시점 |
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
2. **§0 박제 단일소스 사슬 정독** — 9 곳 정합 상태 확인.
3. **§1.2 정합 검증 명령 실행** (선택, 안전 진입 시):
   ```bash
   # 90 tool 8 카테고리 정합 확인
   cd backend && uv run python -c "..." (§1.2)
   # 기대: total 90, 8 카테고리 분포 정합
   ```
4. **§2.2 권장 우선순위** 중 선택 → 사용자 결정.
5. 진입 시 §6 함정 + §7 진입 안전 준수.

---

## 5. 함정·교훈 (작업 ④·⑤·⑥·⑦ 누적)

1. **박제 단일소스 분산** — 카테고리 박제 = 9 곳 (enum + 폴더 + 33/* + 32 + _schema + ADR + 30·API + frontend). 1 곳 갱신 시 다른 8 곳 일관성 확인 필수.
2. **agent attribution 오류** — workflow agent 가 line 번호 잘못 박제 가능 (작업 ⑤ §4·§9 의 §6 line 인용 오류). 직접 Read 로 spot-check 필수.
3. **계획서 검증 ROI 감소** — 1차 검증 5건 가치, 2차 5건, 3차 0건. 4차+ ROI 한계. 실 commit 진입이 최종 검증.
4. **fail verdict 노이즈** — agent 가 "계획 미실행 = fail" 잘못 verdict. 계획 = 미래 청사진, 실 파일 즉시 불일치가 정상.
5. **line shift 영향** — 표 행 추가 시 후속 line 번호 +1. 메서드명 기준 grep 권장 (line 인용 fragile).
6. **status 박제 2 시스템** — yaml status (registry, 폐기) vs team_catalog status (Planner, 활성). 갱신 시 구분.
7. **ADR amend vs supersede** — POC 단계 ADR 본문 갱신 = amend (헤더 박제 + 본문 정정). supersede 절차 과잉.
8. **dry-run ≠ 안전판** — 스크립트가 실 write 한다. preview + rollback (git checkout) 절차 박제.
9. **glob 의존성** — `**/*.yaml` bash globstar 옵션 의존. `find ... -name "*.yaml"` 권장.
10. **PowerShell vs Bash** — `&` background, `kill %1`, here-doc 부적합. Bash 명시 또는 git-bash 사용.
11. **broken link 점검** — 32 §6 예제 yaml link 가 실 없는 파일 (`naver_collector.yaml`) 박제 가능 (작업 ⑤ C4 발견).
12. **이력 박제 보존** — ADR §10 "46 tool DI 전환 ≈ 13 commits" = 작업 회고, 갱신 불요 (history).

---

## 6. 진입 안전 (compact 후 작업 ⑧ 진입 시)

- 작업 진입 전 골든 baseline 확인 (303/3 + 275/11/2 + sprint15 17/54).
- ONE 변경 원칙: 한 turn = 한 의미 단위 commit.
- 큰 결정만 surface, 작은 진행은 자명.
- 死코드 즉시 폐기 (사용자 원칙).
- 계획서 → 검증 → 작업 (큰 작업 시).
- 사용자 = 비전공자, 직설 전문가 단일 권장.
- workflow tool 적극 활용 (ultracode 모드 정합).

---

## 7. 작업 ⑧ 진입 candidate (compact 직후)

### 7.1 (가) 33/* 7 문서 점검

대상: 33_collection·normalization·cleaning·preprocessing·metrics·comparison·report (33_analysis 외).

점검 사항:
- tool 수 정합 (실 yaml count vs 박제)
- tool 이름 정합 (rename·이동·분리 반영)
- status 컬럼 정합 (complete/partial/planned)
- anti-pattern 박제 정합 (작업 ③ decision tree 정합)

작업: 7 문서 spot-check → outdated 발견 시 일괄 갱신 (1~7 commit, 분량 가변).

### 7.2 (나) `_claude/*` outdated grep

대상: `docs/_claude/architecture/`, `docs/_claude/plans/`, `docs/_claude/INDEX.md`.

점검: 32·33·ADR·코드 인용 outdated 잔존 grep.

작업: outdated 발견 시 갱신 또는 폐기 (history 박제 보존 vs 활성 박제 갱신 구분).

### 7.3 (다) sprint15 broken 정리

대상: backend/tests/sprint15/* (17 passed / 54 failed broken baseline).

큰 작업: agent team 결합 분석 + 통과 가능 테스트 분리 + broken 테스트 재설계 또는 폐기.

별 계획서 권장.

---

**작성 완료**: 2026-05-31. 본 문서 = 작업 ④·⑤·⑥·⑦ 완료 박제. compact 진입 가능.
