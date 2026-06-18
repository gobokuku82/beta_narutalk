# 실행 에이전트 및 기능 목록

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - AI 에이전트 |
| 진행상태 | 작업중 |
| 버전 | **v0.6** |
| 최종 수정일 | 2026-04-19 |
| 이전 버전 | v0.5 (2026-04-09) |

> v0.5 변경 사항:
> - **report_agent 역할 재정의**: 기존 "분석 종합 + 보고서 + PDF"에서 "분석 결과 종합 + LLM 스토리 구성"으로 축소
> - **pdf_agent 신설**: PDF 렌더링 전담 (report_agent에서 분리)
> - **preprocessing_agent**: 텍스트 클렌징 8단계 파이프라인 명시 + 누락 Tool 5개 추가
> - **analysis_agent**: POC 분석 시나리오 8개(POC-01~08) 명시 + LLM 사용 원칙 추가. 내부는 다양한 Tool(ML/LLM/인과분석/분석프레임워크) 조합으로 점진 확장
> - **video_creation_agent**: POC 범위 "스토리보드까지" 명시 (영상 제작은 3차)
> - 모든 agent에 POC/2차/3차 범위 표 추가
>
> 총 Agent: **7개** (collection / preprocessing / analysis / report / pdf / image_creation / video_creation) + 공유 Tool.
> 현재는 모두 "Tool 팀" 성격(라우팅 단위)이며, 의사결정 로직은 Phase 5 이후 재평가.

---

## 1. 전체 구조

```
Execution Layer (Orchestrator)
  │
  ├── collection_agent          ← 채널별 데이터/성과 지표 수집, 요서 파싱
  │     └── Tool 7개  (수집 4 + 성과수집 2 + 요서파싱 1)
  │
  ├── preprocessing_agent       ← 데이터 정규화 + 텍스트 클렌징 8단계
  │     └── Tool 10개 (데이터 전처리 5 + 텍스트 클렌징 5)
  │
  ├── analysis_agent            ← ML/LLM/인과분석/분석프레임워크 조합
  │     └── Tool 14개+ (ML 7 + LLM 7) — 점진 확장 예정
  │     └── POC 시나리오: POC-01~08 (8개)
  │
  ├── report_agent              ← 분석 결과 종합 + LLM 스토리 구성
  │     └── Tool 4개
  │     └── POC 시나리오: POC-09 (AI 리포트 스토리)
  │
  ├── pdf_agent                 ← PDF 렌더링 (신설)
  │     └── Tool 3개
  │
  ├── image_creation_agent      ← 단독 광고 이미지 + 슬로건
  │     └── Tool 10개
  │
  ├── video_creation_agent      ← 스토리보드 (POC) → 영상 제작 (3차)
  │     └── Tool 7개
  │
  └── 공유 Tool                 ← 여러 Agent가 사용
        └── Tool 5개
```

---

## 2. Agent별 기능 매핑

> v0.5부터 다음 변경:
> - `data_analysis_agent` → `collection_agent` / `preprocessing_agent` / `analysis_agent` 3개로 분리 (v0.4)
> - `report_agent`에서 PDF 렌더링을 분리하여 `pdf_agent` 신설 (v0.5)
> - `report_agent`는 "분석 결과 종합 + LLM 스토리 구성"으로 역할 축소
>
> 현재는 모두 "Tool 팀" 성격(라우팅 단위). Planning이 채널/도구를 결정하고, 각 agent는 라우팅된 Tool을 실행한다.
> 향후 의사결정 로직 도입 시 각 agent의 판단 영역이 독립화될 예정.

### Agent 1: `collection_agent` (수집)

**역할**: 외부 채널과 광고 플랫폼에서 데이터/성과 지표를 수집하고, 클라이언트 요서(Brief)를 파싱한다.

**단계별 범위:**

| 단계 | 범위 |
|------|------|
| **1차 (POC)** | mock 데이터 파일 로드 (블루밍글로우 4채널 RAW) |
| **2차 (MVP)** | 4개 매체 API 실시간 수집 (네이버 SA / 메타 / 카카오 / 구글), 매일 02:00 자동 + 재시도 3회 |
| **3차 (자동화)** | 외부 트렌드 소스(DataLab/유튜브/올리브영) + 요서 파싱 자동화 |

**향후 판단할 것 (현재는 Planning이 결정):**
- 어느 채널에서 뭘 수집할지 (수집 전략)
- 요서에서 어떤 정보를 추출할지

**포함하는 기능:**

| 기능 | 분류 | 왜 Tool인가 |
|------|------|------------|
| ① 데이터 수집 | Tool (여러 개) | 채널+키워드 정해지면 수집만 |
| ② 성과 지표 수집 | Tool (여러 개) | 채널+기간 정해지면 API 호출만 |
| 요서 파싱 (신규) | Subgraph | 문서 포맷 판별 → 파싱 → 구조화. 복합 단계 |

**Tool 목록:**

| Tool | 유형 | 그룹 | 설명 |
|------|------|------|------|
| `naver_collector` | tool/subgraph | 수집 | 네이버 블로그/카페/쇼핑 리뷰 수집 |
| `youtube_collector` | tool/subgraph | 수집 | 유튜브 댓글/자막 수집 |
| `tiktok_collector` | tool/subgraph | 수집 | 틱톡 댓글/해시태그 수집 |
| `oliveyoung_collector` | tool/subgraph | 수집 | 글로벌 올리브영 리뷰 수집 |
| `naver_ads_collector` | tool/subgraph | 성과수집 | 네이버 광고 성과 데이터 수집 |
| `meta_ads_collector` | tool/subgraph | 성과수집 | 메타 광고 성과 데이터 수집 |
| `brief_parser` | subgraph | 요서 (신규) | 요서 문서 파싱 (PDF/DOCX/PPTX → 구조화 JSON) |

---

### Agent 2: `preprocessing_agent` (전처리)

**역할**: 두 가지 전처리를 담당한다.
1. **데이터 전처리**: 4개 채널의 서로 다른 형식을 통일된 스키마로 변환 + KPI 자동 계산
2. **텍스트 전처리(클렌징)**: 리뷰/댓글 등 raw 텍스트를 ML 분석 전 정제

> 클렌징 적용 시 감성 분석 정확도 평균 **15~25% 향상**.

**단계별 범위:**

| 단계 | 범위 |
|------|------|
| **1차 (POC)** | 배치(일 1회) — 클렌징 1~8단계 + 데이터 정규화 + KPI 계산 |
| **2차 (MVP)** | 실시간(1~7단계) + 배치(8단계 맞춤법) 병행 |
| **3차** | 멀티 언어 지원 (en/ja 등) |

**향후 판단할 것 (현재는 Planning이 결정):**
- 어떤 전처리 단계를 적용할지 (사용자 커스텀 해석 포함)
- 채널별 포맷 차이를 어떻게 통일할지
- 협찬 콘텐츠를 어떻게 처리할지 (제외 vs 가중치 0.3배)

#### 2-1. 데이터 전처리

**기능 요약:**
- **컬럼명 정규화**: 4채널(네이버 SA / 메타 / 카카오 / 구글)의 서로 다른 컬럼을 통일 스키마로 매핑
- **KPI 자동 계산**: CTR, CVR, CPC, CPA, ROAS (분모 0이면 NULL)
- **소재 집행 이력 테이블 생성**: `ad_creative_history` (creative_id, campaign_id, channel, status, daily_budget, ab_test_group 등)

> 컬럼 매핑 표 + KPI 공식 + 테이블 스키마는 `30_DATA_MODELS_v1.1.md` 담당자 영역.

#### 2-2. 텍스트 클렌징 8단계 파이프라인

| 단계 | 처리 | 비고 |
|------|------|------|
| 1 | 이모지 처리 | 제거 또는 의미 변환 (`emoji.demojize`) — POC: 변환 권장 |
| 2 | 반복 문자 정규화 | "ㅋㅋㅋㅋ" → "ㅋㅋ" (3회 이상 → 2회) |
| 3 | HTML 태그 & URL 제거 | BeautifulSoup + re |
| 4 | 협찬 감지 & 플래그 | "협찬/제공받/PR/유료광고" 키워드 → `is_sponsored=True` 플래그 |
| 5 | 길이 필터 | < 5자 제거, > 500자 절단 (KoBERT 토큰 제한) |
| 6 | 중복 제거 | md5 해시 기반 |
| 7 | 언어 감지 | `langdetect` — POC: 한국어(ko)만 통과 |
| 8 | 맞춤법 정규화 | py-hanspell — 느림 → **배치만**, 실시간 제외 |

**주의사항:**
1. **과도한 클렌징 금지** — 의미에 영향 주는 수정 최소화
2. **신조어/슬랭 보존** — "레전드/갓벽/찐이에요" 등 강한 긍정 표현 단순 제거 금지
3. **협찬 처리 정책** — POC: 별도 집계, 가중치는 분석 단계에서 결정
4. **개인정보 마스킹** — `010-XXXX-XXXX` 자동 처리

**출력 테이블**: `cleaned_text` (`text_id`, `source`, `original_text`, `cleaned_text`, `is_sponsored`, `language`, `is_valid`, `cleaned_at`)
→ analysis_agent의 감성 분석 입력으로 사용

**Tool 목록:**

| Tool | 유형 | 그룹 | 설명 |
|------|------|------|------|
| `text_preprocessor` | tool | 텍스트 클렌징 | 불용어/이모지/특수표현 통합 처리 |
| `emoji_handler` | tool | 텍스트 클렌징 | 이모지 보존/제거/변환 (1단계) |
| `repeat_char_normalizer` | tool | 텍스트 클렌징 | 반복 문자 정규화 (2단계) **신규** |
| `html_url_stripper` | tool | 텍스트 클렌징 | HTML 태그 & URL 제거 (3단계) **신규** |
| `sponsored_detector` | tool | 텍스트 클렌징 | 협찬 감지 & 플래그 (4단계) **신규** |
| `length_filter` | tool | 텍스트 클렌징 | 최소/최대 길이 필터 (5단계) **신규** |
| `duplicate_detector` | tool | 텍스트 클렌징 | md5 해시 기반 중복 제거 (6단계) **신규** |
| `language_detector` | tool | 텍스트 클렌징 | langdetect 기반 언어 감지 (7단계) **신규** |
| `spell_normalizer` | tool | 텍스트 클렌징 | 맞춤법 정규화 (8단계, 배치 전용) **신규** |
| `format_normalizer` | tool | 데이터 전처리 | 채널별 컬럼명/포맷 통일 |
| `kpi_format_parser` | tool | 데이터 전처리 | 성과 지표 채널별 포맷 파싱 |
| `kpi_calculator` | tool | 데이터 전처리 | CTR/CVR/CPC/CPA/ROAS 자동 계산 **신규** |
| `text_tokenizer` | tool | 데이터 전처리 | 토큰화, 정규화 |
| `pii_masker` | tool | 데이터 전처리 | 개인정보 마스킹 (전화번호 등) **신규** |

---

### Agent 3: `analysis_agent` (분석)

**역할**: 전처리된 데이터에 다양한 분석 기법을 적용하여 인사이트와 트렌드를 추출한다.

**구현 철학:**
- 다양한 분석 Tool(ML / LLM / 인과분석 / 분석 프레임워크)을 만들고, **각각을 조합**하는 방식
- **점진적 확장**: 일부 기능을 확정 짓고 점점 확대 → 최종적으로 시나리오 단위 조합 가능
- 추후 사람이 분석에 개입하여 **맞춤형 가이드**를 만들 수 있도록 설계 (앱 정체성)

**단계별 범위:**

| 단계 | 범위 |
|------|------|
| **1차 (POC)** | POC-01~08 8개 시나리오, mock 데이터 기반, 핵심 Tool로 시연 |
| **2차 (MVP)** | 실데이터 + ML 정확도 향상, 분석 Tool 카탈로그 확장 |
| **3차** | 사람 개입 맞춤형 분석 가이드, 인과분석 본격 도입, 멀티 시나리오 자동 조합 |

**향후 판단할 것 (현재는 Planning이 결정):**
- 어떤 ML/LLM/인과분석을 조합할지
- KPI 이상치·트렌드를 어떻게 해석할지
- 키워드 최적화 방향을 어떻게 잡을지
- 결과를 어떻게 해석할지

**포함하는 기능:**

| 기능 | 분류 | 왜 Tool인가 |
|------|------|------------|
| ④ ML 분석 | Tool (여러 개) | 모델 지정되면 실행만 |
| ⑤ LLM 분석 | Tool (여러 개) | 분석 방법 지정되면 실행만 |
| KPI 트렌드 분석 (신규) | Tool | 이상치 탐지, 변화점 감지, 상관분석 |
| 키워드 최적화 (신규) | Tool | 키워드 추출 + 외부 API 조회 + 추천 |
| 인과분석 (확장) | Tool/Subgraph | Granger 인과성, DiD, Causal Inference |
| 분석 프레임워크 (확장) | Subgraph | 시나리오 단위 조합 (예: A/B 테스트 전체 흐름) |

#### POC 분석 시나리오 (8개)

> POC 단계에서 mock 데이터로 시연하는 분석 8개. 각 시나리오는 Tool 1개~여러 개의 조합으로 구현.
> POC-09(AI 리포트 스토리)는 `report_agent`로 이동.

| ID | 시나리오 | 트리거 | 주요 로직 | 사용 Tool (예상) | 출력 |
|----|---------|--------|----------|---------------|------|
| **POC-01** | KPI 이상 감지 | 매일 자동 | CPA 전일 대비 +30% 주의 / +100% 긴급. 전환 0 + 클릭 50+ → 픽셀 오류 | `kpi_anomaly_detector` + `kpi_insight_generator` (LLM 1~2줄) | 대시보드 알림 카드 + AI 인사이트 박스 |
| **POC-02** | 소재 피로도 감지 | 매일 자동 | Frequency ≥ 3.5 AND CTR 2주 연속 하락 → 교체권고. 수명 잔여일 = (3.5 − Freq) / 주간 증가속도 × 7 | `frequency_analyzer` + `ctr_trend_analyzer` + `summary_generator` | 소재 카드 상태 뱃지 (유지/주시/교체권고) |
| **POC-03** | A/B 테스트 자동 판정 | 채팅 요청 또는 전환 50건 도달 시 | proportion_ztest → p-value → 신뢰도. 신뢰도 ≥ 95% AND 전환 ≥ 50건 → 판정 | `ab_test_runner` + `summary_generator` | "A 우수 (97%)" 또는 "N일 더 필요" |
| **POC-04** | 무전환 키워드 감지 | 매일 자동 | 클릭 ≥ 100 AND 전환 0 → 무전환. 원인 추정: 검색 의도 불일치 / 랜딩 / 경쟁사 | `keyword_filter` + `cause_estimator` (LLM) | 비용최적화 화면 무전환 목록 + 중지 권고 |
| **POC-05** | AI 품질 채점 | 채팅 요청 또는 소재 신규 등록 | GPT-4o Vision → 5차원 채점 (Sales/Short/Clear/Visual/Benefit, 각 0~100) | `creative_quality_scorer` (Vision LLM) | 소재 사이드패널 레이더 차트 + 개선 제안 |
| **POC-06** | KPI 예측 | 매일 자동 | 최근 14일 이동평균 → 월말 선형 외삽. 예측값 = 누적 / 경과일 × 월 총일수 | `moving_average_forecaster` + `summary_generator` | 대시보드 KPI 카드 "AI 예측값" |
| **POC-07** | 검색량 급등 감지 | 매일 자동 | DataLab ratio 전주 대비 +20% → 급등 | `trend_detector` + `kpi_insight_generator` | 트렌드분석 화면 하이라이트 |
| **POC-08** | 감성 분석 | 일 1회 배치 | `cleaned_text` 입력 → KoBERT 사전학습 → 긍/중/부 분류. `is_sponsored=True` 별도 집계 | `sentiment_analyzer` + `summary_generator` | 트렌드분석 파이 차트 + 콘텐츠 카드 |

> POC-09 (AI 리포트 스토리)는 `report_agent`로 이동.
> Tool 이름은 예상이며, 실제 구현 시 카탈로그 최종 명칭은 별도 확정.

#### LLM 활용 원칙

**사용 O:**
- 분석 결과 → 한국어 1~2줄 변환
- 소재 품질 채점 (Vision)
- 리포트 스토리 구성 (→ report_agent로 이관)
- 원인 추정 자연어 설명

**사용 X:**
- 이상 감지 계산 (규칙 / Z-score)
- 통계 검정 (statsmodels)
- KPI 계산 (사칙연산)
- 피로도 판정 (규칙)

**환각 방지:**
- 숫자는 반드시 프롬프트에 직접 포함 (LLM이 만들지 못하게)
- JSON 출력 강제 후 파싱
- "추정" / "가능성" 표현 사용 지시

**Tool 목록 — ML:**

| Tool | 유형 | 설명 |
|------|------|------|
| `sentiment_analyzer` | tool | ML 감성 분석 |
| `morpheme_analyzer` | tool | 형태소 분석 |
| `keyword_extractor` | tool | 키워드/토픽 추출 |
| `clustering_analyzer` | tool | 클러스터링 |
| `trend_detector` | tool | 시계열 트렌드 탐지 |
| `kpi_trend_analyzer` | tool | KPI 이상치 탐지, 변화점 감지, Granger 인과성 (신규) |
| `keyword_optimizer` | tool | 키워드 추출 + Google Ads Planner 등 외부 API 조회 + 추천 (신규) |

**Tool 목록 — LLM:**

| Tool | 유형 | 설명 |
|------|------|------|
| `llm_sentiment_analyzer` | tool | LLM 기반 감성 분석 (맥락 이해) |
| `insight_extractor` | tool | 데이터에서 인사이트 도출 |
| `competitor_analyzer` | tool | 경쟁사 비교 분석 |
| `trend_interpreter` | tool | 트렌드 해석 및 원인 분석 |
| `summary_generator` | tool | 분석 결과 요약 |
| `ml_analysis_reporter` | tool | ML 분석 결과를 자연어로 해석 |
| `kpi_insight_generator` | tool | KPI 분석 결과 → 인사이트 생성 (신규) |

---

### Agent 4: `report_agent` (분석 결과 종합 + LLM 스토리)

> v0.5 변경: 기존 "분석 종합 + 보고서 + PDF"에서 "분석 결과 종합 + LLM 스토리 구성"으로 역할 축소.
> PDF 렌더링은 `pdf_agent`로 분리.

**역할**: 여러 분석 결과를 하나의 스토리로 종합하고, LLM 기반 자연어 보고서 텍스트를 생성한다.

**향후 판단할 것 (현재는 Planning이 결정):**
- 어떤 분석 결과를 어떻게 종합할지
- 보고서 스토리 구성 (순서, 강조점)
- 어떤 인사이트를 강조할지

**단계별 범위:**

| 단계 | 범위 |
|------|------|
| **1차 (POC)** | POC-09 시나리오 (LLM 스토리 3단계: 핵심성과 → 원인분석 → 다음액션) |
| **2차 (MVP)** | 멀티 클라이언트 톤 학습, 인사이트 자동 우선순위화 |
| **3차** | 자동 인사이트 발견(이상 패턴 자동 보고), 정기 리포트 자동 발행 |

#### POC 시나리오

| ID | 시나리오 | 트리거 | 주요 로직 | 사용 Tool (예상) | 출력 |
|----|---------|--------|----------|---------------|------|
| **POC-09** | AI 리포트 스토리 | 채팅 요청 (리포트 생성) | 성과 데이터 요약 → LLM 스토리 구성 (3단계: 핵심성과 → 원인분석 → 다음액션) | `insight_synthesizer` + `report_writer` (LLM) | `pdf_agent`로 전달 (마케터 확인 후 확정) |

**Tool 목록:**

| Tool | 유형 | 설명 |
|------|------|------|
| `insight_synthesizer` | tool | 여러 분석 결과를 하나의 인사이트로 종합 |
| `report_writer` | tool | 인사이트 기반 보고서 텍스트 생성 (LLM) |
| `report_section_planner` | tool | 포함 섹션 결정 (KPI/채널/소재/비용/트렌드/AI 인사이트) |
| `summary_generator` | tool | 핵심 요약문 생성 |

> 차트 생성, PDF 변환 등은 `pdf_agent`로 이동.

---

### Agent 5: `pdf_agent` (PDF 렌더링) — 신설

> v0.5 신설. report_agent의 보고서 텍스트를 받아 PDF/PPT/Excel로 렌더링하는 전담 에이전트.

**역할**: report_agent에서 생성한 보고서 텍스트와 분석 데이터를 시각화하고 PDF로 출력한다.

**향후 판단할 것 (현재는 Planning이 결정):**
- 어떤 차트로 시각화할지
- PDF 템플릿 선택 (클라이언트 브랜드 컬러)
- 출력 포맷 (PDF / PPT / Excel)

**단계별 범위:**

| 단계 | 범위 |
|------|------|
| **1차 (POC)** | PDF 1종 출력, 클라이언트 브랜드 컬러 적용, 차트 자동 생성 |
| **2차 (MVP)** | PPT/Excel 출력 추가, 템플릿 다양화 |
| **3차** | 인터랙티브 리포트 (HTML/Notion), 자동 업로드 |

**처리 흐름:**

```
report_agent → 보고서 텍스트 + 인사이트
                 ↓
           [chart_generator] 데이터 시각화
                 ↓
           [template_selector] PDF 템플릿 결정
                 ↓
           [pdf_converter] 최종 PDF 렌더링
                 ↓
           HITL — 채팅 미리보기 → 마케터 확인 → [최종 다운로드]
```

**포함 섹션 (마케터 선택):**

| 섹션 | 내용 |
|------|------|
| KPI 요약 | ROAS / 전환수 / 광고비 / 달성률 / 전월 대비 |
| 채널별 성과 | 4개 채널 비교 테이블 + ROAS 바 차트 |
| 소재 분석 | 베스트 소재 / 교체 필요 소재 / 피로도 현황 |
| 비용 최적화 | 무전환 키워드 절감 / 예산 배분 추천 |
| 트렌드 | 검색량 급등 키워드 / 감성 분석 결과 |
| AI 인사이트 | 핵심 발견 3가지 / 다음 달 액션 플랜 |

**Tool 목록:**

| Tool | 유형 | 설명 |
|------|------|------|
| `chart_generator` | tool | 데이터 시각화 차트 생성 (matplotlib/plotly) |
| `template_selector` | tool | PDF 프레임/템플릿 선택 (브랜드 컬러 적용) |
| `pdf_converter` | tool/subgraph | 보고서 → PDF 변환 (템플릿 기반) |

---

### Agent 6: `image_creation_agent` (광고 이미지)

**역할**: 고품질 단독 광고 이미지를 생성하고, 슬로건을 합성한다.

**단계별 범위:**

| 단계 | 범위 |
|------|------|
| **1차 (POC)** | DALL-E 3 또는 SD로 3가지 방향 생성, 브랜드 가이드 적용, 매체별 규격 변환 |
| **2차 (MVP)** | 과거 성과 좋은 소재 패턴 학습, 슬로건 자동 합성 |
| **3차** | 자동 A/B 변형 생성, 매체 자동 업로드 |

**향후 판단할 것 (현재는 Planning이 결정):**
- 브랜드 가이드라인에 맞는 이미지 방향 판단
- 이미지 프롬프트 작성 (스타일, 구도)
- 생성 결과 품질 검수
- 슬로건 생성 및 합성 여부

**Tool 목록:**

| Tool | 유형 | 그룹 | 설명 |
|------|------|------|------|
| `ad_prompt_generator` | tool | 이미지 | 브랜드/인사이트 기반 프롬프트 작성 |
| `ad_image_generator` | tool | 이미지 | 외부 이미지 생성 API 호출 |
| `quality_checker` | tool | 이미지 | 이미지 품질 검증 (해상도, 유해성) |
| `brand_guideline_analyzer` | subgraph | 이미지 (신규) | 브랜드 가이드 문서 RAG 분석 → 스타일 기준 추출 |
| `slogan_generator` | tool | 슬로건 | LLM 기반 슬로건 생성 |
| `slogan_rag_search` | tool | 슬로건 | 기존 슬로건 DB에서 참고 사례 검색 |
| `slogan_evaluator` | tool | 슬로건 | 생성 슬로건 품질 평가 |
| `slogan_overlay` | tool | 합성 | 슬로건 텍스트를 이미지에 합성 |
| `image_resizer` | tool (공유) | 리사이징 | 매체별 리사이징 |
| `thumbnail_creator` | tool (공유) | 리사이징 | 썸네일 생성 |

---

### Agent 7: `video_creation_agent` (영상 제작)

> **POC 범위: 스토리보드까지만**. 실제 영상 제작은 3차 단계.
> 향후 명칭 `storyboard_agent`로 변경 가능성 있으나, 영상 제작까지 확장 예정이므로 현재 명칭 유지.

**역할**:
- **POC**: 영상 광고 스토리보드 기획·생성 (텍스트 + 장면 설명 + 각 컷 참고 이미지 + PDF 출력)
- **3차**: 스토리보드 → 실제 영상 제작 (Runway/Sora) + 음악·나레이션 + 매체별 업로드

**단계별 범위:**

| 단계 | 범위 |
|------|------|
| **1차 (POC)** | 스토리보드 텍스트 + 장면 설명 (LLM) + 각 컷 참고 이미지 (image_creation_agent 협력) + PDF 출력 |
| **2차 (MVP)** | 스토리보드 → 영상 프레임 이미지 자동 생성, 컷 연속성 유지 |
| **3차 (자동화)** | 실제 영상 제작 (Runway/Sora), 음악/나레이션 자동 생성, 매체 자동 업로드 |

**스토리보드 입력:**

직접 입력 (마케터 채팅에서 제공):
- 제품명, 영상 길이 (6초/15초/30초)
- 타겟 (연령, 피부 고민)
- 목적 (인지/고려/전환)

자동 참조 (analysis_agent 결과):
- 최근 성과 좋은 소재 패턴
- 현재 트렌드 키워드 (검색량 급등)
- 소비자 감성 분석 결과 (긍정 키워드)
- 경쟁사 영상 트렌드 (유튜브 수집)

**향후 판단할 것 (현재는 Planning이 결정):**
- 브랜드 가이드라인에 맞는 영상 방향 판단
- 스토리보드 구성 (컷 수, 흐름)
- 컷별 이미지 스타일 및 연속성
- 영상 편집 방향 (트랜지션, 속도)

**Tool 목록:**

| Tool | 유형 | 설명 |
|------|------|------|
| `storyboard_planner` | tool | 컷 구성 + 흐름 설계 |
| `frame_image_generator` | tool | 컷별 이미지 생성 (영상 프레임 규격) |
| `video_compositor` | subgraph | 이미지 → 영상 변환 + 트랜지션 |
| `voice_generator` | tool | 나레이션/음성 생성 (병렬 가능) |
| `video_merger` | tool | 개별 영상 + 음성 → 최종 합본 |
| `subtitle_generator` | tool | 자막 생성 |
| `brand_guideline_analyzer` | subgraph (공유) | 브랜드 가이드 RAG 분석 (image_creation_agent와 공유) |

---

## 3. 공유 Tool

여러 Agent가 공통으로 사용하는 Tool:

| Tool | 유형 | 사용 Agent | 설명 |
|------|------|-----------|------|
| `image_resizer` | tool | image, video, report | 이미지 크기 조정 |
| `thumbnail_creator` | tool | image, report | 썸네일 생성 |
| `format_converter` | tool | image, video | 이미지 포맷 변환 (PNG/JPG/WebP) |
| `brand_guideline_analyzer` | subgraph (신규) | image, video | 브랜드 가이드 문서 RAG 분석 → 스타일 기준 추출 |
| `brand_safety_checker` | subgraph (신규) | image, video, report | 법규/규정 RAG + LLM 판단. 생성물 안전성 검수 |

---

## 4. 기능 ↔ Agent 매핑 요약

### 기존 기능 (v0.2)

| # | 기능 | 분류 | 소속 Agent |
|---|------|------|-----------|
| ① | 데이터 수집 | Tool (여러 개) | `collection_agent` |
| ② | 성과 지표 수집 | Tool (여러 개) | `collection_agent` |
| ③ | 전처리 (데이터 + 텍스트 클렌징 8단계) | Tool (여러 개) | `preprocessing_agent` |
| ④ | ML 분석 | Tool (여러 개) | `analysis_agent` |
| ⑤ | LLM 분석 | Tool (여러 개) | `analysis_agent` |
| ⑥ | 분석 결과 종합 + LLM 스토리 | Agent | `report_agent` |
| ⑥' | PDF 렌더링 | Agent | `pdf_agent` (v0.5 신설) |
| ⑦ | 스토리보드 (POC) → 영상 (3차) | Agent | `video_creation_agent` |
| ⑧ | 광고 이미지 | Agent | `image_creation_agent` |
| ⑨ | 슬로건 | Tool | `image_creation_agent` |
| ⑩ | 리사이징/썸네일 | Tool (공유) | 공유 Tool |

### 추가 기능 (v0.3 신규)

| 기능 | 분류 | 소속 | 출처 |
|------|------|------|------|
| 요서 파싱 (Brief Parser) | Subgraph | `collection_agent` | 고도화 계획 |
| KPI 트렌드 분석 | Tool | `analysis_agent` | 고도화 계획 |
| 키워드 최적화 | Tool | `analysis_agent` | 고도화 계획 |
| 가이드라인 분석 | Subgraph (공유) | `image_creation_agent`, `video_creation_agent` | 고도화 계획 |
| 세이프티 검수 | Subgraph (공유) | 공유 Tool | 고도화 계획 |

### POC 분석 시나리오 (v0.5 신규)

| ID | 시나리오 | 소속 Agent |
|----|---------|-----------|
| POC-01 | KPI 이상 감지 | `analysis_agent` |
| POC-02 | 소재 피로도 감지 | `analysis_agent` |
| POC-03 | A/B 테스트 자동 판정 | `analysis_agent` |
| POC-04 | 무전환 키워드 감지 | `analysis_agent` |
| POC-05 | AI 품질 채점 (Vision LLM) | `analysis_agent` |
| POC-06 | KPI 예측 (이동평균) | `analysis_agent` |
| POC-07 | 검색량 급등 감지 | `analysis_agent` |
| POC-08 | 감성 분석 (KoBERT) | `analysis_agent` |
| POC-09 | AI 리포트 스토리 | `report_agent` |

---

## 4-A. Tool YAML `requires_approval` 필드 (Sprint 14 예정)

> Sprint 14 (HITL 고도화) A3 항목에서 사용 예정. 본 문서의 Tool 카탈로그 정의 시 후속 적용 대상이다.

각 Tool YAML에 `requires_approval: bool` 필드를 추가하여 **실행 전 사용자 확인 필요 여부**를 표시한다.

| Tool 후보 | 사유 |
|---|---|
| `pdf_converter` | 유료 API + 외부 출력물 |
| `ad_image_generator` | 유료 LLM Vision API |
| `frame_image_generator` | 영상 프레임 (다량 호출) |
| `video_compositor` | 무거운 연산 + 외부 처리 |
| `voice_generator` | 유료 TTS |
| `meta_ads_collector` (실집행 시) | 유료 매체 API quota |

> Sprint 14 구현 시 execution_stage가 Todo 실행 전 `requires_approval=true`인 경우 interrupt() 호출 → 사용자 승인 후 실행. 거부 시 해당 Todo skip.

---

## 5. 미확정 사항

| 항목 | 선택지 | 결정 시점 |
|------|--------|----------|
| ⑨ 슬로건의 위치 | image_creation_agent의 Tool (현재) vs 독립 Agent | 단독 요청 빈도 확인 후 |
| brand_guideline_analyzer 위치 | image/video 각각 vs 공유 Tool | 사용 패턴 확인 후 |
| brand_safety_checker 범위 | 법규만 vs 법규+브랜드 규정+유해성 통합 | 검수 요구사항 구체화 후 |
| 각 수집 Tool의 유형 | tool vs subgraph | 채널 API 복잡도에 따라 개별 구현 시 |
| 각 agent의 의사결정 로직 도입 | 현재 Tool 팀 (Planning이 모든 결정) vs agent별 자체 판단 | Phase 5 이후 재평가 |
| analysis_agent의 분석 Tool 카탈로그 | POC 시나리오 8개의 핵심 Tool부터 → ML/LLM/인과분석/분석프레임워크 점진 확장 | POC 시연 후 우선순위 재평가 |
| 사람 개입 맞춤형 분석 가이드 | 분석 결과 + 사용자 가이드 조합 방식 (앱 정체성) | 추후 구현 방식 구체화 필요 |
| `video_creation_agent` 명칭 변경 여부 | 현재 명칭 유지 (POC=스토리보드, 3차=영상까지 확장 예정) vs `storyboard_agent`로 변경 | 영상 제작 단계 진입 시 재평가 |

### 결정 사항 (확정됨)

| 항목 | 결정 | 일자 |
|------|------|------|
| `data_analysis_agent` 분리 | `collection_agent` / `preprocessing_agent` / `analysis_agent` 3개로 분리 | 2026-04-09 |
| `report_agent` 역할 축소 | "분석 종합 + 보고서 + PDF" → "분석 결과 종합 + LLM 스토리"로 축소 | 2026-04-09 |
| `pdf_agent` 신설 | PDF 렌더링 전담 (report_agent에서 분리). 향후 PPT/Excel 출력도 흡수 | 2026-04-09 |
| `video_creation_agent` POC 범위 | 스토리보드까지만 (실제 영상 제작은 3차) | 2026-04-09 |
| `preprocessing_agent` 텍스트 클렌징 | 8단계 파이프라인 도입 (이모지/반복문자/HTML/협찬/길이/중복/언어/맞춤법) | 2026-04-09 |
| `analysis_agent` POC 시나리오 | POC-01~08 8개 정의 (POC-09는 report_agent로 이동) | 2026-04-09 |

---

## 변경 이력

| 버전 | 날짜 | 변경자 | 변경 내용 |
|------|------|--------|----------|
| v0.1 | 2026-03-31 | 도윤 | 초기 작성. 10개 기능 나열 |
| v0.2 | 2026-04-01 | 도윤 | Agent/Tool 경계 확정. 4 Agent + 공유 Tool 구조 |
| v0.3 | 2026-04-01 | 도윤 | 고도화 계획 반영. 요서파서, KPI분석, 키워드최적화, 가이드라인분석, 세이프티검수 추가 |
| v0.4 | 2026-04-09 | 도윤 | `data_analysis_agent`를 `collection_agent` / `preprocessing_agent` / `analysis_agent` 3개로 분리. 6 Agent + 공유 Tool 구조로 재편. Agent 1 섹션 → Agent 1/2/3 섹션, image/video는 Agent 5/6으로 번호 이동. 기능 매핑 표·트리 구조·미확정 사항 동기화 |
| v0.5 | 2026-04-09 | 도윤 | OctorAD 기능 명세서 흡수. (1) `report_agent` 역할 축소(분석 종합+LLM 스토리). (2) `pdf_agent` 신설(PDF 렌더링 전담). (3) `preprocessing_agent`에 텍스트 클렌징 8단계 파이프라인 + 5개 Tool 추가(repeat_char_normalizer/html_url_stripper/sponsored_detector/length_filter/duplicate_detector/language_detector/spell_normalizer/kpi_calculator/pii_masker). (4) `analysis_agent`에 POC-01~08 8개 시나리오 + LLM 사용 원칙 추가. (5) `video_creation_agent` POC 범위 명시(스토리보드까지). (6) 모든 agent에 1차/2차/3차 단계별 범위 표 추가. 7 Agent + 공유 Tool 구조 |
| **v0.6** | **2026-04-19** | **도윤 + Sprint 12 메모** | §4-A 신규 — Sprint 14(HITL 고도화) A3 항목에 대비한 Tool YAML `requires_approval: bool` 필드 적용 대상 명시(pdf_converter, ad_image_generator, frame_image_generator, video_compositor, voice_generator, meta_ads_collector). Tool 카탈로그/도메인 정의 자체 변경 없음. |
