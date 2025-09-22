# Agents 완전 상세 문서

## 1. Sales Analytics Agent

### 파일: `backend/service/agents/sales_analytics_agent.py`

#### 파일 목적
매출 데이터 분석을 위한 에이전트. Text-to-SQL 변환, 데이터 분석, 시각화 구성을 담당합니다.

#### Imports 및 Dependencies
```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any, Optional
import sqlite3
import pandas as pd
import json
import logging
from pathlib import Path
from ..utils import LLMManager, PromptTemplates
```

#### 로깅 설정
```python
logger = logging.getLogger(__name__)
```

---

### State 정의

#### SalesAnalyticsState(TypedDict)
```python
class SalesAnalyticsState(TypedDict):
    query: str                      # 사용자의 원본 쿼리
    sql_query: str                  # LLM이 생성한 SQL 쿼리
    query_results: List[Dict]       # SQL 실행 결과
    analysis: Dict[str, Any]        # 데이터 분석 결과
    visualization: Dict[str, Any]   # 시각화 설정 정보
```

---

### SalesAnalyticsAgent 클래스

#### 클래스 초기화
```python
class SalesAnalyticsAgent:
    def __init__(self):
        # LangGraph workflow 초기화
        self.workflow = StateGraph(SalesAnalyticsState)

        # LLM 매니저 초기화 (싱글톤)
        self.llm = LLMManager()

        # 프롬프트 템플릿 초기화
        self.prompts = PromptTemplates()

        # 데이터베이스 경로 설정 (환경 변수에서 읽거나 기본값 사용)
        self.db_paths = {
            "clients": Path("database/storage/sales_performance/clients_db.db"),
            "clients_info": Path("database/storage/sales_performance/clients_info_db.db"),
            "sales_performance": Path("database/storage/sales_performance/sales_performance_db.db"),
            "sales_target": Path("database/storage/sales_performance/sales_target_db.db")
        }

        # 스키마 정보 로드
        self.schema_info = self.load_schema_info()

        # 그래프 구성
        self._build_graph()
```

#### 그래프 구성 (_build_graph)
```python
def _build_graph(self):
    """LangGraph 워크플로우 구성"""

    # 노드 추가
    self.workflow.add_node("parse_query", self.parse_sales_query)
    self.workflow.add_node("generate_sql", self.text_to_sql)
    self.workflow.add_node("execute_query", self.execute_sql_query)
    self.workflow.add_node("analyze_data", self.perform_analysis)
    self.workflow.add_node("visualize", self.create_visualization)

    # 엣지 추가
    self.workflow.add_edge(START, "parse_query")
    self.workflow.add_edge("parse_query", "generate_sql")
    self.workflow.add_edge("generate_sql", "execute_query")
    self.workflow.add_edge("execute_query", "analyze_data")

    # 조건부 엣지: 시각화 필요 여부 판단
    self.workflow.add_conditional_edges(
        "analyze_data",
        self.check_visualization_need,
        {
            "need_viz": "visualize",
            "text_only": END
        }
    )

    self.workflow.add_edge("visualize", END)

    # 워크플로우 컴파일
    self.app = self.workflow.compile()
```

---

### 노드 함수 상세

#### 1. parse_sales_query(self, state: SalesAnalyticsState)
```python
def parse_sales_query(self, state: SalesAnalyticsState):
    """매출 관련 쿼리 파싱 및 기간/지역 추출"""
    query = state["query"]

    # 기간 추출 패턴
    period_patterns = {
        "지난달": "MONTH(CURRENT_DATE, '-1 month')",
        "이번달": "MONTH(CURRENT_DATE)",
        "지난 분기": "QUARTER(CURRENT_DATE, '-1 quarter')",
        "이번 분기": "QUARTER(CURRENT_DATE)",
        "작년": "YEAR(CURRENT_DATE, '-1 year')",
        "올해": "YEAR(CURRENT_DATE)"
    }

    # 지역 추출 패턴
    regions = ["서울", "경기", "부산", "대구", "인천", "광주", "대전", "울산"]

    extracted_info = {
        "period": None,
        "region": None,
        "keywords": []
    }

    # 기간 추출
    for period_text, sql_func in period_patterns.items():
        if period_text in query:
            extracted_info["period"] = sql_func
            break

    # 지역 추출
    for region in regions:
        if region in query:
            extracted_info["region"] = region
            break

    # 키워드 추출 (매출, 실적, 거래처 등)
    keywords = ["매출", "실적", "거래처", "제품", "목표", "달성률", "성장률"]
    extracted_info["keywords"] = [kw for kw in keywords if kw in query]

    # state 업데이트
    state["analysis"] = {"query_info": extracted_info}

    logger.info(f"Query parsed: {extracted_info}")
    return state
```

#### 2. text_to_sql(self, state: SalesAnalyticsState)
```python
def text_to_sql(self, state: SalesAnalyticsState):
    """자연어 쿼리를 SQL로 변환"""
    query = state["query"]
    query_info = state.get("analysis", {}).get("query_info", {})

    # 스키마 정보를 포함한 프롬프트 생성
    schema_text = self._format_schema_for_llm()

    prompt = self.prompts.get_prompt(
        category="text_to_sql",
        subcategory="sales_performance",
        user_query=query,
        schema_info=schema_text,
        extracted_info=json.dumps(query_info, ensure_ascii=False)
    )

    # LLM을 통한 SQL 생성
    response = self.llm.generate(
        prompt=prompt,
        model="openai_strict",  # SQL은 정확도가 중요하므로 temperature=0
        category="sql_generation"
    )

    sql_query = response["content"].strip()

    # SQL 검증
    if not self._validate_sql(sql_query):
        # 안전하지 않은 SQL이면 기본 쿼리로 대체
        sql_query = "SELECT * FROM sales_performance LIMIT 10"
        logger.warning("Unsafe SQL detected, using default query")

    state["sql_query"] = sql_query
    logger.info(f"Generated SQL: {sql_query}")

    return state
```

#### 3. execute_sql_query(self, state: SalesAnalyticsState)
```python
def execute_sql_query(self, state: SalesAnalyticsState):
    """SQL 쿼리 실행"""
    sql_query = state["sql_query"]

    # 적절한 데이터베이스 선택
    db_name = self._select_database(sql_query)
    db_path = self.db_paths[db_name]

    results = []
    error = None

    try:
        # SQLite 연결
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        cursor = conn.cursor()

        # 쿼리 실행
        cursor.execute(sql_query)

        # 결과 가져오기
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]

        # 컬럼 정보 저장
        if results:
            column_names = list(results[0].keys())
            state["analysis"] = state.get("analysis", {})
            state["analysis"]["columns"] = column_names

        conn.close()

    except Exception as e:
        error = str(e)
        logger.error(f"SQL execution error: {error}")
        results = []
        state["analysis"] = state.get("analysis", {})
        state["analysis"]["error"] = error

    state["query_results"] = results
    logger.info(f"Query returned {len(results)} rows")

    return state
```

#### 4. perform_analysis(self, state: SalesAnalyticsState)
```python
def perform_analysis(self, state: SalesAnalyticsState):
    """데이터 분석 수행"""
    results = state["query_results"]

    if not results:
        state["analysis"]["summary"] = "No data found"
        return state

    # Pandas DataFrame으로 변환
    df = pd.DataFrame(results)

    analysis = {
        "row_count": len(df),
        "columns": list(df.columns),
        "data_types": df.dtypes.to_dict(),
        "statistics": {}
    }

    # 숫자 컬럼에 대한 기본 통계
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns

    for col in numeric_columns:
        analysis["statistics"][col] = {
            "mean": float(df[col].mean()),
            "sum": float(df[col].sum()),
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "std": float(df[col].std()) if len(df) > 1 else 0
        }

    # Top 5 집계 (첫 번째 문자열 컬럼 기준)
    string_columns = df.select_dtypes(include=['object']).columns
    if len(string_columns) > 0 and len(numeric_columns) > 0:
        group_col = string_columns[0]
        value_col = numeric_columns[0]

        top_5 = df.groupby(group_col)[value_col].sum().nlargest(5)
        analysis["top_5"] = top_5.to_dict()

    # 월별/분기별 트렌드 분석 (날짜 컬럼이 있는 경우)
    date_columns = [col for col in df.columns if 'date' in col.lower() or '날짜' in col]
    if date_columns:
        try:
            df[date_columns[0]] = pd.to_datetime(df[date_columns[0]])
            df['year_month'] = df[date_columns[0]].dt.to_period('M')

            if len(numeric_columns) > 0:
                monthly_trend = df.groupby('year_month')[numeric_columns[0]].sum()
                analysis["monthly_trend"] = monthly_trend.to_dict()
        except:
            pass

    state["analysis"].update(analysis)
    logger.info(f"Analysis completed: {analysis.keys()}")

    return state
```

#### 5. create_visualization(self, state: SalesAnalyticsState)
```python
def create_visualization(self, state: SalesAnalyticsState):
    """시각화 구성 생성"""
    analysis = state.get("analysis", {})
    results = state["query_results"]

    viz_config = {
        "charts": [],
        "recommended_type": None
    }

    # 데이터가 없으면 시각화 불가
    if not results:
        state["visualization"] = viz_config
        return state

    # Top 5가 있으면 막대 차트 추천
    if "top_5" in analysis:
        viz_config["charts"].append({
            "type": "bar",
            "data": analysis["top_5"],
            "title": "상위 5개 항목",
            "x_label": list(analysis["top_5"].keys()),
            "y_label": "매출액"
        })
        viz_config["recommended_type"] = "bar"

    # 월별 트렌드가 있으면 라인 차트 추천
    if "monthly_trend" in analysis:
        viz_config["charts"].append({
            "type": "line",
            "data": analysis["monthly_trend"],
            "title": "월별 매출 트렌드",
            "x_label": "기간",
            "y_label": "매출액"
        })
        viz_config["recommended_type"] = "line"

    # 통계 정보가 있으면 요약 카드 추천
    if "statistics" in analysis and analysis["statistics"]:
        stat_cards = []
        for col, stats in analysis["statistics"].items():
            stat_cards.append({
                "title": col,
                "value": f"{stats['sum']:,.0f}",
                "sub_values": {
                    "평균": f"{stats['mean']:,.0f}",
                    "최대": f"{stats['max']:,.0f}",
                    "최소": f"{stats['min']:,.0f}"
                }
            })

        viz_config["summary_cards"] = stat_cards

    # 테이블 뷰 항상 포함
    viz_config["table"] = {
        "columns": list(results[0].keys()) if results else [],
        "rows": results[:100]  # 최대 100행만
    }

    state["visualization"] = viz_config
    logger.info(f"Visualization config created: {viz_config.get('recommended_type')}")

    return state
```

---

### 조건부 라우팅 함수

#### check_visualization_need(self, state: SalesAnalyticsState) -> str
```python
def check_visualization_need(self, state: SalesAnalyticsState) -> str:
    """시각화 필요 여부 판단"""
    query = state["query"].lower()
    results = state.get("query_results", [])

    # 시각화 관련 키워드
    viz_keywords = ["차트", "그래프", "시각화", "보여줘", "표시"]

    # 결과가 없으면 시각화 불필요
    if not results:
        return "text_only"

    # 키워드가 있거나 결과가 10행 이상이면 시각화 필요
    if any(keyword in query for keyword in viz_keywords) or len(results) > 10:
        return "need_viz"

    return "text_only"
```

---

### 보조 메서드

#### load_schema_info(self) -> Dict[str, Any]
```python
def load_schema_info(self) -> Dict[str, Any]:
    """데이터베이스 스키마 정보 로드"""
    schema_info = {}

    for db_name, db_path in self.db_paths.items():
        if not db_path.exists():
            logger.warning(f"Database not found: {db_path}")
            continue

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 테이블 목록 가져오기
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            schema_info[db_name] = {}

            for table in tables:
                table_name = table[0]

                # 컬럼 정보 가져오기
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                schema_info[db_name][table_name] = [
                    {
                        "name": col[1],
                        "type": col[2],
                        "nullable": not col[3],
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ]

            conn.close()

        except Exception as e:
            logger.error(f"Error loading schema for {db_name}: {e}")

    return schema_info
```

#### _validate_sql(self, sql: str) -> bool
```python
def _validate_sql(self, sql: str) -> bool:
    """SQL 쿼리 안전성 검증"""
    sql_upper = sql.upper()

    # 위험한 키워드 체크
    dangerous_keywords = [
        "DROP", "DELETE", "INSERT", "UPDATE", "CREATE",
        "ALTER", "TRUNCATE", "EXEC", "EXECUTE"
    ]

    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False

    # SELECT 문만 허용
    if not sql_upper.strip().startswith("SELECT"):
        return False

    return True
```

#### _select_database(self, sql: str) -> str
```python
def _select_database(self, sql: str) -> str:
    """SQL 쿼리 내용을 분석하여 적절한 데이터베이스 선택"""
    sql_lower = sql.lower()

    # 테이블명 기반 데이터베이스 선택
    if "clients_info" in sql_lower:
        return "clients_info"
    elif "clients" in sql_lower or "거래처" in sql_lower:
        return "clients"
    elif "target" in sql_lower or "목표" in sql_lower:
        return "sales_target"
    else:
        return "sales_performance"  # 기본값
```

#### _format_schema_for_llm(self) -> str
```python
def _format_schema_for_llm(self) -> str:
    """LLM이 이해하기 쉬운 형태로 스키마 정보 포맷팅"""
    schema_text = "Available databases and tables:\n\n"

    for db_name, tables in self.schema_info.items():
        schema_text += f"Database: {db_name}\n"

        for table_name, columns in tables.items():
            schema_text += f"  Table: {table_name}\n"
            schema_text += "    Columns:\n"

            for col in columns:
                pk = " (PRIMARY KEY)" if col["primary_key"] else ""
                nullable = " (NULLABLE)" if col["nullable"] else " (NOT NULL)"
                schema_text += f"      - {col['name']}: {col['type']}{pk}{nullable}\n"

        schema_text += "\n"

    return schema_text
```

---

### 메인 실행 메서드

#### execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]
```python
def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """에이전트 실행 메인 메서드"""

    # 초기 state 생성
    initial_state = {
        "query": input_data.get("query", ""),
        "sql_query": "",
        "query_results": [],
        "analysis": {},
        "visualization": {}
    }

    try:
        # 워크플로우 실행
        final_state = self.app.invoke(initial_state)

        # 결과 포맷팅
        result = {
            "success": True,
            "sql_query": final_state.get("sql_query"),
            "results": final_state.get("query_results"),
            "analysis": final_state.get("analysis"),
            "visualization": final_state.get("visualization"),
            "row_count": len(final_state.get("query_results", []))
        }

    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        result = {
            "success": False,
            "error": str(e),
            "results": [],
            "analysis": {},
            "visualization": {}
        }

    return result
```

---

## 2. Document Generation Agent

### 파일: `backend/service/agents/document_generation_agent.py`

#### 파일 목적
다양한 문서 타입(보고서, 계약서, 메모, 양식)을 자동 생성하는 에이전트

#### Imports 및 Dependencies
```python
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from datetime import datetime
import json
from pathlib import Path
import logging
from jinja2 import Template, Environment, FileSystemLoader
```

---

### State 정의

#### DocumentState(TypedDict)
```python
class DocumentState(TypedDict):
    document_type: str              # 문서 타입 (report, contract, memo, form)
    template_id: str                # 템플릿 식별자
    input_data: Dict[str, Any]      # 문서 생성을 위한 입력 데이터
    generated_content: str          # 생성된 문서 내용
    format_type: str                # 출력 형식 (pdf, docx, html, text)
    metadata: Dict[str, Any]        # 문서 메타데이터
    validation_errors: List[str]    # 검증 에러 목록
    final_document: Dict[str, Any]  # 최종 문서 출력
    execution_status: str           # 현재 실행 상태
```

---

### DocumentGenerationAgent 클래스

#### 클래스 초기화
```python
class DocumentGenerationAgent:
    def __init__(self):
        # LangGraph workflow 초기화
        self.workflow = StateGraph(DocumentState)

        # 템플릿 시스템 초기화
        self.template_dir = Path("backend/service/tools/templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True  # XSS 방지
        )

        # 템플릿 레지스트리
        self.template_registry = {
            "sales_report": {
                "template_file": "sales_report.html",
                "required_fields": ["period", "sales_data", "analysis"],
                "description": "매출 실적 보고서"
            },
            "compliance_report": {
                "template_file": "compliance_report.html",
                "required_fields": ["check_date", "violations", "recommendations"],
                "description": "컴플라이언스 검토 보고서"
            },
            "meeting_minutes": {
                "template_file": "meeting_minutes.html",
                "required_fields": ["date", "attendees", "agenda", "decisions"],
                "description": "회의록"
            },
            "purchase_order": {
                "template_file": "purchase_order.html",
                "required_fields": ["order_date", "vendor", "items", "total_amount"],
                "description": "구매 주문서"
            },
            "hr_notice": {
                "template_file": "hr_notice.html",
                "required_fields": ["title", "content", "effective_date"],
                "description": "HR 공지사항"
            }
        }

        # 그래프 구성
        self._build_graph()

        logger.info("DocumentGenerationAgent initialized")
```

#### 그래프 구성 (_build_graph)
```python
def _build_graph(self):
    """LangGraph 워크플로우 구성"""

    # 노드 추가
    self.workflow.add_node("identify_template", self.identify_document_template)
    self.workflow.add_node("validate_data", self.validate_input_data)
    self.workflow.add_node("prepare_data", self.prepare_document_data)
    self.workflow.add_node("generate_content", self.generate_document_content)
    self.workflow.add_node("format_document", self.format_final_document)
    self.workflow.add_node("add_metadata", self.add_document_metadata)
    self.workflow.add_node("handle_errors", self.handle_generation_errors)

    # 엣지 추가
    self.workflow.add_edge(START, "identify_template")
    self.workflow.add_edge("identify_template", "validate_data")

    # 조건부 엣지: 데이터 검증 결과에 따라
    self.workflow.add_conditional_edges(
        "validate_data",
        self.check_validation_status,
        {
            "valid": "prepare_data",
            "invalid": "handle_errors"
        }
    )

    self.workflow.add_edge("prepare_data", "generate_content")
    self.workflow.add_edge("generate_content", "format_document")
    self.workflow.add_edge("format_document", "add_metadata")
    self.workflow.add_edge("add_metadata", END)
    self.workflow.add_edge("handle_errors", END)

    # 워크플로우 컴파일
    self.app = self.workflow.compile()
```

---

### 노드 함수 상세

#### 1. identify_document_template(self, state: DocumentState)
```python
def identify_document_template(self, state: DocumentState):
    """적절한 문서 템플릿 식별"""
    document_type = state.get("document_type", "")
    template_id = state.get("template_id", "")

    # template_id가 명시적으로 제공된 경우
    if template_id and template_id in self.template_registry:
        state["template_id"] = template_id
        state["execution_status"] = "template_identified"
        logger.info(f"Using specified template: {template_id}")
        return state

    # document_type으로 템플릿 추론
    type_to_template = {
        "sales": "sales_report",
        "매출": "sales_report",
        "compliance": "compliance_report",
        "컴플라이언스": "compliance_report",
        "meeting": "meeting_minutes",
        "회의": "meeting_minutes",
        "purchase": "purchase_order",
        "구매": "purchase_order",
        "hr": "hr_notice",
        "인사": "hr_notice"
    }

    for key, template in type_to_template.items():
        if key in document_type.lower():
            state["template_id"] = template
            state["execution_status"] = "template_identified"
            logger.info(f"Inferred template: {template}")
            return state

    # 기본 템플릿 사용
    state["template_id"] = "sales_report"
    state["execution_status"] = "template_defaulted"
    logger.warning(f"No matching template for {document_type}, using default")

    return state
```

#### 2. validate_input_data(self, state: DocumentState)
```python
def validate_input_data(self, state: DocumentState):
    """입력 데이터 검증"""
    template_id = state["template_id"]
    input_data = state.get("input_data", {})
    validation_errors = []

    # 템플릿이 레지스트리에 있는지 확인
    if template_id not in self.template_registry:
        validation_errors.append(f"Unknown template: {template_id}")
        state["validation_errors"] = validation_errors
        state["execution_status"] = "validation_failed"
        return state

    # 필수 필드 확인
    required_fields = self.template_registry[template_id]["required_fields"]

    for field in required_fields:
        if field not in input_data or input_data[field] is None:
            validation_errors.append(f"Missing required field: {field}")

    # 데이터 타입 검증
    if "sales_data" in input_data and not isinstance(input_data["sales_data"], (list, dict)):
        validation_errors.append("sales_data must be a list or dict")

    if "attendees" in input_data and not isinstance(input_data["attendees"], list):
        validation_errors.append("attendees must be a list")

    if "items" in input_data and not isinstance(input_data["items"], list):
        validation_errors.append("items must be a list")

    # 날짜 형식 검증
    date_fields = ["date", "order_date", "check_date", "effective_date", "period"]
    for field in date_fields:
        if field in input_data:
            try:
                # ISO 형식이나 한국어 날짜 형식 허용
                if isinstance(input_data[field], str):
                    if not any(char in input_data[field] for char in ["-", "/", "년", "월", "일"]):
                        validation_errors.append(f"Invalid date format for {field}")
            except:
                validation_errors.append(f"Invalid date value for {field}")

    # 금액 필드 검증
    amount_fields = ["total_amount", "amount"]
    for field in amount_fields:
        if field in input_data:
            try:
                float(input_data[field])
            except:
                validation_errors.append(f"{field} must be a number")

    state["validation_errors"] = validation_errors
    state["execution_status"] = "validation_complete"

    if validation_errors:
        logger.warning(f"Validation errors: {validation_errors}")
    else:
        logger.info("Input data validation successful")

    return state
```

#### 3. prepare_document_data(self, state: DocumentState)
```python
def prepare_document_data(self, state: DocumentState):
    """문서 데이터 준비 및 전처리"""
    input_data = state["input_data"].copy()
    template_id = state["template_id"]

    # 날짜 포매팅
    date_fields = ["date", "order_date", "check_date", "effective_date"]
    for field in date_fields:
        if field in input_data:
            # ISO 형식을 한국어 형식으로 변환
            if isinstance(input_data[field], str) and "T" in input_data[field]:
                dt = datetime.fromisoformat(input_data[field].replace("Z", "+00:00"))
                input_data[field] = dt.strftime("%Y년 %m월 %d일")

    # 숫자 포매팅
    amount_fields = ["total_amount", "amount"]
    for field in amount_fields:
        if field in input_data:
            try:
                amount = float(input_data[field])
                # 천단위 구분자 추가
                input_data[f"{field}_formatted"] = f"{amount:,.0f}원"
            except:
                pass

    # 매출 데이터 처리
    if "sales_data" in input_data and isinstance(input_data["sales_data"], list):
        total_sales = 0
        for item in input_data["sales_data"]:
            if "amount" in item:
                amount = float(item["amount"])
                total_sales += amount
                item["amount_formatted"] = f"{amount:,.0f}원"

        input_data["total_sales"] = total_sales
        input_data["total_sales_formatted"] = f"{total_sales:,.0f}원"

    # 문서 번호 생성
    input_data["document_number"] = self._generate_document_number()

    # 생성 일시 추가
    input_data["generated_at"] = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")

    # 작성자 정보 (없으면 기본값)
    if "author" not in input_data:
        input_data["author"] = "시스템 자동 생성"

    state["input_data"] = input_data
    state["execution_status"] = "data_prepared"

    logger.info(f"Document data prepared for template: {template_id}")

    return state
```

#### 4. generate_document_content(self, state: DocumentState)
```python
def generate_document_content(self, state: DocumentState):
    """템플릿을 사용한 문서 내용 생성"""
    template_id = state["template_id"]
    input_data = state["input_data"]

    try:
        # 템플릿 파일 로드
        template_info = self.template_registry[template_id]
        template_file = template_info["template_file"]

        # Jinja2 템플릿 렌더링
        if self.template_dir.joinpath(template_file).exists():
            template = self.jinja_env.get_template(template_file)
            content = template.render(**input_data)
        else:
            # 템플릿 파일이 없으면 기본 템플릿 사용
            logger.warning(f"Template file not found: {template_file}")
            content = self._generate_fallback_content(template_id, input_data)

        state["generated_content"] = content
        state["execution_status"] = "content_generated"

        logger.info(f"Document content generated: {len(content)} characters")

    except Exception as e:
        logger.error(f"Error generating document content: {e}")
        state["generated_content"] = f"Error generating content: {str(e)}"
        state["execution_status"] = "generation_error"

    return state
```

#### 5. format_final_document(self, state: DocumentState)
```python
def format_final_document(self, state: DocumentState):
    """최종 문서 포맷팅"""
    content = state["generated_content"]
    format_type = state.get("format_type", "html")

    formatted_document = {
        "content": content,
        "format": format_type,
        "encoding": "utf-8"
    }

    # 포맷별 처리
    if format_type == "html":
        # HTML은 그대로 사용
        formatted_document["mime_type"] = "text/html"

    elif format_type == "text":
        # HTML 태그 제거 (간단한 변환)
        import re
        text_content = re.sub('<[^<]+?>', '', content)
        text_content = text_content.replace('&nbsp;', ' ')
        text_content = text_content.replace('&amp;', '&')
        formatted_document["content"] = text_content
        formatted_document["mime_type"] = "text/plain"

    elif format_type == "json":
        # JSON 형식으로 변환
        formatted_document["content"] = json.dumps({
            "template_id": state["template_id"],
            "data": state["input_data"],
            "generated_html": content
        }, ensure_ascii=False, indent=2)
        formatted_document["mime_type"] = "application/json"

    elif format_type == "pdf":
        # PDF 생성 (실제 구현 시 wkhtmltopdf, reportlab 등 사용)
        formatted_document["mime_type"] = "application/pdf"
        formatted_document["note"] = "PDF conversion requires additional library"

    elif format_type == "docx":
        # DOCX 생성 (실제 구현 시 python-docx 사용)
        formatted_document["mime_type"] = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        formatted_document["note"] = "DOCX conversion requires additional library"

    state["final_document"] = formatted_document
    state["execution_status"] = "formatting_complete"

    logger.info(f"Document formatted as {format_type}")

    return state
```

#### 6. add_document_metadata(self, state: DocumentState)
```python
def add_document_metadata(self, state: DocumentState):
    """문서 메타데이터 추가"""

    metadata = {
        "document_id": self._generate_document_id(),
        "template_id": state["template_id"],
        "document_type": state.get("document_type", "unknown"),
        "created_at": datetime.now().isoformat(),
        "format": state.get("format_type", "html"),
        "version": "1.0",
        "generator": "DocumentGenerationAgent",
        "status": "completed",
        "validation_passed": len(state.get("validation_errors", [])) == 0
    }

    # 입력 데이터에서 일부 메타데이터 추출
    input_data = state.get("input_data", {})
    if "author" in input_data:
        metadata["author"] = input_data["author"]
    if "document_number" in input_data:
        metadata["document_number"] = input_data["document_number"]

    # 문서 크기 정보
    if "final_document" in state and "content" in state["final_document"]:
        metadata["content_size"] = len(state["final_document"]["content"])

    state["metadata"] = metadata
    state["execution_status"] = "completed"

    logger.info(f"Document metadata added: {metadata['document_id']}")

    return state
```

#### 7. handle_generation_errors(self, state: DocumentState)
```python
def handle_generation_errors(self, state: DocumentState):
    """문서 생성 에러 처리"""

    validation_errors = state.get("validation_errors", [])

    error_document = {
        "content": f"<div class='error'>문서 생성 실패: {', '.join(validation_errors)}</div>",
        "format": "html",
        "mime_type": "text/html",
        "error": True,
        "errors": validation_errors
    }

    error_metadata = {
        "document_id": self._generate_document_id(),
        "status": "failed",
        "error_count": len(validation_errors),
        "errors": validation_errors,
        "created_at": datetime.now().isoformat()
    }

    state["final_document"] = error_document
    state["metadata"] = error_metadata
    state["execution_status"] = "error_handled"

    logger.error(f"Document generation failed with {len(validation_errors)} errors")

    return state
```

---

### 조건부 라우팅 함수

#### check_validation_status(self, state: DocumentState) -> str
```python
def check_validation_status(self, state: DocumentState) -> str:
    """검증 상태 확인"""
    validation_errors = state.get("validation_errors", [])

    if len(validation_errors) == 0:
        return "valid"
    else:
        return "invalid"
```

---

### 보조 메서드

#### _generate_fallback_content(self, template_id: str, data: Dict) -> str
```python
def _generate_fallback_content(self, template_id: str, data: Dict) -> str:
    """템플릿 파일이 없을 때 기본 컨텐츠 생성"""

    content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{self.template_registry.get(template_id, {}).get('description', '문서')}</title>
        <style>
            body {{ font-family: 'Noto Sans KR', sans-serif; margin: 40px; }}
            h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
            .metadata {{ background: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .content {{ line-height: 1.6; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background: #007bff; color: white; }}
        </style>
    </head>
    <body>
        <h1>{self.template_registry.get(template_id, {}).get('description', '문서')}</h1>

        <div class="metadata">
            <strong>문서번호:</strong> {data.get('document_number', 'N/A')}<br>
            <strong>생성일시:</strong> {data.get('generated_at', 'N/A')}<br>
            <strong>작성자:</strong> {data.get('author', 'N/A')}
        </div>

        <div class="content">
    """

    # 템플릿별 기본 컨텐츠
    if template_id == "sales_report":
        content += f"""
            <h2>매출 실적</h2>
            <p>기간: {data.get('period', 'N/A')}</p>

            <table>
                <thead>
                    <tr><th>항목</th><th>금액</th></tr>
                </thead>
                <tbody>
        """

        sales_data = data.get('sales_data', [])
        for item in sales_data:
            content += f"""
                    <tr>
                        <td>{item.get('item', 'N/A')}</td>
                        <td>{item.get('amount_formatted', item.get('amount', 0))}</td>
                    </tr>
            """

        content += f"""
                </tbody>
                <tfoot>
                    <tr>
                        <th>총계</th>
                        <th>{data.get('total_sales_formatted', '0원')}</th>
                    </tr>
                </tfoot>
            </table>

            <h3>분석</h3>
            <p>{data.get('analysis', '분석 내용이 없습니다.')}</p>
        """

    elif template_id == "compliance_report":
        content += f"""
            <h2>컴플라이언스 검토 결과</h2>
            <p>검토일: {data.get('check_date', 'N/A')}</p>

            <h3>위반 사항</h3>
            <ul>
        """

        violations = data.get('violations', [])
        if violations:
            for violation in violations:
                content += f"<li>{violation}</li>"
        else:
            content += "<li>위반 사항 없음</li>"

        content += f"""
            </ul>

            <h3>권고 사항</h3>
            <ul>
        """

        recommendations = data.get('recommendations', [])
        if recommendations:
            for rec in recommendations:
                content += f"<li>{rec}</li>"
        else:
            content += "<li>권고 사항 없음</li>"

        content += "</ul>"

    # 기타 템플릿들도 유사하게 처리...

    content += """
        </div>
    </body>
    </html>
    """

    return content
```

#### _generate_document_number(self) -> str
```python
def _generate_document_number(self) -> str:
    """문서 번호 생성"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import random
    random_suffix = random.randint(1000, 9999)
    return f"DOC-{timestamp}-{random_suffix}"
```

#### _generate_document_id(self) -> str
```python
def _generate_document_id(self) -> str:
    """문서 고유 ID 생성"""
    import uuid
    return str(uuid.uuid4())
```

#### _get_required_fields(self, template_id: str) -> List[str]
```python
def _get_required_fields(self, template_id: str) -> List[str]:
    """템플릿의 필수 필드 반환"""
    if template_id in self.template_registry:
        return self.template_registry[template_id]["required_fields"]
    return []
```

---

### 메인 실행 메서드

#### execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]
```python
def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """에이전트 실행 메인 메서드"""

    # 초기 state 생성
    initial_state = {
        "document_type": input_data.get("document_type", ""),
        "template_id": input_data.get("template_id", ""),
        "input_data": input_data.get("data", {}),
        "format_type": input_data.get("format", "html"),
        "generated_content": "",
        "metadata": {},
        "validation_errors": [],
        "final_document": {},
        "execution_status": "started"
    }

    try:
        # 워크플로우 실행
        final_state = self.app.invoke(initial_state)

        # 결과 포맷팅
        result = {
            "success": final_state["execution_status"] == "completed",
            "document": final_state.get("final_document", {}),
            "metadata": final_state.get("metadata", {}),
            "validation_errors": final_state.get("validation_errors", [])
        }

    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        result = {
            "success": False,
            "error": str(e),
            "document": {},
            "metadata": {},
            "validation_errors": [str(e)]
        }

    return result
```

---

## 3. Search Agent

### 파일: `backend/service/agents/search_agent.py`

#### 파일 목적
회사 내부 정보 검색을 위한 서브그래프 에이전트. HR 정보와 내부 규정을 검색합니다.

#### Imports 및 Dependencies
```python
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
import chromadb
from chromadb.config import Settings
import sqlite3
import asyncio
from pathlib import Path
import logging
from datetime import datetime
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer
```

---

### State 정의

#### SearchState(TypedDict)
```python
class SearchState(TypedDict):
    query: str                              # 검색 쿼리
    search_type: str                        # 검색 타입 (hr_info, hr_rules, both)
    filters: Dict[str, Any]                 # 검색 필터
    hr_results: List[Dict[str, Any]]        # HR 정보 검색 결과
    rules_results: List[Dict[str, Any]]     # 규정 검색 결과
    reranked_results: List[Dict[str, Any]]  # 리랭킹된 결과
    relevance_scores: Dict[str, float]      # 관련성 점수
    sources: List[str]                      # 데이터 소스
    final_results: Dict[str, Any]           # 최종 검색 결과
    execution_status: str                   # 실행 상태
```

---

### SearchAgent 클래스

#### 클래스 초기화
```python
class SearchAgent:
    def __init__(self):
        # LangGraph workflow 초기화
        self.workflow = StateGraph(SearchState)

        # 데이터베이스 경로 설정
        self.hr_rules_db = Path("database/storage/hr_rules/chromadb/chroma.sqlite3")
        self.hr_info_db = Path("database/storage/hr_information/hr_data")

        # ChromaDB 클라이언트 초기화
        self.chroma_client = None
        if self.hr_rules_db.exists():
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.hr_rules_db.parent),
                settings=Settings(anonymized_telemetry=False)
            )

        # 임베딩 모델 초기화
        try:
            self.embedding_model = SentenceTransformer('upskyy/kf-deberta-multitask')  # Kure-v1
            logger.info("Kure-v1 embedding model loaded")
        except:
            logger.warning("Failed to load Kure-v1, using default model")
            self.embedding_model = None

        # 리랭킹 모델 초기화
        try:
            self.reranker_tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-reranker-v2-m3')
            self.reranker_model = AutoModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-v2-m3')
            self.reranker_model.eval()
            logger.info("BGE reranker model loaded")
        except:
            logger.warning("Failed to load reranker model")
            self.reranker_model = None
            self.reranker_tokenizer = None

        # 그래프 구성
        self._build_graph()

        logger.info("SearchAgent initialized")
```

#### 그래프 구성 (_build_graph)
```python
def _build_graph(self):
    """LangGraph 워크플로우 구성"""

    # 노드 추가
    self.workflow.add_node("analyze_query", self.analyze_search_query)
    self.workflow.add_node("search_hr_info", self.search_hr_information)
    self.workflow.add_node("search_hr_rules", self.search_hr_rules)
    self.workflow.add_node("merge_results", self.merge_search_results)
    self.workflow.add_node("rerank_results", self.rerank_with_model)
    self.workflow.add_node("format_response", self.format_final_response)

    # 엣지 추가
    self.workflow.add_edge(START, "analyze_query")

    # 조건부 엣지: 검색 타입에 따라
    self.workflow.add_conditional_edges(
        "analyze_query",
        self.determine_search_targets,
        {
            "hr_info_only": "search_hr_info",
            "hr_rules_only": "search_hr_rules",
            "both": "search_hr_info"
        }
    )

    # HR 정보 검색 후 라우팅
    self.workflow.add_conditional_edges(
        "search_hr_info",
        lambda state: "search_hr_rules" if state.get("search_type") == "both" else "merge_results",
        {
            "search_hr_rules": "search_hr_rules",
            "merge_results": "merge_results"
        }
    )

    self.workflow.add_edge("search_hr_rules", "merge_results")
    self.workflow.add_edge("merge_results", "rerank_results")
    self.workflow.add_edge("rerank_results", "format_response")
    self.workflow.add_edge("format_response", END)

    # 워크플로우 컴파일
    self.app = self.workflow.compile()
```

---

### 노드 함수 상세

#### 1. analyze_search_query(self, state: SearchState)
```python
def analyze_search_query(self, state: SearchState):
    """검색 쿼리 분석 및 키워드 추출"""
    query = state["query"]

    # 검색 타입 추론
    hr_keywords = ["직원", "사원", "팀", "부서", "연락처", "이메일", "전화"]
    rule_keywords = ["규정", "규칙", "정책", "가이드", "지침", "컴플라이언스"]

    hr_score = sum(1 for kw in hr_keywords if kw in query)
    rule_score = sum(1 for kw in rule_keywords if kw in query)

    if hr_score > 0 and rule_score > 0:
        search_type = "both"
    elif hr_score > rule_score:
        search_type = "hr_info"
    elif rule_score > hr_score:
        search_type = "hr_rules"
    else:
        search_type = "both"  # 기본값

    # 키워드 추출
    keywords = self._extract_keywords(query)

    # 필터 생성
    filters = {}

    # 부서 필터
    departments = ["영업", "마케팅", "개발", "인사", "재무", "법무", "연구"]
    for dept in departments:
        if dept in query:
            filters["department"] = dept
            break

    # 직급 필터
    positions = ["대표", "이사", "부장", "차장", "과장", "대리", "사원"]
    for pos in positions:
        if pos in query:
            filters["position"] = pos
            break

    state["search_type"] = search_type
    state["filters"] = filters
    state["execution_status"] = "query_analyzed"

    logger.info(f"Query analyzed - Type: {search_type}, Filters: {filters}")

    return state
```

#### 2. search_hr_information(self, state: SearchState)
```python
def search_hr_information(self, state: SearchState):
    """HR 정보 데이터베이스 검색"""
    query = state["query"]
    filters = state.get("filters", {})
    results = []

    if not self.hr_info_db.exists():
        logger.warning("HR info database not found")
        state["hr_results"] = []
        return state

    try:
        conn = sqlite3.connect(self.hr_info_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 기본 쿼리 구성
        base_query = """
            SELECT * FROM employees
            WHERE 1=1
        """

        params = []

        # 키워드 검색 (이름, 부서, 직급에서)
        keywords = self._extract_keywords(query)
        if keywords:
            keyword_conditions = []
            for kw in keywords:
                keyword_conditions.append(
                    "(name LIKE ? OR department LIKE ? OR position LIKE ? OR skills LIKE ?)"
                )
                params.extend([f"%{kw}%"] * 4)

            if keyword_conditions:
                base_query += f" AND ({' OR '.join(keyword_conditions)})"

        # 필터 적용
        if "department" in filters:
            base_query += " AND department = ?"
            params.append(filters["department"])

        if "position" in filters:
            base_query += " AND position = ?"
            params.append(filters["position"])

        # 쿼리 실행
        cursor.execute(base_query + " LIMIT 50", params)
        rows = cursor.fetchall()

        # 결과 포맷팅
        for row in rows:
            result = dict(row)
            result["source"] = "hr_database"
            result["relevance_score"] = 0.0  # 나중에 계산
            results.append(result)

        conn.close()

        logger.info(f"Found {len(results)} HR records")

    except Exception as e:
        logger.error(f"Error searching HR database: {e}")

    state["hr_results"] = results
    state["sources"] = state.get("sources", []) + ["hr_database"]

    return state
```

#### 3. search_hr_rules(self, state: SearchState)
```python
def search_hr_rules(self, state: SearchState):
    """HR 규정 벡터 데이터베이스 검색"""
    query = state["query"]
    results = []

    if not self.chroma_client:
        logger.warning("ChromaDB client not initialized")
        state["rules_results"] = []
        return state

    try:
        # 컬렉션 가져오기
        collection = self.chroma_client.get_collection("hr_rules")

        # 쿼리 임베딩 생성
        if self.embedding_model:
            query_embedding = self.embedding_model.encode(query).tolist()

            # 벡터 검색
            search_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=20,
                include=["documents", "metadatas", "distances"]
            )
        else:
            # 텍스트 검색 (fallback)
            search_results = collection.query(
                query_texts=[query],
                n_results=20,
                include=["documents", "metadatas", "distances"]
            )

        # 결과 포맷팅
        if search_results and "documents" in search_results:
            documents = search_results["documents"][0]
            metadatas = search_results.get("metadatas", [[]])[0]
            distances = search_results.get("distances", [[]])[0]

            for i, doc in enumerate(documents):
                result = {
                    "content": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else 1.0,
                    "relevance_score": 1.0 - (distances[i] if i < len(distances) else 1.0),
                    "source": "hr_rules"
                }
                results.append(result)

        logger.info(f"Found {len(results)} rule documents")

    except Exception as e:
        logger.error(f"Error searching rules database: {e}")

    state["rules_results"] = results
    state["sources"] = state.get("sources", []) + ["hr_rules"]

    return state
```

#### 4. merge_search_results(self, state: SearchState)
```python
def merge_search_results(self, state: SearchState):
    """여러 소스의 검색 결과 병합"""
    hr_results = state.get("hr_results", [])
    rules_results = state.get("rules_results", [])

    # 모든 결과 합치기
    all_results = []

    # HR 결과 추가
    for result in hr_results:
        result["result_type"] = "hr_info"
        all_results.append(result)

    # 규정 결과 추가
    for result in rules_results:
        result["result_type"] = "hr_rule"
        all_results.append(result)

    # 초기 관련성 점수 계산
    query = state["query"]
    query_keywords = set(self._extract_keywords(query))

    for result in all_results:
        # 키워드 기반 점수 계산
        if result["result_type"] == "hr_info":
            text = f"{result.get('name', '')} {result.get('department', '')} {result.get('position', '')}"
        else:
            text = result.get("content", "")

        result_keywords = set(self._extract_keywords(text))
        overlap = len(query_keywords & result_keywords)

        # 기존 점수가 있으면 조합, 없으면 키워드 점수 사용
        if "relevance_score" in result and result["relevance_score"] > 0:
            result["relevance_score"] = (result["relevance_score"] + (overlap / max(len(query_keywords), 1))) / 2
        else:
            result["relevance_score"] = overlap / max(len(query_keywords), 1)

    # 점수 기준 정렬
    all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    state["reranked_results"] = all_results[:50]  # 상위 50개만 유지
    state["execution_status"] = "results_merged"

    logger.info(f"Merged {len(all_results)} total results")

    return state
```

#### 5. rerank_with_model(self, state: SearchState)
```python
def rerank_with_model(self, state: SearchState):
    """ML 모델을 사용한 결과 리랭킹"""
    results = state.get("reranked_results", [])
    query = state["query"]

    if not results:
        return state

    # 리랭킹 모델이 없으면 스킵
    if not self.reranker_model or not self.reranker_tokenizer:
        logger.info("Reranker not available, using original scores")
        return state

    try:
        # 리랭킹을 위한 텍스트 쌍 준비
        pairs = []
        for result in results:
            if result["result_type"] == "hr_info":
                text = f"{result.get('name', '')} - {result.get('department', '')} {result.get('position', '')}"
            else:
                text = result.get("content", "")[:500]  # 처음 500자만

            pairs.append([query, text])

        # 배치 토크나이징
        with torch.no_grad():
            inputs = self.reranker_tokenizer(
                pairs,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )

            # 리랭킹 점수 계산
            scores = self.reranker_model(**inputs).logits.squeeze(-1)
            scores = torch.sigmoid(scores).cpu().numpy()

        # 점수 업데이트
        for i, score in enumerate(scores):
            if i < len(results):
                # 기존 점수와 리랭킹 점수 조합
                old_score = results[i].get("relevance_score", 0)
                results[i]["relevance_score"] = (old_score + float(score)) / 2
                results[i]["rerank_score"] = float(score)

        # 새로운 점수로 재정렬
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        state["reranked_results"] = results[:30]  # 상위 30개만 유지

        logger.info("Results reranked with ML model")

    except Exception as e:
        logger.error(f"Error during reranking: {e}")

    return state
```

#### 6. format_final_response(self, state: SearchState)
```python
def format_final_response(self, state: SearchState):
    """최종 응답 포맷팅"""
    results = state.get("reranked_results", [])

    # 타입별로 분류
    hr_info_results = [r for r in results if r.get("result_type") == "hr_info"]
    rule_results = [r for r in results if r.get("result_type") == "hr_rule"]

    # 최종 응답 구성
    final_response = {
        "total_results": len(results),
        "search_type": state.get("search_type"),
        "sources_used": state.get("sources", []),
        "hr_information": {
            "count": len(hr_info_results),
            "results": hr_info_results[:10]  # 상위 10개
        },
        "hr_rules": {
            "count": len(rule_results),
            "results": rule_results[:10]  # 상위 10개
        },
        "top_results": results[:5],  # 전체 상위 5개
        "filters_applied": state.get("filters", {}),
        "execution_status": "completed"
    }

    # 관련성 점수 통계
    if results:
        scores = [r.get("relevance_score", 0) for r in results]
        final_response["relevance_stats"] = {
            "max": max(scores),
            "min": min(scores),
            "avg": sum(scores) / len(scores)
        }

    state["final_results"] = final_response
    state["execution_status"] = "completed"

    logger.info(f"Final response formatted with {len(results)} results")

    return state
```

---

### 조건부 라우팅 함수

#### determine_search_targets(self, state: SearchState) -> str
```python
def determine_search_targets(self, state: SearchState) -> str:
    """검색 대상 결정"""
    search_type = state.get("search_type", "both")

    if search_type == "hr_info":
        return "hr_info_only"
    elif search_type == "hr_rules":
        return "hr_rules_only"
    else:
        return "both"
```

---

### 보조 메서드

#### _extract_keywords(self, query: str) -> List[str]
```python
def _extract_keywords(self, query: str) -> List[str]:
    """쿼리에서 키워드 추출"""
    # 불용어 제거
    stopwords = ["의", "를", "을", "가", "이", "은", "는", "와", "과", "에", "에서", "으로", "로"]

    # 단어 분리 (간단한 공백 기반)
    words = query.split()

    # 불용어 제거 및 2글자 이상만 유지
    keywords = [w for w in words if w not in stopwords and len(w) >= 2]

    return keywords
```

#### _build_hr_info_query(self, query: str, filters: Dict) -> str
```python
def _build_hr_info_query(self, query: str, filters: Dict) -> str:
    """HR 정보 검색을 위한 SQL 쿼리 생성"""
    base = "SELECT * FROM employees WHERE 1=1"
    conditions = []

    # 키워드 조건
    keywords = self._extract_keywords(query)
    if keywords:
        keyword_conds = []
        for kw in keywords:
            keyword_conds.append(
                f"(name LIKE '%{kw}%' OR department LIKE '%{kw}%' OR position LIKE '%{kw}%')"
            )
        if keyword_conds:
            conditions.append(f"({' OR '.join(keyword_conds)})")

    # 필터 조건
    if "department" in filters:
        conditions.append(f"department = '{filters['department']}'")

    if "position" in filters:
        conditions.append(f"position = '{filters['position']}'")

    # 조건 결합
    if conditions:
        base += " AND " + " AND ".join(conditions)

    base += " LIMIT 50"

    return base
```

---

### 메인 실행 메서드

#### execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]
```python
def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """에이전트 실행 메인 메서드"""

    # 초기 state 생성
    initial_state = {
        "query": input_data.get("query", ""),
        "search_type": input_data.get("search_type", ""),  # 명시적 지정 가능
        "filters": input_data.get("filters", {}),
        "hr_results": [],
        "rules_results": [],
        "reranked_results": [],
        "relevance_scores": {},
        "sources": [],
        "final_results": {},
        "execution_status": "started"
    }

    try:
        # 워크플로우 실행
        final_state = self.app.invoke(initial_state)

        # 결과 반환
        result = final_state.get("final_results", {})
        result["success"] = True

    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        result = {
            "success": False,
            "error": str(e),
            "total_results": 0,
            "hr_information": {"count": 0, "results": []},
            "hr_rules": {"count": 0, "results": []},
            "top_results": []
        }

    return result
```

---

## 4. Compliance Check Agent

### 파일: `backend/service/agents/compliance_check_agent.py`

#### 파일 목적
제약회사 규정 준수 여부를 확인하는 컴플라이언스 체크 에이전트

#### Imports 및 Dependencies
```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any
import chromadb
from datetime import datetime
import logging
```

---

### State 정의

#### ComplianceState(TypedDict)
```python
class ComplianceState(TypedDict):
    checkpoint: str                     # 컴플라이언스 체크포인트
    document_to_check: Dict[str, Any]   # 검토할 문서/데이터
    relevant_regulations: List[Dict]     # 관련 규정들
    violations: List[Dict]              # 발견된 위반사항
    compliance_score: float             # 컴플라이언스 점수 (0-100)
    report: str                         # 컴플라이언스 보고서
```

---

### ComplianceCheckAgent 클래스

#### 클래스 초기화
```python
class ComplianceCheckAgent:
    def __init__(self):
        # LangGraph workflow 초기화
        self.workflow = StateGraph(ComplianceState)

        # ChromaDB 클라이언트 초기화 (규정 데이터베이스)
        self.chroma_client = chromadb.PersistentClient(
            path="database/storage/compliance/chromadb"
        )

        # KPBMA 규정 컬렉션
        self.regulations_collection = self.chroma_client.get_or_create_collection(
            name="kpbma_regulations",
            metadata={"description": "한국제약바이오협회 규정"}
        )

        # 그래프 구성
        self._build_graph()

        logger.info("ComplianceCheckAgent initialized")
```

#### 그래프 구성 (_build_graph)
```python
def _build_graph(self):
    """LangGraph 워크플로우 구성"""

    # 노드 추가
    self.workflow.add_node("extract_checkpoints", self.extract_compliance_checkpoints)
    self.workflow.add_node("search_regulations", self.vector_search_regulations)
    self.workflow.add_node("cross_reference", self.cross_reference_rules)
    self.workflow.add_node("evaluate_compliance", self.evaluate_compliance_status)
    self.workflow.add_node("generate_report", self.generate_compliance_report)

    # 엣지 추가
    self.workflow.add_edge(START, "extract_checkpoints")
    self.workflow.add_edge("extract_checkpoints", "search_regulations")
    self.workflow.add_edge("search_regulations", "cross_reference")
    self.workflow.add_edge("cross_reference", "evaluate_compliance")

    # 조건부 엣지: 위반사항 발견 여부
    self.workflow.add_conditional_edges(
        "evaluate_compliance",
        self.check_violations,
        {
            "violation_found": "generate_report",
            "compliant": END
        }
    )

    self.workflow.add_edge("generate_report", END)

    # 워크플로우 컴파일
    self.app = self.workflow.compile()
```

---

### 노드 함수 상세

#### 1. extract_compliance_checkpoints(self, state: ComplianceState)
```python
def extract_compliance_checkpoints(self, state: ComplianceState):
    """문서에서 컴플라이언스 체크포인트 추출"""
    document = state.get("document_to_check", {})

    checkpoints = []

    # 리베이트 관련 체크포인트
    if "rebate" in str(document).lower() or "할인" in str(document).lower():
        checkpoints.append({
            "type": "rebate",
            "description": "리베이트 및 할인 정책",
            "severity": "high"
        })

    # 마케팅 비용 관련
    if "marketing" in str(document).lower() or "마케팅" in str(document).lower():
        checkpoints.append({
            "type": "marketing_expense",
            "description": "마케팅 비용 집행",
            "severity": "medium"
        })

    # 샘플 제공 관련
    if "sample" in str(document).lower() or "샘플" in str(document).lower():
        checkpoints.append({
            "type": "sample_provision",
            "description": "의약품 샘플 제공",
            "severity": "high"
        })

    # 학술대회 지원 관련
    if "conference" in str(document).lower() or "학술" in str(document).lower():
        checkpoints.append({
            "type": "conference_support",
            "description": "학술대회 지원",
            "severity": "medium"
        })

    # 금액 관련 (임계값 체크)
    if "amount" in document or "금액" in document:
        amount = document.get("amount", document.get("금액", 0))
        if amount > 1000000:  # 100만원 초과
            checkpoints.append({
                "type": "high_value_transaction",
                "description": "고액 거래",
                "severity": "high",
                "amount": amount
            })

    state["checkpoint"] = checkpoints
    logger.info(f"Extracted {len(checkpoints)} checkpoints")

    return state
```

#### 2. vector_search_regulations(self, state: ComplianceState)
```python
def vector_search_regulations(self, state: ComplianceState):
    """관련 규정 벡터 검색"""
    checkpoints = state.get("checkpoint", [])

    all_regulations = []

    for checkpoint in checkpoints:
        # 체크포인트별 쿼리 생성
        query = f"{checkpoint['type']} {checkpoint['description']}"

        # ChromaDB 벡터 검색
        results = self.regulations_collection.query(
            query_texts=[query],
            n_results=5,
            include=["documents", "metadatas", "distances"]
        )

        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                regulation = {
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "relevance": 1.0 - results["distances"][0][i],
                    "checkpoint_type": checkpoint["type"]
                }
                all_regulations.append(regulation)

    # 관련성 점수로 정렬
    all_regulations.sort(key=lambda x: x["relevance"], reverse=True)

    state["relevant_regulations"] = all_regulations[:10]  # 상위 10개
    logger.info(f"Found {len(all_regulations)} relevant regulations")

    return state
```

#### 3. cross_reference_rules(self, state: ComplianceState)
```python
def cross_reference_rules(self, state: ComplianceState):
    """규정과 문서 교차 검증"""
    document = state.get("document_to_check", {})
    regulations = state.get("relevant_regulations", [])

    violations = []

    for regulation in regulations:
        # 규정별 위반 체크 로직
        reg_content = regulation["content"].lower()

        # 리베이트 규정 위반 체크
        if "리베이트" in reg_content:
            if "rebate" in str(document).lower() or "할인" in str(document).lower():
                # 허용된 할인율 체크 (예: 10% 초과 금지)
                if "discount_rate" in document:
                    if document["discount_rate"] > 10:
                        violations.append({
                            "regulation": regulation["content"][:200],
                            "violation_type": "excessive_rebate",
                            "description": f"할인율 {document['discount_rate']}%는 허용 한도 10% 초과",
                            "severity": "high"
                        })

        # 금액 한도 위반 체크
        if "한도" in reg_content and "amount" in document:
            # 규정에서 한도 추출 (간단한 패턴 매칭)
            import re
            limit_match = re.search(r'(\d+)만원', reg_content)
            if limit_match:
                limit = int(limit_match.group(1)) * 10000
                if document["amount"] > limit:
                    violations.append({
                        "regulation": regulation["content"][:200],
                        "violation_type": "amount_limit_exceeded",
                        "description": f"금액 {document['amount']:,}원은 한도 {limit:,}원 초과",
                        "severity": "high"
                    })

        # 샘플 제공 규정 위반
        if "샘플" in reg_content and "sample" in str(document).lower():
            if "quantity" in document and document["quantity"] > 10:
                violations.append({
                    "regulation": regulation["content"][:200],
                    "violation_type": "excessive_samples",
                    "description": f"샘플 수량 {document['quantity']}개는 허용 한도 초과",
                    "severity": "medium"
                })

        # 학술대회 지원 규정
        if "학술" in reg_content and "conference" in str(document).lower():
            if "sponsorship_type" in document:
                if document["sponsorship_type"] not in ["registration", "travel"]:
                    violations.append({
                        "regulation": regulation["content"][:200],
                        "violation_type": "invalid_sponsorship",
                        "description": f"지원 유형 '{document['sponsorship_type']}'은 허용되지 않음",
                        "severity": "medium"
                    })

    state["violations"] = violations
    logger.info(f"Found {len(violations)} violations")

    return state
```

#### 4. evaluate_compliance_status(self, state: ComplianceState)
```python
def evaluate_compliance_status(self, state: ComplianceState):
    """전체 컴플라이언스 상태 평가"""
    violations = state.get("violations", [])

    # 컴플라이언스 점수 계산 (100점 만점)
    score = 100.0

    for violation in violations:
        if violation["severity"] == "high":
            score -= 20
        elif violation["severity"] == "medium":
            score -= 10
        else:
            score -= 5

    # 최소 0점
    score = max(0, score)

    # 상태 평가
    if score >= 90:
        status = "excellent"
        risk_level = "low"
    elif score >= 70:
        status = "good"
        risk_level = "medium"
    elif score >= 50:
        status = "needs_improvement"
        risk_level = "high"
    else:
        status = "critical"
        risk_level = "critical"

    state["compliance_score"] = score
    state["compliance_status"] = status
    state["risk_level"] = risk_level

    logger.info(f"Compliance score: {score}, Status: {status}")

    return state
```

#### 5. generate_compliance_report(self, state: ComplianceState)
```python
def generate_compliance_report(self, state: ComplianceState):
    """컴플라이언스 검토 보고서 생성"""
    violations = state.get("violations", [])
    score = state.get("compliance_score", 100)
    status = state.get("compliance_status", "unknown")
    risk_level = state.get("risk_level", "unknown")

    # 보고서 헤더
    report = f"""
# 컴플라이언스 검토 보고서

## 검토 일시
{datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}

## 종합 평가
- **컴플라이언스 점수**: {score:.1f}/100
- **상태**: {self._translate_status(status)}
- **리스크 수준**: {self._translate_risk(risk_level)}

## 위반 사항 상세
"""

    if violations:
        # 심각도별 분류
        high_violations = [v for v in violations if v["severity"] == "high"]
        medium_violations = [v for v in violations if v["severity"] == "medium"]
        low_violations = [v for v in violations if v["severity"] == "low"]

        if high_violations:
            report += "\n### 🔴 고위험 위반사항\n"
            for v in high_violations:
                report += f"- **{v['violation_type']}**: {v['description']}\n"
                report += f"  - 관련 규정: {v['regulation'][:100]}...\n"

        if medium_violations:
            report += "\n### 🟡 중위험 위반사항\n"
            for v in medium_violations:
                report += f"- **{v['violation_type']}**: {v['description']}\n"
                report += f"  - 관련 규정: {v['regulation'][:100]}...\n"

        if low_violations:
            report += "\n### 🟢 저위험 위반사항\n"
            for v in low_violations:
                report += f"- **{v['violation_type']}**: {v['description']}\n"
                report += f"  - 관련 규정: {v['regulation'][:100]}...\n"
    else:
        report += "\n✅ 위반사항이 발견되지 않았습니다.\n"

    # 권고사항
    report += "\n## 권고사항\n"

    if score < 50:
        report += "- 즉시 법무팀 검토가 필요합니다.\n"
        report += "- 관련 거래를 중단하고 재검토하시기 바랍니다.\n"
    elif score < 70:
        report += "- 일부 조정이 필요합니다.\n"
        report += "- 컴플라이언스 팀과 상의하시기 바랍니다.\n"
    elif score < 90:
        report += "- 경미한 개선사항이 있습니다.\n"
        report += "- 정기 검토 시 확인이 필요합니다.\n"
    else:
        report += "- 현재 규정을 잘 준수하고 있습니다.\n"
        report += "- 정기적인 모니터링을 계속하시기 바랍니다.\n"

    # 다음 단계
    report += "\n## 다음 단계\n"
    if violations:
        report += "1. 위반사항에 대한 시정 계획 수립\n"
        report += "2. 관련 부서와 협의\n"
        report += "3. 시정 조치 이행\n"
        report += "4. 재검토 실시\n"
    else:
        report += "1. 정기 검토 일정 확인\n"
        report += "2. 규정 변경사항 모니터링\n"

    state["report"] = report
    logger.info("Compliance report generated")

    return state
```

---

### 조건부 라우팅 함수

#### check_violations(self, state: ComplianceState) -> str
```python
def check_violations(self, state: ComplianceState) -> str:
    """위반사항 존재 여부 확인"""
    violations = state.get("violations", [])

    if len(violations) > 0:
        return "violation_found"
    else:
        return "compliant"
```

---

### 보조 메서드

#### _translate_status(self, status: str) -> str
```python
def _translate_status(self, status: str) -> str:
    """상태 한글 번역"""
    translations = {
        "excellent": "우수",
        "good": "양호",
        "needs_improvement": "개선 필요",
        "critical": "심각"
    }
    return translations.get(status, status)
```

#### _translate_risk(self, risk: str) -> str
```python
def _translate_risk(self, risk: str) -> str:
    """리스크 수준 한글 번역"""
    translations = {
        "low": "낮음",
        "medium": "보통",
        "high": "높음",
        "critical": "매우 높음"
    }
    return translations.get(risk, risk)
```

---

### 메인 실행 메서드

#### execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]
```python
def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """에이전트 실행 메인 메서드"""

    # 초기 state 생성
    initial_state = {
        "checkpoint": "",
        "document_to_check": input_data.get("document", {}),
        "relevant_regulations": [],
        "violations": [],
        "compliance_score": 100.0,
        "report": ""
    }

    try:
        # 워크플로우 실행
        final_state = self.app.invoke(initial_state)

        # 결과 포맷팅
        result = {
            "success": True,
            "compliance_score": final_state.get("compliance_score", 100),
            "violations": final_state.get("violations", []),
            "report": final_state.get("report", ""),
            "status": final_state.get("compliance_status", "unknown"),
            "risk_level": final_state.get("risk_level", "unknown")
        }

    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        result = {
            "success": False,
            "error": str(e),
            "compliance_score": 0,
            "violations": [],
            "report": f"Error during compliance check: {str(e)}",
            "status": "error",
            "risk_level": "unknown"
        }

    return result
```

---

이 문서는 4개의 에이전트 파일에 대한 완전한 상세 문서입니다. 각 에이전트의 모든 클래스, 메서드, 노드, state, 그래프 구조를 포함하고 있습니다.