# ADR-018: channel_normalizing_agent 의 의미 영역 — 광고 채널 vs 데이터 채널

## Status

**Proposed** (2026-05-19) — 카테고리 1 재설계 Phase 1 박제. 사용자 결정 후 Accepted 갱신.

후속 이력:
- (예정) Accepted — 사용자 결정 + Planner LLM Prompts 정합 검증 통과 시.

## Context

### 발견 — 사용자 P1 sprint 후 채팅 재테스트 (2026-05-19)

**시나리오 2 ("블루밍글로우 리뷰 분석해줘")**:
```
planning stage2: agents=['collection_agent', 'text_preprocessing_agent', 'analysis_agent', 'report_text_agent']
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                            ❌ channel_normalizing_agent 안 선택
ERROR: Tool 'review_normalizer' under agent 'text_preprocessing_agent' neither implemented nor stub
EXECUTION_ALL_FAILED
```

**원인**: review_normalizer 는 우리 team_catalog 에 channel_normalizing_agent 소속 (P1.4 박제). 하지만 **Planner LLM 이 text_preprocessing_agent 로 추론**.

### LLM 입장의 자연스러운 추론

```
"review_normalizer" → 리뷰 처리 → 텍스트 영역 → text_preprocessing_agent
                                              (LLM 의 직관)

vs

우리 team_catalog 박제 → channel_normalizing_agent
                       (D9 의 "channel" = "데이터 채널" 해석)
```

→ **agent 이름 "channel_normalizing" 의 의미가 LLM 에게 모호**.

### D9 의 원래 의미 재검토

**D9 결정 (2026-05-18)**:
> "전처리 2 분리" = preprocessing 1 agent → text_preprocessing + channel_normalizing 2 agent

**비전 narrative 의 의도**:
- text_preprocessing = 언어 자원 측면 (HTML/URL/공백 정제)
- channel_normalizing = 마케팅 도메인 측면 (4 채널 광고성과 통합)

→ **channel_normalizing 의 본래 의미 = 광고 채널 정규화**. review 정규화는 본래 영역 외.

### P1 sprint 의 결정 자취

P1 sprint 의 §2.9 C1:
> review_normalizer 소속 agent: (a) channel_normalizing_agent 채택 (이름의 "channel" = "데이터 채널" 해석)

→ 본 결정이 **LLM 직관과 불일치**. 시나리오 2 실패의 원인.

### 의도 vs 현실의 괴리

**의도**:
> "channel_normalizing_agent = 모든 데이터 채널 정규화 (광고 + 리뷰 + 트렌드 등 통합)"

**현실**:
> LLM 이 "channel = 광고 채널" 으로 자연스럽게 해석. "리뷰는 텍스트 영역" 으로 매핑.

## Decision (옵션 — 사용자 결정 보류)

### 옵션 (1a) — channel_normalizing → data_normalizing rename

- 방법: agent 이름 변경. 의미 일반화 (channel → data).
- 장점:
  - "data_normalizing" 의미 명확 (모든 데이터 정규화)
  - review_normalizer 소속 자연스러움
  - 향후 trend/external 정규화 Tool 추가 시 자연스러움
- 단점:
  - team_catalog 정정
  - ADR-016 정정 (D9 의 agent 이름 변경)
  - 비전 narrative 문서 갱신
- **추천도**: ⭐⭐⭐ (단순 + 의미 명확)

### 옵션 (1b) — review_normalizer 를 text_preprocessing_agent 로 이동

- 방법: agent 이름 그대로. review_normalizer 의 소속만 이동.
- 장점:
  - LLM 직관 정합 (review = text 영역)
  - agent 이름 변경 X
- 단점:
  - text_preprocessing_agent 의 책임 확장 (정제 + 정규화 = 2 책임)
  - D9 의 책임 분리 (정제 vs 정규화) 약화
  - format_normalizer (광고) 와 review_normalizer (리뷰) 가 다른 agent — 정규화의 통합 책임 분리
- **추천도**: ⭐⭐

### 옵션 (1c) — channel_normalizing 분리 (ads_normalizing + review_normalizing)

- 방법: agent 2 분리 — ads_normalizing_agent (format_normalizer) + review_normalizing_agent (review_normalizer).
- 장점:
  - ADR-014 v2 (Tool 단일 책임) + ADR-017 (analysis 도메인 분리) 패턴 일관
  - 의미 매우 명확
- 단점:
  - agent 카운트 10 → 11 (또는 ADR-017 채택 시 13+)
  - 각 agent 안에 Tool 1개씩 = 과한 분리
- **추천도**: ⭐

### 옵션 (1d) — agent 이름 + prompt 룰 박제 강화

- 방법: channel_normalizing_agent 이름 유지. LLM Prompts (stage2/3) 에 명시 룰 박제.
- 장점:
  - 코드 변경 최소
  - 비전 narrative 유지
- 단점:
  - LLM 환각으로 명시 룰 무시 가능
  - "channel" 의 직관적 의미 변경 안 됨
- **추천도**: ⭐ (마지막 수단)

### 옵션 비교 매트릭스

| 옵션 | 작업 분량 | LLM 직관 | 일관성 (ADR-014/016) | POC 적합 |
|---|---|---|---|---|
| **(1a) data_normalizing rename** | 중 | ⭐⭐⭐ | 중 | ⭐⭐⭐ |
| (1b) review → text_preprocessing | 낮 | ⭐⭐⭐ | ❌ 모순 (정제 + 정규화 혼재) | ⭐⭐ |
| (1c) channel → 분리 (ads + review) | 큼 | ⭐⭐ | ⭐⭐⭐ | ⭐ |
| (1d) prompt 룰 박제 | 낮 | ❌ | ❌ | ⭐ |

→ **추천 = (1a) data_normalizing rename**. 단순 + 의미 명확 + LLM 직관 정합.

## Consequences

### (1a) 채택 시 영향 범위

| 영역 | 변경 |
|---|---|
| `team_catalog.yaml` | `channel_normalizing_agent` → `data_normalizing_agent` rename |
| `task_agent_hints` | `data_preprocessing: [text_preprocessing_agent, channel_normalizing_agent]` → `[text_preprocessing_agent, data_normalizing_agent]` |
| `execution_agent/agents/04_channel_normalizing.md` | `04_data_normalizing.md` rename (또는 내부 갱신) |
| `00_overview.md` | 표 갱신 |
| LLM Prompts (stage2/3) | agent enum 정정 |
| ADR-016 | 정정 (channel_normalizing → data_normalizing) |
| `format_normalizer.md` + `review_normalizer.md` 카드 | 소속 agent 갱신 |
| 향후 Tool 추가 시 | 정규화 책임 영역 명확 |

### 긍정 (+)

- LLM 직관 정합 → Planner stage2/3 자연스러움
- review_normalizer 의 소속 모호 해결
- 향후 trend/external 정규화 Tool 추가 자연스러움

### 부정 (−)

- agent rename 작업 (코드 + docs + Prompts)
- 비전 narrative 문서 갱신
- D9 의 명명 자취 (channel → data) 변경

## Alternatives Considered

이미 §Decision 의 (1a)/(1b)/(1c)/(1d) 4 옵션.

## Related

- **ADR-014 v2** — Tool 단일 책임 분리 (P1 의 review_normalizer 분리 결과)
- **ADR-016** — 10 에이전트 구조 (channel_normalizing 명명 박제)
- **ADR-017** (예정) — analysis agent 도메인 분리 (같은 sprint)
- **ADR-019** (예정) — summary_generator 책임 (같은 sprint)
- 사용자 채팅 시나리오 2 발견 (2026-05-19 22:26) — EXECUTION_ALL_FAILED 원인
- P1 fix plan: docs/_claude/tool/TOBE_MVP/06 §2.9 C1 (gitignored)

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-19 | Proposed — 카테고리 1 재설계 Phase 1 박제. (1a)/(1b)/(1c)/(1d) 옵션 매트릭스. 사용자 결정 보류. 추천 = (1a) data_normalizing rename. |
