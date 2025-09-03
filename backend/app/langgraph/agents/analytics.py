"""
Analytics Agent - 실적 및 거래처분석 에이전트
판매 데이터 분석, 거래처 프로파일링, Text2SQL
"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from loguru import logger
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

from app.langgraph.state import AgentState
from app.core.config import settings


class AnalyticsAgent:
    """실적 및 거래처 분석 전문 에이전트"""
    
    def __init__(self):
        # LLM 초기화 (Text2SQL용)
        self.llm = ChatOpenAI(
            model=settings.SQL_MODEL,
            temperature=0.0,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # 관계형 DB 경로
        self.db_path = settings.RELATION_DB_DIR / "sales.db"
        
        # DB 초기화
        self._initialize_database()
        
        # 도구 등록
        self.tools = {
            "analyze_sales": self.analyze_sales,
            "profile_customer": self.profile_customer,
            "predict_trend": self.predict_trend,
            "text_to_sql": self.text_to_sql,
            "generate_report": self.generate_analytics_report
        }
    
    def _initialize_database(self):
        """샘플 데이터베이스 생성"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    customer_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER,
                    amount REAL,
                    region VARCHAR(50)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    type VARCHAR(50),
                    region VARCHAR(50),
                    tier VARCHAR(20)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100),
                    category VARCHAR(50),
                    unit_price REAL
                )
            """)
            
            # 샘플 데이터 확인 및 삽입
            cursor.execute("SELECT COUNT(*) FROM customers")
            if cursor.fetchone()[0] == 0:
                self._insert_sample_data(cursor)
            
            conn.commit()
            conn.close()
            logger.info("분석 데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 초기화 오류: {e}")
    
    def _insert_sample_data(self, cursor):
        """샘플 데이터 삽입"""
        # 거래처 데이터
        customers = [
            (1, "서울대병원", "종합병원", "서울", "VIP"),
            (2, "연세세브란스병원", "종합병원", "서울", "VIP"),
            (3, "강남성심병원", "종합병원", "서울", "Premium"),
            (4, "부산대병원", "종합병원", "부산", "VIP"),
            (5, "김내과의원", "의원", "서울", "Standard"),
            (6, "박소아과", "의원", "경기", "Standard"),
            (7, "중앙약국", "약국", "서울", "Premium"),
            (8, "건강약국", "약국", "인천", "Standard")
        ]
        
        cursor.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
            customers
        )
        
        # 제품 데이터
        products = [
            (1, "혈압약A", "순환기계", 15000),
            (2, "당뇨약B", "내분비계", 25000),
            (3, "항생제C", "항감염제", 8000),
            (4, "진통제D", "신경계", 5000),
            (5, "위장약E", "소화기계", 12000)
        ]
        
        cursor.executemany(
            "INSERT INTO products VALUES (?, ?, ?, ?)",
            products
        )
        
        # 판매 데이터 (최근 3개월)
        import random
        from datetime import date
        
        sales_data = []
        start_date = date.today() - timedelta(days=90)
        
        for i in range(500):
            sale_date = start_date + timedelta(days=random.randint(0, 90))
            customer_id = random.randint(1, 8)
            product_id = random.randint(1, 5)
            quantity = random.randint(10, 200)
            
            # 제품 가격 조회
            price = products[product_id - 1][3]
            amount = quantity * price
            
            # 지역 조회
            region = customers[customer_id - 1][3]
            
            sales_data.append((
                None,  # id는 자동생성
                sale_date.isoformat(),
                customer_id,
                product_id,
                quantity,
                amount,
                region
            ))
        
        cursor.executemany(
            "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?)",
            sales_data
        )
        
        logger.info(f"샘플 데이터 삽입 완료: {len(sales_data)}개 판매 기록")
    
    async def text_to_sql(self, question: str) -> Dict:
        """자연어를 SQL로 변환"""
        try:
            # 스키마 정보
            schema = """
            Tables:
            1. sales (id, date, customer_id, product_id, quantity, amount, region)
            2. customers (id, name, type, region, tier)
            3. products (id, name, category, unit_price)
            """
            
            # SQL 생성
            prompt = f"""
            다음 질문을 SQL 쿼리로 변환하세요:
            
            질문: {question}
            
            데이터베이스 스키마:
            {schema}
            
            SQLite 문법을 사용하고, 쿼리만 반환하세요.
            """
            
            response = await self.llm.ainvoke(prompt)
            sql_query = response.content.strip()
            
            # SQL에서 불필요한 마크다운 제거
            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[1].split("```")[0].strip()
            
            # SQL 실행
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            conn.close()
            
            return {
                "query": sql_query,
                "columns": columns,
                "results": results,
                "row_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Text2SQL 오류: {e}")
            return {"error": str(e)}
    
    async def analyze_sales(self, period: str = "month") -> Dict:
        """판매 실적 분석"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 기간 설정
            if period == "month":
                days = 30
            elif period == "quarter":
                days = 90
            else:
                days = 365
            
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 총 매출
            query_total = f"""
                SELECT SUM(amount) as total_sales, COUNT(*) as transaction_count
                FROM sales
                WHERE date >= '{start_date}'
            """
            
            cursor = conn.cursor()
            cursor.execute(query_total)
            total_result = cursor.fetchone()
            
            # 제품별 매출
            query_product = f"""
                SELECT p.name, SUM(s.amount) as sales, SUM(s.quantity) as qty
                FROM sales s
                JOIN products p ON s.product_id = p.id
                WHERE s.date >= '{start_date}'
                GROUP BY p.id
                ORDER BY sales DESC
            """
            
            cursor.execute(query_product)
            product_results = cursor.fetchall()
            
            # 거래처별 매출
            query_customer = f"""
                SELECT c.name, c.type, SUM(s.amount) as sales
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                WHERE s.date >= '{start_date}'
                GROUP BY c.id
                ORDER BY sales DESC
                LIMIT 10
            """
            
            cursor.execute(query_customer)
            customer_results = cursor.fetchall()
            
            conn.close()
            
            return {
                "period": period,
                "total_sales": total_result[0] if total_result[0] else 0,
                "transaction_count": total_result[1] if total_result[1] else 0,
                "top_products": [
                    {"name": r[0], "sales": r[1], "quantity": r[2]}
                    for r in product_results
                ],
                "top_customers": [
                    {"name": r[0], "type": r[1], "sales": r[2]}
                    for r in customer_results
                ]
            }
            
        except Exception as e:
            logger.error(f"판매 분석 오류: {e}")
            return {"error": str(e)}
    
    async def profile_customer(self, customer_name: str) -> Dict:
        """거래처 프로파일링"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 거래처 정보
            cursor.execute(
                "SELECT * FROM customers WHERE name LIKE ?",
                (f"%{customer_name}%",)
            )
            customer_info = cursor.fetchone()
            
            if not customer_info:
                return {"error": "거래처를 찾을 수 없습니다."}
            
            customer_id = customer_info[0]
            
            # 구매 패턴 분석
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    MAX(date) as last_order
                FROM sales
                WHERE customer_id = ?
            """, (customer_id,))
            
            purchase_stats = cursor.fetchone()
            
            # 선호 제품
            cursor.execute("""
                SELECT p.name, SUM(s.quantity) as total_qty
                FROM sales s
                JOIN products p ON s.product_id = p.id
                WHERE s.customer_id = ?
                GROUP BY p.id
                ORDER BY total_qty DESC
                LIMIT 3
            """, (customer_id,))
            
            preferred_products = cursor.fetchall()
            
            conn.close()
            
            return {
                "customer_info": {
                    "name": customer_info[1],
                    "type": customer_info[2],
                    "region": customer_info[3],
                    "tier": customer_info[4]
                },
                "purchase_stats": {
                    "total_orders": purchase_stats[0],
                    "total_amount": purchase_stats[1],
                    "average_amount": purchase_stats[2],
                    "last_order": purchase_stats[3]
                },
                "preferred_products": [
                    {"name": p[0], "quantity": p[1]}
                    for p in preferred_products
                ]
            }
            
        except Exception as e:
            logger.error(f"거래처 프로파일링 오류: {e}")
            return {"error": str(e)}
    
    async def predict_trend(self, product_name: Optional[str] = None) -> Dict:
        """판매 트렌드 예측"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 월별 판매 추이
            if product_name:
                query = """
                    SELECT 
                        strftime('%Y-%m', date) as month,
                        SUM(amount) as sales
                    FROM sales s
                    JOIN products p ON s.product_id = p.id
                    WHERE p.name LIKE ?
                    GROUP BY month
                    ORDER BY month
                """
                df = pd.read_sql_query(query, conn, params=(f"%{product_name}%",))
            else:
                query = """
                    SELECT 
                        strftime('%Y-%m', date) as month,
                        SUM(amount) as sales
                    FROM sales
                    GROUP BY month
                    ORDER BY month
                """
                df = pd.read_sql_query(query, conn)
            
            conn.close()
            
            if df.empty:
                return {"error": "데이터가 없습니다."}
            
            # 간단한 트렌드 분석
            sales_list = df['sales'].tolist()
            
            # 성장률 계산
            if len(sales_list) > 1:
                growth_rate = ((sales_list[-1] - sales_list[0]) / sales_list[0]) * 100
            else:
                growth_rate = 0
            
            # 예측 (간단한 선형 예측)
            if len(sales_list) >= 2:
                trend = sales_list[-1] - sales_list[-2]
                next_month_prediction = sales_list[-1] + trend
            else:
                next_month_prediction = sales_list[-1] if sales_list else 0
            
            return {
                "product": product_name or "전체",
                "monthly_sales": df.to_dict('records'),
                "growth_rate": round(growth_rate, 2),
                "trend": "상승" if growth_rate > 0 else "하락",
                "next_month_prediction": round(next_month_prediction, 0)
            }
            
        except Exception as e:
            logger.error(f"트렌드 예측 오류: {e}")
            return {"error": str(e)}
    
    async def generate_analytics_report(self, params: Dict) -> str:
        """분석 리포트 생성"""
        sales_analysis = await self.analyze_sales(params.get("period", "month"))
        
        report = f"""
# 판매 분석 리포트

## 기간: 최근 {params.get("period", "month")}

### 📊 전체 실적
- 총 매출: {sales_analysis.get('total_sales', 0):,.0f}원
- 거래 건수: {sales_analysis.get('transaction_count', 0)}건

### 🏆 TOP 제품
"""
        
        for i, product in enumerate(sales_analysis.get('top_products', [])[:5], 1):
            report += f"{i}. {product['name']}: {product['sales']:,.0f}원\n"
        
        report += "\n### 🏥 주요 거래처\n"
        
        for i, customer in enumerate(sales_analysis.get('top_customers', [])[:5], 1):
            report += f"{i}. {customer['name']} ({customer['type']}): {customer['sales']:,.0f}원\n"
        
        return report
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """에이전트 처리 로직"""
        logger.info("분석 에이전트 처리 시작")
        
        # 최신 메시지 확인
        last_message = state["messages"][-1]
        user_query = last_message.get("content", "")
        
        # Text2SQL 시도
        sql_result = await self.text_to_sql(user_query)
        
        # 분석 수행
        sales_analysis = await self.analyze_sales("month")
        
        # 응답 생성
        response = "📊 **데이터 분석 결과**\n\n"
        
        if sql_result.get("results"):
            response += f"**쿼리 결과** ({sql_result['row_count']}건):\n"
            response += "```\n"
            
            # 헤더
            response += " | ".join(sql_result['columns']) + "\n"
            response += "-" * 50 + "\n"
            
            # 데이터 (최대 10행)
            for row in sql_result['results'][:10]:
                response += " | ".join(str(v) for v in row) + "\n"
            
            if sql_result['row_count'] > 10:
                response += f"\n... 외 {sql_result['row_count'] - 10}건\n"
            
            response += "```\n\n"
        
        # 요약 통계
        response += f"""
**월간 실적 요약**:
- 총 매출: {sales_analysis.get('total_sales', 0):,.0f}원
- 거래 건수: {sales_analysis.get('transaction_count', 0)}건

**TOP 3 제품**:
"""
        
        for i, product in enumerate(sales_analysis.get('top_products', [])[:3], 1):
            response += f"{i}. {product['name']}: {product['sales']:,.0f}원\n"
        
        return {
            "messages": [{"role": "assistant", "content": response}],
            "agent_outputs": {
                "analytics": {
                    "sql_result": sql_result,
                    "sales_analysis": sales_analysis
                }
            },
            "next_agent": None
        }