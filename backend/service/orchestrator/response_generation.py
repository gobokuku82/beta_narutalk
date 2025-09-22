class ResponseGenerationSubGraph:
    def __init__(self):
        self.workflow = StateGraph(ResponseState)
        self._build_graph()
    
    def _build_graph(self):
        self.workflow.add_node("format_selection", self.select_format)
        self.workflow.add_node("generate_text", self.generate_text_response)
        self.workflow.add_node("generate_table", self.generate_table_response)
        self.workflow.add_node("generate_chart", self.generate_chart_response)
        self.workflow.add_node("generate_document", self.generate_document_response)
        self.workflow.add_node("add_citations", self.add_references)
        self.workflow.add_node("final_review", self.final_quality_check)
        
        self.workflow.set_entry_point("format_selection")
        
        self.workflow.add_conditional_edges(
            "format_selection",
            self.route_by_format,
            {
                "text": "generate_text",
                "table": "generate_table", 
                "chart": "generate_chart",
                "document": "generate_document"
            }
        )
        
        # 모든 생성 노드는 citations로
        for node in ["generate_text", "generate_table", "generate_chart", "generate_document"]:
            self.workflow.add_edge(node, "add_citations")
        
        self.workflow.add_edge("add_citations", "final_review")
        self.workflow.add_edge("final_review", END)