class SalesAnalyticsAgent:
    def __init__(self):
        self.workflow = StateGraph(SalesAnalyticsState)
        self._build_graph()
    
    def _build_graph(self):
        self.workflow.add_node("parse_query", self.parse_sales_query)
        self.workflow.add_node("generate_sql", self.text_to_sql)
        self.workflow.add_node("execute_query", self.execute_sql_query)
        self.workflow.add_node("analyze_data", self.perform_analysis)
        self.workflow.add_node("visualize", self.create_visualization)
        
        self.workflow.set_entry_point("parse_query")
        self.workflow.add_edge("parse_query", "generate_sql")
        self.workflow.add_edge("generate_sql", "execute_query")
        self.workflow.add_edge("execute_query", "analyze_data")
        
        self.workflow.add_conditional_edges(
            "analyze_data",
            self.check_visualization_need,
            {
                "need_viz": "visualize",
                "text_only": END
            }
        )
        self.workflow.add_edge("visualize", END)
    
    async def text_to_sql(self, state):
        """Text2SQL 변환"""
        schema_info = self.load_schema_info()
        prompt = f"""
        스키마 정보:
        - clients_db: 거래처 기본 정보
        - clients_info: 거래처 상세 정보
        - sales_performance_db: 실적 데이터
        - sales_target_db: 목표 데이터
        
        사용자 요청: {state['query']}
        SQL 쿼리 생성:
        """
        # GPT-4 호출하여 SQL 생성
        return state