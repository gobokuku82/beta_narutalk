# ADR-017: Analysis Agent 의 도메인 분리 — 광고 / 리뷰 / 검색

## Status

**Proposed** (2026-05-19) — 카테고리 1 (collection → normalize → analysis) 재설계 Phase 1 박제. 사용자 결정 후 Accepted 갱신.

**Amended** (2026-06-01, 작업 ⑫ 후속) — broken 5 ads collector 폐기 박제:
- 본문 line 17 의 `meta_collector → format_normalizer → summary_generator` 시나리오 1 인용 = 결정 박제 시점 (2026-05-19) 이력 보존
- 실 상태: broken 5 폐기됨 (⑫.A). 신 ads chain (external/meta_ads_performance_collector → ...) 재구성 시 본 ADR 재검토 권장.

이전 이력: (없음 — 신규)

후속 이력:
- (예정) Accepted — 사용자 결정 + analysis agent 재구성 sprint 완료 시.

## Context

### 발견 — 사용자 P1 sprint 후 채팅 재테스트 (2026-05-19)

**시나리오 1 ("2024년 10월 메타 광고 성과 보여줘")**:
- meta_collector → format_normalizer (P1 fix ✅ 248 행) → summary_generator (광고 데이터 인식 못함)
- 채팅 응답: "분석 결과가 비어 있어 요약을 제공할 수 없습니다"
- **원인**: 분석 Tool 없이 summary 만 호출 → 광고 성과 분석 영역 자체가 미흡

### 현 박제 vs 이미지 명세

| Tool | 현재 박제 | 이미지 명세 (MVP) | 도메인 |
|---|---|---|---|
| sentiment_analyzer (POC-07) | ✅ implemented | ✅ | review |
| keyword_extractor (POC-06+08) | ✅ implemented | ✅ | review + 검색 |
| insight_extractor (POC-09) | ✅ implemented | ✅ | 둘 다 |
| trend_analyzer | 🟡 stub | ❌ 없음 | (모호) |
| competitor_comparator | 🟡 stub | ❌ 없음 | (모호) |
| kpi_anomaly_detector (POC-01) | — | ⬜ MVP | 광고 |
| kpi_forecaster (POC-02) | — | ⬜ MVP | 광고 |
| roas_root_cause_analyzer (POC-03) | — | ⬜ MVP | 광고 |
| creative_fatigue_detector (POC-04) | — | ⬜ MVP | 광고 |
| ab_test_judge (POC-05) | — | ⬜ MVP | 광고 |
| search_surge_detector (POC-08) | — | ⬜ MVP | 검색 |

→ **이미지 명세 9 Tool 모두 도메인 명확**. 단일 analysis_agent 에 묶이는 게 자연스러운지 결정 필요.

### 도메인 분류

```
광고 성과 분석 (5):
  kpi_anomaly_detector / kpi_forecaster / roas_root_cause_analyzer /
  creative_fatigue_detector / ab_test_judge
  → 입력: normalized_ads (daily_performance)

검색 분석 (1):
  search_surge_detector
  → 입력: DataLab 검색량 (별도 collector 필요)

리뷰 분석 (3):
  sentiment_analyzer / keyword_extractor (리뷰 영역) / insight_extractor
  → 입력: cleaned_texts (text_preprocessor 출력)
```

→ 9 Tool 이 명확히 3 도메인. **단일 analysis_agent 안에서 책임 모호 가능성**.

### ADR-014 v2 패턴과의 정합 의문

ADR-014 v2 = "Tool 단일 책임 분리" (도메인별). format_normalizer + review_normalizer 분리 사례.

→ analysis 영역에도 같은 패턴 적용? 즉 **agent 단도 분리?**

### 의도 vs 현실의 괴리

**의도** (ADR-016 = 10 에이전트):
> "analysis_agent = 9 분석 모듈 (POC-01~09) 통합"

**현실**:
- 9 Tool 의 도메인이 명확히 분리 (광고 / 검색 / 리뷰)
- Planner LLM 이 task 별 적절한 Tool 선택 부담 (도메인 enum 학습 필요)
- 사용자 시나리오 1 의 갭 = 광고 분석 Tool 자체가 없어서 발생

## Decision (옵션 — 사용자 결정 보류)

### 옵션 (a) — 단일 analysis_agent 유지 (현재 ADR-016)

- 방법: 9 Tool 모두 analysis_agent 안. Tool 별 도메인 자율 (Tool 이름 + description 으로 식별).
- 장점:
  - ADR-016 정정 불필요
  - Tool 추가 시 등록 단순
  - Planner stage2 의 agent 선택 단일
- 단점:
  - 9 Tool 의 책임 모호 (단일 책임 위반 가능성)
  - Planner stage3 LLM 이 도메인별 Tool 선택 부담
  - 다도메인 agent = ADR-014 v2 (Tool 단일 책임) 패턴과 모순

### 옵션 (b) — 도메인별 agent 분리 (3 agent)

- 방법: `ads_analysis_agent` + `review_analysis_agent` + `search_analysis_agent` 3 agent 분리.
- 장점:
  - ADR-014 v2 (Tool 단일 책임) + ADR-016 (D9 preprocessing 2 분리) 패턴 일관
  - 단일 책임 명확 (agent 단위로 도메인)
  - Planner stage2 가 task 도메인 → agent 1:1 매핑 자연스러움
- 단점:
  - team_catalog 의 agent 카운트 10 → 12 (search 까지) 증가
  - ADR-016 정정 필요 (10 에이전트 → 12)
  - 사용자 명세 이미지 (단일 analysis 영역) 와 모순

### 옵션 (c) — Tool 명에 도메인 prefix (단일 agent + 직관적 이름)

- 방법: 단일 analysis_agent + Tool 이름에 prefix (예: `ads_kpi_anomaly_detector`, `review_sentiment_analyzer`, `search_surge_detector`).
- 장점:
  - agent 카운트 유지
  - Tool 이름만으로 도메인 식별 가능
  - LLM 의 도메인 추론 부담 ↓
- 단점:
  - Tool 이름 verbose
  - 기존 sentiment_analyzer / keyword_extractor 의 rename 비용 (Tool 카드 + test + LLM Prompts 동기)
  - "ads_" prefix 가 모든 Tool 에 의미 있는지 (예: insight_extractor = 둘 다)

### 옵션 (d) — Tool 단 분리 (sentiment 의 ads/review 분리 등)

- 방법: 일부 Tool 을 도메인별로 분리. 예: `ads_kpi_anomaly_detector` + `review_keyword_extractor` 등 명시적 매핑.
- 장점: 책임 매우 명확.
- 단점: Tool 카운트 폭발 (9 → 12+). 관리 부담.
- **기각**: 과한 분리.

### 옵션 비교 매트릭스

| 옵션 | agent 카운트 | Tool 카운트 | ADR-014 일관 | LLM 부담 | POC 적합 |
|---|---|---|---|---|---|
| (a) 단일 agent | 10 (변경 X) | 9 | ❌ 모순 | 높 | ⭐⭐⭐ |
| **(b) 도메인 분리 3 agent** | 12 | 9 | ⭐⭐⭐ 일관 | 낮 | ⭐⭐ |
| (c) Tool 명 prefix | 10 | 9 (rename) | △ 중간 | 중 | ⭐⭐ |

→ **사용자 결정 보류** — (a)/(b)/(c) 중 선택.

#### 추천 = (b) 도메인 분리 ⭐

- ADR-014 v2 + ADR-016 (D9) 패턴 일관
- Planner LLM 매핑 자연스러움
- 단일 책임 명확
- agent 카운트 증가는 수용 가능 (D9 의 8→10 사례)

## Consequences

### (b) 채택 시 영향 범위

| 영역 | 변경 |
|---|---|
| `team_catalog.yaml` | analysis_agent 1 → 3 (ads/review/search) |
| `task_agent_hints` | sentiment_analysis → review_analysis_agent / kpi_anomaly → ads_analysis_agent 등 |
| `execution_agent/agents/` | 05_analysis.md → 05_ads_analysis.md + 06_review_analysis.md + 07_search_analysis.md |
| `00_overview.md` | 10 에이전트 → 12 에이전트 |
| LLM Prompts (stage2/3) | agent enum 확장 + 도메인 매핑 명시 |
| ADR-016 | 정정 (10 → 12 에이전트) |
| Tool 카드 | 분류 명확화 |
| 신규 Tool 6 (POC-01~05, 08) | ads_analysis_agent / search_analysis_agent 에 등록 |

### 긍정 (+)

- 책임 명확 + Planner LLM 자연스러움
- 패턴 일관성 (ADR-014 v2 + ADR-016)
- 향후 Tool 추가 시 소속 agent 결정 단순

### 부정 (−)

- ADR-016 정정 + team_catalog 재구성 비용
- 사용자 명세 이미지 (단일 analysis 영역) 와 모순 — 사용자 의도 재확인 필요
- agent 카운트 12 — POC 단계 과한 분리 가능성

## Alternatives Considered

이미 §Decision 의 (a)/(b)/(c)/(d) 4 옵션.

## Related

- ADR-014 v2 (Tool 단일 책임 분리) — 본 ADR 의 패턴 source
- ADR-016 (10 에이전트 구조) — 본 ADR 채택 시 정정 필요
- ADR-018 (channel_normalizing 의미) — 본 카테고리 1 재설계 동시
- ADR-019 (summary_generator 책임) — 본 카테고리 1 재설계 동시
- P1 fix plan: docs/_claude/tool/TOBE_MVP/06 (gitignored)
- 사용자 채팅 시나리오 1 발견 (2026-05-19 22:25): "분석 결과 비어 있음" UX 메시지

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-19 | Proposed — 카테고리 1 재설계 Phase 1 박제. (a)/(b)/(c) 옵션 매트릭스. 사용자 결정 보류. |
