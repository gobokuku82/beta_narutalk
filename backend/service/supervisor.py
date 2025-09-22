# 메인 실행 코드
async def main():
    # 초기화
    orchestrator = MainOrchestrator()
    app = orchestrator.workflow.compile(
        checkpointer=orchestrator.checkpointer
    )
    
    # 실행 예시
    user_input = {
        "user_id": "pharm_user_001",
        "session_id": "session_123",
        "user_query": "지난 분기 서울 지역 거래처별 매출 실적을 분석하고 규정 위반 사항이 있는지 검토해줘",
        "timestamp": datetime.now().isoformat()
    }
    
    # 스트리밍 실행
    async for event in app.astream(
        user_input,
        config={"configurable": {"thread_id": "thread_123"}},
        stream_mode="values"
    ):
        print(f"Current State: {event}")
        
    # 최종 결과
    final_state = await app.aget_state(
        config={"configurable": {"thread_id": "thread_123"}}
    )
    
    return final_state.values