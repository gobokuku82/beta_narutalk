# Dream Agent 유스케이스 문서

> **상태**: 작성 필요
> **최종 수정**: 2026-02-03

---

## 유스케이스 목록

| ID | 이름 | Domain | 상태 |
|----|------|--------|------|
| UC-001 | 웹 데이터 수집 | DATA_SCIENCE | 작성 필요 |
| UC-002 | 데이터 분석 | DATA_SCIENCE | 작성 필요 |
| UC-003 | 시각화 생성 | DATA_SCIENCE | 작성 필요 |
| UC-004 | 리포트 생성 | MARKETING | 작성 필요 |
| UC-005 | 콘텐츠 생성 | MARKETING | 작성 필요 |
| ... | ... | ... | ... |

---

## UC-001: 웹 데이터 수집

### 기본 정보
- **Actor**: 마케터, 데이터 분석가
- **Domain**: DATA_SCIENCE
- **Category**: data_collection
- **관련 도구**: web_scraper, crawler

### 목표
웹사이트에서 리뷰, 상품 정보 등의 데이터를 수집

### 사전 조건
- 수집 대상 URL 또는 키워드 제공
- 수집할 데이터 유형 명시

### 기본 시나리오

```
1. 사용자: "올리브영 리뷰 수집해줘"
2. Cognitive Layer:
   - 의도 분석: DATA_SCIENCE.data_collection.web_scraping
   - 엔티티 추출: {target: "올리브영", data_type: "리뷰"}
3. Planning Layer:
   - 도구 선택: web_scraper
   - 실행 계획 생성
4. Execution Layer:
   - WebScraperAgent 실행
   - 데이터 수집
5. Response Layer:
   - 결과 포맷팅
   - 사용자에게 반환
```

### 입력 예시

```
"올리브영 리뷰 수집해줘"
"네이버 쇼핑에서 '아이폰' 리뷰 1000개 모아줘"
"쿠팡 베스트셀러 상품 정보 수집"
```

### 출력 예시

```json
{
  "status": "success",
  "data": {
    "items_collected": 1000,
    "source": "oliveyoung.co.kr",
    "data_type": "reviews",
    "file_path": "/data/output/reviews_20260203.csv"
  },
  "message": "올리브영에서 리뷰 1000개를 수집했습니다."
}
```

### 예외 시나리오

| 상황 | 처리 |
|------|------|
| 사이트 접근 차단 | 에러 메시지 + 대안 제시 |
| 데이터 없음 | 빈 결과 반환 + 안내 |
| 타임아웃 | 부분 결과 반환 + 재시도 옵션 |

### 관련 Agent
- `WebScraperAgent` (backend/app/dream_agent/execution/domain/web_scraper.py)

---

## UC-002: 데이터 분석

### 기본 정보
- **Actor**: 데이터 분석가
- **Domain**: DATA_SCIENCE
- **Category**: data_analysis
- **관련 도구**: data_analyzer, statistical_analyzer

### 목표
수집된 데이터에 대한 분석 수행

### 사전 조건
- 분석할 데이터 존재 (파일 경로 또는 이전 수집 결과)
- 분석 목적 명시

### 기본 시나리오

```
1. 사용자: "수집한 리뷰 데이터 분석해줘"
2. Cognitive Layer:
   - 의도 분석: DATA_SCIENCE.data_analysis
   - 엔티티 추출: {data_source: "이전 수집 결과", analysis_type: "general"}
3. Planning Layer:
   - 도구 선택: data_analyzer
   - 실행 계획 생성
4. Execution Layer:
   - DataAnalyzerAgent 실행
   - 분석 수행
5. Response Layer:
   - 분석 결과 요약
   - 시각화 첨부 (선택적)
```

### 입력 예시

```
"수집한 리뷰 데이터 분석해줘"
"이 CSV 파일의 트렌드 분석 해줘"
"감성 분석 결과 보여줘"
```

### 출력 예시

```json
{
  "status": "success",
  "data": {
    "analysis_type": "sentiment",
    "summary": {
      "positive": 65,
      "negative": 20,
      "neutral": 15
    },
    "insights": ["긍정 리뷰 중 '배송' 키워드 다수", ...]
  },
  "visualizations": ["chart_sentiment.png"]
}
```

---

## UC-003: 시각화 생성

<!-- 템플릿 반복 -->

### 기본 정보
- **Actor**:
- **Domain**:
- **Category**:
- **관련 도구**:

### 목표


### 기본 시나리오

```
1. 사용자: ""
2. Cognitive Layer:
3. Planning Layer:
4. Execution Layer:
5. Response Layer:
```

---

## 작성 가이드

각 유스케이스 작성 시 다음을 포함해야 합니다:

1. **기본 정보**: Actor, Domain, Category, 관련 도구
2. **목표**: 한 문장으로 명확히
3. **시나리오**: 4-Layer를 거치는 전체 흐름
4. **입력 예시**: 실제 사용자 입력 3개 이상
5. **출력 예시**: JSON 형식의 예상 결과
6. **예외 시나리오**: 발생 가능한 문제와 처리 방법

### 도구별 유스케이스 매핑

| 도구 (YAML) | 유스케이스 ID |
|-------------|---------------|
| web_scraper | UC-001 |
| data_analyzer | UC-002 |
| visualizer | UC-003 |
| report_generator | UC-004 |
| content_generator | UC-005 |
| trend_analyzer | UC-006 |
| sentiment_analyzer | UC-007 |
| ... | ... |

---

*이 문서는 ZERO_BASE_GUIDE.md Step 2에 해당합니다.*
