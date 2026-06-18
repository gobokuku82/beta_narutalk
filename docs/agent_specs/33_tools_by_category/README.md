# 33. Tools by Category — 카테고리별 tool 인벤토리

> 32 §2.5 의 **카테고리 8 정의** (7 본 + 1 보조 report) 가 잣대. 본 폴더 = **카테고리별 tool 인벤토리** (자주 변경).

## 폴더 원칙

| 분리 | 이유 |
|---|---|
| **32 = 카테고리 정의·잣대** | 변경 빈도 낮음 (북극성) |
| **33/* = tool 인벤토리** | 변경 빈도 높음 (신규/이동/폐기) — 32 안 건드림 |

## 7 + 1(보조) 카테고리 진입

| 카테고리 | 문서 | 의도 (32 §2.5 요약) | tool 수 |
|---|---|---|---:|
| collection | [33_collection.md](33_collection.md) | raw 데이터 가져오기 | 27 |
| normalization | [33_normalization.md](33_normalization.md) | 컬럼·형식·단위·시간대 표준화 | 6 |
| cleaning | [33_cleaning.md](33_cleaning.md) | 결측·이상치·필터·검증·보정 | 3 |
| preprocessing | [33_preprocessing.md](33_preprocessing.md) | 자연어 텍스트 전처리 | 1 |
| metrics | [33_metrics.md](33_metrics.md) | 순수 계산 | 35 |
| comparison | [33_comparison.md](33_comparison.md) | 두 metrics 조합·비교 | 7 |
| analysis | [33_analysis.md](33_analysis.md) | LLM·ML·통계 추론 | 9 |
| report (보조) | [33_report.md](33_report.md) | 보고서 텍스트 산출 (LLM) | 2 |

## 각 33_*.md 표준 구조

```
1. header (카테고리·의도·짝)
2. tool 목록 표 (name · input · output · status · 의도)
3. sub-folder (있으면) — 예: metrics/marketing, analysis/llm
4. anti-pattern 노트 (해당 카테고리에서 자주 보는 잘못된 패턴)
```

## 상태 표기

| status | 의미 |
|---|---|
| complete | 구현 완료, 회귀 테스트 통과 |
| partial | 일부 기능만 (제약 docstring 명시) |
| planned | yaml/계약만 박제, 코드 미구현 |
| deprecated | 폐기 예정 (대체 tool 명시) |
| split-pending | 끼워맞춤 진단, 분리 대기 (anti-pattern 참조) |
