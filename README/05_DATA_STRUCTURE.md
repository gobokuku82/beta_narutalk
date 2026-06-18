# 05. 데이터 구조

## 데이터 디렉토리

```
data/
├── mock/                   # Mock 테스트 데이터
│   ├── reviews/           # 리뷰 데이터
│   ├── analysis/          # 분석 결과
│   ├── insights/          # 인사이트
│   ├── trends/            # 트렌드 데이터
│   ├── internal/          # 내부 데이터
│   └── ads/               # 광고 데이터
│
├── collected/              # 수집된 원본 데이터
│   ├── reviews/
│   └── trends/
│
├── processed/              # 처리된 데이터
│
├── cache/                  # 실행 캐시
│
├── sessions/               # 세션 데이터
│
├── reports/                # 생성된 리포트
│
├── result_trend/           # 최종 트렌드 분석 결과
│
└── system/
    └── todos/              # Todo 관리 데이터
```

---

## Mock 데이터 구조

### 1. 리뷰 데이터 (`mock/reviews/`)

#### naver_reviews.json
```json
{
  "source": "naver_shopping",
  "collected_at": "2026-01-31T10:00:00",
  "keyword": "라네즈",
  "reviews": [
    {
      "id": "review_001",
      "text": "워터슬리핑마스크 정말 촉촉해요! 자고 일어나면 피부가 달라져 있어요.",
      "author": "beauty_lover",
      "rating": 5,
      "date": "2026-01-30",
      "product_name": "라네즈 워터슬리핑마스크",
      "source": "naver",
      "skin_type": "건성",
      "likes": 42,
      "hashtags": ["촉촉", "보습력", "추천"]
    }
  ]
}
```

#### instagram_reviews.json
```json
{
  "source": "instagram",
  "collected_at": "2026-01-31T10:00:00",
  "keyword": "라네즈",
  "reviews": [
    {
      "id": "ig_001",
      "text": "겨울철 필수템! #라네즈 #워터슬리핑마스크",
      "author": "@skincare_daily",
      "date": "2026-01-29",
      "likes": 1523,
      "comments_count": 89,
      "hashtags": ["라네즈", "워터슬리핑마스크", "겨울스킨케어"],
      "source": "instagram"
    }
  ]
}
```

### 2. 분석 결과 (`mock/analysis/`)

#### sentiment_result.json
```json
{
  "analysis_type": "sentiment",
  "analyzed_at": "2026-01-31T11:00:00",
  "total_reviews": 100,
  "sentiment_distribution": {
    "positive": 68,
    "neutral": 20,
    "negative": 12
  },
  "average_sentiment_score": 0.72,
  "reviews": [
    {
      "id": "review_001",
      "text": "정말 촉촉해요!",
      "sentiment": {
        "label": "positive",
        "score": 0.95,
        "aspects": [
          {"aspect": "보습력", "sentiment": "positive", "score": 0.98}
        ]
      }
    }
  ]
}
```

#### keywords_result.json
```json
{
  "analysis_type": "keyword_extraction",
  "analyzed_at": "2026-01-31T11:00:00",
  "total_documents": 100,
  "keywords": [
    {"keyword": "보습력", "frequency": 45, "tfidf_score": 0.82},
    {"keyword": "촉촉함", "frequency": 32, "tfidf_score": 0.75},
    {"keyword": "가성비", "frequency": 28, "tfidf_score": 0.68}
  ],
  "top_bigrams": [
    {"bigram": "피부 촉촉", "frequency": 18},
    {"bigram": "수분 충전", "frequency": 15}
  ]
}
```

### 3. 인사이트 (`mock/insights/`)

#### insight_result.json
```json
{
  "analysis_type": "insight_generation",
  "generated_at": "2026-01-31T11:00:00",
  "brand": "라네즈",
  "insights": [
    {
      "id": "ins_001",
      "type": "positive",
      "category": "product_strength",
      "title": "보습력에 대한 강한 긍정적 반응",
      "content": "고객들은 라네즈 제품의 보습력에 대해 매우 긍정적으로 평가합니다.",
      "confidence": 0.92,
      "evidence": ["리뷰 65% 보습 관련 긍정 언급"],
      "impact": "high"
    },
    {
      "id": "ins_002",
      "type": "warning",
      "category": "product_concern",
      "title": "민감성 피부 고객의 자극 보고",
      "content": "일부 민감성 피부 고객에서 자극 반응이 보고되고 있습니다.",
      "confidence": 0.78,
      "impact": "medium"
    }
  ],
  "recommendations": [
    "민감성 피부 고객을 위한 패치 테스트 권장 문구 추가",
    "보습 효과 강조 마케팅 유효",
    "슬리핑마스크 라인 중심 프로모션 기획"
  ]
}
```

### 4. 트렌드 데이터 (`mock/trends/`)

#### google_trends.json
```json
{
  "source": "google_trends",
  "analyzed_at": "2026-01-31T10:00:00",
  "timeframe": "today 3-m",
  "geo": "KR",
  "trends_data": {
    "라네즈": {
      "interest_over_time": [78, 82, 85, 79, 88, 92, 95, 89, 87, 90, 93, 100],
      "dates": ["2024-11-01", "2024-11-08", "..."],
      "average": 88.2,
      "peak": 100,
      "trend_direction": "rising"
    }
  },
  "related_queries": {
    "라네즈": {
      "rising": ["라네즈 립마스크", "라네즈 슬리핑마스크 가격"],
      "top": ["라네즈 립슬리핑마스크", "라네즈 워터슬리핑마스크"]
    }
  },
  "comparison_summary": {
    "market_leader": "라네즈",
    "fastest_growing": "이니스프리"
  }
}
```

### 5. 내부 데이터 (`mock/internal/`)

#### products.json
```json
{
  "source": "internal_db",
  "updated_at": "2026-01-31T09:00:00",
  "brand": "라네즈",
  "products": [
    {
      "product_id": "LNZ001",
      "name": "라네즈 워터슬리핑마스크",
      "category": "마스크/팩",
      "subcategory": "슬리핑마스크",
      "price": 32000,
      "original_price": 35000,
      "volume": "70ml",
      "launch_date": "2022-03-01",
      "status": "active",
      "stock": 1250,
      "monthly_sales": 3500,
      "rating": 4.7,
      "review_count": 2840,
      "main_ingredients": ["히알루론산", "미네랄워터", "프로바이오틱스"],
      "target_skin_type": ["건성", "복합성", "일반"],
      "key_benefits": ["수분공급", "피부진정", "톤업"]
    }
  ],
  "category_summary": {
    "total_products": 15,
    "active_products": 12,
    "top_seller": "LNZ002"
  }
}
```

### 6. 광고 데이터 (`mock/ads/`)

#### ad_prompts.json
```json
{
  "generated_at": "2026-01-31T12:00:00",
  "brand": "라네즈",
  "campaign": "Winter Hydration 2026",
  "target_platform": "instagram",
  "ad_concepts": [
    {
      "concept_id": "ad_001",
      "name": "촉촉한 아침의 비밀",
      "tagline": "밤새 채우는 수분, 아침에 만나는 촉촉함",
      "description": "72시간 보습력을 강조하는 감성적 광고",
      "image_prompts": [
        {
          "scene": 1,
          "prompt": "Young Korean woman waking up in soft morning light...",
          "aspect_ratio": "1:1",
          "style": "photorealistic"
        }
      ],
      "copy_texts": [
        "자는 동안 피부에 수분 충전 완료",
        "72시간 보습, 아침이 달라집니다"
      ],
      "hashtags": ["라네즈", "워터슬리핑마스크", "수분폭탄"]
    }
  ],
  "video_script": {
    "duration": 15,
    "format": "instagram_reels",
    "scenes": [
      {"time": "0-3s", "visual": "Woman applying mask", "text": ""}
    ]
  }
}
```

---

## Mock 데이터 로더

### 위치
`backend/app/dream_agent/tools/data/mock_loader.py`

### 사용법

```python
from backend.app.dream_agent.tools.data import MockDataLoader, get_mock_loader

# 싱글톤 인스턴스
loader = get_mock_loader()

# 리뷰 로드
reviews = loader.load_reviews("naver")  # naver_reviews.json

# 전처리된 결과
preprocessed = loader.get_preprocessed_reviews()

# 트렌드 데이터
trends = loader.get_trends_result("라네즈", timeframe="today 3-m")

# 인사이트
insights = loader.get_insights_result()

# 제품 검색
products = loader.search_products("슬리핑마스크")

# 광고 컨셉
concepts = loader.get_ad_concepts()
```

### 환경변수

```bash
# Mock 모드 활성화
USE_MOCK_DATA=true

# Python에서
import os
os.environ["USE_MOCK_DATA"] = "true"
```

---

## 핵심 데이터 모델

### TodoItem

```python
class TodoItem(BaseModel):
    id: str                              # UUID
    task: str                            # "리뷰 데이터 수집"
    task_type: str = "general"           # collect, analyze, generate
    layer: Literal[
        "cognitive",
        "planning",
        "ml_execution",
        "biz_execution",
        "response"
    ]
    status: Literal[
        "pending",
        "in_progress",
        "completed",
        "failed",
        "blocked",
        "skipped"
    ]
    priority: int = Field(ge=0, le=10)   # 0-10
    metadata: TodoMetadata
    version: int = 1
    history: List[Dict] = []
```

### TodoMetadata

```python
class TodoMetadata(BaseModel):
    execution: ExecutionConfig = None    # tool, tool_params
    dependency: DependencyConfig = None  # depends_on, blocks
    data: DataConfig = None              # input_data, output_path
    progress: ProgressConfig = None      # progress_percentage
    approval: ApprovalConfig = None      # requires_approval
    context: Dict = {}
```

### ExecutionResult

```python
class ExecutionResult(BaseModel):
    success: bool
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    metadata: Dict = {}
    todo_id: Optional[str] = None
```

### AgentState

```python
class AgentState(TypedDict):
    user_input: str
    session_id: str
    cognitive_result: Optional[Dict]
    plan: Optional[Plan]
    todos: Annotated[List[TodoItem], todo_reducer]
    ml_result: Annotated[Dict, ml_result_reducer]
    biz_result: Annotated[Dict, biz_result_reducer]
    response: str
    final_answer: str
    current_context: Dict
    language: str
```

---

## 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│  Mock 데이터 (USE_MOCK_DATA=true)                               │
│  data/mock/{reviews, analysis, insights, trends, internal, ads} │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  MockDataLoader                                                  │
│  - load_reviews(), get_preprocessed_reviews()                    │
│  - get_trends_result(), get_insights_result()                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tools (collector, preprocessor, analyze_trends)                 │
│  - Mock 모드면 MockDataLoader 사용                               │
│  - 실제 모드면 API/크롤러 사용                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Executors (DataExecutor, InsightExecutor, ...)                  │
│  - Tool 결과를 ExecutionResult로 래핑                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AgentState                                                      │
│  - ml_result, biz_result에 저장                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Response Layer                                                  │
│  - 결과 요약 → 마크다운 응답                                      │
│  - data/result_trend/에 리포트 저장                               │
└─────────────────────────────────────────────────────────────────┘
```
