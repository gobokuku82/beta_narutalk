# ADR-019: summary_generator 의 책임 영역 — review 전용 vs 다도메인

## Status

**Proposed** (2026-05-19) — 카테고리 1 재설계 Phase 1 박제. 사용자 결정 후 Accepted 갱신.

후속 이력:
- (예정) Accepted — 사용자 결정 + summary_generator 정합 sprint 완료 시.

**Amended** (2026-05-31, 작업 ⑩ 후속) — path 갱신:
- 작업 ③ commit `906f4a3` 에서 `tools/shared/summary_generator.py` → `tools/report/summary_generator.py` 이동 (report 보조 카테고리로 승격)
- 본문 line 27 `tools/shared/summary_generator.py:49-60` 박제 = 결정 시점 (2026-05-19) 이력 보존, 실 위치 = `tools/report/summary_generator.py`

**Amended** (2026-06-01, 작업 ⑫ 후속) — broken 5 ads collector 폐기 박제:
- 본문 line 54 의 `meta_collector → format_normalizer → summary_generator` chain 인용 = 결정 박제 시점 (2026-05-19) 이력 보존
- 실 상태: broken 5 폐기됨 (⑫.A). 신 ads chain (external/meta_ads_performance_collector → ...) 재구성 시 광고 chain summary 시나리오 재검토 권장.

## Context

### 발견 — 사용자 P1 sprint 후 채팅 재테스트 (2026-05-19)

**시나리오 1 ("2024년 10월 메타 광고 성과 보여줘")**:
```
2026-05-19 22:25:11 summary_generator completed    length=24
status=completed
```

채팅 응답:
> "분석 결과가 비어 있어 요약을 제공할 수 없습니다"

→ Tool 자체는 "정상 완료" (length=24 길이의 응답 반환). 하지만 사용자에게는 빈 결과.

### 원인 추적

`tools/shared/summary_generator.py:49-60`:

```python
@staticmethod
def _collect_payload(previous: dict) -> dict:
    """이전 결과 중 요약에 쓸만한 키만 추림."""
    keep = ["sentiment_distribution", "top_keywords", "insights", "report_text"]
    out: dict = {}
    for result in previous.values():
        data = result.get("data") if isinstance(result, dict) else None
        src = data if isinstance(data, dict) else (result if isinstance(result, dict) else {})
        for k in keep:
            if k in src and k not in out:
                out[k] = src[k]
    return out
```

→ `keep` 리스트가 **review 분석 결과 위주**:
- `sentiment_distribution` (review 감성 분석)
- `top_keywords` (review 키워드)
- `insights` (review/광고 인사이트 모두)
- `report_text` (보고서 텍스트)

→ **광고 chain 의 `normalized_ads` 인식 못함**. 시나리오 1 의 chain (meta_collector → format_normalizer → summary_generator) 에서 summary 가 받을 데이터 = `normalized_ads` 만. 리스트에 없음. → 빈 payload → LLM 이 "분석 결과 비어있다" 메시지 생성.

### summary_generator 의 책임 영역 모호

| 의도 (catalog yaml) | 현재 구현 |
|---|---|
| "분석 결과를 한 문장(요약)으로 압축 (LLM)" | review 분석 결과만 인식 |

→ **광고 성과 요약 = 별도 Tool? 단일 Tool 의 확장? cross-cutting?**

### ADR-014 v2 패턴과의 충돌

ADR-014 v2 = "Tool 단일 책임 분리 (도메인별)". format_normalizer + review_normalizer 분리 사례.

→ summary_generator 도 도메인별 분리?
- `ads_summary_generator` (광고 성과 요약)
- `review_summary_generator` (리뷰 요약)
- `report_summary_generator` (보고서 요약)

→ but **summary 는 본래 cross-cutting Tool** (어떤 분석이든 요약 가능). 도메인별 분리 시 카운트 증가 + 책임 분산.

### 이미지 명세 (MVP) 의 단서

이미지 명세의 report_text 영역:
- report_writer — 리포트 본문 작성 (markdown)
- summary_generator — KPI 요약·핵심 인사이트 생성

→ summary_generator 의 본래 책임 = **"KPI / 인사이트 요약"** (도메인 무관). 즉 cross-cutting Tool 의도.

### 의도 vs 현실의 괴리

**의도**:
> summary_generator = 모든 분석 결과의 한 문장 요약 (도메인 무관 cross-cutting)

**현실**:
> review 분석 결과만 인식 (keep 리스트 한정). 광고 성과 미지원.

## Decision (옵션 — 사용자 결정 보류)

### 옵션 (2a) — keep 리스트 확장 (단순 fix)

- 방법: `keep` 리스트에 `normalized_ads / normalized_reviews / channel_counts` 등 추가.
- 장점:
  - 코드 변경 최소 (1 line)
  - cross-cutting Tool 의도 유지
  - 향후 도메인 추가 시 키만 추가
- 단점:
  - keep 리스트 유지보수 부담 (Tool 추가 시마다 갱신)
  - silent failure 위험 (새 도메인 키 추가 안 하면 누락)
  - LLM 이 raw 데이터 요약하기 부담 (분석 결과가 아닌 raw payload)
- **추천도**: ⭐⭐⭐ (POC 단계)

### 옵션 (2b) — summary_generator 도메인별 분리

- 방법: `ads_summary_generator` + `review_summary_generator` 2 Tool.
- 장점:
  - ADR-014 v2 (Tool 단일 책임) 패턴 일관
  - 각 도메인 LLM prompt 최적화 가능 (광고는 KPI/ROAS 강조, 리뷰는 감성/키워드 강조)
- 단점:
  - Tool 카운트 1 → 2 (또는 3 with trend)
  - shared/ 카테고리 의 의의 약화
  - Planner LLM 의 Tool 선택 부담
- **추천도**: ⭐⭐

### 옵션 (2c) — summary_generator = 메타 Tool (호출자 명시 domain)

- 방법: `params.domain` 매개변수 추가. 호출자 (Planner) 가 명시.
- 장점:
  - 단일 Tool 유지
  - 도메인별 prompt 분기 가능
- 단점:
  - ADR-014 v1 의 패턴 (자동 식별 vs 명시) 회귀
  - Planner LLM 학습 부담 (도메인 enum 학습 필요)
  - silent failure 위험 (domain 매개변수 누락 시)
- **추천도**: ⭐

### 옵션 (2d) — summary_generator 가 자동 도메인 식별 (ADR-014 v1 패턴)

- 방법: `_collect_payload` 가 previous_results 의 키 보고 자동 분기.
- 장점:
  - 호출자 부담 0
  - 단일 Tool 유지
- 단점:
  - ADR-014 v2 "Tool 단일 책임 분리" 패턴과 모순 (v1 으로 회귀)
  - 자동 식별 오판 위험
- **추천도**: ⭐ (ADR-014 진화 자취와 모순)

### 옵션 (2e) — chain 재설계 (analysis Tool 강제 + summary 는 분석 결과만)

- 방법: summary_generator 는 분석 결과만 (현 그대로). 광고 chain 에 광고 분석 Tool (kpi_anomaly 등) 강제 추가 → 분석 결과 생성 → summary 가 받음.
- 장점:
  - summary_generator 책임 변경 X
  - ADR-017 (analysis 도메인 분리) 결정과 통합 (광고 분석 Tool 5 신규 권장)
  - architectural 일관성
- 단점:
  - 광고 chain 의 todos 수 증가 (collection + normalize + 분석 1+ + summary)
  - Cognitive 가 task=summary_generation 만 추출했어도 분석 task 추가 필요 (implicit_prerequisites 갱신)
- **추천도**: ⭐⭐⭐ (architectural 정합)

### 옵션 비교 매트릭스

| 옵션 | 작업 분량 | ADR 일관성 | POC 적합 | 향후 확장 |
|---|---|---|---|---|
| **(2a) keep 확장** | 낮 | 중 | ⭐⭐⭐ | △ 유지보수 |
| (2b) 도메인별 분리 | 큼 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| (2c) 메타 Tool (명시 domain) | 중 | ❌ (v1 회귀) | ⭐ | △ |
| (2d) 자동 식별 (v1 회귀) | 중 | ❌ (v2 모순) | ⭐ | ❌ |
| **(2e) chain 재설계** | 중 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

→ **추천 = (2a) + (2e) 하이브리드**:
- (2e): 광고 chain 에 광고 분석 Tool 추가 (ADR-017 결정 의존)
- (2a): summary_generator 의 keep 리스트는 확장 가능 (safety net)
- 우선 (2e) 채택 + (2a) 보조 = 본질적 fix + 안전망

## Consequences

### (2e) + (2a) 채택 시 영향 범위

| 영역 | 변경 |
|---|---|
| `summary_generator.py` keep 리스트 | `normalized_ads / normalized_reviews / channel_counts` 추가 (안전망) |
| 광고 분석 Tool 6 신규 | ADR-017 결정 의존 (POC-01~05, 08) |
| `team_catalog.yaml` task_agent_hints | `summary_generation` 트리거 시 분석 task 자동 후행 (implicit_prerequisites) |
| LLM Prompts (stage3) | 광고 chain 에 분석 Tool 강제 명시 |
| 광고 chain 의 표준 패턴 | collection → normalize → kpi_anomaly (또는 다른 분석) → summary |
| 사용자 채팅 시나리오 1 재테스트 | "광고 성과 요약" → 분석 Tool 호출 후 자연스러운 요약 |

### 긍정 (+)

- summary_generator 의 cross-cutting Tool 의도 유지
- ADR-014 v2 패턴 일관 (summary 는 분석 결과 요약 책임)
- 광고 chain 자연스러움 (분석 없이 요약 X = 본질적 패턴)
- 안전망 (keep 확장) 으로 silent failure 회피

### 부정 (−)

- ADR-017 결정 의존 (광고 분석 Tool 6 신규 sprint 필요)
- 광고 chain todos 수 증가
- summary_generator 의 LLM prompt 도 광고/리뷰 별 최적화 가능 (별도 sprint)

## Alternatives Considered

이미 §Decision 의 (2a)/(2b)/(2c)/(2d)/(2e) 5 옵션.

## Related

- **ADR-014 v2** — Tool 단일 책임 분리 (cross-cutting Tool 의 패턴 의문)
- **ADR-016** — 10 에이전트 구조 (summary_generator 의 shared/ 카테고리 의도)
- **ADR-017** (예정) — analysis agent 도메인 분리 (광고 분석 Tool 6 신규)
- **ADR-018** (예정) — channel_normalizing 의미 (같은 sprint)
- 사용자 채팅 시나리오 1 발견 (2026-05-19 22:25) — "분석 결과 비어 있음" UX 메시지
- summary_generator.py: 본 ADR 변경 대상 (keep 리스트)

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-19 | Proposed — 카테고리 1 재설계 Phase 1 박제. (2a)~(2e) 옵션 매트릭스. 사용자 결정 보류. 추천 = (2a) + (2e) 하이브리드. |
